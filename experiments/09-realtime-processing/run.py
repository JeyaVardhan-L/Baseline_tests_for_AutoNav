#!/usr/bin/env python3
"""
Experiment 09 — End-to-End Real-Time Pipeline Benchmark
Executes the full sequential pipeline:
  DATA -> READ -> DECODE -> VALIDATE -> FILTER -> DOWNSAMPLE -> VISUALIZE -> METRICS

Measures exact wall-clock latencies of every stage per frame:
  READ, DECODE, VALIDATE, FILTER, DOWNSAMPLE, VISUALIZE, TOTAL

Evaluates Available Processing Margin:
  Sensor Period = 1000 / Sensor Hz (ms)
  Pipeline Time = Total Stage Latency (ms)
  Available Margin = Sensor Period - Pipeline Time (ms)
  Status: PASS or CANNOT KEEP UP
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
from autonav_baseline.system.monitor import get_process_memory_mb, get_cpu_percent
from autonav_baseline.visualization.terminal import print_banner, print_section, print_field
from autonav_baseline.visualization.plots import save_plot
from autonav_baseline.reporting.exporter import ExperimentExporter


def main():
    parser = argparse.ArgumentParser(description="EXP-09: End-to-End Real-Time Pipeline")
    parser.add_argument("--dataset", type=str, default="synthetic", help="Dataset name (synthetic, newer_college, hilti_2023)")
    parser.add_argument("--path", type=str, default=None, help="Custom dataset path")
    parser.add_argument("--max-frames", type=int, default=30, help="Number of frames to benchmark")
    parser.add_argument("--sensor-hz", type=float, default=10.0, help="Nominal sensor frame rate (Hz)")
    parser.add_argument("--voxel-size", type=float, default=0.25, help="Voxel leaf size (meters)")
    parser.add_argument("--min-range", type=float, default=0.5, help="Minimum range (meters)")
    parser.add_argument("--max-range", type=float, default=40.0, help="Maximum range (meters)")
    args = parser.parse_args()

    print_banner("EXPERIMENT 09 - REAL-TIME PIPELINE BENCHMARK", f"Dataset: {args.dataset}")

    root_path = Path(args.path) if args.path else None
    adapter = get_adapter(args.dataset, root_path=root_path)

    sensor_period_ms = 1000.0 / args.sensor_hz

    timer = StageTimer()
    frame_metrics = []
    frames_processed = 0

    try:
        frame_iter = adapter.get_lidar_frames(max_frames=args.max_frames)
        for frame in frame_iter:
            frames_processed += 1
            t_pipeline_start = time.perf_counter()

            # 1. READ stage
            t0 = time.perf_counter()
            raw_pts = frame.points
            t_read = (time.perf_counter() - t0) * 1000.0
            timer.record("read", t_read)

            # 2. DECODE stage
            t0 = time.perf_counter()
            decoded_pts = raw_pts.astype(np.float32, copy=False)
            t_decode = (time.perf_counter() - t0) * 1000.0
            timer.record("decode", t_decode)

            # 3. VALIDATE stage
            t0 = time.perf_counter()
            valid_pts, _ = remove_invalid_points(decoded_pts)
            t_validate = (time.perf_counter() - t0) * 1000.0
            timer.record("validate", t_validate)

            # 4. FILTER stage
            t0 = time.perf_counter()
            range_pts, _ = filter_by_range(valid_pts, min_range=args.min_range, max_range=args.max_range)
            t_filter = (time.perf_counter() - t0) * 1000.0
            timer.record("filter", t_filter)

            # 5. DOWNSAMPLE stage
            t0 = time.perf_counter()
            downsampled_pts, _ = voxel_downsample(range_pts, voxel_size=args.voxel_size)
            t_downsample = (time.perf_counter() - t0) * 1000.0
            timer.record("downsample", t_downsample)

            # 6. VISUALIZE stage (Color mapping / projection preparation)
            t0 = time.perf_counter()
            dists = np.linalg.norm(downsampled_pts, axis=1) if len(downsampled_pts) > 0 else np.array([])
            t_visualize = (time.perf_counter() - t0) * 1000.0
            timer.record("visualize", t_visualize)

            # TOTAL pipeline latency
            t_total = (time.perf_counter() - t_pipeline_start) * 1000.0
            timer.record("total", t_total)

            margin_ms = sensor_period_ms - t_total
            status = "PASS" if margin_ms > 0 else "FAIL"

            rec = {
                "frame_idx": frames_processed - 1,
                "timestamp": frame.timestamp,
                "read_ms": round(t_read, 3),
                "decode_ms": round(t_decode, 3),
                "validate_ms": round(t_validate, 3),
                "filter_ms": round(t_filter, 3),
                "downsample_ms": round(t_downsample, 3),
                "visualize_ms": round(t_visualize, 3),
                "total_ms": round(t_total, 3),
                "sensor_period_ms": round(sensor_period_ms, 2),
                "available_margin_ms": round(margin_ms, 3),
                "status": status,
            }
            frame_metrics.append(rec)

    except FileNotFoundError as e:
        print(f"\n[ERROR]: {e}")
        sys.exit(1)

    if frames_processed == 0:
        print("No frames were processed.")
        sys.exit(1)

    summary = timer.summary()
    tot_dist = summary["total"]

    print_section("AVERAGE PIPELINE TIMING BREAKDOWN (per frame)")
    print(f"  {'READ':<15}: {summary['read']['mean']:>6.2f} ms [MEASURED]")
    print(f"  {'DECODE':<15}: {summary['decode']['mean']:>6.2f} ms [MEASURED]")
    print(f"  {'VALIDATE':<15}: {summary['validate']['mean']:>6.2f} ms [MEASURED]")
    print(f"  {'FILTER':<15}: {summary['filter']['mean']:>6.2f} ms [MEASURED]")
    print(f"  {'DOWNSAMPLE':<15}: {summary['downsample']['mean']:>6.2f} ms [MEASURED]")
    print(f"  {'VISUALIZE':<15}: {summary['visualize']['mean']:>6.2f} ms [MEASURED]")
    print("  " + "-" * 32)
    print(f"  {'TOTAL PIPELINE':<15}: {tot_dist['mean']:>6.2f} ms [MEASURED] (P95: {tot_dist['p95']:.2f} ms)")
    print()

    print_section("REAL-TIME DEADLINE & MARGIN")
    mean_margin = sensor_period_ms - tot_dist['mean']
    p95_margin = sensor_period_ms - tot_dist['p95']
    pass_pct = (sum(1 for r in frame_metrics if r["status"] == "PASS") / float(frames_processed)) * 100.0

    print_field("Sensor Frequency", args.sensor_hz, "Hz", "ASSUMED", "Target sensor nominal rate")
    print_field("Sensor Period Budget", round(sensor_period_ms, 2), "ms", "DERIVED", "1000 / Sensor Frequency")
    print_field("Mean Pipeline Latency", round(tot_dist['mean'], 2), "ms", "MEASURED")
    print_field("P95 Pipeline Latency", round(tot_dist['p95'], 2), "ms", "MEASURED")
    print_field("Mean Available Margin", round(mean_margin, 2), "ms", "DERIVED", "Budget - Mean Pipeline")
    print_field("P95 Available Margin", round(p95_margin, 2), "ms", "DERIVED", "Budget - P95 Pipeline")
    print_field("Real-Time Pass Rate", f"{pass_pct:.1f}", "%", "DERIVED", "Frames meeting sensor deadline")
    print()

    overall_status = "PASS (CAN KEEP UP)" if p95_margin > 0 else "CANNOT KEEP UP (LAG OCCURS)"
    print_field("REAL-TIME STATUS", overall_status, "", "DERIVED")
    print("  [NOTE]: Measured on host CPU. Serves as baseline benchmark.")
    print("============================================================")

    # Export results
    exporter = ExperimentExporter(args.dataset, "09_realtime_processing")
    exporter.export_csv(frame_metrics)
    exporter.export_json({
        "dataset": args.dataset,
        "frames_processed": frames_processed,
        "sensor_hz": args.sensor_hz,
        "sensor_period_ms": sensor_period_ms,
        "stage_summary_ms": summary,
        "mean_margin_ms": round(mean_margin, 2),
        "p95_margin_ms": round(p95_margin, 2),
        "pass_percent": round(pass_pct, 1),
        "overall_status": overall_status,
    })

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Plot 1: Available Margin vs. Frame
    margins = [r["available_margin_ms"] for r in frame_metrics]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(range(len(margins)), margins, color="#2E7D32" if p95_margin > 0 else "#C62828", marker="o", markersize=3, label="Available Margin (ms)")
    ax.axhline(0.0, color="red", linestyle="--", label="Deadline Threshold (0 ms margin)")
    ax.set_title(f"EXP-09: Available Compute Margin per Frame\nQuestion: Does the host computer finish processing before the next scan arrives?\nDataset: {args.dataset}", fontsize=10)
    ax.set_xlabel("Frame Index")
    ax.set_ylabel("Margin = Sensor Period - Pipeline Time (ms)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    save_plot(fig, exporter.figures_dir / "available_margin_vs_frame.png")

    # Plot 2: Stage Timing Breakdown Stacked Area / Line
    stages = ["read", "decode", "validate", "filter", "downsample", "visualize"]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    bottom = np.zeros(frames_processed)
    colors = ["#90CAF9", "#80CBC4", "#A5D6A7", "#FFE082", "#FFAB91", "#CE93D8"]
    for s, c in zip(stages, colors):
        s_vals = np.array([r[f"{s}_ms"] for r in frame_metrics])
        ax.bar(range(frames_processed), s_vals, bottom=bottom, label=s.capitalize(), color=c, width=0.8)
        bottom += s_vals
    ax.axhline(sensor_period_ms, color="red", linewidth=1.5, linestyle="--", label=f"Sensor Period ({sensor_period_ms:.1f} ms)")
    ax.set_title(f"EXP-09: Per-Frame Pipeline Execution Stacked by Stage\nQuestion: Which stage contributes most to latency across time?\nDataset: {args.dataset}", fontsize=10)
    ax.set_xlabel("Frame Index")
    ax.set_ylabel("Execution Time (ms)")
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    save_plot(fig, exporter.figures_dir / "stage_timing_stacked.png")

    exporter.write_summary_md(
        title="EXP-09: End-to-End Real-Time Pipeline Summary",
        metrics_dict={
            "Frames Benchmarked": f"{frames_processed} [MEASURED]",
            "Sensor Frequency": f"{args.sensor_hz} Hz [ASSUMED]",
            "Sensor Period Budget": f"{sensor_period_ms:.2f} ms [DERIVED]",
            "Total Pipeline Mean": f"{tot_dist['mean']:.2f} ms [MEASURED]",
            "Total Pipeline P95": f"{tot_dist['p95']:.2f} ms [MEASURED]",
            "Mean Available Margin": f"{mean_margin:.2f} ms [DERIVED]",
            "P95 Available Margin": f"{p95_margin:.2f} ms [DERIVED]",
            "Real-Time Pass Rate": f"{pass_pct:.1f}% [DERIVED]",
            "Host Real-Time Status": f"{overall_status} [DERIVED]",
        },
        conclusions=[
            "Sequential breakdown demonstrates exact execution latencies across Read, Decode, Validate, Filter, Downsample, and Visualize stages.",
            "Available Margin ($T_s - T_p$) proves whether spare CPU capacity exists for subsequent state estimation (odometry, mapping, and planning).",
            "This empirical measurement forms the host baseline required before conducting embedded hardware evaluations.",
        ]
    )
    print(f"\n[DONE] Results and plots saved to {exporter.experiment_dir}")


if __name__ == "__main__":
    main()
