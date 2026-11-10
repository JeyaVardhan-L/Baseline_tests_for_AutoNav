"""
LiDAR-only scan-to-scan odometry baseline (point-to-point ICP).

Frame conventions (these matter; they are verified in tests/unit/test_pose_math.py):

  * Scan k is expressed in the sensor frame S_k.
  * ICP registers a SOURCE cloud (scan k, in S_k) onto a TARGET cloud (scan k-1, in S_{k-1}).
    The returned 4x4 matrix T maps source points into the target frame:  p_{k-1} = T @ p_k.
    Therefore T = T_{k-1}^{k}, the pose of S_k expressed in S_{k-1}.
  * The world pose of the sensor accumulates as  W_k = W_{k-1} @ T.
    (Not inv(T): that would run the trajectory backwards.)

Registration validity gate:
  ICP "success" only means the solver ran. A registration is ACCEPTED only if it also passes
  RegistrationGate (inlier ratio, residual, motion plausibility). Rejected registrations leave the
  pose and the reference scan unchanged and are counted, never silently accepted.

Known limitations of this baseline: no loop closure or map (drift is unbounded), no motion prior,
no deskewing, point-to-point error metric only.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any, List, Callable
import time
import numpy as np
from scipy.spatial import cKDTree

from autonav_baseline.lidar.filtering import remove_invalid_points, filter_by_range, voxel_downsample


@dataclass
class ICPResult:
    """Result of registering a single pair of point clouds."""
    success: bool               # solver ran to a result (NOT a validity verdict; see RegistrationGate)
    transformation: np.ndarray  # 4x4 T with p_target = T @ p_source
    rotation: np.ndarray        # 3x3
    translation: np.ndarray     # 3-vector, meters
    fitness_score: float        # mean Euclidean residual of inliers at the start of the last iteration (m)
    inlier_ratio: float         # inliers / source points
    num_inliers: int
    iterations: int
    status: str                 # CONVERGED, MAX_ITERATIONS, INSUFFICIENT_POINTS, DEGENERATE_MATCHES_UNDER_THRESHOLD
    residual_history: List[float] = field(default_factory=list)  # mean inlier residual per iteration (m)


@dataclass
class RegistrationGate:
    """
    Thresholds that turn an ICP result into an accepted / rejected registration.

    The values are fixed a priori from sensor physics (a walking sensor moves about 0.1 m between
    10 Hz scans) and were NOT tuned against ground-truth error. They are recorded in run.json.
    """
    min_inlier_ratio: float = 0.30
    max_mean_residual_m: float = 0.25
    max_step_translation_m: float = 1.0
    max_step_rotation_deg: float = 20.0

    def check(self, icp: ICPResult) -> Tuple[bool, str]:
        if not icp.success:
            return False, f"icp_failed:{icp.status}"
        if icp.inlier_ratio < self.min_inlier_ratio:
            return False, "low_inlier_ratio"
        if icp.fitness_score > self.max_mean_residual_m:
            return False, "high_residual"
        step = float(np.linalg.norm(icp.translation))
        if step > self.max_step_translation_m:
            return False, "implausible_translation"
        if rotation_angle_deg(icp.rotation) > self.max_step_rotation_deg:
            return False, "implausible_rotation"
        return True, "accepted"

    def to_dict(self) -> Dict[str, float]:
        return {
            "min_inlier_ratio": self.min_inlier_ratio,
            "max_mean_residual_m": self.max_mean_residual_m,
            "max_step_translation_m": self.max_step_translation_m,
            "max_step_rotation_deg": self.max_step_rotation_deg,
        }


@dataclass
class OdometryStepResult:
    """Result of processing one frame in the odometry sequence."""
    frame_index: int
    timestamp: Optional[float]
    success: bool               # True if the frame is the initial frame or its registration was ACCEPTED
    pose_4x4: np.ndarray        # world pose of the sensor after this frame
    position_xyz: np.ndarray
    step_translation_m: float   # accepted motion since the reference scan (0 if rejected)
    registration_latency_ms: float  # total processing time of this frame (preprocess + register); excludes file I/O
    raw_points_count: int
    downsampled_points_count: int
    fitness_score: float
    inlier_ratio: float
    status: str
    # --- fields added for the measurement harness ---
    accepted: bool = True
    reject_reason: str = ""
    preprocess_ms: float = 0.0
    register_ms: float = 0.0
    icp_iterations: int = 0
    num_inliers: int = 0
    points_after_valid: int = 0
    points_after_range: int = 0
    step_rotation_deg: float = 0.0
    residual_history: List[float] = field(default_factory=list)


def rotation_angle_deg(rotation: np.ndarray) -> float:
    """Rotation angle of a 3x3 rotation matrix in degrees (axis-angle magnitude)."""
    cos_theta = (float(np.trace(rotation)) - 1.0) / 2.0
    return float(np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0))))


def compute_best_rigid_transform(source: np.ndarray, target: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Optimal rigid transform [R, t] aligning source to target (Kabsch/Umeyama via SVD).
    Minimizes sum(||target_i - (R * source_i + t)||^2).
    """
    assert len(source) == len(target) and len(source) >= 3

    centroid_source = np.mean(source, axis=0)
    centroid_target = np.mean(target, axis=0)

    p = source - centroid_source
    q = target - centroid_target

    h = p.T @ q
    u, _, vt = np.linalg.svd(h)
    r = vt.T @ u.T

    if np.linalg.det(r) < 0:  # reflection -> proper rotation
        vt[-1, :] *= -1
        r = vt.T @ u.T

    t = centroid_target - r @ centroid_source
    return r, t


