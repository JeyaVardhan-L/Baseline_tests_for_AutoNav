"""
Unit tests for point cloud parsing, timestamp discovery, and evidence-based dataset inspection.
"""

import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from autonav_baseline.datasets.io import (
    load_point_cloud_file,
    parse_pcd_file,
    parse_ply_file,
    discover_timestamps,
)
from autonav_baseline.datasets.newer_college import NewerCollegeAdapter
from autonav_baseline.datasets.base import SensorType


class TestDatasetIO(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_npy_valid(self):
        pts = np.array([[1.0, 2.0, 3.0, 10.0], [4.0, 5.0, 6.0, 20.0]], dtype=np.float32)
        fpath = self.dir_path / "scan.npy"
        np.save(fpath, pts)

        xyz, intensity, meta = load_point_cloud_file(fpath)
        self.assertEqual(xyz.shape, (2, 3))
        self.assertTrue(np.allclose(xyz[0], [1.0, 2.0, 3.0]))
        self.assertIsNotNone(intensity)
        self.assertTrue(np.allclose(intensity, [10.0, 20.0]))

    def test_load_bin_valid(self):
        pts = np.array([[1.0, 2.0, 3.0, 10.0], [4.0, 5.0, 6.0, 20.0]], dtype=np.float32)
        fpath = self.dir_path / "scan.bin"
        pts.tofile(str(fpath))

        xyz, intensity, meta = load_point_cloud_file(fpath)
        self.assertEqual(xyz.shape, (2, 3))
        self.assertTrue(np.allclose(xyz[1], [4.0, 5.0, 6.0]))
        self.assertIsNotNone(intensity)

    def test_load_bin_malformed_raises_error(self):
        # 5 floats is not divisible by 3 or 4
        raw = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
        fpath = self.dir_path / "bad.bin"
        raw.tofile(str(fpath))

        with self.assertRaises(ValueError):
            load_point_cloud_file(fpath)

    def test_load_empty_file_raises_error(self):
        fpath = self.dir_path / "empty.pcd"
        fpath.write_bytes(b"")

        with self.assertRaises(ValueError):
            load_point_cloud_file(fpath)

    def test_load_unsupported_format_raises_error(self):
        fpath = self.dir_path / "scan.xyz"
        fpath.write_text("1.0 2.0 3.0\n", encoding="utf-8")

        with self.assertRaises(ValueError):
            load_point_cloud_file(fpath)

    def test_parse_pcd_ascii(self):
        pcd_content = (
            "# .PCD v0.7\n"
            "VERSION 0.7\n"
            "FIELDS x y z intensity\n"
            "SIZE 4 4 4 4\n"
            "TYPE F F F F\n"
            "COUNT 1 1 1 1\n"
            "WIDTH 2\n"
            "HEIGHT 1\n"
            "POINTS 2\n"
            "DATA ascii\n"
            "1.5 2.5 3.5 100.0\n"
            "4.5 5.5 6.5 200.0\n"
        )
        fpath = self.dir_path / "scan.pcd"
        fpath.write_text(pcd_content, encoding="utf-8")

        xyz, intensity, meta = parse_pcd_file(fpath)
        self.assertEqual(xyz.shape, (2, 3))
        self.assertTrue(np.allclose(xyz[0], [1.5, 2.5, 3.5]))
        self.assertIsNotNone(intensity)
        self.assertTrue(np.allclose(intensity, [100.0, 200.0]))

    def test_parse_ply_ascii(self):
        ply_content = (
            "ply\n"
            "format ascii 1.0\n"
            "element vertex 2\n"
            "property float x\n"
            "property float y\n"
            "property float z\n"
            "end_header\n"
            "1.0 2.0 3.0\n"
            "4.0 5.0 6.0\n"
        )
        fpath = self.dir_path / "scan.ply"
        fpath.write_text(ply_content, encoding="utf-8")

        xyz, intensity, meta = parse_ply_file(fpath)
        self.assertEqual(xyz.shape, (2, 3))
        self.assertTrue(np.allclose(xyz[1], [4.0, 5.0, 6.0]))

    def test_discover_timestamps_from_file(self):
        scan1 = self.dir_path / "scan1.bin"
        scan2 = self.dir_path / "scan2.bin"
        scan1.write_bytes(b"\x00" * 16)
        scan2.write_bytes(b"\x00" * 16)

        ts_file = self.dir_path / "timestamps.txt"
        ts_file.write_text("1600000000.00\n1600000000.10\n", encoding="utf-8")

        ts = discover_timestamps(self.dir_path, [scan1, scan2])
        self.assertIsNotNone(ts)
        self.assertEqual(len(ts), 2)
        self.assertAlmostEqual(ts[1] - ts[0], 0.10, places=4)

    def test_discover_timestamps_missing_returns_none(self):
        scan1 = self.dir_path / "scan_a.bin"
        scan2 = self.dir_path / "scan_b.bin"
        scan1.write_bytes(b"\x00" * 16)
        scan2.write_bytes(b"\x00" * 16)

        ts = discover_timestamps(self.dir_path, [scan1, scan2])
        self.assertIsNone(ts)

    def test_newer_college_honest_inspection(self):
        # Create a directory with 2 PCD files and no timestamps
        pcd_content = (
            "VERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\n"
            "WIDTH 1\nHEIGHT 1\nPOINTS 1\nDATA ascii\n1.0 2.0 3.0\n"
        )
        (self.dir_path / "frame_001.pcd").write_text(pcd_content, encoding="utf-8")
        (self.dir_path / "frame_002.pcd").write_text(pcd_content, encoding="utf-8")

        adapter = NewerCollegeAdapter(root_path=self.dir_path)
        result = adapter.inspect()

        self.assertEqual(result.frame_count, 2)
        # Without timestamps, observed rate must be None and is_rate_measured must be False!
        self.assertIsNone(result.observed_rate_hz)
        self.assertFalse(result.is_rate_measured)
        # Only LIDAR should be reported because no IMU or camera files exist
        self.assertEqual(result.sensor_types, [SensorType.LIDAR])

        # Frames generator yields real points and None timestamp
        frames = list(adapter.get_lidar_frames(max_frames=2))
        self.assertEqual(len(frames), 2)
        self.assertIsNone(frames[0].timestamp)
        self.assertEqual(frames[0].points.shape, (1, 3))

    def test_parse_pcd_binary(self):
        header = (
            "# .PCD v0.7\nVERSION 0.7\nFIELDS x y z intensity\nSIZE 4 4 4 4\nTYPE F F F F\n"
            "COUNT 1 1 1 1\nWIDTH 2\nHEIGHT 1\nPOINTS 2\nDATA binary\n"
        ).encode("ascii")
        pts_data = np.array([
            (1.1, 2.2, 3.3, 10.0),
            (4.4, 5.5, 6.6, 20.0),
        ], dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("intensity", "<f4")])
        fpath = self.dir_path / "binary_scan.pcd"
        fpath.write_bytes(header + pts_data.tobytes())

        xyz, intensity, meta = parse_pcd_file(fpath)
        self.assertEqual(xyz.shape, (2, 3))
        self.assertAlmostEqual(xyz[0, 0], 1.1, places=4)
        self.assertAlmostEqual(xyz[1, 2], 6.6, places=4)
        self.assertIsNotNone(intensity)
        self.assertAlmostEqual(intensity[0], 10.0, places=4)

    def test_parse_ply_binary(self):
        header = (
            "ply\nformat binary_little_endian 1.0\nelement vertex 2\n"
            "property float x\nproperty float y\nproperty float z\nend_header\n"
        ).encode("ascii")
        pts_data = np.array([
            (10.0, 20.0, 30.0),
            (40.0, 50.0, 60.0),
        ], dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4")])
        fpath = self.dir_path / "binary_scan.ply"
        fpath.write_bytes(header + pts_data.tobytes())

        xyz, intensity, meta = parse_ply_file(fpath)
        self.assertEqual(xyz.shape, (2, 3))
        self.assertAlmostEqual(xyz[0, 1], 20.0, places=4)
        self.assertAlmostEqual(xyz[1, 0], 40.0, places=4)

    def test_discover_timestamps_csv_with_header(self):
        scan1 = self.dir_path / "scan_1.bin"
        scan2 = self.dir_path / "scan_2.bin"
        scan1.write_bytes(b"\x00" * 16)
        scan2.write_bytes(b"\x00" * 16)

        csv_content = "frame_id,timestamp_sec,quality\n0,1650000000.0,100\n1,1650000000.1,100\n"
        (self.dir_path / "timestamps.csv").write_text(csv_content, encoding="utf-8")

        ts = discover_timestamps(self.dir_path, [scan1, scan2])
        self.assertIsNotNone(ts)
        self.assertEqual(len(ts), 2)
        self.assertAlmostEqual(ts[0], 1650000000.0, places=3)
        self.assertAlmostEqual(ts[1], 1650000000.1, places=3)


if __name__ == "__main__":
    unittest.main()
