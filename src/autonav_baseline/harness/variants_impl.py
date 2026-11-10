"""
Implementations of the `optimized` and `p2plane` variants (selected through harness/variants.py).

optimized  Same algorithm as baseline (same filters, same point-to-point ICP, same convergence rule, same
           validity gate). Implementation speedups only: packed-key voxel filter, one-pass validity+range
           mask, cached KD-tree (default settings; see DEC-019), KD-tree queries spread over the CPUs the
           process may use. Accuracy must match baseline within tolerance (checked in tests and in the
           published comparison).

p2plane    Point-to-plane ICP with a constant-velocity initial guess (the last accepted relative motion).
           Preprocessing is identical to baseline on purpose, so differences in register_ms are caused by
           the registration algorithm and not by implementation tuning. Target normals are computed once per
           reference scan inside the registration step and are part of its measured cost.
"""

import os
from typing import Optional

import numpy as np
from scipy.spatial import cKDTree

from autonav_baseline.lidar.fast_voxel import voxel_downsample_fast
from autonav_baseline.lidar.odometry import ICPOdometry, ICPResult, icp_point_to_point
from autonav_baseline.lidar.registration_p2plane import estimate_normals, icp_point_to_plane


def _usable_cpus() -> int:
    try:
        import psutil
        return max(1, len(psutil.Process().cpu_affinity()))
    except Exception:
        return os.cpu_count() or 1


class OptimizedOdometry(ICPOdometry):
    def __init__(self, **params):
        super().__init__(voxel_fn=voxel_downsample_fast, **params)
        self._workers = _usable_cpus()
        self._tree_for = None
        self._tree: Optional[cKDTree] = None

    def _preprocess(self, raw_points):
        xyz = raw_points[:, :3]
        r2 = np.einsum("ij,ij->i", xyz, xyz)
        finite = np.isfinite(r2)
        n_valid = int(np.count_nonzero(finite))
        with np.errstate(invalid="ignore"):
            keep = (r2 >= self.min_range ** 2) & (r2 <= self.max_range ** 2)
        n_range = int(np.count_nonzero(keep))
        rng = xyz[keep]
        if n_range == 0 or self.voxel_size <= 0:
            return rng, n_valid, n_range
        return voxel_downsample_fast(rng, self.voxel_size)[0], n_valid, n_range

    def _register(self, pts) -> ICPResult:
        if self._tree_for is not self.previous_points:
            self._tree = cKDTree(self.previous_points)  # default (balanced) tree: see DEC-019
            self._tree_for = self.previous_points
        return icp_point_to_point(
            pts, self.previous_points, self.max_correspondence_distance, self.max_iterations, self.tolerance,
            target_tree=self._tree, workers=self._workers,
        )


class P2PlaneOdometry(ICPOdometry):
    def __init__(self, normals_k: int = 10, **params):
        super().__init__(**params)
        self.normals_k = normals_k
        self._ref_for = None
        self._tree: Optional[cKDTree] = None
        self._normals = None
        self._last_rel = np.eye(4)
        self._pending: Optional[ICPResult] = None
        self.last_condition = float("nan")

    def _register(self, pts) -> ICPResult:
        if self._ref_for is not self.previous_points:
            self._tree = cKDTree(self.previous_points)
            self._normals = estimate_normals(self.previous_points, self._tree, self.normals_k)
            self._ref_for = self.previous_points
        res, cond = icp_point_to_plane(
            pts, self.previous_points, self._normals, self._tree, self.max_correspondence_distance,
            self.max_iterations, self.tolerance, initial_transform=self._last_rel,
        )
        self.last_condition = cond
        self._pending = res
        return res

    def process_frame(self, raw_points, frame_index, timestamp=None):
        self._pending = None
        step = super().process_frame(raw_points, frame_index, timestamp)
        if self._pending is not None:
            # constant-velocity guess: next frame starts from the last accepted motion; reset on rejection
            self._last_rel = self._pending.transformation.copy() if step.accepted else np.eye(4)
        return step