#!/usr/bin/env python3
"""
Experiment 02 — LiDAR Characterization
Measures point counts, frame sizes, data throughput (MB/s, GB/hour), range distributions,
spatial bounding boxes, and host processing latency.
"""

import argparse
import sys
import time
from pathlib import Path
import numpy as np

# Add src to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.lidar.statistics import compute_point_cloud_statistics
from autonav_baseline.metrics.data_rate import DataRateMetrics
from autonav_baseline.metrics.classification import Classification, tag
from autonav_baseline.timing.profiler import StageTimer, evaluate_realtime_status
from autonav_baseline.system.monitor import get_process_memory_mb, get_cpu_percent
from autonav_baseline.visualization.terminal import print_banner, print_experiment_summary
from autonav_baseline.visualization.plots import plot_point_counts, plot_range_histogram, plot_processing_latency
from autonav_baseline.reporting.exporter import ExperimentExporter


def main():
    parser = argparse.ArgumentParser(description="EXP-02: LiDAR Characterization")
    parser.add_argument("--dataset", type=str, default="synthetic", help="Dataset name")
    parser.add_argument("--path", type=str, default=None, help="Custom dataset path")
    parser.add_argument("--frames", "--max-frames", dest="frames", type=int, default=50, help="Max frames to process")
    args = parser.parse_args()

    print_banner("EXPERIMENT 02 - LIDAR CHARACTERIZATION", f"Dataset: {args.dataset}")

    root_path = Path(args.path) if args.path else None
    adapter = get_adapter(args.dataset, root_path=root_path)

    frame_records = []
    all_ranges_list = []
    latencies_ms = []
    frame_sizes_bytes = []
    point_counts = []
    frame_indices = []

    timer = StageTimer()

    print(f"Streaming and characterizing up to {args.frames} LiDAR frames...")

    t_start_total = time.perf_counter()

    try:
        stream = adapter.get_lidar_frames(max_frames=args.frames)
        for frame in stream:
            t0 = time.perf_counter()
            stats = compute_point_cloud_statistics(frame.points, frame.intensity)
            dt_proc_ms = (time.perf_counter() - t0) * 1000.0

            latencies_ms.append(dt_proc_ms)
            frame_indices.append(frame.index)
            point_counts.append(frame.num_points)
            frame_sizes_bytes.append(frame.byte_size)

            if "ranges" in stats and len(stats["ranges"]) > 0:
                # Subsample ranges to keep memory bounded
                r = stats["ranges"]
                if len(r) > 5000:
                    r = np.random.default_rng(frame.index).choice(r, size=5000, replace=False)
                all_ranges_list.append(r)

            frame_records.append({
                "frame_index": frame.index,
                "timestamp_s": round(frame.timestamp, 4),
                "points": frame.num_points,
                "byte_size": frame.byte_size,
                "range_mean_m": stats["range_mean_m"]["value"],
                "range_max_m": stats["range_max_m"]["value"],
                "latency_ms": round(dt_proc_ms, 3),
            })
    except FileNotFoundError as e:
        print(f"\n[ERROR]: {e}")
        sys.exit(1)

    t_total_s = time.perf_counter() - t_start_total
    num_processed = len(frame_records)

    if num_processed == 0:
        print("[!] No frames processed.")
        sys.exit(1)

    avg_size = float(np.mean(frame_sizes_bytes))
    avg_points = float(np.mean(point_counts))
    all_ranges = np.concatenate(all_ranges_list) if all_ranges_list else np.array([0.0])

    # Rate calculations
    nominal_hz = 10.0
    rate_metrics = DataRateMetrics(
        avg_frame_size_bytes=avg_size,
        frame_rate_hz=nominal_hz,
        is_frame_rate_measured=False,
    )

    sensor_period_ms = 1000.0 / nominal_hz
    mean_lat_ms = float(np.mean(latencies_ms))
    p95_lat_ms = float(np.percentile(latencies_ms, 95))
    rt_check = evaluate_realtime_status(mean_lat_ms, sensor_period_ms)

    sensor_summary = {
        "frames_analyzed": tag(num_processed, Classification.MEASURED, "frames"),
        "average_points_per_frame": tag(round(avg_points, 1), Classification.MEASURED, "pts/frame"),
        "points_per_second": tag(round(avg_points * nominal_hz, 0), Classification.DERIVED, "pts/s"),
        "average_frame_size": tag(round(avg_size / (1024.0 * 1024.0), 3), Classification.MEASURED, "MB/frame"),
        "observed_raw_data_rate": tag(round(rate_metrics.mb_per_sec, 2), Classification.DERIVED, "MB/s"),
        "projected_storage_rate": tag(round(rate_metrics.gib_per_hour, 2), Classification.DERIVED, "GiB/hour"),
        "mean_point_distance": tag(round(float(np.mean(all_ranges)), 2), Classification.MEASURED, "m"),
        "p95_point_distance": tag(round(float(np.percentile(all_ranges, 95)), 2), Classification.MEASURED, "m"),
    }

    proc_summary = {
        "mean_latency": tag(round(mean_lat_ms, 2), Classification.MEASURED, "ms"),
        "p95_latency": tag(round(p95_lat_ms, 2), Classification.MEASURED, "ms"),
        "p99_latency": tag(round(float(np.percentile(latencies_ms, 99)), 2), Classification.MEASURED, "ms"),
        "throughput_fps": tag(round(1000.0 / max(mean_lat_ms, 1e-6), 1), Classification.DERIVED, "FPS"),
    }

    sys_summary = {
        "process_ram_rss": tag(round(get_process_memory_mb(), 1), Classification.MEASURED, "MB"),
        "process_cpu_load": tag(round(get_cpu_percent(), 1), Classification.MEASURED, "%"),
    }

    print_experiment_summary(
        dataset_name=adapter.name,
        sequence_name="Standard Evaluation Slice",
        frames_count=num_processed,
        sensor_metrics=sensor_summary,
        processing_metrics=proc_summary,
        system_metrics=sys_summary,
        realtime_check=rt_check,
    )

    # Export results and figures
    exporter = ExperimentExporter(args.dataset, "02_lidar_characterization")
    exporter.export_csv(frame_records, "frame_metrics.csv")

    summary_payload = {
        "sensor": sensor_summary,
        "processing": proc_summary,
        "system": sys_summary,
        "realtime": rt_check,
    }
    exporter.export_json(summary_payload, "summary.json")
    exporter.export_metadata({"dataset": args.dataset, "frames": num_processed}, "metadata.json")

    # Generate Figures
    fig_pts = exporter.figures_dir / "01_point_counts.png"
    fig_rng = exporter.figures_dir / "02_range_histogram.png"
    fig_lat = exporter.figures_dir / "03_processing_latency.png"

    plot_point_counts(frame_indices, point_counts, fig_pts, adapter.name)
    plot_range_histogram(all_ranges, fig_rng, adapter.name)
    plot_processing_latency(frame_indices, latencies_ms, sensor_period_ms, fig_lat, adapter.name)

    print(f"[+] Output figures and tables saved to: {exporter.output_dir}/")


if __name__ == "__main__":
    main()
