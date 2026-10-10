import importlib.util
import pathlib
import unittest

SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "benchmark.py"
spec = importlib.util.spec_from_file_location("benchmark", SCRIPT)
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class ParserTests(unittest.TestCase):
    def test_parse_flaser_record(self):
        line = "FLASER 4 1.0 2.0 3.0 4.0 1.5 2.5 0.1 1.5 2.5 0.1 123.0 122.9"
        scan = benchmark.parse_flaser_line(line, line_number=1)
        self.assertEqual(scan["ranges_m"], [1.0, 2.0, 3.0, 4.0])
        self.assertAlmostEqual(scan["x_m"], 1.5)
        self.assertAlmostEqual(scan["theta_rad"], 0.1)
        self.assertAlmostEqual(scan["timestamp"], 123.0)

    def test_malformed_count_fails(self):
        with self.assertRaises(ValueError):
            benchmark.parse_flaser_line("FLASER 3 1.0 2.0 1 2 0 1 2 3 4 5", 9)

    def test_non_scan_record_ignored(self):
        self.assertIsNone(benchmark.parse_flaser_line("ODOM 1 2 3 4 5", 2))


if __name__ == "__main__":
    unittest.main()
