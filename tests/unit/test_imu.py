"""
Unit tests for IMU statistics and timing jitter calculations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import unittest
import numpy as np
from autonav_baseline.imu.statistics import compute_imu_statistics
from tests.fixtures.sample_data import create_known_imu_data


class TestIMU(unittest.TestCase):
    def test_compute_imu_statistics(self):
        ts, accel, gyro = create_known_imu_data(count=100, rate_hz=200.0)
        stats = compute_imu_statistics(ts, accel, gyro)

        self.assertEqual(stats["num_samples"]["value"], 100)
        self.assertAlmostEqual(stats["observed_frequency_hz"]["value"], 200.0, places=1)
        self.assertAlmostEqual(stats["mean_interval_ms"]["value"], 5.0, places=2)
        self.assertAlmostEqual(stats["jitter_ms"]["value"], 0.0, places=2)
        self.assertEqual(stats["suspected_dropped_packets"]["value"], 0)
        self.assertAlmostEqual(stats["accel"]["mean_norm_mps2"], 9.81, places=2)


if __name__ == "__main__":
    unittest.main()
