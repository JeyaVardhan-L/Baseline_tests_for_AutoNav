"""
End-to-end pipeline integration and regression test.
Verifies the complete research workflow:
1. Dataset inspection (health, formats, rates).
2. Scan-to-scan ICP odometry execution.
3. Latency profiling and real-time margin derivation.
4. Export format structure (CSV, JSON, Markdown).
"""

import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.lidar.odometry import ICPOdometry
from autonav_baseline.timing.profiler import compute_distribution, evaluate_realtime_status
from autonav_baseline.reporting.exporter import ExperimentExporter


class TestPipelineIntegration(unittest.TestCase):
    def test_end_to_end_synthetic_pipeline(self):
        # 1. Dataset Inspection
        adapter = get_adapter("synthetic")
        inspection = adapter.inspect()

        self.assertEqual(inspection.name, "Synthetic Demonstration Stream")
        self.assertEqual(inspection.frame_count, 100)
        self.assertTrue(inspection.is_rate_measured)
        self.assertEqual(inspection.observed_rate_hz, 10.0)

        # 2. Odometry Processing
        odometry = ICPOdometry(voxel_size=0.20, max_correspondence_distance=1.5, max_iterations=20)
        frames = list(adapter.get_lidar_frames(max_frames=6))
        self.assertEqual(len(frames), 6)

        results = []
        for f in frames:
            step = odometry.process_frame(
                raw_points=f.points,
                frame_index=f.index,
                timestamp=f.timestamp,
            )
            results.append(step)

        self.assertEqual(len(results), 6)
        self.assertTrue(all(r.success for r in results))

        # Check trajectory accumulation
        positions = odometry.get_trajectory_positions()
        self.assertEqual(positions.shape, (6, 3))
        # Initial frame must be at origin (0, 0, 0)
        self.assertTrue(np.allclose(positions[0], [0.0, 0.0, 0.0]))

        # Check summary statistics
        summary = odometry.get_summary_statistics()
        self.assertEqual(summary["total_frames_processed"], 6)
        self.assertEqual(summary["successful_registrations"], 6)
        self.assertEqual(summary["failed_registrations"], 0)
        self.assertEqual(summary["success_rate_percent"], 100.0)

        # 3. Latency & Real-Time Evaluation
        latencies = [r.registration_latency_ms for r in results]
        lat_dist = compute_distribution(latencies)
        self.assertGreater(lat_dist["mean"], 0.0)
        self.assertGreater(lat_dist["p95"], 0.0)

        realtime = evaluate_realtime_status(lat_dist["p95"], sensor_period_ms=100.0)
        self.assertIn("status", realtime)
        self.assertIn("can_keep_up", realtime)

        # 4. Artifact Export Integrity
        with tempfile.TemporaryDirectory() as tmp_dir:
            exporter = ExperimentExporter("synthetic", "test_integration", base_results_dir=Path(tmp_dir))
            rows = [
                {
                    "frame_index": r.frame_index,
                    "timestamp": r.timestamp,
                    "latency_ms": r.registration_latency_ms,
                    "x": r.position_xyz[0],
                    "y": r.position_xyz[1],
                    "z": r.position_xyz[2],
                }
                for r in results
            ]
            csv_path = exporter.export_csv(rows, "metrics.csv")
            self.assertTrue(csv_path.exists())
            self.assertGreater(csv_path.stat().st_size, 0)

            json_path = exporter.export_json(summary, "summary.json")
            self.assertTrue(json_path.exists())
            self.assertGreater(json_path.stat().st_size, 0)

            md_path = exporter.write_summary_md(
                "Integration Test Summary",
                {"Frames": "6", "Success Rate": "100%"},
                conclusions=["Pipeline executed successfully."],
            )
            self.assertTrue(md_path.exists())
            self.assertGreater(md_path.stat().st_size, 0)

    def test_newer_college_unmeasured_when_empty(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            adapter = get_adapter("newer_college", root_path=Path(empty_dir))
            inspection = adapter.inspect()

            # Empty directory must NOT claim measurements or fake streams
            self.assertEqual(inspection.frame_count, 0)
            self.assertFalse(inspection.is_rate_measured)
            self.assertIsNone(inspection.observed_rate_hz)
            self.assertIsNone(inspection.approx_duration_s)

            # Generator must raise FileNotFoundError with actionable instructions
            with self.assertRaises(FileNotFoundError):
                list(adapter.get_lidar_frames(max_frames=1))


if __name__ == "__main__":
    unittest.main()
