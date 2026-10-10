import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "benchmark.py"
spec = importlib.util.spec_from_file_location("benchmark", SCRIPT)
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)

REPO = pathlib.Path(__file__).parents[3]
LEGACY_OFFLINE = REPO / "results" / "lidar-pi-slam-benchmark" / "offline_runs.csv"


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


class PercentileSemanticsTests(unittest.TestCase):
    def test_linear_interpolation_known_values(self):
        v = [4.0, 1.0, 3.0, 2.0]  # unsorted on purpose
        self.assertAlmostEqual(benchmark.percentile(v, 0), 1.0)
        self.assertAlmostEqual(benchmark.percentile(v, 50), 2.5)
        self.assertAlmostEqual(benchmark.percentile(v, 95), 3.85)  # idx 2.85 -> 3*.15 + 4*.85
        self.assertAlmostEqual(benchmark.percentile(v, 99), 3.97)
        self.assertAlmostEqual(benchmark.percentile(v, 100), 4.0)

    def test_single_sample_and_empty(self):
        self.assertEqual(benchmark.percentile([7.0], 99), 7.0)
        self.assertIsNone(benchmark.percentile([], 50))

    def test_method_is_documented_in_output(self):
        s = benchmark.summarize_runs({1: [1.0, 2.0]})
        self.assertIn("linear", s["percentile_method"])
        self.assertIn("(n-1)*p/100", s["percentile_method"])


class AggregateSemanticsTests(unittest.TestCase):
    # A=[1,1,1,10], B=[2,2,2,2], C=[3,3,3,3]: chosen so that median-of-run-statistics
    # differs from the statistic of the pooled samples for p95 and mean.
    RUNS = {1: [1.0, 1.0, 1.0, 10.0], 2: [2.0] * 4, 3: [3.0] * 4}

    def setUp(self):
        self.s = benchmark.summarize_runs(self.RUNS)

    def test_per_run(self):
        self.assertAlmostEqual(self.s["per_run"][1]["p95"], 8.65)  # idx 2.85 -> 1*.15 + 10*.85
        self.assertAlmostEqual(self.s["per_run"][1]["mean"], 3.25)
        self.assertEqual(self.s["per_run"][2]["median"], 2.0)
        self.assertEqual(self.s["per_run"][3]["n"], 4)

    def test_median_across_runs_is_median_of_run_statistics(self):
        m = self.s["median_across_runs"]
        self.assertAlmostEqual(m["p95"], 3.0)  # median(8.65, 2, 3)
        self.assertAlmostEqual(m["mean"], 3.0)  # median(3.25, 2, 3)
        self.assertAlmostEqual(m["median"], 2.0)  # median(1, 2, 3)
        self.assertAlmostEqual(m["max"], 3.0)  # median(10, 2, 3)

    def test_pooled_differs_from_median_across_runs(self):
        p = self.s["pooled"]
        self.assertEqual(p["n"], 12)
        self.assertAlmostEqual(p["p95"], 6.15)  # sorted idx 10.45 -> 3*.55 + 10*.45
        self.assertAlmostEqual(p["mean"], 33.0 / 12)
        self.assertAlmostEqual(p["max"], 10.0)
        self.assertNotAlmostEqual(p["p95"], self.s["median_across_runs"]["p95"])

    def test_worst_run(self):
        w = self.s["worst_run"]
        self.assertAlmostEqual(w["p95"], 8.65)
        self.assertEqual(w["max"], 10.0)

    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError):
            benchmark.summarize_runs({})


def offline_rows(per_run_ms, x_mm=5000.0):
    rows = []
    for run, vals in per_run_ms.items():
        for i, ms in enumerate(vals):
            rows.append({"run": str(run), "scan_index": str(20 + i), "processing_ms": str(ms),
                         "pose_x_mm": str(x_mm + 1000.0 * i), "pose_y_mm": "5000.0",
                         "pose_theta_deg": "0.0"})
    return rows


