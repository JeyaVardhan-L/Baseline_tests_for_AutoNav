"""
Phase 0 correctness tests: pose conventions, voxel filter, registration gate, ATE/RPE.

Expected values come from closed-form maths written in this file (hand-built rotation matrices,
a hand-counted voxel example, known synthetic drift), NOT from re-running the implementation.
"""

import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from autonav_baseline.datasets.synthetic import SyntheticAdapter
from autonav_baseline.lidar.filtering import voxel_downsample
from autonav_baseline.lidar.odometry import ICPOdometry, ICPResult, RegistrationGate, rotation_angle_deg
from autonav_baseline.metrics.trajectory_evaluation import (
    align_umeyama_rigid,
    associate_by_time,
    evaluate_trajectory,
    poses_from_xyz_quat,
    quat_xyzw_to_rotation,
)


def rz(deg):
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def rx(deg):
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    return np.array([[1.0, 0, 0], [0, c, -s], [0, s, c]])


def yaw_of(rot):
    return np.degrees(np.arctan2(rot[1, 0], rot[0, 0]))


class TestQuaternions(unittest.TestCase):
    def test_yaw_90_maps_x_to_y(self):
        s = np.sqrt(0.5)
        r = quat_xyzw_to_rotation(np.array([[0.0, 0.0, s, s]]))[0]
        expected = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
        self.assertTrue(np.allclose(r, expected, atol=1e-12))

    def test_roll_90_maps_y_to_z(self):
        s = np.sqrt(0.5)
        r = quat_xyzw_to_rotation(np.array([[s, 0.0, 0.0, s]]))[0]
        self.assertTrue(np.allclose(r @ np.array([0.0, 1.0, 0.0]), [0.0, 0.0, 1.0], atol=1e-12))

    def test_identity(self):
        self.assertTrue(np.allclose(quat_xyzw_to_rotation(np.array([[0, 0, 0, 1.0]]))[0], np.eye(3)))


class TestPoseComposition(unittest.TestCase):
    """The sensor moves through a known room; the estimate must follow it in the right direction."""

    def _run(self, frames, step, yaw_step):
        adapter = SyntheticAdapter(config={"num_frames": frames, "step_m": step, "yaw_step_deg": yaw_step})
        odom = ICPOdometry(voxel_size=0.1, max_correspondence_distance=1.5)
        for f in adapter.get_lidar_frames():
            odom.process_frame(f.points, f.index, f.timestamp)
        _, gt = adapter.ground_truth()
        return odom, gt

    def test_forward_motion_has_positive_x_and_known_yaw(self):
        # Sensor advances 0.3 m forward while turning 3 deg. In frame-0 coordinates that is
        # translation (0.3, 0, 0) and a 3 deg yaw. The old implementation returned x = -0.3.
        odom, _ = self._run(2, 0.3, 3.0)
        pose = odom.get_trajectory_poses()[1]
        self.assertAlmostEqual(pose[0, 3], 0.3, delta=0.03)
        self.assertAlmostEqual(pose[1, 3], 0.0, delta=0.03)
        self.assertAlmostEqual(yaw_of(pose[:3, :3]), 3.0, delta=0.5)

    def test_chain_matches_ground_truth_and_is_order_sensitive(self):
        odom, gt = self._run(10, 0.3, 2.0)
        est = odom.get_trajectory_poses()
        truth = np.linalg.inv(gt[0]) @ gt            # sensor pose relative to the first frame
        err = np.linalg.norm(est[:, :3, 3] - truth[:, :3, 3], axis=1)
        self.assertLess(err.max(), 0.15)
        self.assertAlmostEqual(yaw_of(est[-1, :3, :3]), 18.0, delta=1.5)

        # Sensitivity check: replaying the OLD bug (pose @ inv(T) for each accepted step) must land
        # far from the truth, so this test genuinely distinguishes the two conventions.
        rel = [np.linalg.inv(est[k - 1]) @ est[k] for k in range(1, len(est))]
        buggy = np.eye(4)
        for t in rel:
            buggy = buggy @ np.linalg.inv(t)
        self.assertGreater(np.linalg.norm(buggy[:3, 3] - truth[-1, :3, 3]), 3.0)

    def test_rotation_angle_helper(self):
        self.assertAlmostEqual(rotation_angle_deg(rz(25.0)), 25.0, places=9)
        self.assertAlmostEqual(rotation_angle_deg(rx(-40.0)), 40.0, places=9)


