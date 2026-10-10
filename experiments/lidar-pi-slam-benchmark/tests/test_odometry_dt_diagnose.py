"""Regression tests for the confirmed pose-input defects (signed dxy, recorded-timestamp dt).

All tests here use synthetic data or a stub SLAM; none exercises the real BreezySLAM.
The last class reads the committed intel.clf (read-only) when it is present.
"""
import argparse
import contextlib
import importlib.util
import io
import math
import pathlib
import sys
import tempfile
import types
import unittest

SCRIPTS = pathlib.Path(__file__).parents[1] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


benchmark = load("benchmark")
diagnose = load("diagnose_inputs")
try:
    import numpy as np  # noqa: F401
    import scipy  # noqa: F401
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False

REPO = pathlib.Path(__file__).parents[3]
INTEL = REPO / "data" / "lidar-pi-slam-benchmark" / "intel.clf"


def pose(x, y, th=0.0, ts=0.0, n=4):
    return {"x_m": x, "y_m": y, "theta_rad": th, "timestamp": ts, "ranges_m": [1.0] * n}


class SignedDxyTests(unittest.TestCase):
    def test_forward_motion_is_positive(self):
        dxy, dth, _ = benchmark.odom_delta(pose(0, 0, 0.0), pose(0.1, 0, 0.0), dt_override=1.0)
        self.assertAlmostEqual(dxy, 100.0)
        self.assertAlmostEqual(dth, 0.0)

    def test_reversing_motion_is_negative(self):
        dxy, _, _ = benchmark.odom_delta(pose(0, 0, 0.0), pose(-0.1, 0, 0.0), dt_override=1.0)
        self.assertAlmostEqual(dxy, -100.0)

    def test_sign_is_relative_to_heading_not_world_axes(self):
        # facing -x: moving toward -x is forward, toward +x is reverse
        fwd, _, _ = benchmark.odom_delta(pose(0, 0, math.pi), pose(-0.2, 0, math.pi), dt_override=1.0)
        rev, _, _ = benchmark.odom_delta(pose(0, 0, math.pi), pose(0.2, 0, math.pi), dt_override=1.0)
        self.assertAlmostEqual(fwd, 200.0)
        self.assertAlmostEqual(rev, -200.0)

    def test_no_motion_is_zero_and_heading_delta_wraps(self):
        dxy, dth, _ = benchmark.odom_delta(pose(1, 1, 3.0), pose(1, 1, -3.0), dt_override=1.0)
        self.assertEqual(dxy, 0.0)
        self.assertAlmostEqual(dth, math.degrees(-3.0 - 3.0 + 2 * math.pi))

    def test_dead_reckoning_with_reversal_matches_odometry_only_when_signed(self):
        # drive +x for 1 m, back up 0.8 m, then forward 0.5 m (recorded odometry heading 0)
        xs = [i * 0.05 for i in range(21)] + [1.0 - i * 0.05 for i in range(1, 17)]
        xs += [xs[-1] + i * 0.05 for i in range(1, 11)]
        scans = [pose(x, 0.0, 0.0, ts=0.1 * i) for i, x in enumerate(xs)]
        self.assertLess(diagnose.dead_reckoning_error(scans, signed=True), 1e-9)
        self.assertGreater(diagnose.dead_reckoning_error(scans, signed=False), 0.5)

    def test_reverse_step_counter(self):
        scans = [pose(0, 0), pose(0.1, 0), pose(0.0, 0), pose(0.001, 0)]
        r = benchmark.odometry_reverse_steps(scans)
        self.assertEqual((r["moving_steps"], r["reversing_steps"]), (2, 1))  # last step < 2 cm ignored


class TimestampDiagnosticsTests(unittest.TestCase):
    def test_counts_short_backward_and_median(self):
        ts = [0.0, 0.001, 0.101, 0.100, 0.300]  # +1ms, +100ms, -1ms (backward), +200ms
        scans = [pose(0, 0, ts=t) for t in ts]
        d = benchmark.timestamp_diagnostics(scans)
        self.assertEqual(d["intervals"], 4)
        self.assertEqual(d["backward_or_zero_transitions"], 1)
        self.assertEqual(d["positive_short_intervals"], 1)
        self.assertAlmostEqual(d["median_positive_interval_s"], 0.1)


