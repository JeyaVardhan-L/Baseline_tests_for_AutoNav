"""
Unit tests for metrics, classification tagging, and trajectory accuracy evaluation.
"""

import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from autonav_baseline.metrics.classification import Classification, tag
from autonav_baseline.metrics.data_rate import DataRateMetrics
from autonav_baseline.metrics.trajectory_evaluation import (
    align_umeyama_rigid,
    compute_trajectory_accuracy,
)


class TestMetrics(unittest.TestCase):
    def test_classification_tagging(self):
        t = tag(100.5, Classification.MEASURED, "MB/s", "Observed transfer rate")
        self.assertEqual(t["value"], 100.5)
        self.assertEqual(t["classification"], "MEASURED")
        self.assertEqual(t["unit"], "MB/s")
        self.assertEqual(t["note"], "Observed transfer rate")

    def test_all_six_evidence_classes(self):
        expected = ["MEASURED", "DERIVED", "DECLARED", "ASSUMED", "UNAVAILABLE", "UNVERIFIED"]
        for c_str in expected:
            c = Classification(c_str)
            self.assertEqual(str(c), c_str)

    def test_data_rate_metrics(self):
        rate = DataRateMetrics(
            avg_frame_size_bytes=100_000.0,
            frame_rate_hz=10.0,
            is_frame_rate_measured=True,
        )
        self.assertEqual(rate.bytes_per_sec, 1_000_000.0)
        self.assertAlmostEqual(rate.mb_per_sec, 1.0, places=4)
        self.assertAlmostEqual(rate.mib_per_sec, 1_000_000.0 / (1024.0**2), places=4)
        self.assertAlmostEqual(rate.frame_rate_hz, 10.0, places=2)
        d = rate.to_dict()
        self.assertEqual(d["bytes_per_sec"]["classification"], "DERIVED")

    def test_trajectory_accuracy_with_known_ground_truth(self):
        # 5 positions along a curve
        t_arr = np.linspace(0, 2, 5)
        gt = np.column_stack([t_arr, np.sin(t_arr), np.zeros_like(t_arr)])
        # Shift estimated by pure translation (0.5, 0.2, 0.0)
        est = gt - np.array([0.5, 0.2, 0.0])

        res = compute_trajectory_accuracy(est, gt)
        self.assertEqual(res["status"], "MEASURED")
        self.assertAlmostEqual(res["ate_rmse_m"]["value"], 0.0, places=4)
        self.assertEqual(res["ate_rmse_m"]["classification"], "DERIVED")

    def test_trajectory_accuracy_when_ground_truth_absent(self):
        est = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        res = compute_trajectory_accuracy(est, None)
        self.assertEqual(res["status"], "UNAVAILABLE")
        self.assertEqual(res["ate_rmse_m"]["classification"], "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