class CsvSummaryTests(unittest.TestCase):
    def test_offline_csv_summary_and_validity_from_poses(self):
        rows = offline_rows({1: [1.0, 2.0, 3.0], 2: [2.0, 3.0, 4.0]})
        s = benchmark.summarize_offline_csv(rows, map_meters=10.0)
        self.assertEqual(s["run_count"], 2)
        self.assertAlmostEqual(s["per_run"][1]["median"], 2.0)
        self.assertAlmostEqual(s["median_across_runs"]["median"], 2.5)
        self.assertEqual(s["pooled"]["n"], 6)
        v = s["pose_validity"]
        self.assertTrue(v["evaluated"])
        # x = 5000, 6000, 7000 -> all inside a 10 m map
        self.assertTrue(v["valid_for_performance_claims"])
        v = benchmark.summarize_offline_csv(rows, map_meters=5.5)["pose_validity"]
        # 5.5 m map: x=5000 is inside, 6000 and 7000 are outside -> 2 per run x 2 runs
        self.assertEqual(v["invalid_scans"], 4)
        self.assertEqual(v["first_invalid_scan_index"], (1, 21))

    def test_validity_not_evaluated_without_map_size(self):
        s = benchmark.summarize_offline_csv(offline_rows({1: [1.0]}))
        self.assertFalse(s["pose_validity"]["evaluated"])
        self.assertIn("NOT EVALUATED", benchmark.format_summary(s))

    def test_recorded_pose_in_map_column_is_used_when_map_size_not_given(self):
        rows = offline_rows({1: [1.0, 2.0, 3.0]})
        for r, flag in zip(rows, ("True", "True", "False")):
            r["pose_in_map"] = flag
        v = benchmark.summarize_offline_csv(rows)["pose_validity"]
        self.assertTrue(v["evaluated"])
        self.assertIn("recorded during the run", v["source"])
        self.assertEqual((v["invalid_scans"], v["first_invalid_scan_index"]), (1, (1, 22)))
        self.assertIn("INVALID", benchmark.format_summary(benchmark.summarize_offline_csv(rows)))

    def test_caller_supplied_map_size_is_labelled_as_such(self):
        v = benchmark.summarize_offline_csv(offline_rows({1: [1.0]}), map_meters=10.0)["pose_validity"]
        self.assertIn("caller-supplied", v["source"])

    def test_wrong_csv_for_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            benchmark.summarize_paced_csv(offline_rows({1: [1.0]}))
        with self.assertRaises(ValueError):
            benchmark.summarize_offline_csv([{"index": "0", "processing_duration_ns": "1"}])

    def test_paced_csv_summary(self):
        rows = [{"index": str(i), "processing_duration_ns": str(int(ms * 1e6)),
                 "start_lateness_ns": "50000", "processing_budget_exceeded": "False",
                 "deadline_missed": "True" if i == 1 else "False",
                 "pose_x_mm": "100.0", "pose_y_mm": "100.0"} for i, ms in enumerate([1.0, 2.0, 3.0])]
        s = benchmark.summarize_paced_csv(rows, map_meters=10.0)
        self.assertEqual(s["scans"], 3)
        self.assertAlmostEqual(s["processing_ms"]["median"], 2.0)
        self.assertAlmostEqual(s["start_lateness_ms"]["median"], 0.05)
        self.assertEqual(s["deadline_misses"], 1)
        self.assertEqual(s["processing_budget_exceedances"], 0)
        self.assertTrue(s["pose_validity"]["valid_for_performance_claims"])

    def test_format_labels_every_aggregate_and_flags_invalid(self):
        text = benchmark.format_summary(
            benchmark.summarize_offline_csv(offline_rows({1: [1.0, 2.0], 2: [3.0, 4.0]}), map_meters=5.5))
        for label in ("[per run 1]", "[per run 2]", "median across 2 runs", "worst run", "pooled over all 4"):
            self.assertIn(label, text)
        self.assertIn("percentile method", text)
        self.assertIn("INVALID", text)
        self.assertIn("NOT valid for performance claims", text)


class SummaryCommandPreservesDataTests(unittest.TestCase):
    def test_summary_is_read_only_and_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            csv_path = d / "offline_runs.csv"
            benchmark.write_csv(csv_path, offline_rows({1: [1.0, 2.0], 2: [2.0, 3.0]}))
            before = {p.name: sha(p) for p in d.iterdir()}
            ns = argparse.Namespace(mode="offline", csv=None, out_dir=str(d), map_meters=None,
                                    json=False, output=None, overwrite=False)
            with contextlib.redirect_stdout(io.StringIO()):
                benchmark.command_summary(ns)
            self.assertEqual({p.name: sha(p) for p in d.iterdir()}, before)

            ns.output = str(d / "agg.json")
            with contextlib.redirect_stdout(io.StringIO()):
                benchmark.command_summary(ns)
            self.assertEqual(json.loads((d / "agg.json").read_text())["mode"], "offline")
            self.assertEqual(sha(csv_path), before["offline_runs.csv"])
            with self.assertRaises(FileExistsError):
                with contextlib.redirect_stdout(io.StringIO()):
                    benchmark.command_summary(ns)

    def test_missing_csv_fails_instead_of_falling_back_to_other_mode(self):
        with tempfile.TemporaryDirectory() as d:
            benchmark.write_csv(pathlib.Path(d) / "paced_scan_timings.csv",
                                [{"index": "0", "processing_duration_ns": "1", "start_lateness_ns": "0"}])
            ns = argparse.Namespace(mode="offline", csv=None, out_dir=d, map_meters=None,
                                    json=False, output=None, overwrite=False)
            with self.assertRaises(FileNotFoundError):
                benchmark.command_summary(ns)


@unittest.skipUnless(LEGACY_OFFLINE.exists(), "committed historical offline CSV not present")
class HistoricalMeasurementTests(unittest.TestCase):
    """Reads (never writes) the committed Raspberry Pi 5 measurements.

    Expected values are recomputed-from-raw regression anchors, not copied from a screenshot.
    """

    @classmethod
    def setUpClass(cls):
        cls.before = sha(LEGACY_OFFLINE)
        cls.summary = benchmark.summarize_offline_csv(benchmark.load_csv_rows(LEGACY_OFFLINE), map_meters=35.0)

    def test_raw_file_untouched(self):
        self.assertEqual(sha(LEGACY_OFFLINE), self.before)

    def test_shape(self):
        self.assertEqual(self.summary["run_count"], 5)
        self.assertEqual(self.summary["pooled"]["n"], 5 * 13611)

    def test_median_of_run_p99_is_not_the_screenshot_value(self):
        m = self.summary["median_across_runs"]["p99"]
        self.assertAlmostEqual(m, 4.1670, places=3)
        self.assertGreater(abs(m - 4.20), 0.02)
        # pooled P99 is a different statistic and is reported separately
        self.assertAlmostEqual(self.summary["pooled"]["p99"], 4.168, places=3)

    def test_old_35m_map_is_flagged_invalid_by_the_new_check(self):
        v = self.summary["pose_validity"]
        self.assertFalse(v["valid_for_performance_claims"])
        self.assertEqual(v["invalid_scans"], 5 * 10688)
        self.assertEqual(v["first_invalid_scan_index"], (1, 2943))


if __name__ == "__main__":
    unittest.main()