def install_recording_stub():
    calls = []

    class Laser:
        def __init__(self, *a, **k):
            pass

    class RMHC_SLAM:
        def __init__(self, laser, px, m, random_seed=0):
            self.m = m

        def update(self, ranges_mm, pose_change=(0, 0, 0)):
            calls.append(tuple(pose_change))

        def getpos(self):
            return (self.m * 500.0, self.m * 500.0, 0.0)

        def getmap(self, buf):
            buf[:] = bytes([127]) * len(buf)

    pkg, alg, sen = (types.ModuleType(n) for n in ("breezyslam", "breezyslam.algorithms", "breezyslam.sensors"))
    alg.RMHC_SLAM, sen.Laser = RMHC_SLAM, Laser
    pkg.algorithms, pkg.sensors = alg, sen
    names = ("breezyslam", "breezyslam.algorithms", "breezyslam.sensors")
    saved = {n: sys.modules.get(n) for n in names}
    sys.modules.update(dict(zip(names, (pkg, alg, sen))))
    return calls, saved


class OfflineDtPolicyTests(unittest.TestCase):
    """Stub SLAM records the pose_change (dxy_mm, dtheta_deg, dt_s) given for every scan."""

    # arrival timestamps with the dataset's pathologies: 1 ms pairs and a backward step
    TS = [1000.000, 1000.001, 1000.101, 1000.102, 1000.100, 1000.300, 1000.301, 1000.401]

    def setUp(self):
        self.calls, self.saved = install_recording_stub()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        lines = [f"FLASER 4 1.0 2.0 3.0 4.0 {0.05 * i} 0 0 {0.05 * i} 0 0 {t} nohost {t - 1000}"
                 for i, t in enumerate(self.TS)]
        (self.root / "s.clf").write_text("\n".join(lines) + "\n")

    def tearDown(self):
        for n, m in self.saved.items():
            if m is None:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = m
        self.tmp.cleanup()

    def run_offline(self, **over):
        self.calls.clear()
        base = dict(input=str(self.root / "s.clf"), hz=6.0, fov=180.0, max_range_m=12.0, map_pixels=20,
                    map_meters=10.0, seed=1, out_dir=str(self.root / f"out{len(over)}{over.get('dt_source', '')}"),
                    overwrite=False, runs=1, warmup=0)
        base.update(over)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            benchmark.command_offline(argparse.Namespace(**base))
        return [c[2] for c in self.calls[1:]]  # first scan has no odometry delta

    def test_default_uses_one_constant_dt_equal_to_median_positive_interval(self):
        dts = self.run_offline()
        positive = [b - a for a, b in zip(self.TS, self.TS[1:]) if b - a > 0]
        median = sorted(positive)[len(positive) // 2] if len(positive) % 2 else \
            sum(sorted(positive)[len(positive) // 2 - 1:len(positive) // 2 + 1]) / 2
        self.assertEqual(len(set(dts)), 1)
        self.assertAlmostEqual(dts[0], median)
        self.assertGreater(min(dts), 0.01)  # never the 1 ms arrival gap

    def test_recorded_option_reproduces_legacy_per_scan_dt(self):
        dts = self.run_offline(dt_source="recorded")
        self.assertLess(min(dts), 0.0015)            # the 1 ms arrival pairs reach the SLAM
        self.assertGreater(len(set(dts)), 1)
        self.assertTrue(all(d > 0 for d in dts))     # backward step replaced by the median

    def test_summary_json_records_dt_policy(self):
        self.run_offline()
        import json
        s = json.loads((self.root / "out0" / "offline_summary.json").read_text())
        self.assertEqual(s["dt_policy"]["dt_source"], "nominal")
        self.assertIsInstance(s["dt_policy"]["dt_seconds"], float)
        self.run_offline(dt_source="recorded")
        s = json.loads((self.root / "out1recorded" / "offline_summary.json").read_text())
        self.assertEqual(s["dt_policy"]["dt_source"], "recorded")


@unittest.skipUnless(HAVE_SCIPY, "numpy/scipy not installed")
class DiagnoseToolTests(unittest.TestCase):
    def room_scan(self, x, y, th, n=180):
        """Ranges of a 10 x 6 m room with an inner pillar-free wall layout, seen from (x, y, th)."""
        out = []
        for k in range(n):
            a = th + math.radians(-90 + k * 180 / (n - 1))
            c, s = math.cos(a), math.sin(a)
            best = 12.0
            for t in ((0 - x) / c if c < -1e-9 else None, (10 - x) / c if c > 1e-9 else None,
                      (0 - y) / s if s < -1e-9 else None, (6 - y) / s if s > 1e-9 else None):
                if t is not None and 0 < t < best:
                    best = t
            out.append(best)
        return out

    def test_icp_recovers_known_relative_pose(self):
        a, b = (3.0, 2.0, 0.1), (3.3, 2.1, 0.2)
        pa = diagnose.scan_points(self.room_scan(*a), max_range=11.9)
        pb = diagnose.scan_points(self.room_scan(*b), max_range=11.9)
        # pose of b in a's frame
        dx, dy = b[0] - a[0], b[1] - a[1]
        ca, sa = math.cos(a[2]), math.sin(a[2])
        truth = (ca * dx + sa * dy, -sa * dx + ca * dy, b[2] - a[2])
        x, y, th = diagnose.icp(pb, pa, (0.0, 0.0, 0.0))
        self.assertAlmostEqual(x, truth[0], delta=0.03)
        self.assertAlmostEqual(y, truth[1], delta=0.03)
        self.assertAlmostEqual(th, truth[2], delta=0.02)

    def test_scan_points_follow_breezyslam_convention(self):
        # index 0 at -90 deg (right), last index at +90 deg (left), CCW positive
        pts = diagnose.scan_points([1.0] * 5)
        self.assertAlmostEqual(pts[0][1], -1.0, places=6)
        self.assertAlmostEqual(pts[-1][1], 1.0, places=6)
        self.assertAlmostEqual(pts[2][0], 1.0, places=6)

    def test_velocity_compensation_explodes_for_millisecond_dt(self):
        scans = [pose(0, 0, 0.0, n=180), pose(0.055, 0, 0.05, n=180)]
        sh_bad, st_bad = diagnose.velocity_compensation(scans, [0.001], 6.0)
        sh_ok, st_ok = diagnose.velocity_compensation(scans, [0.1], 6.0)
        self.assertGreater(st_bad[0], 0.2)
        self.assertLess(st_ok[0], 0.05)
        self.assertGreater(sh_bad[0], 50 * sh_ok[0])


@unittest.skipUnless(INTEL.exists(), "committed intel.clf not present")
class CommittedDatasetFacts(unittest.TestCase):
    """Recomputed-from-raw anchors for the data the diagnosis was based on (read-only)."""

    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stderr(io.StringIO()):
            cls.scans = benchmark.load_scans(INTEL)

    def test_timestamp_facts(self):
        d = benchmark.timestamp_diagnostics(self.scans)
        self.assertEqual(d["backward_or_zero_transitions"], 631)
        self.assertEqual(d["positive_short_intervals"], 4552)

    def test_reversing_steps(self):
        self.assertEqual(benchmark.odometry_reverse_steps(self.scans)["reversing_steps"], 67)

    @unittest.skipUnless(HAVE_SCIPY, "numpy/scipy not installed")
    def test_signed_dxy_reduces_dead_reckoning_error_on_real_data(self):
        self.assertLess(diagnose.dead_reckoning_error(self.scans, True), 1.0)
        self.assertGreater(diagnose.dead_reckoning_error(self.scans, False), 4.0)


if __name__ == "__main__":
    unittest.main()