class TestVoxelKnownAnswer(unittest.TestCase):
    def test_counts_and_centroids_on_hand_counted_cloud(self):
        pts = np.array([
            [0.1, 0.1, 0.1], [0.9, 0.9, 0.9],      # voxel (0,0,0) -> centroid (0.5,0.5,0.5)
            [1.1, 0.1, 0.1], [1.9, 0.1, 0.1],      # voxel (1,0,0) -> centroid (1.5,0.1,0.1)
            [-0.1, -0.1, -0.1],                    # voxel (-1,-1,-1) -> itself
        ], dtype=np.float64)
        out, _ = voxel_downsample(pts, voxel_size=1.0)
        self.assertEqual(len(out), 3)
        got = out[np.lexsort(out.T[::-1])]
        expected = np.array([[-0.1, -0.1, -0.1], [0.5, 0.5, 0.5], [1.5, 0.1, 0.1]])
        self.assertTrue(np.allclose(got, expected, atol=1e-9))

    def test_voxel_boundary_uses_floor(self):
        out, _ = voxel_downsample(np.array([[0.999, 0.0, 0.0], [1.0, 0.0, 0.0]]), voxel_size=1.0)
        self.assertEqual(len(out), 2)

    def test_empty_and_disabled(self):
        empty, _ = voxel_downsample(np.zeros((0, 3)), voxel_size=0.1)
        self.assertEqual(len(empty), 0)
        pts = np.random.default_rng(0).uniform(size=(10, 3))
        same, _ = voxel_downsample(pts, voxel_size=0.0)
        self.assertEqual(len(same), 10)


def _icp(inlier=0.9, fit=0.05, trans=(0.1, 0, 0), rot=None, success=True):
    r = np.eye(3) if rot is None else rot
    t = np.array(trans, dtype=float)
    m = np.eye(4)
    m[:3, :3], m[:3, 3] = r, t
    return ICPResult(success, m, r, t, fit, inlier, 100, 5, "CONVERGED")


class TestRegistrationGate(unittest.TestCase):
    def test_accepts_plausible_registration(self):
        ok, reason = RegistrationGate().check(_icp())
        self.assertTrue(ok)
        self.assertEqual(reason, "accepted")

    def test_rejection_reasons(self):
        g = RegistrationGate()
        self.assertEqual(g.check(_icp(inlier=0.1))[1], "low_inlier_ratio")
        self.assertEqual(g.check(_icp(fit=0.6))[1], "high_residual")
        self.assertEqual(g.check(_icp(trans=(2.0, 0, 0)))[1], "implausible_translation")
        self.assertEqual(g.check(_icp(rot=rz(30.0)))[1], "implausible_rotation")
        self.assertTrue(g.check(_icp(success=False))[1].startswith("icp_failed"))

    def test_unrelated_scans_are_rejected_and_counted(self):
        a = np.random.default_rng(1).uniform([-10, -10, 0], [10, 10, 4], size=(3000, 3))
        b = np.random.default_rng(2).uniform([-10, -10, 0], [10, 10, 4], size=(3000, 3))
        odom = ICPOdometry(voxel_size=0.0, min_range=0.0)
        odom.process_frame(a.astype(np.float32), 0)
        step = odom.process_frame(b.astype(np.float32), 1)
        self.assertFalse(step.accepted)
        self.assertFalse(step.success)
        self.assertEqual(odom.failed_steps, 1)
        self.assertEqual(sum(odom.reject_counts.values()), 1)
        self.assertTrue(np.allclose(odom.current_pose, np.eye(4)))     # pose untouched
        summary = odom.get_summary_statistics()
        self.assertEqual(summary["successful_registrations"], 0)
        self.assertEqual(summary["success_rate_percent"], 0.0)
        self.assertEqual(summary["initialization_frames"], 1)


