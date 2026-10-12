"""
End-to-end pipeline integration and regression test.
Verifies the complete research workflow on real-format point cloud files:
1. Real dataset inspection (health, formats, rates).
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
from autonav_baseline.datasets.newer_college import NewerCollegeAdapter
from autonav_baseline.lidar.odometry import ICPOdometry
from autonav_baseline.timing.profiler import compute_distribution, evaluate_realtime_status
from autonav_baseline.reporting.exporter import ExperimentExporter


class TestPipelineIntegration(unittest.TestCase):
    def test_end_to_end_real_format_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            seq_dir = Path(tmp_dir) / "01_short_experiment"
            pc_dir = seq_dir / "point_clouds"
            pc_dir.mkdir(parents=True)

            # Generate 50 points on a 5x5x2 spatial grid with distances > 1.0m from origin
            grid = []
            for x in range(1, 6):
                for y in range(1, 6):
                    grid.append([float(x), float(y), 1.0])
                    grid.append([float(x), float(y), 2.0])
            base_points = np.array(grid, dtype=np.float32)

            for i in range(5):
                # Shift each frame by 0.1m along X
                shifted = base_points + np.array([i * 0.1, 0.0, 0.0], dtype=np.float32)
                pcd_lines = [
                    "# .PCD v0.7",
                    "VERSION 0.7",
                    "FIELDS x y z",
                    "SIZE 4 4 4",
                    "TYPE F F F",
                    "COUNT 1 1 1",
                    f"WIDTH {len(shifted)}",
                    "HEIGHT 1",
                    f"POINTS {len(shifted)}",
                    "DATA ascii",
                ]
                for pt in shifted:
                    pcd_lines.append(f"{pt[0]:.4f} {pt[1]:.4f} {pt[2]:.4f}")
                (pc_dir / f"frame_{i:04d}.pcd").write_text("\n".join(pcd_lines) + "\n", encoding="utf-8")

            # Write authentic timestamps.csv
            ts_lines = ["timestamp_sec", "1600000000.0", "1600000000.1", "1600000000.2", "1600000000.3", "1600000000.4"]
            (seq_dir / "timestamps.csv").write_text("\n".join(ts_lines) + "\n", encoding="utf-8")

            # 1. Dataset Inspection
            adapter = get_adapter("newer_college", root_path=seq_dir)
            inspection = adapter.inspect()

            self.assertEqual(inspection.name, "Newer College Dataset (Oxford)")
            self.assertEqual(inspection.frame_count, 5)
            self.assertTrue(inspection.is_rate_measured)
            self.assertAlmostEqual(inspection.observed_rate_hz, 10.0, places=2)

            # 2. Odometry Processing
            odometry = ICPOdometry(voxel_size=0.05, max_correspondence_distance=1.0, max_iterations=25)
            frames = list(adapter.get_lidar_frames(max_frames=5))
            self.assertEqual(len(frames), 5)

            results = []
            for f in frames:
                step = odometry.process_frame(
                    raw_points=f.points,
                    frame_index=f.index,
                    timestamp=f.timestamp,
                )
                results.append(step)

            self.assertEqual(len(results), 5)
            self.assertTrue(all(r.success for r in results))

            # Check trajectory accumulation
            positions = odometry.get_trajectory_positions()
            self.assertEqual(positions.shape, (5, 3))
            self.assertTrue(np.allclose(positions[0], [0.0, 0.0, 0.0]))

            # Check summary statistics
            summary = odometry.get_summary_statistics()
            self.assertEqual(summary["total_frames_processed"], 5)
            self.assertEqual(summary["successful_registrations"], 5)
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
            exporter = ExperimentExporter("newer_college", "test_integration", base_results_dir=seq_dir / "results")
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
                {"Frames": "5", "Success Rate": "100%"},
                conclusions=["Real-format pipeline executed successfully."],
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
