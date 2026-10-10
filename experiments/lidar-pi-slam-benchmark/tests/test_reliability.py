"""Reliability tests: error reporting, interruption, figure/live-map failures, atomic writes and
timing-metadata definitions. Synthetic data and stubs only; the real BreezySLAM is never used.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import signal
import sys
import tempfile
import threading
import types
import unittest
from unittest import mock

BENCH_DIR = pathlib.Path(__file__).parents[1]
SCRIPTS = BENCH_DIR / "scripts"
REPO = pathlib.Path(__file__).parents[3]
INTEL = REPO / "data" / "lidar-pi-slam-benchmark" / "intel.clf"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


benchmark = load("benchmark")
live_publish = load("live_publish")
viewer = load("live_viewer")
try:
    import matplotlib  # noqa: F401
    import numpy  # noqa: F401
    HAVE_PLOTTING = True
except ImportError:
    HAVE_PLOTTING = False

SLAM_MODULES = ("breezyslam", "breezyslam.algorithms", "breezyslam.sensors")


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def run_main(argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    old = sys.argv
    sys.argv = ["benchmark.py"] + [str(a) for a in argv]
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch.dict(os.environ, env or {}):
            try:
                code = benchmark.main()
            except SystemExit as exc:
                code = exc.code
    finally:
        sys.argv = old
    return code, out.getvalue(), err.getvalue()


def write_clf(path, n=12):
    lines = [f"FLASER 4 1.0 2.0 3.0 4.0 {0.05 * i} 0 0 {0.05 * i} 0 0 {1000 + 0.1 * i} nohost {0.1 * i}"
             for i in range(n)]
    pathlib.Path(path).write_text("\n".join(lines) + "\n")


class Base(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._t.name)
        self.clf = self.dir / "s.clf"
        write_clf(self.clf)
        self._saved_modules = {n: sys.modules.get(n) for n in SLAM_MODULES}
        self.calls = []

    def tearDown(self):
        for n, m in self._saved_modules.items():
            if m is None:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = m
        self._t.cleanup()

    def files(self, d):
        d = pathlib.Path(d)
        return sorted(p.name for p in d.iterdir()) if d.exists() else []

    def install_stub(self, interrupt_at=None, getmap_error=None):
        """Stub BreezySLAM. update() raises KeyboardInterrupt on global call number `interrupt_at`."""
        calls, outer = self.calls, self

        class Laser:
            def __init__(self, *a, **k):
                pass

        class RMHC_SLAM:
            def __init__(self, laser, px, m, random_seed=0):
                self.m = m

            def update(self, ranges_mm, pose_change=(0, 0, 0)):
                calls.append(pose_change)
                if interrupt_at is not None and len(calls) == interrupt_at:
                    raise KeyboardInterrupt()

            def getpos(self):
                return (self.m * 500.0, self.m * 500.0, 0.0)  # always on the map

            def getmap(self, buf):
                if getmap_error:
                    raise getmap_error
                buf[:] = bytes([127]) * len(buf)

        pkg, alg, sen = (types.ModuleType(n) for n in SLAM_MODULES)
        alg.RMHC_SLAM, sen.Laser = RMHC_SLAM, Laser
        pkg.algorithms, pkg.sensors = alg, sen
        for n, m in zip(SLAM_MODULES, (pkg, alg, sen)):
            sys.modules[n] = m

    def argv(self, mode, out, *extra):
        base = [mode, "--input", self.clf, "--map-pixels", "20", "--map-meters", "1000", "--out-dir", out]
        if mode == "offline":
            base += ["--warmup", "2"]
        return base + list(extra)


# ---------------------------------------------------------------------------------- 1. error reporting
class ErrorReportingTests(Base):
    def test_user_errors_are_one_line_without_traceback(self):
        for argv in (["verify", "--input", self.dir / "missing.clf"],          # OSError
                     ["offline", "--input", self.clf, "--runs", "0"],           # ValueError
                     ["summary", "--mode", "offline", "--csv", self.dir / "x.csv"]):
            code, _, err = run_main(argv + ["--out-dir", self.dir / "o"])
            self.assertEqual(code, 2, argv)
            self.assertTrue(err.startswith("ERROR: "), err)
            self.assertNotIn("Traceback", err)
            self.assertEqual(len(err.strip().splitlines()), 1, err)

    def test_debug_flag_and_env_add_traceback_without_changing_exit_code(self):
        argv = ["offline", "--input", self.clf, "--runs", "0", "--out-dir", self.dir / "o"]
        for extra, env in (([], {"AUTONAV_DEBUG": "1"}), (["--debug"], {})):
            code, _, err = run_main(argv + extra, env)
            self.assertEqual(code, 2)
            self.assertIn("Traceback", err)
            self.assertIn("--runs must be an integer >= 1", err)
        code, _, err = run_main(argv, {"AUTONAV_DEBUG": "0"})
        self.assertNotIn("Traceback", err)

    def test_unexpected_exception_is_reported_as_internal_error_not_success_or_usage_error(self):
        def buggy(args):
            return {}["missing key"]
        with mock.patch.object(benchmark, "command_verify", buggy):
            code, out, err = run_main(["verify", "--input", self.clf, "--out-dir", self.dir / "o"])
        self.assertEqual(code, 70)
        self.assertNotIn(code, (0, 2))
        self.assertEqual(out, "")
        self.assertIn("INTERNAL ERROR (KeyError)", err)
        self.assertIn("test_reliability.py", err)          # where it happened
        self.assertIn("--debug", err)
        self.assertNotIn("Traceback", err)
        with mock.patch.object(benchmark, "command_verify", buggy):
            code, _, err = run_main(["verify", "--input", self.clf, "--out-dir", self.dir / "o", "--debug"])
        self.assertEqual(code, 70)
        self.assertIn("Traceback", err)

    def test_interrupt_outside_a_run_exits_130_with_a_message(self):
        def interrupted(args):
            raise KeyboardInterrupt()
        with mock.patch.object(benchmark, "command_verify", interrupted):
            code, _, err = run_main(["verify", "--input", self.clf, "--out-dir", self.dir / "o"])
        self.assertEqual(code, 130)
        self.assertIn("INTERRUPTED", err)

    def test_command_return_code_is_propagated(self):
        with mock.patch.object(benchmark, "command_verify", lambda a: 130):
            self.assertEqual(run_main(["verify", "--input", self.clf, "--out-dir", self.dir / "o"])[0], 130)

    def test_taxonomy(self):
        self.assertTrue(issubclass(benchmark.EnvironmentProblem, RuntimeError))
        self.assertIn(benchmark.EnvironmentProblem, benchmark.USER_ERRORS)
        for exc in (KeyError, TypeError, AttributeError, ZeroDivisionError, IndexError):
            self.assertFalse(issubclass(exc, benchmark.USER_ERRORS), exc)
        self.assertEqual((benchmark.EXIT_USER_ERROR, benchmark.EXIT_INTERNAL_ERROR, benchmark.EXIT_INTERRUPTED),
                         (2, 70, 130))


# ------------------------------------------------------------------------------- 2. interrupted paced
class PacedInterruptionTests(Base):
    def interrupted_paced(self, at=5, *extra):
        self.install_stub(interrupt_at=at)
        out = self.dir / "paced_out"
        code, stdout, err = run_main(self.argv("paced", out, "--hz", "1000", "--minutes", "1", *extra))
        return out, code, stdout, err

    def test_partial_results_are_preserved_and_marked_incomplete(self):
        out, code, stdout, err = self.interrupted_paced(at=5)
        self.assertEqual(code, 130)
        rows = benchmark.load_csv_rows(out / "paced_scan_timings.csv")
        self.assertEqual([int(r["index"]) for r in rows], [0, 1, 2, 3])   # the interrupted 5th scan is not invented
        s = json.loads((out / "paced_summary.json").read_text())
        self.assertEqual(s["run_status"], "interrupted")
        self.assertFalse(s["valid_for_performance_claims"], "an interrupted run is never valid for claims")
        self.assertTrue(s["pose_validity"]["valid_for_performance_claims"], "pose itself stayed on the map")
        self.assertEqual(s["scans_processed"], 4)
        inc = s["incomplete"]
        self.assertEqual((inc["scans_processed"], inc["requested_minutes"]), (4, 1.0))
        self.assertLess(inc["elapsed_minutes_at_last_scan"], 0.5)
        self.assertIn("INTERRUPTED", err)
        self.assertIn('"run_status": "interrupted"', stdout)

    def test_statistics_cover_only_processed_scans(self):
        out, *_ = self.interrupted_paced(at=6)
        rows = benchmark.load_csv_rows(out / "paced_scan_timings.csv")
        s = json.loads((out / "paced_summary.json").read_text())
        expected = benchmark.stats([int(r["processing_duration_ns"]) / 1e6 for r in rows])
        self.assertEqual(s["processing_latency_ms"], expected)
        self.assertEqual(len(rows), 5)

    def test_completed_run_is_marked_complete_and_valid(self):
        self.install_stub()
        out = self.dir / "ok"
        code, _, _ = run_main(self.argv("paced", out, "--hz", "1000", "--minutes", "0.0005"))
        self.assertEqual(code, 0)
        s = json.loads((out / "paced_summary.json").read_text())
        self.assertEqual((s["run_status"], s["incomplete"]), ("complete", None))
        self.assertTrue(s["valid_for_performance_claims"])

    def test_nothing_processed_writes_nothing(self):
        out, code, _, err = self.interrupted_paced(at=1)
        self.assertEqual(code, 130)
        self.assertIn("nothing was written", err)
        self.assertFalse(out.exists())

    def test_no_temp_files_and_summary_command_flags_the_interruption(self):
        out, *_ = self.interrupted_paced(at=4)
        self.assertEqual([n for n in self.files(out) if n.endswith(".tmp")], [])
        code, stdout, _ = run_main(["summary", "--mode", "paced", "--out-dir", out])
        self.assertEqual(code, 0)
        self.assertIn("RUN STATUS: INTERRUPTED", stdout)
        self.assertIn("NOT valid for performance claims", stdout)

    def test_existing_results_are_never_overwritten_by_a_later_interrupted_run(self):
        out = self.dir / "existing"
        out.mkdir()
        keep = out / "paced_scan_timings.csv"
        keep.write_text("precious\n")
        before = sha(keep)
        self.install_stub(interrupt_at=3)
        code, _, err = run_main(self.argv("paced", out, "--hz", "1000", "--minutes", "1"))
        self.assertEqual(code, 2)
        self.assertIn("Refusing to overwrite", err)
        self.assertEqual(sha(keep), before)
        self.assertEqual(self.calls, [], "the run must not even start")

    @unittest.skipUnless(HAVE_PLOTTING, "matplotlib/numpy not installed")
    def test_interrupted_figures_are_labelled_incomplete(self):
        out, *_ = self.interrupted_paced(at=4)
        s = json.loads((out / "paced_summary.json").read_text())
        self.assertTrue(s["figures"]["written"])
        self.assertIn("paced_slam_map.png", self.files(out))


# ------------------------------------------------------------------------------ interrupted offline
class OfflineInterruptionTests(Base):
    def run_offline(self, at, runs=3):
        self.install_stub(interrupt_at=at)
        out = self.dir / "off"
        code, stdout, err = run_main(self.argv("offline", out, "--runs", str(runs)))
        return out, code, stdout, err

    def test_completed_runs_are_kept_and_partial_run_is_discarded(self):
        out, code, _, err = self.run_offline(at=18)       # run 1 = calls 1-12; call 18 = run 2, scan 6
        self.assertEqual(code, 130)
        rows = benchmark.load_csv_rows(out / "offline_runs.csv")
        self.assertEqual({r["run"] for r in rows}, {"1"})
        self.assertEqual(len(rows), 10)                    # 12 scans - 2 warm-up
        s = json.loads((out / "offline_summary.json").read_text())
        self.assertEqual((s["run_status"], s["runs_requested"], s["runs_completed"], s["interrupted_during_run"]),
                         ("interrupted", 3, 1, 2))
        self.assertEqual([r["run"] for r in s["runs"]], [1])
        self.assertFalse(s["all_runs_valid_for_performance_claims"])
        self.assertIn("INCOMPLETE", s["note"])
        self.assertIn("discarded, not estimated", s["note"])
        self.assertEqual(s["figures"]["written"], False)
        self.assertIn("INTERRUPTED", err)

    def test_interrupt_during_first_run_writes_nothing(self):
        out, code, _, err = self.run_offline(at=4)
        self.assertEqual(code, 130)
        self.assertIn("nothing was written", err)
        self.assertFalse(out.exists())

    def test_partial_offline_summary_command_reports_interruption_and_only_completed_runs(self):
        out, *_ = self.run_offline(at=30)                  # inside run 3
        code, stdout, _ = run_main(["summary", "--mode", "offline", "--out-dir", out])
        self.assertEqual(code, 0)
        self.assertIn("RUN STATUS: INTERRUPTED", stdout)
        self.assertIn("median across 2 runs", stdout)

    def test_uninterrupted_offline_run_is_complete(self):
        self.install_stub()
        out = self.dir / "full"
        code, _, _ = run_main(self.argv("offline", out, "--runs", "2"))
        self.assertEqual(code, 0)
        s = json.loads((out / "offline_summary.json").read_text())
        self.assertEqual((s["run_status"], s["runs_completed"], s["interrupted_during_run"]), ("complete", 2, None))
        self.assertTrue(s["all_runs_valid_for_performance_claims"])


class SigtermHelperTests(unittest.TestCase):
    def test_handler_installed_and_restored(self):
        before = signal.getsignal(signal.SIGTERM)
        with benchmark.sigterm_as_keyboard_interrupt():
            self.assertNotEqual(signal.getsignal(signal.SIGTERM), before)
        self.assertEqual(signal.getsignal(signal.SIGTERM), before)

    def test_sigterm_becomes_keyboard_interrupt(self):
        before = signal.getsignal(signal.SIGTERM)
        with self.assertRaises(KeyboardInterrupt):
            with benchmark.sigterm_as_keyboard_interrupt():
                signal.raise_signal(signal.SIGTERM)
        self.assertEqual(signal.getsignal(signal.SIGTERM), before)

    def test_noop_outside_main_thread(self):
        result = {}

        def worker():
            try:
                with benchmark.sigterm_as_keyboard_interrupt():
                    result["ok"] = True
            except Exception as exc:  # pragma: no cover
                result["error"] = repr(exc)
        t = threading.Thread(target=worker)
        t.start()
        t.join()
        self.assertEqual(result, {"ok": True})


# --------------------------------------------------------------------------- figures never cost data
class FigureFailureTests(Base):
    def complete_offline(self, **stub):
        self.install_stub(**stub)
        out = self.dir / "o"
        code, _, err = run_main(self.argv("offline", out, "--runs", "1"))
        return out, code, err

    def test_missing_matplotlib_keeps_measurements_and_records_why(self):
        for n in ("matplotlib", "matplotlib.pyplot"):
            self.addCleanup(lambda n=n, v=sys.modules.get(n): sys.modules.__setitem__(n, v) if v is not None else sys.modules.pop(n, None))
        sys.modules["matplotlib"] = None
        sys.modules["matplotlib.pyplot"] = None
        out, code, err = self.complete_offline()
        self.assertEqual(code, 0)
        self.assertIn("offline_runs.csv", self.files(out))
        s = json.loads((out / "offline_summary.json").read_text())
        self.assertFalse(s["figures"]["written"])
        self.assertIn("matplotlib", s["figures"]["reason"])
        self.assertIn("figures not written", err)
        self.assertTrue(s["all_runs_valid_for_performance_claims"], "figure failure must not change validity")

    @unittest.skipUnless(HAVE_PLOTTING, "matplotlib/numpy not installed")
    def test_rendering_error_keeps_measurements_and_is_reported(self):
        out, code, err = self.complete_offline(getmap_error=RuntimeError("boom"))
        self.assertEqual(code, 0)
        s = json.loads((out / "offline_summary.json").read_text())
        self.assertEqual(s["figures"]["written"], False)
        self.assertIn("RuntimeError: boom", s["figures"]["reason"])
        self.assertIn("RuntimeError: boom", err)
        self.assertEqual(len(benchmark.load_csv_rows(out / "offline_runs.csv")), 10)

    @unittest.skipUnless(HAVE_PLOTTING, "matplotlib/numpy not installed")
    def test_success_records_written_files(self):
        out, code, _ = self.complete_offline()
        s = json.loads((out / "offline_summary.json").read_text())
        self.assertTrue(s["figures"]["written"])
        self.assertEqual(sorted(s["figures"]["files"]), ["offline_slam_map.png", "offline_trajectory.png"])


class AtomicWriteTests(unittest.TestCase):
    def test_write_csv_and_json_roundtrip_leave_no_temp(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            benchmark.write_csv(d / "a.csv", [{"x": 1, "y": 2}])
            benchmark.write_json(d / "a.json", {"k": [1, 2]})
            self.assertEqual(sorted(p.name for p in d.iterdir()), ["a.csv", "a.json"])
            self.assertEqual(benchmark.load_csv_rows(d / "a.csv"), [{"x": "1", "y": "2"}])
            self.assertEqual(json.loads((d / "a.json").read_text()), {"k": [1, 2]})

    def test_failed_replace_keeps_the_original_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "a.csv").write_text("original\n")
            (d / "a.json").write_text('{"original": true}')
            with mock.patch.object(benchmark.os, "replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    benchmark.write_csv(d / "a.csv", [{"x": 1}])
                with self.assertRaises(OSError):
                    benchmark.write_json(d / "a.json", {"new": 1})
            self.assertEqual((d / "a.csv").read_text(), "original\n")
            self.assertEqual(json.loads((d / "a.json").read_text()), {"original": True})
            self.assertEqual(sorted(p.name for p in d.iterdir()), ["a.csv", "a.json"])

    def test_csv_line_endings_are_not_doubled(self):
        with tempfile.TemporaryDirectory() as d:
            benchmark.write_csv(pathlib.Path(d) / "a.csv", [{"x": 1}])
            self.assertNotIn(b"\r\r", (pathlib.Path(d) / "a.csv").read_bytes())


# ----------------------------------------------------------------------------------- 3. live map
class FakeSlam:
    def __init__(self, error=None):
        self.error = error

    def getmap(self, buf):
        if self.error:
            raise self.error
        buf[:] = bytes([100]) * len(buf)


@unittest.skipUnless(HAVE_PLOTTING, "matplotlib/numpy not installed")
class LiveMapFailureTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._t.name)
        live_publish.LAST_MAP_ERROR = None

    def tearDown(self):
        live_publish.LAST_MAP_ERROR = None
        self._t.cleanup()

    def save(self, slam=None):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ok = live_publish.save_live_map(slam or FakeSlam(), self.dir, 8)
        return ok, err.getvalue()

    def test_success_writes_map_and_no_marker(self):
        ok, err = self.save()
        self.assertTrue(ok)
        self.assertEqual(err, "")
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), ["live_map.png"])
        self.assertIsNone(live_publish.LAST_MAP_ERROR)

    def test_missing_matplotlib_is_reported_not_swallowed(self):
        with mock.patch.dict(sys.modules, {"matplotlib": None, "matplotlib.pyplot": None}):
            ok, err = self.save()
            ok2, err2 = self.save()
        self.assertFalse(ok)
        self.assertFalse(ok2)
        self.assertIn("matplotlib/numpy not available", live_publish.LAST_MAP_ERROR)
        self.assertIn("WARNING: live map not updated", err)
        self.assertEqual(err2, "", "an unchanged reason is reported once, not on every retry")
        marker = self.dir / live_publish.MAP_ERROR_FILE
        self.assertIn("matplotlib", marker.read_text())
        self.assertFalse((self.dir / "live_map.png").exists())
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), [live_publish.MAP_ERROR_FILE])

    def test_rendering_error_is_reported_and_temp_file_removed(self):
        ok, err = self.save(FakeSlam(RuntimeError("boom")))
        self.assertFalse(ok)
        self.assertEqual(live_publish.LAST_MAP_ERROR, "RuntimeError: boom")
        self.assertIn("RuntimeError: boom", err)
        self.assertNotIn("live_map.tmp.png", [p.name for p in self.dir.iterdir()])

    def test_changed_reason_is_reported_again(self):
        self.save(FakeSlam(RuntimeError("one")))
        _, err = self.save(FakeSlam(ValueError("two")))
        self.assertIn("ValueError: two", err)

    def test_failed_refresh_hides_the_older_map_in_the_viewer_until_a_later_success(self):
        import time
        started = time.time() - 1.0
        self.assertTrue(self.save()[0])
        old = (self.dir / "live_map.png").read_bytes()
        path, msg = viewer.resolve_live_map(self.dir, run_started=started)
        self.assertEqual(path.name, "live_map.png")

        time.sleep(0.02)
        ok, _ = self.save(FakeSlam(RuntimeError("disk full")))
        self.assertFalse(ok)
        self.assertEqual((self.dir / "live_map.png").read_bytes(), old, "a failed refresh must not touch the old map")
        path, msg = viewer.resolve_live_map(self.dir, run_started=started)
        self.assertIsNone(path, "the older map would be presented as current")
        self.assertIn("failing", msg)
        self.assertIn("disk full", msg)

        time.sleep(0.02)
        self.assertTrue(self.save()[0])
        self.assertFalse((self.dir / live_publish.MAP_ERROR_FILE).exists())
        self.assertIsNotNone(viewer.resolve_live_map(self.dir, run_started=started)[0])

    def test_failure_without_any_map_still_explains_why(self):
        import time
        started = time.time() - 1.0
        self.save(FakeSlam(RuntimeError("no render")))
        path, msg = viewer.resolve_live_map(self.dir, run_started=started)
        self.assertIsNone(path)
        self.assertIn("no render", msg)

    def test_marker_from_an_earlier_run_is_ignored(self):
        import time
        self.save(FakeSlam(RuntimeError("old failure")))
        started = time.time() + 5.0               # the current run began after that marker was written
        (self.dir / "live_map.png").write_bytes(b"fresh")
        os.utime(self.dir / "live_map.png", (started + 1, started + 1))
        path, msg = viewer.resolve_live_map(self.dir, run_started=started)
        self.assertEqual(path.name, "live_map.png")


# --------------------------------------------------------------------------------- 4. metadata
class TimingRateTests(unittest.TestCase):
    TS = [0.0, 0.1, 0.2, 0.2, 0.1, 1.0]   # intervals .1, .1, 0, -.1, .9

    def test_definitions_on_a_deterministic_sequence(self):
        r = benchmark.timing_rates(self.TS)
        self.assertEqual((r["scan_count"], r["intervals"], r["positive_intervals"], r["zero_or_backward_intervals"]),
                         (6, 5, 3, 2))
        self.assertAlmostEqual(r["median_positive_interval_s"], 0.1)
        self.assertAlmostEqual(r["median_positive_interval_rate_hz"], 10.0)
        self.assertAlmostEqual(r["recording_span_s"], 1.0)
        self.assertAlmostEqual(r["mean_rate_hz_over_recording"], 5.0)   # 5 intervals / 1.0 s
        self.assertNotAlmostEqual(r["median_positive_interval_rate_hz"], r["mean_rate_hz_over_recording"])

    def test_notes_explain_nonpositive_intervals_and_that_neither_is_a_sensor_rate(self):
        text = " ".join(benchmark.timing_rates(self.TS)["notes"])
        for needle in ("NOT a sustained sensor rate", "excluded from the median", "backward", "arrival times"):
            self.assertIn(needle, text)

    def test_no_positive_intervals(self):
        r = benchmark.timing_rates([5.0, 5.0, 5.0])
        self.assertIsNone(r["median_positive_interval_s"])
        self.assertIsNone(r["median_positive_interval_rate_hz"])
        self.assertIsNone(r["mean_rate_hz_over_recording"])      # zero span
        self.assertEqual(r["zero_or_backward_intervals"], 2)

    def test_backward_steps_do_not_change_the_span(self):
        a = benchmark.timing_rates([0.0, 1.0, 2.0, 3.0])
        b = benchmark.timing_rates([0.0, 2.0, 1.0, 3.0])   # same max/min, one backward step
        self.assertEqual(a["recording_span_s"], b["recording_span_s"])
        self.assertEqual(a["mean_rate_hz_over_recording"], b["mean_rate_hz_over_recording"])
        self.assertEqual((a["zero_or_backward_intervals"], b["zero_or_backward_intervals"]), (0, 1))

    @unittest.skipUnless(INTEL.exists(), "committed intel.clf not present")
    def test_committed_dataset_values(self):
        with contextlib.redirect_stderr(io.StringIO()):
            scans = benchmark.load_scans(INTEL)
        r = benchmark.timing_rates([s["timestamp"] for s in scans])
        self.assertAlmostEqual(r["median_positive_interval_rate_hz"], 9.4753, places=3)
        self.assertAlmostEqual(r["mean_rate_hz_over_recording"], 5.0646, places=3)
        self.assertEqual(r["zero_or_backward_intervals"], 631)


class VerifyMetadataTests(Base):
    def test_verify_reports_honest_rate_names_and_sampling_note(self):
        out = self.dir / "v"
        code, stdout, _ = run_main(["verify", "--input", self.clf, "--out-dir", out])
        self.assertEqual(code, 0)
        d = json.loads((out / "dataset_summary.json").read_text())
        self.assertNotIn("nominal_hz_from_median_interval", d)
        self.assertIn("median_positive_interval_rate_hz", d["timing_rates"])
        self.assertIn("mean_rate_hz_over_recording", d["timing_rates"])
        sysm = d["system"]
        self.assertNotIn("cpu_percent_snapshot", sysm)
        self.assertIn("single readings", sysm["metadata_sampling_note"])
        self.assertIn("not sampled during the benchmark", sysm["metadata_sampling_note"])
        if "ram_total_bytes" in sysm:          # psutil present
            self.assertIn("system_cpu_percent_over_100ms_at_metadata_time", sysm)

    def test_historical_metadata_is_preserved_not_rewritten(self):
        hist = REPO / "results" / "lidar-pi-slam-benchmark" / "dataset_summary.json"
        if not hist.exists():
            self.skipTest("historical results not present")
        text = hist.read_text()
        self.assertIn("nominal_hz_from_median_interval", text)
        self.assertIn("cpu_percent_snapshot", text)
        self.assertNotIn("timing_rates", text)


# ----------------------------------------------------------------------------------- docs
class DocumentationTests(unittest.TestCase):
    def test_docs_describe_the_new_behaviour(self):
        readme = (BENCH_DIR / "README.md").read_text(encoding="utf-8")
        for needle in ("--debug", "AUTONAV_DEBUG", "130", "70", "run_status", "interrupted",
                       "median_positive_interval_rate_hz", "mean_rate_hz_over_recording",
                       "system_cpu_percent_over_100ms_at_metadata_time"):
            self.assertIn(needle, readme)
        live = (BENCH_DIR / "LIVE_VIEWER.md").read_text(encoding="utf-8")
        self.assertIn("live_map.error.txt", live)


if __name__ == "__main__":
    unittest.main()
