#!/usr/bin/env python3
"""
Experiment 05 — Data Rate + Computational Load (Pipeline Stage Profiling)
Measures the per-frame execution time of every individual stage in the point cloud pipeline:
  1. Read
  2. Decode
  3. Validate (NaN removal)
  4. Filter (Range bounding)
  5. Downsample (Voxel grid)
  6. Visualization / Prep

Computes statistical distribution across all frames:
  mean, median, p95, p99, minimum, maximum, standard deviation

Compares processing FPS to sensor FPS and determines host-machine Real-Time Status:
  PASS or CANNOT KEEP UP
"""

import argparse
import sys
import time
from pathlib import Path
import numpy as np

# Add src to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.lidar.filtering import remove_invalid_points, filter_by_range, voxel_downsample
from autonav_baseline.timing.profiler import StageTimer, compute_distribution, evaluate_realtime_status
from autonav_baseline.visualization.terminal import print_banner, print_section, print_field
from autonav_baseline.visualization.plots import save_plot
from autonav_baseline.reporting.exporter import ExperimentExporter


def main():
    parser = argparse.ArgumentParser(description="EXP-05: Computational Load & Stage Profiling")
    parser.add_argument("--dataset", type=str, default="synthetic", help="Dataset name")
    parser.add_argument("--path", type=str, default=None, help="Custom dataset path")
    parser.add_argument("--max-frames", type=int, default=50, help="Number of frames to profile")
    parser.add_argument("--voxel-size", type=float, default=0.20, help="Voxel size in meters")
    parser.add_argument("--min-range", type=float, default=0.5, help="Minimum range in meters")
    parser.add_argument("--max-range", type=float, default=30.0, help="Maximum range in meters")
    parser.add_argument("--sensor-hz", type=float, default=10.0, help="Nominal sensor frequency (Hz)")
    args = parser.parse_args()

    print_banner("EXPERIMENT 05 - DATA RATE + COMPUTATIONAL LOAD", f"Dataset: {args.dataset}")

    root_path = Path(args.path) if args.path else None
    adapter = get_adapter(args.dataset, root_path=root_path)

    timer = StageTimer()
    total_pipeline_latencies = []
    frames_processed = 0

    try:
        frame_iter = adapter.get_lidar_frames(max_frames=args.max_frames)
        for frame in frame_iter:
            frames_processed += 1
            t_frame_start = time.perf_counter()

            # 1. READ time (simulated read/buffer access)
            t0 = time.perf_counter()
            pts_raw = frame.points
            t_read = (time.perf_counter() - t0) * 1000.0
            timer.record("read", t_read)

            # 2. DECODE time (type conversion / float32 validation)
            t0 = time.perf_counter()
            pts_decoded = pts_raw.astype(np.float32, copy=False)
            t_decode = (time.perf_counter() - t0) * 1000.0
            timer.record("decode", t_decode)

            # 3. VALIDATE time (invalid / NaN removal)
            t0 = time.perf_counter()
            pts_valid, _ = remove_invalid_points(pts_decoded)
            t_validate = (time.perf_counter() - t0) * 1000.0
            timer.record("validate", t_validate)

            # 4. FILTER time (range bounding)
            t0 = time.perf_counter()
            pts_range, _ = filter_by_range(pts_valid, min_range=args.min_range, max_range=args.max_range)
            t_filter = (time.perf_counter() - t0) * 1000.0
            timer.record("filter", t_filter)

            # 5. DOWNSAMPLE time (voxel grid)
            t0 = time.perf_counter()
            pts_downsampled, _ = voxel_downsample(pts_range, voxel_size=args.voxel_size)
            t_downsample = (time.perf_counter() - t0) * 1000.0
            timer.record("downsample", t_downsample)

            # 6. VISUALIZATION / PREP time (color indexing / packing)
            t0 = time.perf_counter()
            # Compute distance for color mapping as viewer prep
            _ = np.linalg.norm(pts_downsampled, axis=1)
            t_vis = (time.perf_counter() - t0) * 1000.0
            timer.record("visualization_prep", t_vis)

            total_lat = (time.perf_counter() - t_frame_start) * 1000.0
            timer.record("total_pipeline", total_lat)
            total_pipeline_latencies.append(total_lat)

    except FileNotFoundError as e:
        print(f"\n[ERROR]: {e}")
        sys.exit(1)

    if frames_processed == 0:
        print("No frames were processed.")
        sys.exit(1)

    summary = timer.summary()
    tot_dist = summary["total_pipeline"]

    sensor_period_ms = 1000.0 / args.sensor_hz
    rt_eval = evaluate_realtime_status(tot_dist["mean"], sensor_period_ms)
    rt_eval_p95 = evaluate_realtime_status(tot_dist["p95"], sensor_period_ms)

    print_section("STAGE TIMING BREAKDOWN (DISTRIBUTION ACROSS FRAMES in ms)")
    print(f"{'Stage':<20} {'Mean':<8} {'Median':<8} {'P95':<8} {'P99':<8} {'Min':<8} {'Max':<8} {'Std':<8}")
    print("-" * 76)
    for stage_name, dist in summary.items():
        print(f"{stage_name:<20} {dist['mean']:<8.2f} {dist['median']:<8.2f} {dist['p95']:<8.2f} {dist['p99']:<8.2f} {dist['min']:<8.2f} {dist['max']:<8.2f} {dist['std']:<8.2f}")
    print("=" * 76)

    print_section("REAL-TIME SYSTEM COMPARISON")
    print_field("Sensor Frequency", args.sensor_hz, "Hz", "ASSUMED", "Target sensor nominal rate")
    print_field("Sensor Arrival Period", round(sensor_period_ms, 2), "ms", "DERIVED", "1000 / Sensor Frequency")
    print_field("Mean Pipeline Latency", round(tot_dist["mean"], 2), "ms", "MEASURED")
    print_field("P95 Pipeline Latency", round(tot_dist["p95"], 2), "ms", "MEASURED", "Tail latency threshold")
    print_field("Mean Processing FPS", round(1000.0 / max(tot_dist["mean"], 0.001), 1), "FPS", "DERIVED")
    print_field("P95 Processing FPS", round(1000.0 / max(tot_dist["p95"], 0.001), 1), "FPS", "DERIVED")
    print()

    print_field("Mean Real-Time Margin", round(sensor_period_ms - tot_dist["mean"], 2), "ms", "DERIVED")
    print_field("P95 Real-Time Margin", round(sensor_period_ms - tot_dist["p95"], 2), "ms", "DERIVED")
    print()

    status_str = "PASS (CAN KEEP UP)" if tot_dist["p95"] <= sensor_period_ms else "CANNOT KEEP UP (LAG OCCURS)"
    print_field("REAL-TIME STATUS (P95)", status_str, "", "DERIVED")
    print("  [NOTE]: Evaluated strictly against host machine CPU baseline.")
    print("          Does NOT represent onboard UAV embedded compute capability.")
    print("=" * 76)

    # Export report & plots
    exporter = ExperimentExporter(args.dataset, "05_downsampling_computational_load")
    exporter.export_json({
        "frames_profiled": frames_processed,
        "sensor_hz_nominal": args.sensor_hz,
        "sensor_period_ms": sensor_period_ms,
        "stage_breakdown": summary,
        "realtime_evaluation_mean": rt_eval,
        "realtime_evaluation_p95": rt_eval_p95,
        "realtime_status_p95": status_str,
    })

    # Plot 1: Stage latency breakdown (bar chart)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    stages = ["read", "decode", "validate", "filter", "downsample", "visualization_prep"]
    means = [summary[s]["mean"] for s in stages if s in summary]
    stage_labels = [s.capitalize() for s in stages if s in summary]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    bars = ax.bar(stage_labels, means, color="#1976D2")
    ax.set_ylabel("Mean Execution Time (ms)")
    ax.set_title(f"EXP-05: Computational Load by Pipeline Stage\nQuestion: Which stage is the bottleneck?\nDataset: {args.dataset}")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for b in bars:
        h = b.get_height()
        ax.annotate(f"{h:.2f} ms", xy=(b.get_x() + b.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
    save_plot(fig, exporter.figures_dir / "stage_latency_breakdown.png")

    # Plot 2: Total Latency vs Frame with Sensor Period threshold line
    from autonav_baseline.visualization.plots import plot_processing_latency
    plot_processing_latency(
        indices=list(range(len(total_pipeline_latencies))),
        latencies_ms=total_pipeline_latencies,
        sensor_period_ms=sensor_period_ms,
        output_path=exporter.figures_dir / "pipeline_latency_vs_frame.png",
        dataset_name=args.dataset,
    )

    exporter.write_summary_md(
        title="EXP-05: Data Rate + Computational Load Summary",
        metrics_dict={
            "Frames Profiled": str(frames_processed),
            "Nominal Sensor Hz": f"{args.sensor_hz} Hz [ASSUMED]",
            "Sensor Period": f"{sensor_period_ms:.2f} ms [DERIVED]",
            "Mean Pipeline Latency": f"{tot_dist['mean']:.2f} ms [MEASURED]",
            "P95 Pipeline Latency": f"{tot_dist['p95']:.2f} ms [MEASURED]",
            "P99 Pipeline Latency": f"{tot_dist['p99']:.2f} ms [MEASURED]",
            "Max Pipeline Latency": f"{tot_dist['max']:.2f} ms [MEASURED]",
            "Host Real-Time Status": f"{status_str} [DERIVED]",
        },
        conclusions=[
            "Stage timing breakdown reveals the primary computational bottleneck in the point cloud processing pipeline.",
            "Evaluating both mean and P95 latency demonstrates why average timing alone is insufficient for real-time robotic systems (tail latency causes buffer backlog).",
            "This result is a baseline measurement of the host CPU and must not be interpreted as final UAV companion computer capability.",
        ]
    )
    print(f"\n[DONE] Results and plots saved to {exporter.experiment_dir}")


if __name__ == "__main__":
    main()