def _compose(r: np.ndarray, t: np.ndarray) -> np.ndarray:
    m = np.eye(4, dtype=np.float64)
    m[:3, :3] = r
    m[:3, 3] = t
    return m


def icp_point_to_point(
    source_points: np.ndarray,
    target_points: np.ndarray,
    max_correspondence_distance: float = 1.5,
    max_iterations: int = 30,
    tolerance: float = 1e-4,
    initial_transform: Optional[np.ndarray] = None,
    min_inliers: int = 20,
    target_tree: Optional[cKDTree] = None,
) -> ICPResult:
    """
    Point-to-point ICP using NumPy and SciPy cKDTree.

    Args:
        source_points: (M, 3) moving scan.
        target_points: (N, 3) fixed reference scan.
        max_correspondence_distance: correspondences farther than this (meters) are ignored.
        max_iterations: iteration cap.
        tolerance: converged when the update translation norm, or the change in mean residual, is below this (m).
        initial_transform: optional 4x4 initial guess for T (source -> target).
        min_inliers: fewer matched points than this aborts the registration.
        target_tree: optional pre-built KD-tree of target_points (avoids rebuilding).

    Returns:
        ICPResult. `transformation` maps source points into the target frame.
    """
    if len(source_points) < min_inliers or len(target_points) < min_inliers:
        return ICPResult(
            success=False,
            transformation=np.eye(4, dtype=np.float64),
            rotation=np.eye(3, dtype=np.float64),
            translation=np.zeros(3, dtype=np.float64),
            fitness_score=float("inf"),
            inlier_ratio=0.0,
            num_inliers=0,
            iterations=0,
            status="INSUFFICIENT_POINTS",
        )

    start_t = np.eye(4, dtype=np.float64) if initial_transform is None else np.array(initial_transform, dtype=np.float64)
    r_accum = start_t[:3, :3].copy()
    t_accum = start_t[:3, 3].copy()

    tree = target_tree if target_tree is not None else cKDTree(target_points)

    num_source = len(source_points)
    src_pts = np.asarray(source_points, dtype=np.float64)
    target_pts = np.asarray(target_points)

    prev_error = float("inf")
    converged = False
    iterations_run = 0
    final_inliers = 0
    final_error = float("inf")
    history: List[float] = []

    for it in range(max_iterations):
        iterations_run = it + 1

        transformed_src = src_pts @ r_accum.T + t_accum
        distances, indices = tree.query(transformed_src, k=1, workers=1)

        inlier_mask = distances <= max_correspondence_distance
        num_inliers = int(np.count_nonzero(inlier_mask))
        final_inliers = num_inliers

        if num_inliers < min_inliers:
            return ICPResult(
                success=False,
                transformation=_compose(r_accum, t_accum),
                rotation=r_accum,
                translation=t_accum,
                fitness_score=float("inf"),
                inlier_ratio=num_inliers / num_source,
                num_inliers=num_inliers,
                iterations=iterations_run,
                status="DEGENERATE_MATCHES_UNDER_THRESHOLD",
                residual_history=history,
            )

        matched_src = transformed_src[inlier_mask]
        matched_tgt = target_pts[indices[inlier_mask]]

        mean_error = float(np.mean(distances[inlier_mask]))
        final_error = mean_error
        history.append(mean_error)

        delta_r, delta_t = compute_best_rigid_transform(matched_src, matched_tgt)

        # T_new = delta_T @ T_current
        r_accum = delta_r @ r_accum
        t_accum = delta_r @ t_accum + delta_t

        trans_delta_norm = float(np.linalg.norm(delta_t))
        if trans_delta_norm < tolerance or abs(prev_error - mean_error) < tolerance:
            converged = True
            break

        prev_error = mean_error

    return ICPResult(
        success=True,
        transformation=_compose(r_accum, t_accum),
        rotation=r_accum,
        translation=t_accum,
        fitness_score=final_error,
        inlier_ratio=final_inliers / max(num_source, 1),
        num_inliers=final_inliers,
        iterations=iterations_run,
        status="CONVERGED" if converged else "MAX_ITERATIONS",
        residual_history=history,
    )


