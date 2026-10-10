import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import pathlib
import sys
import tempfile
import types
import unittest

SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "benchmark.py"
spec = importlib.util.spec_from_file_location("benchmark", SCRIPT)
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)

try:
    import matplotlib  # noqa: F401
    import numpy  # noqa: F401
    HAVE_PLOTTING = True
except ImportError:
    HAVE_PLOTTING = False

MAP_M = 10.0
MAP_PX = 20


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


class PoseValidityTests(unittest.TestCase):
    def test_boundaries_are_half_open(self):
        size_mm = MAP_M * 1000
        self.assertTrue(benchmark.pose_in_map(0.0, 0.0, MAP_M))
        self.assertTrue(benchmark.pose_in_map(size_mm - 0.001, 5000.0, MAP_M))
        self.assertFalse(benchmark.pose_in_map(size_mm, 5000.0, MAP_M))
        self.assertFalse(benchmark.pose_in_map(5000.0, size_mm, MAP_M))
        self.assertFalse(benchmark.pose_in_map(-0.001, 5000.0, MAP_M))
        self.assertFalse(benchmark.pose_in_map(5000.0, -1.0, MAP_M))

    def test_non_finite_pose_is_invalid(self):
        self.assertFalse(benchmark.pose_in_map(float("nan"), 1.0, MAP_M))
        self.assertFalse(benchmark.pose_in_map(1.0, float("inf"), MAP_M))

    def test_accounting_counts_first_and_fraction(self):
        flags = [True, True, False, True, False, False, True, False]
        v = benchmark.validity_summary(flags, range(100, 108), MAP_M)
        self.assertEqual(v["scans_evaluated"], 8)
        self.assertEqual(v["invalid_scans"], 4)
        self.assertAlmostEqual(v["invalid_fraction"], 0.5)
        self.assertEqual(v["first_invalid_scan_index"], 102)  # label, not position
        self.assertFalse(v["valid_for_performance_claims"])

    def test_all_valid_run(self):
        v = benchmark.validity_summary([True] * 5, range(5), MAP_M)
        self.assertEqual(v["invalid_scans"], 0)
        self.assertIsNone(v["first_invalid_scan_index"])
        self.assertTrue(v["valid_for_performance_claims"])

    def test_single_invalid_scan_invalidates_run(self):
        v = benchmark.validity_summary([True, True, True, False], range(4), MAP_M)
        self.assertFalse(v["valid_for_performance_claims"])
        self.assertEqual(v["first_invalid_scan_index"], 3)

    def test_empty_run_is_not_valid(self):
        v = benchmark.validity_summary([], [], MAP_M)
        self.assertFalse(v["valid_for_performance_claims"])
        self.assertIsNone(v["invalid_fraction"])

    def test_length_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            benchmark.validity_summary([True], [1, 2], MAP_M)


class OdometryExtentTests(unittest.TestCase):
    def test_extent_relative_to_first_scan(self):
        scans = [{"x_m": 1.0, "y_m": 1.0}, {"x_m": 4.0, "y_m": 5.0}, {"x_m": -5.0, "y_m": 1.0}]
        e = benchmark.odometry_extent(scans, map_meters=10.0)
        self.assertAlmostEqual(e["max_axis_offset_m"], 6.0)
        self.assertAlmostEqual(e["max_radial_offset_m"], 6.0)  # hypot(3,4)=5, |-6,0|=6
        self.assertAlmostEqual(e["min_map_meters_rotation_safe"], 12.0)
        self.assertAlmostEqual(e["min_map_meters_axis_aligned"], 12.0)
        self.assertFalse(e["odometry_path_fits_configured_map"])
        self.assertEqual(e["first_scan_radial_offset_reaches_half_map"], 1)  # 5 >= 10/2

    def test_fits_when_map_large_enough(self):
        scans = [{"x_m": 0.0, "y_m": 0.0}, {"x_m": 3.0, "y_m": 4.0}]
        e = benchmark.odometry_extent(scans, map_meters=20.0)
        self.assertTrue(e["odometry_path_fits_configured_map"])
        self.assertIsNone(e["first_scan_radial_offset_reaches_half_map"])

    def test_default_map_contains_the_documented_recording_extent(self):
        # 62.2 m max radial offset of intel.clf odometry (documented in benchmark.py).
        self.assertGreater(benchmark.DEFAULT_MAP_METERS, 2 * 62.2344)