class TestTrajectoryEvaluation(unittest.TestCase):
    def test_umeyama_recovers_known_rigid_transform(self):
        pts = np.random.default_rng(3).uniform(-5, 5, size=(50, 3))
        r_true = rz(40.0) @ rx(15.0)
        t_true = np.array([1.0, -2.0, 3.0])
        r, t, aligned = align_umeyama_rigid(pts, pts @ r_true.T + t_true)
        self.assertTrue(np.allclose(r, r_true, atol=1e-9))
        self.assertTrue(np.allclose(t, t_true, atol=1e-9))
        self.assertTrue(np.allclose(aligned, pts @ r_true.T + t_true, atol=1e-9))

    def test_association_respects_max_dt_and_uniqueness(self):
        a = np.arange(10) * 0.1
        ia, ib = associate_by_time(a, a + 0.004, max_dt=0.02)
        self.assertEqual(len(ia), 10)
        self.assertEqual(len(associate_by_time(a, a + 0.06, max_dt=0.02)[0]), 0)
        ia, ib = associate_by_time(np.array([0.0, 0.001]), np.array([0.0005]), max_dt=0.02)
        self.assertEqual(len(ia), 1)  # one reference pose can match only one estimate

    def _line(self, step, n=200, yaw_step=0.0):
        poses = np.tile(np.eye(4), (n, 1, 1))
        for k in range(n):
            poses[k, :3, :3] = rz(yaw_step * k)
            poses[k, 0, 3] = step * k
        return poses, np.arange(n) * 0.1

    def test_rigidly_transformed_estimate_has_zero_ate_and_rpe(self):
        gt, t = self._line(0.1, yaw_step=0.5)
        x = np.eye(4)
        x[:3, :3], x[:3, 3] = rz(33.0), [4.0, -1.0, 2.0]
        res = evaluate_trajectory(x @ gt, t, gt, t)["summary"]
        self.assertLess(res["ate_m"]["rmse"], 1e-9)
        self.assertLess(res["rpe"]["time_1s"]["translation_m"]["max"], 1e-9)
        self.assertLess(res["rpe"]["time_1s"]["rotation_deg"]["max"], 1e-4)

    def test_rpe_matches_known_scale_error(self):
        gt, t = self._line(0.10)
        est, _ = self._line(0.11)      # estimate overshoots by 10 %
        res = evaluate_trajectory(est, t, gt, t)["summary"]
        one_s = res["rpe"]["time_1s"]
        self.assertAlmostEqual(one_s["translation_m"]["mean"], 0.10, places=9)   # 1.1 m - 1.0 m
        self.assertAlmostEqual(one_s["translation_percent_of_length"], 10.0, places=6)
        self.assertAlmostEqual(one_s["rotation_deg"]["max"], 0.0, places=6)
        ten_m = res["rpe"]["distance_10m"]
        self.assertAlmostEqual(ten_m["translation_m"]["mean"], 1.0, delta=0.02)   # 11 m - 10 m

    def test_rpe_rotation_drift(self):
        gt, t = self._line(0.0)                       # stationary
        est, _ = self._line(0.0, yaw_step=1.0)        # estimate spins 1 deg per frame
        res = evaluate_trajectory(est, t, gt, t)["summary"]
        self.assertAlmostEqual(res["rpe"]["time_1s"]["rotation_deg"]["mean"], 10.0, places=6)
        self.assertAlmostEqual(res["rpe"]["time_1s"]["translation_m"]["max"], 0.0, places=9)

    def test_unavailable_without_time_overlap(self):
        gt, t = self._line(0.1)
        res = evaluate_trajectory(gt, t, gt, t + 1000.0)["summary"]
        self.assertEqual(res["status"], "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()