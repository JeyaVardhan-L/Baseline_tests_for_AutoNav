"""
Unit tests for dataset adapters and registry.
Verifies real-dataset adapters and alias resolution without synthetic dependencies.
"""

import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.datasets.newer_college import NewerCollegeAdapter
from autonav_baseline.datasets.base import SensorType


class TestAdapters(unittest.TestCase):
    def test_newer_college_adapter_registry(self):
        adapter = get_adapter("newer_college")
        self.assertIsInstance(adapter, NewerCollegeAdapter)
        self.assertEqual(adapter.name, "Newer College Dataset (Oxford)")

    def test_newer_college_adapter_alias(self):
        adapter = get_adapter("newer-college")
        self.assertIsInstance(adapter, NewerCollegeAdapter)

    def test_unknown_adapter_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_adapter("nonexistent_dataset_name")

    def test_newer_college_populates_when_files_present(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            # Create a point cloud file
            pcd_content = (
                "# .PCD v0.7\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\n"
                "COUNT 1 1 1\nWIDTH 3\nHEIGHT 1\nPOINTS 3\nDATA ascii\n"
                "1.0 2.0 3.0\n4.0 5.0 6.0\n7.0 8.0 9.0\n"
            )
            (p / "scan_000.pcd").write_text(pcd_content, encoding="utf-8")
            (p / "scan_001.pcd").write_text(pcd_content, encoding="utf-8")
            (p / "timestamps.csv").write_text("timestamp\n100.0\n100.1\n", encoding="utf-8")

            adapter = get_adapter("newer_college", root_path=p)
            inspection = adapter.inspect()

            self.assertEqual(inspection.frame_count, 2)
            self.assertTrue(inspection.is_rate_measured)
            self.assertAlmostEqual(inspection.observed_rate_hz, 10.0, places=2)
            self.assertIn(SensorType.LIDAR, inspection.sensor_types)

            frames = list(adapter.get_lidar_frames(max_frames=2))
            self.assertEqual(len(frames), 2)
            self.assertEqual(frames[0].num_points, 3)
            self.assertEqual(frames[0].timestamp, 100.0)
            self.assertEqual(frames[1].timestamp, 100.1)


if __name__ == "__main__":
    unittest.main()
