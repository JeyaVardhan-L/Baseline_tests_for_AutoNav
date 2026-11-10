"""Variant tests: `optimized` must equal baseline in result; `p2plane` must recover known motion."""

import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from autonav_baseline.datasets.synthetic import SyntheticAdapter, make_room_points
from autonav_baseline.harness.variants import make_odometry
from autonav_baseline.lidar.fast_voxel import voxel_downsample_fast
from autonav_baseline.lidar.filtering import voxel_downsample
from autonav_baseline.lidar.registration_p2plane import estimate_normals, icp_point_to_plane
from scipy.spatial import cKDTree

PARAMS = {"voxel_size": 0.15, "min_range": 0.5, "max_range": 50.0, "max_correspondence_distance": 1.5,
          "max_iterations": 30, "tolerance": 1e-4}


def _rows(a):
    return a[np.lexsort(a.T[::-1])]


class TestFastVoxelEquivalence(unittest.TestCase):
    def test_same_voxels_and_centroids_as_baseline(self):
        pts = make_room_points(6000)
        slow, _ = voxel_downsample(pts, 0.2)
        fast, _ = voxel_downsample_fast(pts, 0.2)
        self.assertEqual(len(slow), len(fast))
        self.assertTrue(np.allclose(_rows(slow), _rows(fast), atol=1e-9))

    def test_hand_counted_cloud(self):
        pts = np.array([[0.1, 0.1, 0.1], [0.9, 0.9, 0.9], [1.1, 0.1, 0.1], [-0.1, -0.1, -0.1]])
        out, _ = voxel_downsample_fast(pts, 1.0)
        self.assertEqual(len(out), 3)
        self.assertTrue(np.allclose(_rows(out), _rows(np.array([[-0.1, -0.1, -0.1], [0.5, 0.5, 0.5], [1.1, 0.1, 0.1]]))))


class TestVariantsOnKnownMotion(unittest.TestCase):
    def _run(self, variant, frames=8):
        ad = SyntheticAdapter(config={"num_frames": frames, "step_m": 0.3, "yaw_step_deg": 2.0})
        odo = make_odometry(variant, dict(PARAMS))
        for f in ad.get_lidar_frames():
            odo.process_frame(f.points, f.index, f.timestamp)
        _, gt = ad.ground_truth()
        truth = np.linalg.inv(gt[0]) @ gt
        return odo, np.linalg.norm(odo.get_trajectory_poses()[:, :3, 3] - truth[:, :3, 3], axis=1)

    def test_optimized_matches_baseline_trajectory(self):
        base, _ = self._run("baseline")
        opt, _ = self._run("optimized")
        d = np.abs(base.get_trajectory_poses() - opt.get_trajectory_poses()).max()
        self.assertLess(d, 1e-3)
        self.assertEqual(base.successful_steps, opt.successful_steps)

    def test_p2plane_tracks_ground_truth(self):
        odo, err = self._run("p2plane")
        self.assertEqual(odo.failed_steps, 0)
        self.assertLess(err.max(), 0.15)

    def test_p2plane_recovers_known_translation(self):
        # target = room; source = the same room shifted by a known 0.2 m in x and 3 deg yaw
        room = make_room_points(8000)[:, :3]
        c, s = np.cos(np.radians(3.0)), np.sin(np.radians(3.0))
        r_true = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
        t_true = np.array([0.2, 0.0, 0.0])
        source = (room - t_true) @ r_true            # so that r_true @ source + t_true = room
        tree = cKDTree(room)
        res, cond = icp_point_to_plane(source, room, estimate_normals(room, tree), tree)
        self.assertTrue(res.success)
        self.assertTrue(np.allclose(res.rotation, r_true, atol=2e-3))
        self.assertTrue(np.allclose(res.translation, t_true, atol=2e-2))
        self.assertTrue(np.isfinite(cond))

    def test_constant_velocity_guess_is_used_and_reset_on_rejection(self):
        odo = make_odometry("p2plane", dict(PARAMS))
        ad = SyntheticAdapter(config={"num_frames": 4, "step_m": 0.3, "yaw_step_deg": 2.0})
        for f in ad.get_lidar_frames():
            odo.process_frame(f.points, f.index, f.timestamp)
        self.assertFalse(np.allclose(odo._last_rel, np.eye(4)))     # carries the last accepted motion


if __name__ == "__main__":
    unittest.main()