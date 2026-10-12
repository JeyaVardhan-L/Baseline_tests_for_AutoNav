"""
Unit tests for LiDAR-only ICP odometry baseline.
"""

import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from autonav_baseline.lidar.odometry import (
    compute_best_rigid_transform,
    icp_point_to_point,
    ICPOdometry,
)


class TestICPOdometry(unittest.TestCase):
    def setUp(self):
        # Create a simple synthetic 3D box surface (100 points)
        rng = np.random.default_rng(42)
        n = 100
        x = rng.uniform(-5.0, 5.0, size=n)
        y = rng.uniform(-5.0, 5.0, size=n)
        z = rng.uniform(-1.0, 1.0, size=n)
        self.box_points = np.column_stack([x, y, z]).astype(np.float32)

    def test_rigid_transform_translation_only(self):
        source = self.box_points
        true_t = np.array([0.3, -0.2, 0.1], dtype=np.float64)
        target = source + true_t

        r, t = compute_best_rigid_transform(source, target)
        self.assertTrue(np.allclose(r, np.eye(3), atol=1e-5))
        self.assertTrue(np.allclose(t, true_t, atol=1e-5))

    def test_rigid_transform_rotation_and_translation(self):
        source = self.box_points
        # 10 degree yaw rotation around Z
        theta = np.radians(10.0)
        true_r = np.array([
            [np.cos(theta), -np.sin(theta), 0.0],
            [np.sin(theta),  np.cos(theta), 0.0],
            [0.0,            0.0,           1.0],
        ])
        true_t = np.array([0.5, 0.2, -0.1])
        target = (true_r @ source.T).T + true_t

        r, t = compute_best_rigid_transform(source, target)
        self.assertTrue(np.allclose(r, true_r, atol=1e-5))
        self.assertTrue(np.allclose(t, true_t, atol=1e-5))

    def test_icp_converges_on_small_motion(self):
        source = self.box_points
        # Shift target by small delta
        delta_t = np.array([0.15, -0.10, 0.05])
        target = source + delta_t

        result = icp_point_to_point(
            source_points=source,
            target_points=target,
            max_correspondence_distance=1.0,
            max_iterations=25,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.status, "CONVERGED")
        self.assertLess(result.fitness_score, 1e-3)
        self.assertTrue(np.allclose(result.translation, delta_t, atol=1e-2))

    def test_icp_handles_insufficient_points(self):
        sparse = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], dtype=np.float32)
        result = icp_point_to_point(sparse, sparse, min_inliers=10)
        self.assertFalse(result.success)
        self.assertEqual(result.status, "INSUFFICIENT_POINTS")

    def test_odometry_sequential_pipeline(self):
        odom = ICPOdometry(voxel_size=0.10, max_correspondence_distance=1.5)

        # Frame 0: base scan
        f0 = odom.process_frame(self.box_points, frame_index=0, timestamp=0.0)
        self.assertTrue(f0.success)
        self.assertEqual(f0.step_translation_m, 0.0)

        # Frame 1: shifted by 0.2m along X
        pts_f1 = self.box_points + np.array([0.2, 0.0, 0.0], dtype=np.float32)
        f1 = odom.process_frame(pts_f1, frame_index=1, timestamp=0.1)
        self.assertTrue(f1.success)
        self.assertAlmostEqual(f1.step_translation_m, 0.2, places=1)

        # Frame 2: shifted by another 0.2m along X
        pts_f2 = pts_f1 + np.array([0.2, 0.0, 0.0], dtype=np.float32)
        f2 = odom.process_frame(pts_f2, frame_index=2, timestamp=0.2)
        self.assertTrue(f2.success)

        summary = odom.get_summary_statistics()
        self.assertEqual(summary["total_frames_processed"], 3)
        self.assertEqual(summary["registration_attempts"], 2)
        self.assertEqual(summary["successful_registrations"], 2)
        self.assertGreater(summary["total_path_length_m"], 0.3)
        self.assertGreater(summary["latency_mean_ms"], 0.0)


if __name__ == "__main__":
    unittest.main()
