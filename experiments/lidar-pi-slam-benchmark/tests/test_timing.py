import importlib.util
import pathlib
import unittest

SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "benchmark.py"
spec = importlib.util.spec_from_file_location("benchmark", SCRIPT)
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class TimingTests(unittest.TestCase):
    def test_budget_at_six_hz(self):
        self.assertAlmostEqual(benchmark.period_seconds(6.0), 1.0 / 6.0)

    def test_deadline_classification_separates_duration_and_lateness(self):
        period = benchmark.period_seconds(6.0)
        result = benchmark.classify_timing(
            scheduled_ns=1_000_000_000,
            start_ns=1_010_000_000,
            finish_ns=1_100_000_000,
            period_ns=int(period * 1e9),
        )
        self.assertFalse(result["processing_budget_exceeded"])
        self.assertFalse(result["deadline_missed"])


if __name__ == "__main__":
    unittest.main()
