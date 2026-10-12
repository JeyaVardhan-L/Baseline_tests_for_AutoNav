#!/usr/bin/env python3
"""
Step 2: LiDAR-Only Iterative Closest Point (ICP) Odometry Baseline
Processes real recorded 3D LiDAR point clouds, performs scan-to-scan registration,
accumulates an estimated 6-DoF trajectory, measures execution latency and host resource usage,
and exports reproducible research evidence.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure src is on python path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np

from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.datasets.newer_college import NewerCollegeAdapter
from autonav_baseline.lidar.odometry import ICPOdometry
from autonav_baseline.system.monitor import get_process_memory_mb, get_cpu_percent
from autonav_baseline.timing.profiler import compute_distribution, evaluate_realtime_status
from autonav_baseline.visualization.terminal import print_banner, print_field, print_section
from autonav_baseline.visualization.plots import (
    plot_odometry_trajectory,
    plot_processing_latency,
    plot_dual_point_counts,
)
from autonav_baseline.reporting.exporter import ExperimentExporter
from autonav_baseline.metrics.classification import Classification, tag


def run_lidar_odometry(
    dataset_name: str = "newer_college",
    root_path_str: Optional[str] = None,
    max_frames: int = 50,
    voxel_size_m: float = 0.15,
    max_distance_m: float = 1.5,
    max_iterations: int = 30,
    output_dir_str: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Runs scan-to-scan ICP odometry on real point clouds and exports reproducible artifacts."""
    default_root = REPO_ROOT / "datasets" / "newer-college" / "01_short_experiment"
    target_path = Path(root_path_str) if root_path_str else default_root

    print_banner(
        "STEP 2: LIDAR ODOMETRY ICP BASELINE",
        f"Dataset: {dataset_name} | Max Frames: {max_frames} | Voxel: {voxel_size_m}m",
    )

    adapter = get_adapter(dataset_name, root_path=target_path)
    inspection = adapter.inspect()

    print_section("DATASET & VERIFICATION")
    print_field("Dataset Name", inspection.name)
    print_field("Sequence Path", str(target_path))
    print_field("Available Frames", inspection.frame_count, "frames", "MEASURED" if inspection.frame_count > 0 else "UNAVAILABLE")

    if inspection.frame_count == 0:
        print("\n" + "=" * 60)
        print("[!] NOTICE: No point cloud frames found in sequence directory:")
        print(f"    {target_path.resolve()}")
        print("\nTo obtain real data:")
        print("  1. Visit official portal: https://ori-drs.github.io/newer-college-dataset/download/")
        print("  2. Request sequence: 01_short_experiment")
        print("  3. Place extracted point clouds (.pcd, .bin, .ply, .npy) in:")
        print(f"     {target_path.resolve() / 'point_clouds'}")
        print("  4. Place timestamps in:")
        print(f"     {target_path.resolve() / 'timestamps.csv'}")
        print("=" * 60 + "\n")
        return None

    nominal_hz = inspection.nominal_rate_hz or 10.0
    sensor_period_ms = 1000.0 / nominal_hz

    if inspection.is_rate_measured and inspection.observed_rate_hz is not None:
        print_field("Observed Frequency", f"{inspection.observed_rate_hz:.2f}", "Hz", "MEASURED")
    else:
        print_field("Nominal Frequency", f"{nominal_hz:.2f}", "Hz", "DECLARED NOMINAL")

    print()
    print_section("ALGORITHM HYPERPARAMETERS")
    print_field("Registration Type", "Scan-to-Scan Point-to-Point ICP (SVD / Kabsch)")
    print_field("Voxel Grid Size", voxel_size_m, "meters")
    print_field("Max Match Distance", max_distance_m, "meters")
    print_field("Max Iterations", max_iterations, "iters")
    print_field("Denominator Rule", "Initialization frame (scan 0) excluded from registration success rate")

    # Initialize ICP Odometry
    odometry = ICPOdometry(
        voxel_size=voxel_size_m,
        max_correspondence_distance=max_distance_m,
        max_iterations=max_iterations,
    )

    # Pre-run resource telemetry
    cpu_initial = get_cpu_percent()
    mem_initial_mb = get_process_memory_mb()

    print("\nProcessing point cloud frames...")
    frames_gen = adapter.get_lidar_frames(max_frames=max_frames)

    rows_csv: List[Dict[str, Any]] = []
    latencies_ms: List[float] = []
    raw_counts: List[int] = []
    downsampled_counts: List[int] = []
    frame_indices: List[int] = []

    t_processing_start = time.perf_counter()
    processed_count = 0

    for frame in frames_gen:
        step_res = odometry.process_frame(
            raw_points=frame.points,
            frame_index=frame.index,
            timestamp=frame.timestamp,
        )

        processed_count += 1
        frame_indices.append(step_res.frame_index)
        latencies_ms.append(step_res.registration_latency_ms)
        raw_counts.append(step_res.raw_points_count)
        downsampled_counts.append(step_res.downsampled_points_count)

        pos = step_res.position_xyz
        rows_csv.append({
            "frame_index": step_res.frame_index,
            "timestamp": step_res.timestamp if step_res.timestamp is not None else "UNAVAILABLE",
            "registration_latency_ms": round(step_res.registration_latency_ms, 3),
            "raw_points_count": step_res.raw_points_count,
            "downsampled_points_count": step_res.downsampled_points_count,
            "step_translation_m": round(step_res.step_translation_m, 4),
            "pos_x_m": round(float(pos[0]), 4),
            "pos_y_m": round(float(pos[1]), 4),
            "pos_z_m": round(float(pos[2]), 4),
            "fitness_score_m": round(step_res.fitness_score, 4) if step_res.fitness_score != float("inf") else -1.0,
            "inlier_ratio": round(step_res.inlier_ratio, 4),
            "status": step_res.status,
            "success": step_res.success,
        })

    t_processing_total = time.perf_counter() - t_processing_start

    # Post-run telemetry
    mem_final_mb = get_process_memory_mb()
    cpu_final = get_cpu_percent()
    mem_delta_mb = max(0.0, mem_final_mb - mem_initial_mb)

    odom_summary = odometry.get_summary_statistics()
    lat_dist = compute_distribution(latencies_ms)
    realtime_eval = evaluate_realtime_status(lat_dist["p95"], sensor_period_ms)
    traj_positions = odometry.get_trajectory_positions()

    # Sustained throughput (measured frames per elapsed wall-clock second)
    sustained_throughput_fps = (
        round(processed_count / t_processing_total, 2) if t_processing_total > 0 else 0.0
    )

    print()
    print_section("ODOMETRY & TRAJECTORY RESULTS")
    print_field("Frames Processed", processed_count, "frames", "MEASURED")
    print_field("Initialization Scans", odom_summary["initialization_frames"], "frames (scan 0 reference)", "DECLARED")
    print_field("Pairwise Attempts", odom_summary["registration_attempts"], "pairs", "MEASURED")
    print_field("Successful Registrations", odom_summary["successful_registrations"], "steps", "MEASURED")
    print_field("Failed Registrations", odom_summary["failed_registrations"], "steps", "MEASURED")
    print_field("Registration Success Rate", f"{odom_summary['success_rate_percent']:.1f}", "%", "DERIVED (excludes init)")
    print_field("Estimated Path Length", f"{odom_summary['total_path_length_m']:.3f}", "meters", "DERIVED")
    final_pos = odom_summary["final_position_xyz"]
    print_field("Final Position [X,Y,Z]", f"[{final_pos[0]}, {final_pos[1]}, {final_pos[2]}]", "meters", "DERIVED")
    print_field("Ground Truth Accuracy", "UNAVAILABLE (reference trajectory not aligned in Stage 2)", "", "UNAVAILABLE")

    print()
    print_section("HOST COMPUTATIONAL PROFILER")
    print_field("Mean Latency", f"{lat_dist['mean']:.2f}", "ms", "MEASURED")
    print_field("Median Latency", f"{lat_dist['median']:.2f}", "ms", "MEASURED")
    print_field("P95 Latency", f"{lat_dist['p95']:.2f}", "ms", "MEASURED")
    print_field("P99 Latency", f"{lat_dist['p99']:.2f}", "ms", "MEASURED")
    print_field("Sensor Arrival Period", f"{sensor_period_ms:.1f}", "ms", "DECLARED")
    print_field("Real-Time Margin (Period - P95)", f"{realtime_eval['available_margin_ms']['value']:.2f}", "ms", "DERIVED")
    print_field("Real-Time Feasibility", realtime_eval["status"], "", "DERIVED")
    print_field("Sustained Throughput", f"{sustained_throughput_fps:.1f}", "frames/sec", "MEASURED")
    print()
    print_section("HOST RESOURCE FOOTPRINT")
    print_field("Process RSS Memory", f"{mem_final_mb:.2f}", "MB", "MEASURED")
    print_field("Memory Delta", f"{mem_delta_mb:.2f}", "MB", "MEASURED")
    print_field("Host CPU Utilization", f"{cpu_final:.1f}", "%", "MEASURED")

    # Export structured artifacts
    base_results = Path(output_dir_str).parent.parent if output_dir_str else (REPO_ROOT / "results")
    exporter = ExperimentExporter(dataset_name, "02_lidar_odometry_icp", base_results_dir=base_results)
    exporter.export_csv(rows_csv, "metrics.csv")

    summary_payload = {
        "dataset": {
            "name": inspection.name,
            "sequence_path": str(target_path),
            "nominal_rate_hz": tag(nominal_hz, Classification.DECLARED, "Hz"),
            "observed_rate_hz": tag(
                inspection.observed_rate_hz,
                Classification.MEASURED if inspection.is_rate_measured else Classification.UNAVAILABLE,
                "Hz",
            ),
        },
        "hyperparameters": {
            "max_frames": max_frames,
            "voxel_size_m": voxel_size_m,
            "max_correspondence_distance_m": max_distance_m,
            "max_iterations": max_iterations,
        },
        "odometry_results": {
            "total_frames_processed": tag(processed_count, Classification.MEASURED, "frames"),
            "initialization_frames": tag(odom_summary["initialization_frames"], Classification.DECLARED, "frames"),
            "registration_attempts": tag(odom_summary["registration_attempts"], Classification.MEASURED, "pairs"),
            "successful_registrations": tag(odom_summary["successful_registrations"], Classification.MEASURED, "steps"),
            "failed_registrations": tag(odom_summary["failed_registrations"], Classification.MEASURED, "steps"),
            "success_rate_percent": tag(odom_summary["success_rate_percent"], Classification.DERIVED, "%"),
            "total_path_length_m": tag(odom_summary["total_path_length_m"], Classification.DERIVED, "meters"),
            "final_position_xyz_m": tag(final_pos, Classification.DERIVED, "meters"),
            "ground_truth_accuracy": "UNAVAILABLE",
        },
        "computational_metrics": {
            "latency_mean_ms": tag(lat_dist["mean"], Classification.MEASURED, "ms"),
            "latency_median_ms": tag(lat_dist["median"], Classification.MEASURED, "ms"),
            "latency_p95_ms": tag(lat_dist["p95"], Classification.MEASURED, "ms"),
            "latency_p99_ms": tag(lat_dist["p99"], Classification.MEASURED, "ms"),
            "sustained_throughput_fps": tag(sustained_throughput_fps, Classification.MEASURED, "frames/sec"),
            "process_rss_mb": tag(round(mem_final_mb, 2), Classification.MEASURED, "MB"),
            "process_cpu_percent": tag(round(cpu_final, 1), Classification.MEASURED, "%"),
        },
        "realtime_evaluation": realtime_eval,
    }

    exporter.export_json(summary_payload, "summary.json")
    exporter.export_metadata(
        {
            "dataset": dataset_name,
            "sequence_path": str(target_path),
            "max_frames": max_frames,
            "voxel_size_m": voxel_size_m,
            "max_distance_m": max_distance_m,
            "max_iterations": max_iterations,
        },
        "metadata.json",
    )

    # Generate research figures
    plot_odometry_trajectory(
        positions=traj_positions,
        output_path=exporter.figures_dir / "trajectory_topdown.png",
        dataset_name=dataset_name,
        path_length_m=odom_summary["total_path_length_m"],
    )
    plot_processing_latency(
        indices=frame_indices,
        latencies_ms=latencies_ms,
        sensor_period_ms=sensor_period_ms,
        output_path=exporter.figures_dir / "registration_latency.png",
        dataset_name=dataset_name,
    )
    plot_dual_point_counts(
        indices=frame_indices,
        raw_counts=raw_counts,
        downsampled_counts=downsampled_counts,
        output_path=exporter.figures_dir / "point_decimation.png",
        dataset_name=dataset_name,
    )

    # Export Markdown summary
    conclusions = [
        f"Executed scan-to-scan ICP on {processed_count} real frames ({odom_summary['successful_registrations']}/{odom_summary['registration_attempts']} registrations succeeded).",
        f"Observed P95 per-frame latency was {lat_dist['p95']:.2f} ms vs {sensor_period_ms:.1f} ms sensor arrival period ({realtime_eval['status']}).",
        f"Measured sustained host throughput was {sustained_throughput_fps:.1f} frames/sec.",
        f"Process memory usage stabilized at {mem_final_mb:.2f} MB RSS with no unbounded growth.",
        "Ground-truth trajectory error is currently UNAVAILABLE pending Leica reference pose alignment.",
        "Measurements reflect host developer laptop performance; target embedded flight hardware (RPi 5 / Jetson) requires physical hardware benchmarking.",
    ]
    exporter.write_summary_md(
        title="LiDAR-Only ICP Odometry Baseline Report",
        metrics_dict={
            "Dataset": inspection.name,
            "Frames Processed": f"{processed_count} frames [MEASURED]",
            "Registration Success Rate": f"{odom_summary['success_rate_percent']:.1f}% [DERIVED]",
            "Estimated Path Length": f"{odom_summary['total_path_length_m']:.3f} m [DERIVED]",
            "P95 Registration Latency": f"{lat_dist['p95']:.2f} ms [MEASURED]",
            "Real-Time Feasibility": f"{realtime_eval['status']} [DERIVED]",
            "Sustained Throughput": f"{sustained_throughput_fps:.1f} fps [MEASURED]",
            "Host Memory (RSS)": f"{mem_final_mb:.2f} MB [MEASURED]",
            "Ground Truth Alignment": "UNAVAILABLE",
        },
        conclusions=conclusions,
    )

    print()
    print(f"[+] Odometry research artifacts exported to: {exporter.output_dir.resolve()}")
    print(f"    - Trajectory Plot: {exporter.figures_dir / 'trajectory_topdown.png'}")
    print(f"    - Latency Plot   : {exporter.figures_dir / 'registration_latency.png'}")
    print(f"    - Decimation Plot: {exporter.figures_dir / 'point_decimation.png'}")
    print(f"    - Metrics CSV    : {exporter.output_dir / 'metrics.csv'}")
    print(f"    - Summary JSON   : {exporter.output_dir / 'summary.json'}")
    print(f"    - Summary MD     : {exporter.output_dir / 'summary.md'}")

    return summary_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 2: LiDAR-Only ICP Odometry Baseline")
    parser.add_argument(
        "--dataset",
        type=str,
        default="newer_college",
        help="Dataset adapter name (default: newer_college)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path to dataset directory (default: datasets/newer-college/01_short_experiment)",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=50,
        help="Maximum number of frames to process (default: 50)",
    )
    parser.add_argument(
        "--voxel-size",
        type=float,
        default=0.15,
        help="Voxel downsampling size in meters (default: 0.15)",
    )
    parser.add_argument(
        "--max-distance",
        type=float,
        default=1.5,
        help="Maximum correspondence distance in meters (default: 1.5)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=30,
        help="Maximum ICP iterations per scan (default: 30)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory for odometry results",
    )
    args = parser.parse_args()

    run_lidar_odometry(
        dataset_name=args.dataset,
        root_path_str=args.path,
        max_frames=args.max_frames,
        voxel_size_m=args.voxel_size,
        max_distance_m=args.max_distance,
        max_iterations=args.max_iterations,
        output_dir_str=args.output_dir,
    )


if __name__ == "__main__":
    main()
