"""Phase 0 regression tests for loaders, timestamps, KITTI, ground truth, sanitising and the synthetic flag."""

import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from autonav_baseline.datasets.groundtruth import load_pose_csv
from autonav_baseline.datasets.io import discover_timestamps, parse_pcd_file
from autonav_baseline.datasets.kitti import KITTIAdapter
from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.datasets.synthetic import SyntheticAdapter
from autonav_baseline.reporting.exporter import sanitize_paths, sanitize_text

OUSTER_DTYPE = np.dtype([
    ("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("intensity", "<f4"), ("t", "<u4"),
    ("reflectivity", "<u2"), ("ring", "u1"), ("noise", "<u2"), ("range", "<u4"),
])
OUSTER_HEADER = (
    "# .PCD v0.7\nVERSION 0.7\nFIELDS x y z intensity t reflectivity ring noise range\n"
    "SIZE 4 4 4 4 4 2 1 2 4\nTYPE F F F F U U U U U\nCOUNT 1 1 1 1 1 1 1 1 1\n"
    "WIDTH {w}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS {n}\nDATA binary\n"
)


def _ouster_pcd(path: Path, n: int, declared: int, trailing: int = 0):
    rec = np.zeros(n, dtype=OUSTER_DTYPE)
    rec["x"] = np.arange(n, dtype=np.float32)
    rec["y"] = 2.0
    rec["z"] = -1.0
    header = OUSTER_HEADER.format(w=declared, n=declared).encode("ascii")
    path.write_bytes(header + rec.tobytes() + b"\xAB" * trailing)


class TestPcdHeaderIsAuthoritative(unittest.TestCase):
    def test_trailing_bytes_are_not_points(self):
        # Real Newer College files carry bytes after the declared records; the old loader
        # returned 65,668 points for a file declaring 65,536.
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "scan.pcd"
            _ouster_pcd(f, n=100, declared=100, trailing=3846)
            xyz, _, meta = parse_pcd_file(f)
            self.assertEqual(xyz.shape, (100, 3))
            self.assertEqual(meta["trailing_bytes_ignored"], 3846)
            self.assertAlmostEqual(float(xyz[7, 0]), 7.0)
            self.assertAlmostEqual(float(xyz[7, 1]), 2.0)

    def test_truncated_file_raises(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "scan.pcd"
            _ouster_pcd(f, n=50, declared=100)
            with self.assertRaises(ValueError):
                parse_pcd_file(f)


class TestPcdCountAndPadding(unittest.TestCase):
    def test_hesai_style_header_with_padding_fields(self):
        # Header layout of the Oxford Spires clouds: padding fields "_" with COUNT 4 / 14.
        header = (
            "# .PCD v0.7\nVERSION 0.7\nFIELDS x y z _ intensity _ timestamp ring _\n"
            "SIZE 4 4 4 1 4 1 8 2 1\nTYPE F F F U F U F U U\nCOUNT 1 1 1 4 1 4 1 1 14\n"
            "WIDTH 3\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS 3\nDATA binary\n"
        ).encode("ascii")
        step = 4 + 4 + 4 + 4 + 4 + 4 + 8 + 2 + 14   # x y z pad4 intensity pad4 timestamp ring pad14 = 48
        buf = bytearray()
        for i in range(3):
            rec = bytearray(step)
            rec[0:12] = np.array([1.0 + i, 2.0, 3.0], dtype="<f4").tobytes()
            rec[16:20] = np.array([10.0 * (i + 1)], dtype="<f4").tobytes()
            buf += rec
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "hesai.pcd"
            f.write_bytes(header + bytes(buf))
            xyz, inten, meta = parse_pcd_file(f)
            self.assertEqual(xyz.shape, (3, 3))
            self.assertTrue(np.allclose(xyz[:, 0], [1.0, 2.0, 3.0]))
            self.assertTrue(np.allclose(inten, [10.0, 20.0, 30.0]))

class TestRosStyleFilenames(unittest.TestCase):
    def test_sec_nsec_filenames_are_timestamps(self):
        with tempfile.TemporaryDirectory() as d:
            names = ["cloud_1583836655_381094656.pcd", "cloud_1583837922_59876608.pcd"]
            files = []
            for n in names:
                p = Path(d) / n
                p.write_bytes(b"x")
                files.append(p)
            ts = discover_timestamps(Path(d), files)
            self.assertIsNotNone(ts)
            self.assertAlmostEqual(ts[0], 1583836655.381094656, places=5)
            # nsec is an integer count: 59,876,608 ns = 0.059876608 s (not 0.59876608)
            self.assertAlmostEqual(ts[1], 1583837922.059876608, places=5)

    def test_unparseable_names_give_none(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "frame_a.pcd"
            p.write_bytes(b"x")
            self.assertIsNone(discover_timestamps(Path(d), [p]))


class TestChronologicalOrdering(unittest.TestCase):
    def test_unpadded_nanoseconds_sort_chronologically(self):
        # Lexicographic order puts `_59876608` after `_157463040`, scrambling frames within a second.
        from autonav_baseline.datasets.io import scan_sort_key
        names = ["cloud_1583838094_157463040.pcd", "cloud_1583838094_59876608.pcd",
                 "cloud_1583838095_9999999.pcd", "cloud_1583838094_957463040.pcd"]
        self.assertNotEqual(sorted(names), sorted(names, key=scan_sort_key))
        self.assertEqual(
            sorted(names, key=scan_sort_key),
            ["cloud_1583838094_59876608.pcd", "cloud_1583838094_157463040.pcd",
             "cloud_1583838094_957463040.pcd", "cloud_1583838095_9999999.pcd"])

    def test_adapter_yields_frames_in_time_order(self):
        from autonav_baseline.datasets.newer_college import NewerCollegeAdapter
        with tempfile.TemporaryDirectory() as d:
            for n in ("cloud_1583838094_157463040.pcd", "cloud_1583838094_59876608.pcd"):
                _ouster_pcd(Path(d) / n, n=10, declared=10)
            frames = list(NewerCollegeAdapter(root_path=Path(d)).get_lidar_frames())
            self.assertEqual([f.metadata["filename"] for f in frames],
                             ["cloud_1583838094_59876608.pcd", "cloud_1583838094_157463040.pcd"])
            self.assertLess(frames[0].timestamp, frames[1].timestamp)

class TestKittiDoesNotInventTimestamps(unittest.TestCase):
    def _make(self, root: Path, n=3):
        vel = root / "velodyne"
        vel.mkdir()
        for i in range(n):
            np.zeros((10, 4), dtype=np.float32).tofile(str(vel / f"{i:06d}.bin"))
        return vel

    def test_no_times_file_means_no_timestamps(self):
        with tempfile.TemporaryDirectory() as d:
            vel = self._make(Path(d))
            frames = list(KITTIAdapter(root_path=vel).get_lidar_frames())
            self.assertTrue(all(f.timestamp is None for f in frames))

    def test_times_file_is_used_when_present(self):
        with tempfile.TemporaryDirectory() as d:
            vel = self._make(Path(d))
            (Path(d) / "times.txt").write_text("0.0\n0.103\n0.205\n", encoding="utf-8")
            frames = list(KITTIAdapter(root_path=vel).get_lidar_frames())
            self.assertAlmostEqual(frames[1].timestamp, 0.103)
            self.assertAlmostEqual(frames[2].timestamp, 0.205)


class TestGroundTruthLoader(unittest.TestCase):
    def test_newer_college_layout(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "gt.csv"
            f.write_text(
                "#sec,nsec,x,y,z,qx,qy,qz,qw\n"
                "1583836591,182590976,1.0,2.0,3.0,0,0,0,1\n"
                "1583836591,282592512,1.1,2.0,3.0,0,0,0.7071067811865476,0.7071067811865476\n",
                encoding="utf-8")
            t, poses = load_pose_csv(f)
            self.assertAlmostEqual(t[1] - t[0], 0.1, places=5)
            self.assertTrue(np.allclose(poses[0, :3, 3], [1.0, 2.0, 3.0]))
            self.assertTrue(np.allclose(poses[1, :3, :3] @ [1, 0, 0], [0, 1, 0], atol=1e-9))

    def test_rejects_non_monotonic_and_non_unit_quaternion(self):
        with tempfile.TemporaryDirectory() as d:
            bad_t = Path(d) / "a.csv"
            bad_t.write_text("10,0,0,0,0,0,0,0,1\n9,0,0,0,0,0,0,0,1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_pose_csv(bad_t)
            bad_q = Path(d) / "b.csv"
            bad_q.write_text("10,0,0,0,0,0,0,0,2\n11,0,0,0,0,0,0,0,2\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_pose_csv(bad_q)


class TestSanitisingAndSyntheticFlag(unittest.TestCase):
    def test_home_and_repo_paths_are_removed(self):
        home = str(Path.home())
        out = sanitize_paths({"p": home + "\\secret\\x", "n": [home.replace("\\", "/") + "/a"]})
        self.assertNotIn(home, str(out))
        self.assertIn("<home>", out["p"])
        self.assertNotIn(home.replace("\\", "/"), sanitize_text(home.replace("\\", "/") + "/a"))

    def test_synthetic_adapter_is_flagged(self):
        adapter = get_adapter("synthetic", config={"num_frames": 2})
        self.assertIn("SYNTHETIC", adapter.name)
        frames = list(adapter.get_lidar_frames())
        self.assertTrue(all(f.metadata.get("synthetic") is True for f in frames))
        self.assertTrue(adapter.inspect().metadata["synthetic"])


if __name__ == "__main__":
    unittest.main()