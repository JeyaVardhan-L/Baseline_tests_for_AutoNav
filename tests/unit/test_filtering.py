"""
Unit tests for point cloud filtering and downsampling.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import unittest
import numpy as np
from autonav_baseline.lidar.filtering import remove_invalid_points, filter_by_range, voxel_downsample
from tests.fixtures.sample_data import create_tiny_point_cloud


class TestFiltering(unittest.TestCase):
    def setUp(self):
        self.pts = create_tiny_point_cloud()

    def test_remove_invalid_points(self):
        valid, mask = remove_invalid_points(self.pts)
        self.assertEqual(len(valid), 95)
        self.assertFalse(np.any(np.isnan(valid)))
        self.assertFalse(np.any(np.isinf(valid)))

    def test_filter_by_range(self):
        valid, _ = remove_invalid_points(self.pts)
        in_range, mask = filter_by_range(valid, min_range=0.5, max_range=50.0)
        # The 5 far points (range > 150m) should be filtered out
        self.assertEqual(len(in_range), 90)
        ranges = np.linalg.norm(in_range, axis=1)
        self.assertTrue(np.all(ranges >= 0.5))
        self.assertTrue(np.all(ranges <= 50.0))

    def test_voxel_downsampling(self):
        valid, _ = remove_invalid_points(self.pts)
        in_range, _ = filter_by_range(valid, min_range=0.5, max_range=50.0)
        # Using a large voxel size of 2.0 meters on the 90-point grid
        downsampled, mask = voxel_downsample(in_range, voxel_size=2.0)
        self.assertLess(len(downsampled), len(in_range))
        self.assertGreater(len(downsampled), 0)


if __name__ == "__main__":
    unittest.main()
