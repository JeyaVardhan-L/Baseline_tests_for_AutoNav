"""Regression tests for CLI/reporting hardening: run counts, map args, invalid latencies,
diagnostic run selection, result provenance and the live-viewer map source.

Synthetic data and stubs only; nothing here exercises the real BreezySLAM.
"""
import argparse
import contextlib
import importlib.util
import io
import json
import math
import pathlib
import platform
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

BENCH_DIR = pathlib.Path(__file__).parents[1]
SCRIPTS = BENCH_DIR / "scripts"
REPO = pathlib.Path(__file__).parents[3]


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


benchmark = load("benchmark")
diagnose = load("diagnose_inputs")
viewer = load("live_viewer")
try:
    import numpy  # noqa: F401
    import scipy  # noqa: F401
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False


def run_main(argv):
    """Run the real CLI entry point; return (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    old = sys.argv
    sys.argv = ["benchmark.py"] + [str(a) for a in argv]
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = benchmark.main()
            except SystemExit as exc:  # argparse errors
                code = exc.code
    finally:
        sys.argv = old
    return code, out.getvalue(), err.getvalue()


def write_clf(path, n=12):
    lines = [f"FLASER 4 1.0 2.0 3.0 4.0 {0.05 * i} 0 0 {0.05 * i} 0 0 {1000 + 0.1 * i} nohost {0.1 * i}"
             for i in range(n)]
    pathlib.Path(path).write_text("\n".join(lines) + "\n")


class Tmp(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._t.name)
        self.clf = self.dir / "s.clf"
        write_clf(self.clf)

    def tearDown(self):
        self._t.cleanup()

    def files(self, d):
        return sorted(p.name for p in pathlib.Path(d).iterdir()) if pathlib.Path(d).exists() else []


class RunCountTests(Tmp):
    def test_zero_and_negative_runs_exit_nonzero_and_write_nothing(self):
        for bad in ("0", "-1", "-7"):
            out = self.dir / f"o{bad}"
            code, stdout, stderr = run_main(["offline", "--input", self.clf, "--runs", bad, "--out-dir", out])
            self.assertEqual(code, 2, bad)
            self.assertIn("--runs must be an integer >= 1", stderr)
            self.assertNotIn("all_runs_valid", stdout)
            self.assertEqual(self.files(out), [], "no summary may be written for an empty benchmark")

    def test_negative_warmup_and_warmup_larger_than_recording_rejected(self):
        code, _, err = run_main(["offline", "--input", self.clf, "--warmup", "-1", "--out-dir", self.dir / "w1"])
        self.assertEqual(code, 2)
        self.assertIn("--warmup", err)
        code, _, err = run_main(["offline", "--input", self.clf, "--warmup", "12", "--out-dir", self.dir / "w2"])
        self.assertEqual(code, 2)
        self.assertIn("no scan would be timed", err)
        self.assertEqual(self.files(self.dir / "w2"), [])

    def test_check_run_args_unit(self):
        ok = argparse.Namespace(runs=1, warmup=0)
        benchmark.check_run_args(ok)
        for runs in (0, -2, 1.5, True, None):
            with self.assertRaises(ValueError):
                benchmark.check_run_args(argparse.Namespace(runs=runs, warmup=0))

    def test_paced_minutes_must_be_positive_and_finite(self):
        for bad in ("0", "-1", "nan", "inf"):
            code, _, err = run_main(["paced", "--input", self.clf, "--minutes", bad, "--out-dir", self.dir / f"p{bad}"])
            self.assertEqual(code, 2, bad)
            self.assertIn("--minutes must be finite and > 0", err)

    def test_empty_run_list_is_never_valid(self):
        # the aggregate flag expression used by command_offline
        runs = []
        self.assertFalse(bool(runs) and all(r["pose_validity"]["valid_for_performance_claims"] for r in runs))


class MapArgumentTests(Tmp):
    BAD = ("0", "-5", "nan", "inf", "-inf")

    def test_verify_rejects_invalid_map_meters(self):
        for bad in self.BAD:
            out = self.dir / f"v{bad}"
            code, _, err = run_main(["verify", "--input", self.clf, f"--map-meters={bad}", "--out-dir", out])
            self.assertEqual(code, 2, bad)
            self.assertIn("--map-meters must be finite and > 0", err)
            self.assertEqual(self.files(out), [])

    def test_verify_accepts_valid_map_meters(self):
        code, stdout, _ = run_main(["verify", "--input", self.clf, "--map-meters", "50", "--out-dir", self.dir / "ok"])
        self.assertEqual(code, 0)
        self.assertIn("dataset_summary.json", self.files(self.dir / "ok"))

    def test_offline_and_verify_share_the_same_rule(self):
        for bad in self.BAD:
            ns = argparse.Namespace(map_meters=bad and float(bad), map_pixels=100)
            with self.assertRaises(ValueError):
                benchmark.check_map_args(ns)
        with self.assertRaises(ValueError):
            benchmark.check_map_args(argparse.Namespace(map_meters=10.0, map_pixels=0))
        benchmark.check_map_args(argparse.Namespace(map_meters=10.0))  # verify has no map_pixels

    def test_summary_rejects_invalid_map_meters(self):
        csv_path = self.dir / "offline_runs.csv"
        benchmark.write_csv(csv_path, [{"run": "1", "scan_index": "20", "processing_ms": "1.0",
                                        "pose_x_mm": "5000", "pose_y_mm": "5000", "pose_theta_deg": "0"}])
        for bad in self.BAD:
            code, _, err = run_main(["summary", "--mode", "offline", "--csv", csv_path, f"--map-meters={bad}"])
            self.assertEqual(code, 2, bad)
            self.assertIn("--map-meters must be finite and > 0", err)

    def test_positive_finite_rejects_non_numbers(self):
        for bad in (None, "5", True, [1], 0, -1.0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                benchmark.positive_finite("map_meters", bad)
        self.assertEqual(benchmark.positive_finite("map_meters", 130.0), 130.0)


class SensorArgumentTests(Tmp):
    def test_invalid_sensor_arguments_rejected_before_any_work(self):
        for mode in ("offline", "paced"):
            for flag, bad in (("--hz", "0"), ("--hz", "-1"), ("--hz", "nan"), ("--fov", "0"), ("--fov", "inf"),
                              ("--max-range-m", "0"), ("--max-range-m", "-3")):
                out = self.dir / f"{mode}{flag}{bad}"
                code, _, err = run_main([mode, "--input", self.clf, f"{flag}={bad}", "--out-dir", out])
                self.assertEqual(code, 2, (mode, flag, bad))
                self.assertIn(f"{flag} must be finite and > 0", err)
                self.assertFalse(out.exists())

    def test_check_sensor_args_accepts_defaults(self):
        benchmark.check_sensor_args(argparse.Namespace(hz=6.0, fov=180.0, max_range_m=12.0))


class InvalidLatencyTests(Tmp):
    def offline_csv(self, values):
        rows = [{"run": "1", "scan_index": str(20 + i), "processing_ms": v,
                 "pose_x_mm": "5000", "pose_y_mm": "5000", "pose_theta_deg": "0"} for i, v in enumerate(values)]
        path = self.dir / "offline_runs.csv"
        benchmark.write_csv(path, rows)
        return path

    def test_negative_nan_and_inf_latencies_are_rejected_not_summarised(self):
        for bad in ("-1.0", "nan", "inf", "-inf"):
            path = self.offline_csv(["1.0", bad, "2.0"])
            code, stdout, err = run_main(["summary", "--mode", "offline", "--csv", path])
            self.assertEqual(code, 2, bad)
            self.assertIn("invalid latency", err)
            self.assertIn("run 1", err)
            self.assertEqual(stdout, "", "no statistics may be printed for invalid samples")

    def test_summarize_runs_rejects_invalid_directly(self):
        for bad in (float("nan"), float("inf"), -0.001):
            with self.assertRaises(ValueError):
                benchmark.summarize_runs({1: [1.0, bad]})
        benchmark.summarize_runs({1: [0.0, 1.0]})  # zero is a legitimate (if odd) value

    def test_paced_negative_duration_rejected(self):
        rows = [{"index": "0", "processing_duration_ns": "-5", "start_lateness_ns": "0",
                 "processing_budget_exceeded": "False", "deadline_missed": "False",
                 "pose_x_mm": "1", "pose_y_mm": "1"}]
        with self.assertRaises(ValueError):
            benchmark.summarize_paced_csv(rows)
        rows[0].update(processing_duration_ns="5", start_lateness_ns="-1")
        with self.assertRaises(ValueError):
            benchmark.summarize_paced_csv(rows)

    def test_valid_data_still_summarised(self):
        code, stdout, _ = run_main(["summary", "--mode", "offline", "--csv", self.offline_csv(["1.0", "2.0", "3.0"])])
        self.assertEqual(code, 0)
        self.assertIn("pooled over all 3 samples", stdout)


@unittest.skipUnless(HAVE_SCIPY, "numpy/scipy not installed")
class DiagnosticRunSelectionTests(Tmp):
    def csv(self, runs=(1, 2), scan0=20, mode="offline"):
        rows = []
        for r in runs:
            for i in range(5):
                row = {"scan_index": str(scan0 + i), "pose_x_mm": "17500", "pose_y_mm": "17500", "pose_theta_deg": "0"}
                if mode == "offline":
                    row = {"run": str(r), **row}
                else:
                    row = {"index": str(scan0 + i), **{k: v for k, v in row.items() if k != "scan_index"}}
                rows.append(row)
        path = self.dir / f"{mode}.csv"
        benchmark.write_csv(path, rows)
        return path

    def ns(self, path, **over):
        base = dict(input=str(self.clf), csv=str(path), mode="offline", run=1, map_meters=35.0, limit=11,
                    every=1, tolerance_m=5.0)
        base.update(over)
        return argparse.Namespace(**base)

    def compare(self, ns):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            diagnose.cmd_compare(ns)
        return out.getvalue()

    def test_nonexistent_run_fails_clearly_and_lists_available_runs(self):
        with self.assertRaises(ValueError) as cm:
            self.compare(self.ns(self.csv(), run=9))
        self.assertIn("run 9 does not exist", str(cm.exception))
        self.assertIn("[1, 2]", str(cm.exception))

    def test_main_exits_nonzero_for_nonexistent_run(self):
        path = self.csv()
        argv = ["diagnose_inputs.py", "compare", "--input", str(self.clf), "--csv", str(path), "--mode", "offline",
                "--run", "9", "--map-meters", "35"]
        old, sys.argv = sys.argv, argv
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
                code = diagnose.main()
        finally:
            sys.argv = old
        self.assertEqual(code, 2)
        self.assertIn("does not exist", err.getvalue())

    def test_no_overlap_with_reference_range_fails_instead_of_reporting_none(self):
        with self.assertRaises(ValueError) as cm:
            self.compare(self.ns(self.csv(scan0=5000)))
        self.assertIn("no usable observations", str(cm.exception))
        self.assertIn("not evidence", str(cm.exception))

    def test_wrong_csv_columns_and_bad_args_rejected(self):
        with self.assertRaises(ValueError):
            self.compare(self.ns(self.csv(mode="paced"), mode="offline"))  # paced CSV has no run/scan_index
        for over in (dict(map_meters=0), dict(map_meters=float("nan")), dict(tolerance_m=-1), dict(limit=0)):
            with self.assertRaises(ValueError):
                self.compare(self.ns(self.csv(), **over))

    def test_existing_run_reports_how_many_poses_were_compared(self):
        text = self.compare(self.ns(self.csv(scan0=2)))
        # either "first scan ... (N poses compared)" or "no compared pose (N) was > ..."; both state N
        self.assertTrue("poses compared" in text or "no compared pose (5)" in text, text)


class ProvenanceTests(Tmp):
    def write(self, with_flag=False, meta=None, name="offline"):
        rows = []
        for i in range(3):
            r = {"run": "1", "scan_index": str(20 + i), "processing_ms": "1.0",
                 "pose_x_mm": "5000", "pose_y_mm": "5000", "pose_theta_deg": "0"}
            if with_flag:
                r["pose_in_map"] = "True"
            rows.append(r)
        benchmark.write_csv(self.dir / "offline_runs.csv", rows)
        if meta is not None:
            (self.dir / f"{name}_summary.json").write_text(meta if isinstance(meta, str) else json.dumps(meta))
        return self.dir / "offline_runs.csv"

    def prov(self, **kw):
        path = self.write(**kw)
        rows = benchmark.load_csv_rows(path)
        return benchmark.load_provenance(path, "offline", rows), path

    META = {"mode": "offline", "system": {"platform": "Linux-6.18-rpi-2712-aarch64", "machine": "aarch64",
                                          "python": "3.13.5 (main)", "timestamp_utc": "2026-10-10T10:46:56+00:00"}}

    def test_recorded_platform_comes_from_metadata_and_flags_other_machine(self):
        p, path = self.prov(meta=self.META)
        self.assertEqual(p["recorded_platform"], "Linux-6.18-rpi-2712-aarch64")
        self.assertEqual(p["recorded_machine"], "aarch64")
        self.assertEqual(p["recorded_python"], "3.13.5")
        self.assertFalse(p["measured_on_this_machine"])
        self.assertEqual(p["source_csv"], str(path.resolve()))
        self.assertEqual(p["current_machine"], platform.platform())

    def test_same_platform_is_reported_as_this_machine(self):
        meta = json.loads(json.dumps(self.META))
        meta["system"]["platform"] = platform.platform()
        p, _ = self.prov(meta=meta)
        self.assertTrue(p["measured_on_this_machine"])

    def test_missing_metadata_is_stated_not_inferred(self):
        p, _ = self.prov(meta=None)
        self.assertIsNone(p["recorded_platform"])
        self.assertIsNone(p["measured_on_this_machine"])
        self.assertIn("UNKNOWN", p["note"])
        self.assertIn("not inferred", p["note"])

    def test_unreadable_or_mismatched_metadata_is_unknown(self):
        for meta in ("{not json", {"mode": "paced", "system": self.META["system"]},
                     {"mode": "offline"}, {"mode": "offline", "system": {"machine": "x"}}):
            p, _ = self.prov(meta=meta)
            self.assertIsNone(p["recorded_platform"], meta)
            self.assertIn("UNKNOWN", p["note"])

    def test_legacy_vs_current_schema_is_distinguished(self):
        legacy, _ = self.prov(with_flag=False, meta=self.META)
        current, _ = self.prov(with_flag=True, meta=self.META)
        self.assertIn("legacy schema", legacy["result_generation"])
        self.assertIn("historical", legacy["result_generation"])
        self.assertIn("current schema", current["result_generation"])

    def test_summary_command_text_and_json_carry_provenance(self):
        self.write(meta=self.META)
        code, stdout, _ = run_main(["summary", "--mode", "offline", "--out-dir", self.dir])
        self.assertEqual(code, 0)
        for needle in ("source CSV:", "result generation: legacy schema", "recorded platform: Linux-6.18-rpi-2712-aarch64",
                       "DIFFERENT machine", "this machine:"):
            self.assertIn(needle, stdout)
        code, stdout, _ = run_main(["summary", "--mode", "offline", "--out-dir", self.dir, "--json"])
        self.assertEqual(json.loads(stdout)["provenance"]["recorded_machine"], "aarch64")

    def test_summary_text_says_unknown_when_metadata_missing(self):
        self.write(meta=None)
        code, stdout, _ = run_main(["summary", "--mode", "offline", "--out-dir", self.dir])
        self.assertEqual(code, 0)
        self.assertIn("recorded platform: UNKNOWN", stdout)
        self.assertNotIn("measured on", stdout)

    def test_provenance_never_modifies_the_inputs(self):
        path = self.write(meta=self.META)
        before = {p.name: p.read_bytes() for p in self.dir.iterdir() if p.suffix in (".csv", ".json")}
        run_main(["summary", "--mode", "offline", "--out-dir", self.dir])
        after = {p.name: p.read_bytes() for p in self.dir.iterdir() if p.suffix in (".csv", ".json")}
        self.assertEqual(before, after)

    @unittest.skipUnless((REPO / "results" / "lidar-pi-slam-benchmark" / "offline_summary.json").exists(),
                         "committed historical results not present")
    def test_committed_historical_results_are_labelled_legacy_with_recorded_platform(self):
        d = REPO / "results" / "lidar-pi-slam-benchmark"
        rows = benchmark.load_csv_rows(d / "offline_runs.csv")
        p = benchmark.load_provenance(d / "offline_runs.csv", "offline", rows)
        self.assertIn("legacy schema", p["result_generation"])
        self.assertIn("aarch64", p["recorded_platform"])
        self.assertEqual(p["measured_on_this_machine"], platform.platform() == p["recorded_platform"])


class LiveViewerMapSourceTests(Tmp):
    def setUp(self):
        super().setUp()
        self._saved = (viewer.Handler.state, viewer.Handler.state_seen, viewer.Handler.run_started, viewer.DEFAULT_OUT)
        viewer.Handler.state, viewer.Handler.state_seen, viewer.Handler.run_started = (
            {"running": False, "mode": "waiting"}, 0.0, None)

    def tearDown(self):
        (viewer.Handler.state, viewer.Handler.state_seen, viewer.Handler.run_started, viewer.DEFAULT_OUT) = self._saved
        super().tearDown()

    def age(self, path, seconds):
        import os
        t = path.stat().st_mtime - seconds
        os.utime(path, (t, t))

    def test_no_map_gives_message_and_no_path(self):
        path, msg = viewer.resolve_live_map(self.dir, run_started=1.0)
        self.assertIsNone(path)
        self.assertIn("live_map.png", msg)
        self.assertIn("--output-dir", msg)

    def test_legacy_35m_map_is_never_used(self):
        (self.dir / "slam_map.png").write_bytes(b"legacy invalid map")
        path, msg = viewer.resolve_live_map(self.dir, run_started=1.0)
        self.assertIsNone(path)
        self.assertIn("ignored", msg)
        self.assertIn("known-invalid", msg)

    def test_final_mode_maps_are_not_substituted(self):
        for n in ("paced_slam_map.png", "offline_slam_map.png"):
            (self.dir / n).write_bytes(b"x")
        self.assertIsNone(viewer.resolve_live_map(self.dir, run_started=1.0)[0])

    def test_fresh_live_map_is_served(self):
        import time
        started = time.time()
        (self.dir / "live_map.png").write_bytes(b"png")
        path, msg = viewer.resolve_live_map(self.dir, run_started=started - 0.01)
        self.assertEqual(path.name, "live_map.png")
        self.assertIsNone(msg)

    def test_stale_live_map_from_earlier_run_is_not_served(self):
        import time
        m = self.dir / "live_map.png"
        m.write_bytes(b"MAP FROM AN EARLIER RUN")
        self.age(m, 86400)
        path, msg = viewer.resolve_live_map(self.dir, run_started=time.time())
        self.assertIsNone(path)
        self.assertIn("stale", msg)

    def test_live_map_without_any_telemetry_is_not_served(self):
        (self.dir / "live_map.png").write_bytes(b"left over")
        path, msg = viewer.resolve_live_map(self.dir)  # run_started unknown
        self.assertIsNone(path)
        self.assertIn("no telemetry", msg)

    def serve(self):
        viewer.DEFAULT_OUT = self.dir
        server = viewer.ThreadingHTTPServer(("127.0.0.1", 0), viewer.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        return f"http://127.0.0.1:{server.server_address[1]}"

    def post(self, base, payload):
        req = urllib.request.Request(base + "/api/update", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with contextlib.redirect_stdout(io.StringIO()):
            return urllib.request.urlopen(req, timeout=5).status

    def state(self, base):
        with contextlib.redirect_stdout(io.StringIO()):
            return json.loads(urllib.request.urlopen(base + "/api/state", timeout=5).read())

    def test_posted_telemetry_is_visible_to_later_requests(self):
        # Regression: state used to be stored on the per-request handler instance and lost.
        base = self.serve()
        self.assertEqual(self.post(base, {"mode": "paced replay", "scans_processed": 42, "processing_ms": 1.5}), 200)
        st = self.state(base)
        self.assertEqual((st["mode"], st["scans_processed"], st["processing_ms"]), ("paced replay", 42, 1.5))
        self.assertTrue(st["running"])

    def test_http_never_serves_legacy_or_stale_map_and_serves_a_fresh_one(self):
        import time
        (self.dir / "slam_map.png").write_bytes(b"legacy invalid map")
        stale = self.dir / "live_map.png"
        stale.write_bytes(b"STALE")
        self.age(stale, 3600)
        base = self.serve()
        st = self.state(base)
        self.assertFalse(st["map_available"])
        self.assertIn("no telemetry", st["map_message"])
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(base + "/map.png", timeout=5)
        self.assertEqual(cm.exception.code, 404)
        # run starts: first telemetry arrives; the old file is older than that -> still stale
        self.post(base, {"mode": "paced replay", "scans_processed": 1})
        self.assertFalse(self.state(base)["map_available"])
        self.assertIn("stale", self.state(base)["map_message"])
        # the run writes its first snapshot -> served
        time.sleep(0.02)
        stale.write_bytes(b"\x89PNGfresh")
        st = self.state(base)
        self.assertTrue(st["map_available"])
        self.assertEqual(urllib.request.urlopen(base + "/map.png", timeout=5).read(), b"\x89PNGfresh")

    def test_new_run_makes_the_previous_runs_map_stale(self):
        import time
        base = self.serve()
        self.post(base, {"mode": "paced replay", "scans_processed": 500})
        time.sleep(0.02)
        (self.dir / "live_map.png").write_bytes(b"run one map")
        self.assertTrue(self.state(base)["map_available"])
        time.sleep(0.02)
        self.post(base, {"mode": "paced replay", "scans_processed": 1})  # counter reset = new run
        st = self.state(base)
        self.assertFalse(st["map_available"], "previous run's map must not be shown for the new run")
        self.assertIn("stale", st["map_message"])

    def test_gap_in_telemetry_starts_a_new_run(self):
        import time
        base = self.serve()
        self.post(base, {"scans_processed": 10})
        first = viewer.Handler.run_started
        viewer.Handler.state_seen -= 10.0  # simulate a >3 s silence
        time.sleep(0.01)
        self.post(base, {"scans_processed": 11})
        self.assertGreater(viewer.Handler.run_started, first)

    def test_page_shows_the_server_message_for_a_missing_map(self):
        self.assertIn("map_message", viewer.HTML)


class DirectoryCreationTests(Tmp):
    """Failed runs must not leave empty output directories; success must create them."""

    def setUp(self):
        super().setUp()
        self._saved = {n: sys.modules.get(n) for n in ("breezyslam", "breezyslam.algorithms", "breezyslam.sensors")}

    def tearDown(self):
        for n, m in self._saved.items():
            if m is None:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = m
        super().tearDown()

    def hide_breezyslam(self):
        for n in self._saved:
            sys.modules[n] = None  # makes `import` raise ImportError, even if the library is installed

    def test_missing_breezyslam_leaves_no_directory(self):
        self.hide_breezyslam()
        for mode, extra in (("offline", ["--warmup", "1"]), ("paced", ["--minutes", "0.001"])):
            out = self.dir / f"new_{mode}"
            code, _, err = run_main([mode, "--input", self.clf, "--out-dir", out] + extra)
            self.assertEqual(code, 2)
            self.assertIn("BreezySLAM is not importable", err)
            self.assertFalse(out.exists(), f"{mode}: failed run created {out}")

    def test_failure_with_preexisting_directory_leaves_its_contents_untouched(self):
        self.hide_breezyslam()
        out = self.dir / "mine"
        out.mkdir()
        (out / "notes.txt").write_text("keep me")
        code, _, err = run_main(["offline", "--input", self.clf, "--warmup", "1", "--out-dir", out])
        self.assertEqual(code, 2)
        self.assertIn("BreezySLAM is not importable", err)
        self.assertEqual(self.files(out), ["notes.txt"])
        self.assertEqual((out / "notes.txt").read_text(), "keep me")

    def test_invalid_arguments_and_bad_input_create_nothing(self):
        bad = self.dir / "bad.clf"
        bad.write_text("FLASER 3 1 2\n")
        cases = [["offline", "--input", bad], ["paced", "--input", bad],
                 ["offline", "--input", self.clf, "--runs", "0"]]
        for i, argv in enumerate(cases):
            out = self.dir / f"o{i}"
            code, _, _ = run_main(argv + ["--out-dir", out])
            self.assertEqual(code, 2)
            self.assertFalse(out.exists())

    def test_successful_run_still_creates_the_directory(self):
        import types

        class Laser:
            def __init__(self, *a, **k):
                pass

        class RMHC_SLAM:
            def __init__(self, l, px, m, random_seed=0):
                self.m = m

            def update(self, r, pose_change=(0, 0, 0)):
                pass

            def getpos(self):
                return (self.m * 500.0, self.m * 500.0, 0.0)

            def getmap(self, b):
                b[:] = bytes([127]) * len(b)

        pkg, alg, sen = (types.ModuleType(n) for n in self._saved)
        alg.RMHC_SLAM, sen.Laser = RMHC_SLAM, Laser
        pkg.algorithms, pkg.sensors = alg, sen
        for n, m in zip(self._saved, (pkg, alg, sen)):
            sys.modules[n] = m
        out = self.dir / "fresh" / "nested"
        code, _, err = run_main(["offline", "--input", self.clf, "--runs", "1", "--warmup", "1", "--map-pixels", "20",
                                 "--map-meters", "10", "--out-dir", out])
        self.assertEqual(code, 0, err)
        self.assertIn("offline_runs.csv", self.files(out))
        self.assertIn("offline_summary.json", self.files(out))


class SystemMetadataProbeTests(unittest.TestCase):
    def test_source_has_no_shell_redirect_or_popen(self):
        src = (SCRIPTS / "benchmark.py").read_text(encoding="utf-8")
        self.assertNotIn("2>/dev/null", src)
        self.assertNotIn("os.popen", src)

    def meta(self, which, run=None):
        from unittest import mock
        fake_run = run if run is not None else mock.Mock(side_effect=AssertionError("vcgencmd must not be run"))
        with mock.patch.object(benchmark.shutil, "which", return_value=which), \
                mock.patch.object(benchmark.subprocess, "run", side_effect=fake_run):
            return benchmark.system_metadata()

    def test_absent_vcgencmd_is_not_probed_and_recorded_as_not_measured(self):
        self.assertIsNone(self.meta(None)["throttled_state"])

    def test_vcgencmd_output_is_recorded(self):
        import subprocess
        cp = subprocess.CompletedProcess(["vcgencmd"], 0, stdout="throttled=0x0\n", stderr="")
        self.assertEqual(self.meta("/usr/bin/vcgencmd", run=lambda *a, **k: cp)["throttled_state"], "throttled=0x0")

    def test_vcgencmd_failures_are_recorded_as_not_measured(self):
        import subprocess
        bad = subprocess.CompletedProcess(["vcgencmd"], 1, stdout="error=1", stderr="")
        self.assertIsNone(self.meta("/x/vcgencmd", run=lambda *a, **k: bad)["throttled_state"])

        def boom(*a, **k):
            raise OSError("exec failed")
        self.assertIsNone(self.meta("/x/vcgencmd", run=boom)["throttled_state"])

        def slow(*a, **k):
            raise subprocess.TimeoutExpired("vcgencmd", 5)
        self.assertIsNone(self.meta("/x/vcgencmd", run=slow)["throttled_state"])

    def test_no_platform_specific_values_are_invented(self):
        m = self.meta(None)
        for key in ("platform", "machine", "python", "cpu_count", "timestamp_utc"):
            self.assertIn(key, m)
        if platform.system() != "Linux":
            self.assertIsNone(m["cpu_temperature_c"])
            self.assertIsNone(m["cpu_governor"])


class DocumentationConsistencyTests(unittest.TestCase):
    def test_readme_describes_both_clocks(self):
        text = (BENCH_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("perf_counter_ns", text)
        self.assertIn("monotonic_ns", text)
        self.assertNotIn("Per-scan processing time uses `time.perf_counter_ns()`.", text)

    def test_live_viewer_doc_has_no_stale_OUT_and_documents_no_fallback(self):
        text = (BENCH_DIR / "LIVE_VIEWER.md").read_text(encoding="utf-8")
        self.assertNotIn("save_live_map(slam, OUT", text)
        self.assertIn("save_live_map(slam, out_dir", text)
        self.assertIn("does **not** fall back", text)


    def test_dependencies_are_described_accurately(self):
        readme = (BENCH_DIR / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("NumPy is used for summaries", readme)
        req = (BENCH_DIR / "requirements.txt").read_text(encoding="utf-8")
        for pkg in ("numpy", "matplotlib", "psutil", "scipy"):
            self.assertIn(pkg, req)
        self.assertIn("diagnose_inputs.py", req)

    def help_flags(self, main_fn, argv_prefix, subcommands):
        import re
        flags = set()
        for sub in subcommands:
            out = io.StringIO()
            old = sys.argv
            sys.argv = argv_prefix + sub + ["-h"]
            try:
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                    try:
                        main_fn()
                    except SystemExit:
                        pass
            finally:
                sys.argv = old
            flags |= set(re.findall(r"(?<![\w-])--[a-z][a-z-]*", out.getvalue()))
        return flags

    def test_every_flag_in_the_docs_exists_in_some_parser(self):
        import re
        known = self.help_flags(benchmark.main, ["benchmark.py"], [[c] for c in ("verify", "offline", "paced", "summary", "plot")])
        known |= self.help_flags(diagnose.main, ["diagnose_inputs.py"], [["inputs"], ["compare"]])
        known |= self.help_flags(viewer.main, ["live_viewer.py"], [[]])
        known |= {"--help"}
        missing = {}
        for doc in ("README.md", "LIVE_VIEWER.md", "DATASET_NOTES.md"):
            text = (BENCH_DIR / doc).read_text(encoding="utf-8")
            code = "\n".join(re.findall(r"```(?:bash)?\n(.*?)```", text, flags=re.S))
            for flag in set(re.findall(r"(?<![\w-])--[a-z][a-z-]*", code)):
                if flag not in known:
                    missing.setdefault(doc, []).append(flag)
        self.assertEqual(missing, {}, "flags used in documented commands that no parser defines")

    def test_documented_script_paths_exist(self):
        import re
        for doc in ("README.md", "LIVE_VIEWER.md"):
            text = (BENCH_DIR / doc).read_text(encoding="utf-8")
            for rel in set(re.findall(r"experiments/lidar-pi-slam-benchmark/[\w./-]+\.(?:py|sh|txt|json)", text)):
                self.assertTrue((REPO / rel).exists(), f"{doc} references missing {rel}")


if __name__ == "__main__":
    unittest.main()