class OutputPathTests(unittest.TestCase):
    def test_modes_never_share_a_filename(self):
        off = benchmark.output_paths("out", "offline")
        pac = benchmark.output_paths("out", "paced")
        self.assertTrue(set(map(str, off.values())).isdisjoint(set(map(str, pac.values()))))
        for p in off.values():
            self.assertIn("offline", p.name)
        for p in pac.values():
            self.assertIn("paced", p.name)

    def test_new_names_do_not_collide_with_legacy_unlabelled_names(self):
        legacy = {"slam_map.png", "trajectory.png", "latency_distribution.png", "latency_over_time.png"}
        for mode in ("offline", "paced"):
            names = {p.name for p in benchmark.output_paths("out", mode).values()}
            self.assertTrue(names.isdisjoint(legacy))

    def test_unknown_mode_rejected(self):
        with self.assertRaises(ValueError):
            benchmark.output_paths("out", "both")

    def test_ensure_writable_refuses_and_preserves_existing(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "offline_runs.csv"
            f.write_text("precious measurement\n")
            before = sha(f)
            with self.assertRaises(FileExistsError):
                benchmark.ensure_writable([f], overwrite=False)
            self.assertEqual(sha(f), before)
            benchmark.ensure_writable([f], overwrite=True)  # explicit opt-in only
            benchmark.ensure_writable([pathlib.Path(d) / "missing.csv"], overwrite=False)


def install_fake_breezyslam(step_mm=1000.0):
    """Stub of the two BreezySLAM classes used; pose walks +x and leaves a small map."""
    class Laser:
        def __init__(self, *args, **kwargs):
            pass

    class RMHC_SLAM:
        def __init__(self, laser, map_pixels, map_meters, random_seed=0):
            self.px, self.m, self.k = map_pixels, map_meters, 0

        def update(self, ranges_mm, pose_change=(0, 0, 0)):
            self.k += 1

        def getpos(self):
            return (self.m * 500.0 + self.k * step_mm, self.m * 500.0, 0.0)

        def getmap(self, buf):
            buf[:] = bytes([127]) * len(buf)

    pkg = types.ModuleType("breezyslam")
    algorithms = types.ModuleType("breezyslam.algorithms")
    sensors = types.ModuleType("breezyslam.sensors")
    algorithms.RMHC_SLAM, sensors.Laser = RMHC_SLAM, Laser
    pkg.algorithms, pkg.sensors = algorithms, sensors
    saved = {k: sys.modules.get(k) for k in ("breezyslam", "breezyslam.algorithms", "breezyslam.sensors")}
    sys.modules.update({"breezyslam": pkg, "breezyslam.algorithms": algorithms,
                        "breezyslam.sensors": sensors})
    return saved


def restore_modules(saved):
    for k, v in saved.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


def write_clf(path, n=12):
    lines = []
    for i in range(n):
        t = 1000.0 + 0.1 * i
        lines.append(
            f"FLASER 4 1.0 2.0 3.0 4.0 {0.05 * i} 0.0 0.0 {0.05 * i} 0.0 0.0 {t} nohost {0.1 * i}"
        )
    pathlib.Path(path).write_text("\n".join(lines) + "\n")


def args_for(tmp, **over):
    base = dict(
        input=str(pathlib.Path(tmp) / "scans.clf"), hz=1000.0, fov=180.0, max_range_m=12.0,
        map_pixels=MAP_PX, map_meters=MAP_M, seed=1, out_dir=str(pathlib.Path(tmp) / "out"),
        overwrite=False, runs=2, warmup=2, minutes=0.0005,
    )
    base.update(over)
    return argparse.Namespace(**base)


class EndToEndWithStubSlamTests(unittest.TestCase):
    """Runs the real offline/paced commands against a stub SLAM (no Pi, no BreezySLAM)."""

    def setUp(self):
        self.saved = install_fake_breezyslam()
        self.tmp = tempfile.TemporaryDirectory()
        write_clf(pathlib.Path(self.tmp.name) / "scans.clf")
        self.out = pathlib.Path(self.tmp.name) / "out"
        self.out.mkdir()

    def tearDown(self):
        restore_modules(self.saved)
        self.tmp.cleanup()

    def run_cmd(self, fn, args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            fn(args)
        return err.getvalue()

    def test_offline_records_invalid_poses_and_marks_run_invalid(self):
        err = self.run_cmd(benchmark.command_offline, args_for(self.tmp.name))
        summary = json.loads((self.out / "offline_summary.json").read_text())
        self.assertFalse(summary["all_runs_valid_for_performance_claims"])
        v = summary["runs"][0]["pose_validity"]
        # stub: scan i has x = 5000 + (i+1)*1000 mm -> first x >= 10000 at i = 4
        self.assertEqual(v["first_invalid_scan_index"], 4)
        self.assertEqual(v["scans_evaluated"], 12)  # warm-up scans included
        self.assertEqual(v["invalid_scans"], 8)
        self.assertAlmostEqual(v["invalid_fraction"], 8 / 12)
        self.assertIn("INVALID", err)
        self.assertEqual(summary["map"]["map_meters"], MAP_M)

    def test_offline_csv_has_raw_schema_plus_flag_and_nothing_hidden(self):
        self.run_cmd(benchmark.command_offline, args_for(self.tmp.name))
        rows = benchmark.load_csv_rows(self.out / "offline_runs.csv")
        self.assertEqual(
            list(rows[0]),
            ["run", "scan_index", "processing_ms", "pose_x_mm", "pose_y_mm", "pose_theta_deg", "pose_in_map"],
        )
        # warm-up (2 scans) excluded from timing rows, invalid rows NOT dropped
        self.assertEqual(len(rows), 2 * (12 - 2))
        self.assertEqual(sum(r["pose_in_map"] == "False" for r in rows), 2 * 8)
        # poses are stored as reported, never clamped or reset
        self.assertGreater(max(float(r["pose_x_mm"]) for r in rows), MAP_M * 1000)

    def test_offline_writes_only_offline_named_files(self):
        self.run_cmd(benchmark.command_offline, args_for(self.tmp.name))
        names = {p.name for p in self.out.iterdir()}
        self.assertTrue({"offline_runs.csv", "offline_summary.json"} <= names)
        self.assertFalse(any("paced" in n for n in names))
        self.assertNotIn("slam_map.png", names)
        self.assertNotIn("trajectory.png", names)
        if HAVE_PLOTTING:
            self.assertTrue({"offline_slam_map.png", "offline_trajectory.png"} <= names)

    def test_paced_writes_only_paced_named_files_and_validity(self):
        self.run_cmd(benchmark.command_paced, args_for(self.tmp.name))
        names = {p.name for p in self.out.iterdir()}
        self.assertTrue({"paced_scan_timings.csv", "paced_summary.json"} <= names)
        self.assertFalse(any("offline" in n for n in names))
        summary = json.loads((self.out / "paced_summary.json").read_text())
        self.assertFalse(summary["valid_for_performance_claims"])
        self.assertEqual(summary["pose_validity"]["first_invalid_scan_index"], 4)
        self.assertEqual(summary["pose_validity"]["scans_evaluated"], summary["scans_processed"])
        self.assertIn("source scans", summary["source_scan_span"])

    def test_valid_run_is_marked_valid(self):
        self.run_cmd(benchmark.command_offline, args_for(self.tmp.name, map_meters=1000.0))
        summary = json.loads((self.out / "offline_summary.json").read_text())
        self.assertTrue(summary["all_runs_valid_for_performance_claims"])
        self.assertEqual(summary["runs"][0]["pose_validity"]["invalid_scans"], 0)

    def test_second_run_refuses_to_overwrite_and_preserves_bytes(self):
        self.run_cmd(benchmark.command_offline, args_for(self.tmp.name))
        before = {p.name: sha(p) for p in self.out.iterdir()}
        with self.assertRaises(FileExistsError):
            self.run_cmd(benchmark.command_offline, args_for(self.tmp.name))
        self.assertEqual({p.name: sha(p) for p in self.out.iterdir()}, before)

    def test_legacy_unlabelled_results_are_never_touched(self):
        legacy = {n: self.out / n for n in ("slam_map.png", "trajectory.png", "offline_runs_legacy.csv")}
        for n, p in legacy.items():
            p.write_bytes(n.encode())
        before = {n: sha(p) for n, p in legacy.items()}
        self.run_cmd(benchmark.command_offline, args_for(self.tmp.name))
        self.run_cmd(benchmark.command_paced, args_for(self.tmp.name))
        self.assertEqual({n: sha(p) for n, p in legacy.items()}, before)

    def test_invalid_map_args_rejected(self):
        for bad in (dict(map_meters=0.0), dict(map_meters=float("nan")), dict(map_pixels=-5)):
            with self.assertRaises(ValueError):
                self.run_cmd(benchmark.command_offline, args_for(self.tmp.name, **bad))

    def test_plot_requires_matching_mode_csv(self):
        self.run_cmd(benchmark.command_paced, args_for(self.tmp.name))
        # Asking for offline plots when only paced data exists must fail, never fall back.
        ns = argparse.Namespace(mode="offline", csv=None, out_dir=str(self.out), overwrite=False)
        with self.assertRaises(FileNotFoundError):
            benchmark.command_plot(ns)
        # Pointing the offline plot at a paced CSV must also be refused.
        ns = argparse.Namespace(mode="offline", csv=str(self.out / "paced_scan_timings.csv"),
                                out_dir=str(self.out), overwrite=False)
        with self.assertRaises(ValueError):
            benchmark.command_plot(ns)

    @unittest.skipUnless(HAVE_PLOTTING, "matplotlib/numpy not installed")
    def test_plot_writes_mode_specific_files_only(self):
        self.run_cmd(benchmark.command_offline, args_for(self.tmp.name))
        ns = argparse.Namespace(mode="offline", csv=None, out_dir=str(self.out), overwrite=False)
        self.run_cmd(benchmark.command_plot, ns)
        names = {p.name for p in self.out.iterdir()}
        self.assertTrue({"offline_latency_distribution.png", "offline_latency_over_time.png"} <= names)
        self.assertFalse({"latency_distribution.png", "latency_over_time.png"} & names)


if __name__ == "__main__":
    unittest.main()