def _distribution(samples: List[float]) -> Dict[str, float]:
    if not samples:
        return {k: 0.0 for k in ("mean", "p50", "p90", "p95", "p99", "max")}
    a = np.asarray(samples, dtype=np.float64)
    p = np.percentile(a, [50, 90, 95, 99])
    return {"mean": float(a.mean()), "p50": float(p[0]), "p90": float(p[1]),
            "p95": float(p[2]), "p99": float(p[3]), "max": float(a.max())}


class ICPOdometry:
    """Sequential scan-to-scan odometry. Accumulates accepted relative transforms."""

    def __init__(
        self,
        voxel_size: float = 0.15,
        min_range: float = 0.5,
        max_range: float = 50.0,
        max_correspondence_distance: float = 1.5,
        max_iterations: int = 30,
        tolerance: float = 1e-4,
        gate: Optional[RegistrationGate] = None,
        voxel_fn: Callable = voxel_downsample,
    ):
        self.voxel_size = voxel_size
        self.min_range = min_range
        self.max_range = max_range
        self.max_correspondence_distance = max_correspondence_distance
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.gate = gate or RegistrationGate()
        self.voxel_fn = voxel_fn

        self.current_pose = np.eye(4, dtype=np.float64)
        self.previous_points: Optional[np.ndarray] = None
        self.step_history: List[OdometryStepResult] = []
        self.successful_steps = 0   # accepted registrations
        self.failed_steps = 0       # rejected registrations (ICP failure or gate rejection)
        self.reject_counts: Dict[str, int] = {}

    def preprocess_points(self, raw_points: np.ndarray) -> np.ndarray:
        """Filters non-finite points, bounds ranges, and applies voxel downsampling."""
        return self._preprocess(raw_points)[0]

    def _preprocess(self, raw_points: np.ndarray) -> Tuple[np.ndarray, int, int]:
        """Returns (points, count_after_valid, count_after_range)."""
        clean_pts, _ = remove_invalid_points(raw_points)
        n_valid = len(clean_pts)
        if n_valid == 0:
            return clean_pts, 0, 0
        range_pts, _ = filter_by_range(clean_pts, min_range=self.min_range, max_range=self.max_range)
        n_range = len(range_pts)
        if n_range == 0 or self.voxel_size <= 0:
            return range_pts, n_valid, n_range
        downsampled, _ = self.voxel_fn(range_pts, voxel_size=self.voxel_size)
        return downsampled, n_valid, n_range

    def _register(self, pts: np.ndarray) -> ICPResult:
        """Registration step; variants override this."""
        return icp_point_to_point(
            source_points=pts,
            target_points=self.previous_points,
            max_correspondence_distance=self.max_correspondence_distance,
            max_iterations=self.max_iterations,
            tolerance=self.tolerance,
        )

    def process_frame(
        self,
        raw_points: np.ndarray,
        frame_index: int,
        timestamp: Optional[float] = None,
    ) -> OdometryStepResult:
        """Processes one incoming point cloud frame and updates the estimated pose."""
        raw_count = len(raw_points)
        t_start = time.perf_counter()

        pts, n_valid, n_range = self._preprocess(raw_points)
        t_pre = time.perf_counter()
        preprocess_ms = (t_pre - t_start) * 1000.0
        downsampled_count = len(pts)

        # Initial frame (reference only; no registration is performed)
        if self.previous_points is None:
            empty = len(pts) == 0
            if not empty:
                self.previous_points = pts
            total_ms = (time.perf_counter() - t_start) * 1000.0
            res = OdometryStepResult(
                frame_index=frame_index, timestamp=timestamp, success=not empty,
                pose_4x4=self.current_pose.copy(), position_xyz=self.current_pose[:3, 3].copy(),
                step_translation_m=0.0, registration_latency_ms=total_ms,
                raw_points_count=raw_count, downsampled_points_count=downsampled_count,
                fitness_score=0.0, inlier_ratio=1.0,
                status="INITIAL_FRAME_EMPTY" if empty else "INITIAL_FRAME",
                accepted=not empty, reject_reason="empty_initial_frame" if empty else "",
                preprocess_ms=preprocess_ms, register_ms=0.0,
                points_after_valid=n_valid, points_after_range=n_range,
            )
            self.step_history.append(res)
            return res

        icp_res = self._register(pts)
        accepted, reason = self.gate.check(icp_res)

        step_dist = 0.0
        step_rot = 0.0
        if accepted:
            # icp_res.transformation = T_{prev}^{curr}; world_curr = world_prev @ T
            self.current_pose = self.current_pose @ icp_res.transformation
            step_dist = float(np.linalg.norm(icp_res.translation))
            step_rot = rotation_angle_deg(icp_res.rotation)
            self.previous_points = pts
            self.successful_steps += 1
        else:
            self.failed_steps += 1
            self.reject_counts[reason] = self.reject_counts.get(reason, 0) + 1

        t_end = time.perf_counter()
        step_res = OdometryStepResult(
            frame_index=frame_index, timestamp=timestamp, success=accepted,
            pose_4x4=self.current_pose.copy(), position_xyz=self.current_pose[:3, 3].copy(),
            step_translation_m=step_dist, registration_latency_ms=(t_end - t_start) * 1000.0,
            raw_points_count=raw_count, downsampled_points_count=downsampled_count,
            fitness_score=icp_res.fitness_score, inlier_ratio=icp_res.inlier_ratio,
            status=icp_res.status, accepted=accepted, reject_reason="" if accepted else reason,
            preprocess_ms=preprocess_ms, register_ms=(t_end - t_pre) * 1000.0,
            icp_iterations=icp_res.iterations, num_inliers=icp_res.num_inliers,
            points_after_valid=n_valid, points_after_range=n_range,
            step_rotation_deg=step_rot, residual_history=list(icp_res.residual_history),
        )
        self.step_history.append(step_res)
        return step_res

    def get_trajectory_positions(self) -> np.ndarray:
        """(K, 3) estimated sensor positions in the world frame (world = first sensor frame)."""
        if not self.step_history:
            return np.zeros((0, 3), dtype=np.float64)
        return np.array([s.position_xyz for s in self.step_history], dtype=np.float64)

    def get_trajectory_poses(self) -> np.ndarray:
        """(K, 4, 4) estimated sensor poses in the world frame."""
        if not self.step_history:
            return np.zeros((0, 4, 4), dtype=np.float64)
        return np.array([s.pose_4x4 for s in self.step_history], dtype=np.float64)

    def get_total_path_length_m(self) -> float:
        return float(sum(s.step_translation_m for s in self.step_history))

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Aggregate odometry metrics. Latency statistics EXCLUDE the initial frame (it performs no
        registration). The success rate is accepted registrations / registration attempts.
        """
        total_frames = len(self.step_history)
        init_frames = 1 if total_frames else 0
        attempts = max(0, total_frames - init_frames)
        reg_steps = self.step_history[init_frames:]
        latencies = [s.registration_latency_ms for s in reg_steps]
        dist = _distribution(latencies)
        success_rate = round(self.successful_steps / attempts * 100.0, 1) if attempts > 0 else 100.0

        return {
            "total_frames_processed": total_frames,
            "initialization_frames": init_frames,
            "registration_attempts": attempts,
            "successful_registrations": self.successful_steps,
            "failed_registrations": self.failed_steps,
            "rejected_registrations": dict(self.reject_counts),
            "success_rate_percent": success_rate,
            "total_path_length_m": round(self.get_total_path_length_m(), 3),
            "final_position_xyz": [round(c, 3) for c in self.current_pose[:3, 3].tolist()],
            "latency_mean_ms": round(dist["mean"], 2),
            "latency_median_ms": round(dist["p50"], 2),
            "latency_p90_ms": round(dist["p90"], 2),
            "latency_p95_ms": round(dist["p95"], 2),
            "latency_p99_ms": round(dist["p99"], 2),
            "latency_max_ms": round(dist["max"], 2),
            "gate": self.gate.to_dict(),
        }
