"""
Unit tests for dataset adapters and registry.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import unittest
from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.datasets.synthetic import SyntheticAdapter


class TestAdapters(unittest.TestCase):
    def test_synthetic_adapter_registry(self):
        adapter = get_adapter("synthetic")
        self.assertIsInstance(adapter, SyntheticAdapter)
        self.assertEqual(adapter.name, "Synthetic Demonstration Stream")

    def test_synthetic_lidar_stream(self):
        adapter = get_adapter("synthetic")
        frames = list(adapter.get_lidar_frames(max_frames=5))
        self.assertEqual(len(frames), 5)
        self.assertGreater(frames[0].num_points, 1000)
        self.assertEqual(frames[0].points.shape[1], 3)

    def test_synthetic_depth_stream(self):
        adapter = get_adapter("synthetic")
        frames = list(adapter.get_depth_frames(max_frames=3))
        self.assertEqual(len(frames), 3)
        self.assertIsNotNone(frames[0].depth)
        self.assertEqual(len(frames[0].depth.shape), 2)

    def test_synthetic_imu_stream(self):
        adapter = get_adapter("synthetic")
        frames = list(adapter.get_imu_frames(max_frames=10))
        self.assertEqual(len(frames), 10)
        self.assertEqual(frames[0].accel.shape, (3,))
        self.assertEqual(frames[0].gyro.shape, (3,))


if __name__ == "__main__":
    unittest.main()
