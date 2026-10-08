"""
Unit tests for metrics and classification tagging.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import unittest
from autonav_baseline.metrics.classification import Classification, tag
from autonav_baseline.metrics.data_rate import DataRateMetrics


class TestMetrics(unittest.TestCase):
    def test_classification_tagging(self):
        t = tag(100.5, Classification.MEASURED, "MB/s", "Observed transfer rate")
        self.assertEqual(t["value"], 100.5)
        self.assertEqual(t["classification"], "MEASURED")
        self.assertEqual(t["unit"], "MB/s")
        self.assertEqual(t["note"], "Observed transfer rate")

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



if __name__ == "__main__":
    unittest.main()
