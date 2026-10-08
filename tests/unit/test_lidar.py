"""
Unit tests for LiDAR statistics and geometry calculations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import unittest
import numpy as np
from autonav_baseline.lidar.statistics import compute_lidar_statistics
from tests.fixtures.sample_data import create_tiny_point_cloud


class TestLiDARStatistics(unittest.TestCase):
    def setUp(self):
        self.pts = create_tiny_point_cloud()

    def test_point_count_and_finiteness(self):
        self.assertEqual(len(self.pts), 100)
        stats = compute_lidar_statistics(self.pts)
        self.assertEqual(stats["total_points"]["value"], 100)
        self.assertEqual(stats["finite_points"]["value"], 95)
        self.assertAlmostEqual(stats["finite_percent"]["value"], 95.0, places=1)

    def test_range_statistics(self):
        stats = compute_lidar_statistics(self.pts)
        # Minimum range should be for point (0, 0, 1) -> sqrt(0 + 0 + 1) = 1.0
        self.assertAlmostEqual(stats["range_min_m"]["value"], 1.0, places=2)
        # Maximum range is >= 200m from the extreme points
        self.assertGreater(stats["range_max_m"]["value"], 100.0)


if __name__ == "__main__":
    unittest.main()
