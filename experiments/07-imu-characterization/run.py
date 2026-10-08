#!/usr/bin/env python3
"""
Experiment 07 — IMU Characterization
Analyzes high-frequency Inertial Measurement Unit (IMU) telemetry:
  1. Computes sampling rate, interval distribution, and timing jitter
  2. Detects dropped packets or irregularities in timestamp delta
  3. Characterizes accelerometer (X, Y, Z, Norm) and gyroscope (X, Y, Z, Norm)
  4. Generates 4 engineering diagnostic graphs:
     - Acceleration vs. Time
     - Angular Velocity (Gyro) vs. Time
     - Inter-sample Delta Time vs. Time
     - Histogram of Sampling Intervals
"""

import argparse
import sys
import time
from pathlib import Path
import numpy as np

# Add src to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.imu.statistics import compute_imu_statistics
from autonav_baseline.visualization.terminal import print_banner, print_section, print_field
from autonav_baseline.visualization.plots import save_plot, plot_imu_intervals
from autonav_baseline.reporting.exporter import ExperimentExporter


def main():
    parser = argparse.ArgumentParser(description="EXP-07: IMU Characterization")
    parser.add_argument("--dataset", type=str, default="synthetic", help="Dataset name (synthetic, newer_college, hilti_2023, openloris)")
    parser.add_argument("--path", type=str, default=None, help="Custom dataset path")
    parser.add_argument("--max-samples", type=int, default=1000, help="Maximum IMU samples to analyze")
    parser.add_argument("--expected-hz", type=float, default=200.0, help="Nominal manufacturer IMU frequency (Hz)")
    args = parser.parse_args()

    print_banner("EXPERIMENT 07 - IMU CHARACTERIZATION", f"Dataset: {args.dataset}")

    root_path = Path(args.path) if args.path else None
    adapter = get_adapter(args.dataset, root_path=root_path)

    timestamps = []
    accels = []
    gyros = []

    try:
        imu_iter = adapter.get_imu_frames(max_frames=args.max_samples)
        for frame in imu_iter:
            timestamps.append(frame.timestamp)
            accels.append(frame.accel)
            gyros.append(frame.gyro)
    except FileNotFoundError as e:
        print(f"\n[ERROR]: {e}")
        sys.exit(1)

    if len(timestamps) < 2:
        print("Insufficient IMU samples collected (need at least 2).")
        sys.exit(1)

    accel_arr = np.asarray(accels, dtype=np.float64)
    gyro_arr = np.asarray(gyros, dtype=np.float64)

    stats = compute_imu_statistics(timestamps, accel_arr, gyro_arr)
    expected_dt_ms = 1000.0 / args.expected_hz

    print_section("IMU TIMING & SAMPLING RATE")
    print_field("Samples Analyzed", stats["num_samples"]["value"], "samples", "MEASURED")
    print_field("Stream Duration", stats["duration_s"]["value"], "seconds", "MEASURED")
    print_field("Nominal Sensor Rate", args.expected_hz, "Hz", "ASSUMED", "Manufacturer specification")
    print_field("Observed Sampling Rate", stats["observed_frequency_hz"]["value"], "Hz", "DERIVED", "1000 / mean interval")
    print_field("Mean Sample Interval", stats["mean_interval_ms"]["value"], "ms", "MEASURED")
    print_field("Timing Jitter (Std Dev)", stats["jitter_ms"]["value"], "ms", "MEASURED", "Inter-sample variance")
    print_field("Min / Max Interval", f"{stats['min_interval_ms']['value']} / {stats['max_interval_ms']['value']}", "ms", "MEASURED")
    print_field("Suspected Dropped Samples", stats["suspected_dropped_packets"]["value"], "samples", "DERIVED", "dt > 1.8x mean interval")
    print()

    print_section("ACCELEROMETER MEASUREMENTS (m/s^2)")
    print_field("Mean Accel [X, Y, Z]", stats["accel"]["mean_xyz_mps2"], "m/s^2", "MEASURED")
    print_field("Noise / Std [X, Y, Z]", stats["accel"]["std_xyz_mps2"], "m/s^2", "MEASURED")
    print_field("Mean Norm Magnitude", stats["accel"]["mean_norm_mps2"], "m/s^2", "MEASURED", "Earth gravity + motion")
    print()

    print_section("GYROSCOPE MEASUREMENTS (rad/s)")
    print_field("Mean Gyro [X, Y, Z]", stats["gyro"]["mean_xyz_radps"], "rad/s", "MEASURED", "Sensor bias estimate")
    print_field("Noise / Std [X, Y, Z]", stats["gyro"]["std_xyz_radps"], "rad/s", "MEASURED")
    print_field("Mean Norm Magnitude", stats["gyro"]["mean_norm_radps"], "rad/s", "MEASURED")
    print("=" * 60)

    # Exporter
    exporter = ExperimentExporter(args.dataset, "07_imu_characterization")

    # Export metrics CSV
    dt_series = [0.0] + stats["dt_ms_series"]
    csv_rows = []
    for i in range(len(timestamps)):
        csv_rows.append({
            "sample_idx": i,
            "timestamp": timestamps[i],
            "dt_ms": round(dt_series[i], 4),
            "accel_x": round(accel_arr[i, 0], 5),
            "accel_y": round(accel_arr[i, 1], 5),
            "accel_z": round(accel_arr[i, 2], 5),
            "gyro_x": round(gyro_arr[i, 0], 6),
            "gyro_y": round(gyro_arr[i, 1], 6),
            "gyro_z": round(gyro_arr[i, 2], 6),
        })
    exporter.export_csv(csv_rows)

    exporter.export_json({
        "dataset": args.dataset,
        "samples_analyzed": stats["num_samples"]["value"],
        "duration_s": stats["duration_s"]["value"],
        "expected_hz": args.expected_hz,
        "observed_hz": stats["observed_frequency_hz"]["value"],
        "mean_interval_ms": stats["mean_interval_ms"]["value"],
        "jitter_ms": stats["jitter_ms"]["value"],
        "dropped_samples": stats["suspected_dropped_packets"]["value"],
        "accel_summary": stats["accel"],
        "gyro_summary": stats["gyro"],
    })

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t_rel = np.array(timestamps) - timestamps[0]

    # Plot 1: Acceleration vs. Time
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(t_rel, accel_arr[:, 0], label="Ax (m/s^2)", color="#1976D2", alpha=0.8)
    ax.plot(t_rel, accel_arr[:, 1], label="Ay (m/s^2)", color="#388E3C", alpha=0.8)
    ax.plot(t_rel, accel_arr[:, 2], label="Az (m/s^2)", color="#E64A19", alpha=0.8)
    ax.set_title(f"EXP-07: Linear Acceleration vs. Time\nQuestion: What acceleration and vibration forces are sensed?\nDataset: {args.dataset}", fontsize=10)
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Linear Acceleration (m/s^2)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    save_plot(fig, exporter.figures_dir / "accel_vs_time.png")

    # Plot 2: Gyroscope vs. Time
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(t_rel, gyro_arr[:, 0], label="Wx (rad/s)", color="#7B1FA2", alpha=0.8)
    ax.plot(t_rel, gyro_arr[:, 1], label="Wy (rad/s)", color="#00796B", alpha=0.8)
    ax.plot(t_rel, gyro_arr[:, 2], label="Wz (rad/s)", color="#F57C00", alpha=0.8)
    ax.set_title(f"EXP-07: Angular Velocity (Gyro) vs. Time\nQuestion: What rotation rates are experienced?\nDataset: {args.dataset}", fontsize=10)
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Angular Velocity (rad/s)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    save_plot(fig, exporter.figures_dir / "gyro_vs_time.png")

    # Plot 3: Sample Interval vs. Time
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(t_rel[1:], stats["dt_ms_series"], color="#C2185B", linewidth=0.8, label="Inter-sample dt (ms)")
    ax.axhline(expected_dt_ms, color="blue", linestyle="--", label=f"Nominal ({expected_dt_ms:.2f} ms)")
    ax.set_title(f"EXP-07: Inter-Sample Delta Time vs. Time\nQuestion: Does the IMU maintain regular packet spacing?\nDataset: {args.dataset}", fontsize=10)
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Delta Time (ms)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    save_plot(fig, exporter.figures_dir / "sample_interval_vs_time.png")

    # Plot 4: Histogram of Sample Intervals
    plot_imu_intervals(
        intervals_ms=stats["dt_ms_series"],
        expected_dt_ms=expected_dt_ms,
        output_path=exporter.figures_dir / "sample_interval_histogram.png",
        dataset_name=args.dataset,
    )

    exporter.write_summary_md(
        title="EXP-07: IMU Characterization Summary",
        metrics_dict={
            "Samples Analyzed": f"{stats['num_samples']['value']} [MEASURED]",
            "Duration": f"{stats['duration_s']['value']} s [MEASURED]",
            "Nominal Rate": f"{args.expected_hz} Hz [ASSUMED]",
            "Observed Frequency": f"{stats['observed_frequency_hz']['value']} Hz [DERIVED]",
            "Mean Sample Interval": f"{stats['mean_interval_ms']['value']} ms [MEASURED]",
            "Timing Jitter": f"{stats['jitter_ms']['value']} ms [MEASURED]",
            "Suspected Dropped Samples": f"{stats['suspected_dropped_packets']['value']} [DERIVED]",
            "Mean Accel Magnitude": f"{stats['accel']['mean_norm_mps2']} m/s^2 [MEASURED]",
            "Mean Gyro Magnitude": f"{stats['gyro']['mean_norm_radps']} rad/s [MEASURED]",
        },
        conclusions=[
            "IMU sampling frequency is verified empirically against nominal manufacturer ratings.",
            "Timing jitter quantifies operating system bus latency or USB packet buffering delays.",
            "Accelerometer and gyroscope baseline offsets reveal stationary sensor bias that must be estimated during filter initialization.",
        ]
    )
    print(f"\n[DONE] Results and plots saved to {exporter.experiment_dir}")


if __name__ == "__main__":
    main()
