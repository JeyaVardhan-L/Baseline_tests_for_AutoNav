#!/usr/bin/env python3
"""
Experiment 08 — Timestamp + Sensor Synchronization
Analyzes temporal alignment across multi-modal sensor streams:
  - LiDAR timestamps
  - Camera / Depth timestamps
  - IMU timestamps

Calculates nearest-neighbor cross-sensor timestamp offsets:
  - Mean offset
  - Median offset
  - P95 offset
  - Maximum offset

Plots timestamp offset distributions and explains requirements for:
  - LiDAR + IMU fusion (motion de-skewing & preintegration)
  - Camera + IMU fusion (visual-inertial odometry bundle adjustment)
  - LiDAR + Camera fusion (point cloud RGB colorization)
"""

import argparse
import sys
import time
from pathlib import Path
import numpy as np

# Add src to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.timing.jitter import compute_cross_sensor_offsets
from autonav_baseline.visualization.terminal import print_banner, print_section, print_field
from autonav_baseline.visualization.plots import save_plot
from autonav_baseline.reporting.exporter import ExperimentExporter


def main():
    parser = argparse.ArgumentParser(description="EXP-08: Cross-Sensor Timestamp Synchronization")
    parser.add_argument("--dataset", type=str, default="synthetic", help="Dataset name (synthetic, newer_college, hilti_2023, openloris)")
    parser.add_argument("--path", type=str, default=None, help="Custom dataset path")
    parser.add_argument("--max-lidar-frames", type=int, default=50, help="Max LiDAR frames to evaluate")
    parser.add_argument("--max-imu-samples", type=int, default=1000, help="Max IMU samples to evaluate")
    args = parser.parse_args()

    print_banner("EXPERIMENT 08 - TIMESTAMP + SENSOR SYNCHRONIZATION", f"Dataset: {args.dataset}")

    root_path = Path(args.path) if args.path else None
    adapter = get_adapter(args.dataset, root_path=root_path)

    lidar_ts = []
    imu_ts = []
    depth_ts = []

    try:
        # Collect LiDAR timestamps
        for f in adapter.get_lidar_frames(max_frames=args.max_lidar_frames):
            lidar_ts.append(f.timestamp)
    except (NotImplementedError, FileNotFoundError):
        pass

    try:
        # Collect Depth timestamps
        for f in adapter.get_depth_frames(max_frames=args.max_lidar_frames):
            depth_ts.append(f.timestamp)
    except (NotImplementedError, FileNotFoundError):
        pass

    try:
        # Collect IMU timestamps
        for f in adapter.get_imu_frames(max_frames=args.max_imu_samples):
            imu_ts.append(f.timestamp)
    except (NotImplementedError, FileNotFoundError):
        pass

    if len(lidar_ts) == 0 and len(depth_ts) == 0:
        print("[ERROR]: Neither LiDAR nor Camera timestamps were found.")
        sys.exit(1)

    if len(imu_ts) == 0:
        print("[ERROR]: IMU stream is required for cross-sensor synchronization analysis.")
        sys.exit(1)

    # Compute cross-sensor nearest-neighbor offsets
    lidar_to_imu = compute_cross_sensor_offsets(lidar_ts, imu_ts) if lidar_ts else None
    cam_to_imu = compute_cross_sensor_offsets(depth_ts, imu_ts) if depth_ts else None
    lidar_to_cam = compute_cross_sensor_offsets(lidar_ts, depth_ts) if (lidar_ts and depth_ts) else None

    print_section("COLLECTED SENSOR STREAMS")
    if lidar_ts:
        print_field("LiDAR Frames", len(lidar_ts), "scans", "MEASURED")
        print_field("LiDAR Epoch Span", f"{lidar_ts[0]:.3f}s -> {lidar_ts[-1]:.3f}s", "", "MEASURED")
    if depth_ts:
        print_field("Camera Frames", len(depth_ts), "frames", "MEASURED")
        print_field("Camera Epoch Span", f"{depth_ts[0]:.3f}s -> {depth_ts[-1]:.3f}s", "", "MEASURED")
    print_field("IMU Telemetry Packets", len(imu_ts), "packets", "MEASURED")
    print_field("IMU Epoch Span", f"{imu_ts[0]:.3f}s -> {imu_ts[-1]:.3f}s", "", "MEASURED")
    print()

    print_section("CROSS-SENSOR NEAREST-NEIGHBOR SYNCHRONIZATION OFFSETS (ms)")
    if lidar_to_imu:
        print("  [LiDAR to Nearest IMU Sample]:")
        print_field("    Mean Offset", round(lidar_to_imu["mean_offset_ms"], 3), "ms", "MEASURED")
        print_field("    Median Offset", round(lidar_to_imu["median_offset_ms"], 3), "ms", "MEASURED")
        print_field("    P95 Offset", round(lidar_to_imu["p95_offset_ms"], 3), "ms", "MEASURED")
        print_field("    Max Offset", round(lidar_to_imu["max_offset_ms"], 3), "ms", "MEASURED")
        print()

    if cam_to_imu:
        print("  [Camera to Nearest IMU Sample]:")
        print_field("    Mean Offset", round(cam_to_imu["mean_offset_ms"], 3), "ms", "MEASURED")
        print_field("    Median Offset", round(cam_to_imu["median_offset_ms"], 3), "ms", "MEASURED")
        print_field("    P95 Offset", round(cam_to_imu["p95_offset_ms"], 3), "ms", "MEASURED")
        print_field("    Max Offset", round(cam_to_imu["max_offset_ms"], 3), "ms", "MEASURED")
        print()

    if lidar_to_cam:
        print("  [LiDAR to Nearest Camera Frame]:")
        print_field("    Mean Offset", round(lidar_to_cam["mean_offset_ms"], 3), "ms", "MEASURED")
        print_field("    Median Offset", round(lidar_to_cam["median_offset_ms"], 3), "ms", "MEASURED")
        print_field("    P95 Offset", round(lidar_to_cam["p95_offset_ms"], 3), "ms", "MEASURED")
        print_field("    Max Offset", round(lidar_to_cam["max_offset_ms"], 3), "ms", "MEASURED")
    print("=" * 60)

    # Export results
    exporter = ExperimentExporter(args.dataset, "08_timestamp_analysis")

    # CSV export
    csv_rows = []
    if lidar_to_imu:
        for idx, (t, off) in enumerate(zip(lidar_ts, lidar_to_imu["offsets_ms"])):
            csv_rows.append({
                "index": idx,
                "modality": "lidar",
                "timestamp": t,
                "nearest_imu_offset_ms": round(off, 4),
            })
    exporter.export_csv(csv_rows)

    summary_data = {
        "dataset": args.dataset,
        "lidar_frames_count": len(lidar_ts),
        "camera_frames_count": len(depth_ts),
        "imu_samples_count": len(imu_ts),
        "lidar_to_imu_offsets_ms": lidar_to_imu,
        "camera_to_imu_offsets_ms": cam_to_imu,
        "lidar_to_cam_offsets_ms": lidar_to_cam,
    }
    exporter.export_json(summary_data)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Plot 1: Nearest-Neighbor Offset Timeline
    if lidar_to_imu:
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(range(len(lidar_to_imu["offsets_ms"])), lidar_to_imu["offsets_ms"], color="#1976D2", marker="o", markersize=3, label="LiDAR -> IMU Nearest Offset")
        ax.axhline(lidar_to_imu["mean_offset_ms"], color="#D32F2F", linestyle="--", label=f"Mean: {lidar_to_imu['mean_offset_ms']:.2f} ms")
        ax.axhline(lidar_to_imu["p95_offset_ms"], color="#FFA000", linestyle=":", label=f"P95: {lidar_to_imu['p95_offset_ms']:.2f} ms")
        ax.set_title(f"EXP-08: Cross-Sensor Synchronization Offset\nQuestion: How close in time is each LiDAR scan to an IMU measurement?\nDataset: {args.dataset}", fontsize=10)
        ax.set_xlabel("Scan Index")
        ax.set_ylabel("Nearest Neighbor Delta (ms)")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper right")
        save_plot(fig, exporter.figures_dir / "cross_sensor_offset_vs_time.png")

    # Plot 2: Offset Histogram
    if lidar_to_imu:
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.hist(lidar_to_imu["offsets_ms"], bins=20, color="#388E3C", edgecolor="white", alpha=0.85)
        ax.set_title(f"EXP-08: Synchronization Offset Distribution\nQuestion: What is the maximum temporal discrepancy before sensor fusion?\nDataset: {args.dataset}", fontsize=10)
        ax.set_xlabel("Offset (ms)")
        ax.set_ylabel("Frequency (frames)")
        ax.grid(True, linestyle=":", alpha=0.6)
        save_plot(fig, exporter.figures_dir / "cross_sensor_offset_histogram.png")

    exporter.write_summary_md(
        title="EXP-08: Timestamp & Synchronization Summary",
        metrics_dict={
            "LiDAR Scans Count": f"{len(lidar_ts)} [MEASURED]",
            "IMU Samples Count": f"{len(imu_ts)} [MEASURED]",
            "LiDAR-IMU Mean Offset": f"{lidar_to_imu['mean_offset_ms']:.3f} ms [MEASURED]" if lidar_to_imu else "N/A",
            "LiDAR-IMU P95 Offset": f"{lidar_to_imu['p95_offset_ms']:.3f} ms [MEASURED]" if lidar_to_imu else "N/A",
            "LiDAR-IMU Max Offset": f"{lidar_to_imu['max_offset_ms']:.3f} ms [MEASURED]" if lidar_to_imu else "N/A",
            "Cam-IMU Mean Offset": f"{cam_to_imu['mean_offset_ms']:.3f} ms [MEASURED]" if cam_to_imu else "N/A",
            "LiDAR-Cam Mean Offset": f"{lidar_to_cam['mean_offset_ms']:.3f} ms [MEASURED]" if lidar_to_cam else "N/A",
        },
        conclusions=[
            "LiDAR+IMU synchronization: At UAV cruise speeds (e.g., 5 m/s), a 20 ms time offset causes a 10 cm spatial state estimation error if uncompensated.",
            "High-frequency IMU telemetry (>= 200 Hz) ensures the maximum temporal distance to any visual or LiDAR frame is bounded within half the IMU sample period (<= 2.5 ms).",
            "Hardware triggering (PTP / PPS / hardware sync pulse) minimizes clock drift across distinct embedded microcontrollers.",
        ]
    )
    print(f"\n[DONE] Results and plots saved to {exporter.experiment_dir}")


if __name__ == "__main__":
    main()
