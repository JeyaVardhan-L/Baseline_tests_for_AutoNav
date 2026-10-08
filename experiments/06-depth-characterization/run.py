#!/usr/bin/env python3
"""
Experiment 06 — Depth Characterization
Analyzes depth sensor data (TUM RGB-D, OpenLORIS, or Synthetic):
  1. Computes depth image statistics (min, max, mean, median, valid coverage %)
  2. Measures frame buffer size, FPS, processing latency, and process RAM
  3. Back-projects 2D depth into a metric 3D point cloud using the pinhole camera model
  4. Generates depth distance histogram and 2D/3D depth representations
"""

import argparse
import sys
import time
from pathlib import Path
import numpy as np

# Add src to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.depth.statistics import compute_depth_statistics, depth_to_point_cloud
from autonav_baseline.system.monitor import get_process_memory_mb
from autonav_baseline.visualization.terminal import print_banner, print_section, print_field
from autonav_baseline.visualization.plots import save_plot
from autonav_baseline.reporting.exporter import ExperimentExporter


def main():
    parser = argparse.ArgumentParser(description="EXP-06: Depth Characterization")
    parser.add_argument("--dataset", type=str, default="synthetic", help="Dataset name (synthetic, tum_rgbd, openloris)")
    parser.add_argument("--path", type=str, default=None, help="Custom dataset path")
    parser.add_argument("--max-frames", type=int, default=30, help="Max depth frames to analyze")
    parser.add_argument("--min-depth", type=float, default=0.2, help="Near clip distance in meters")
    parser.add_argument("--max-depth", type=float, default=10.0, help="Far clip distance in meters")
    parser.add_argument("--save-pointcloud", action="store_true", help="Generate 3D point cloud from depth")
    args = parser.parse_args()

    print_banner("EXPERIMENT 06 - DEPTH CHARACTERIZATION", f"Dataset: {args.dataset}")

    root_path = Path(args.path) if args.path else None
    adapter = get_adapter(args.dataset, root_path=root_path)

    frame_records = []
    latencies_ms = []
    all_valid_depths = []
    frames_processed = 0

    try:
        frame_iter = adapter.get_depth_frames(max_frames=args.max_frames)
        for frame in frame_iter:
            frames_processed += 1
            t0 = time.perf_counter()

            stats = compute_depth_statistics(
                frame.depth,
                min_depth_m=args.min_depth,
                max_depth_m=args.max_depth,
            )

            # Optional 3D back-projection
            pts_3d, _ = depth_to_point_cloud(
                frame.depth,
                min_depth=args.min_depth,
                max_depth=args.max_depth,
            )

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(elapsed_ms)

            depth_bytes = frame.depth.nbytes
            rgb_bytes = frame.rgb.nbytes if frame.rgb is not None else 0
            total_frame_bytes = depth_bytes + rgb_bytes

            rec = {
                "frame_idx": frames_processed - 1,
                "timestamp": frame.timestamp,
                "resolution": stats["resolution"],
                "total_pixels": stats["total_pixels"]["value"],
                "valid_pixels": stats["valid_pixels"]["value"],
                "valid_percent": stats["valid_percent"]["value"],
                "min_depth_m": stats["min_depth_m"]["value"],
                "max_depth_m": stats["max_depth_m"]["value"],
                "mean_depth_m": stats["mean_depth_m"]["value"],
                "median_depth_m": stats["median_depth_m"]["value"],
                "depth_bytes": depth_bytes,
                "total_frame_bytes": total_frame_bytes,
                "projected_3d_points": len(pts_3d),
                "latency_ms": round(elapsed_ms, 3),
            }
            frame_records.append(rec)

            if "valid_depths" in stats and len(stats["valid_depths"]) > 0:
                # Sample up to 10,000 depths per frame for aggregated histogram
                sampled = np.random.default_rng(frames_processed).choice(
                    stats["valid_depths"],
                    size=min(10000, len(stats["valid_depths"])),
                    replace=False,
                )
                all_valid_depths.append(sampled)

    except FileNotFoundError as e:
        print(f"\n[ERROR]: {e}")
        sys.exit(1)

    if frames_processed == 0:
        print("No depth frames were processed.")
        sys.exit(1)

    avg_valid_pct = float(np.mean([r["valid_percent"] for r in frame_records]))
    avg_mean_depth = float(np.mean([r["mean_depth_m"] for r in frame_records]))
    avg_median_depth = float(np.mean([r["median_depth_m"] for r in frame_records]))
    avg_frame_mb = float(np.mean([r["total_frame_bytes"] for r in frame_records])) / (1024.0 * 1024.0)
    avg_latency_ms = float(np.mean(latencies_ms))
    p95_latency_ms = float(np.percentile(latencies_ms, 95))
    processing_fps = 1000.0 / max(avg_latency_ms, 0.001)
    process_ram_mb = get_process_memory_mb()

    print_section("DEPTH SENSOR MEASUREMENTS")
    print_field("Frames Analyzed", frames_processed, "frames", "MEASURED")
    print_field("Resolution", frame_records[0]["resolution"], "WxH", "MEASURED")
    print_field("Average Valid Coverage", round(avg_valid_pct, 1), "%", "MEASURED", "Pixels with valid distance return")
    print_field("Mean Detected Depth", round(avg_mean_depth, 2), "m", "MEASURED")
    print_field("Median Detected Depth", round(avg_median_depth, 2), "m", "MEASURED")
    print_field("Average Frame Size", round(avg_frame_mb, 3), "MB", "MEASURED", "Depth + RGB uncompressed memory")
    print()

    print_section("PROCESSING & COMPUTATIONAL LOAD")
    print_field("Mean Processing Time", round(avg_latency_ms, 2), "ms", "MEASURED", "Stats + 3D back-projection")
    print_field("P95 Processing Time", round(p95_latency_ms, 2), "ms", "MEASURED")
    print_field("Processing Throughput", round(processing_fps, 1), "FPS", "DERIVED", "Host single-core rate")
    print_field("Process Memory (RAM)", round(process_ram_mb, 1), "MB", "MEASURED")
    print("=" * 60)

    # Export results
    exporter = ExperimentExporter(args.dataset, "06_depth_characterization")
    exporter.export_csv(frame_records)
    exporter.export_json({
        "frames_analyzed": frames_processed,
        "resolution": frame_records[0]["resolution"],
        "avg_valid_percent": round(avg_valid_pct, 2),
        "avg_mean_depth_m": round(avg_mean_depth, 3),
        "avg_median_depth_m": round(avg_median_depth, 3),
        "avg_frame_mb": round(avg_frame_mb, 3),
        "avg_latency_ms": round(avg_latency_ms, 2),
        "p95_latency_ms": round(p95_latency_ms, 2),
        "processing_fps": round(processing_fps, 1),
        "process_ram_mb": round(process_ram_mb, 1),
    })

    # Plot: Depth Histogram
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if all_valid_depths:
        flat_depths = np.concatenate(all_valid_depths)
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.hist(flat_depths, bins=80, color="#00897B", edgecolor="white", alpha=0.85)
        ax.axvline(avg_mean_depth, color="#D32F2F", linestyle="--", label=f"Mean: {avg_mean_depth:.2f} m")
        ax.axvline(avg_median_depth, color="#1976D2", linestyle=":", label=f"Median: {avg_median_depth:.2f} m")
        ax.set_title(
            f"EXP-06: Depth Distance Histogram\nQuestion: What range of distances is observed by the depth sensor?\nDataset: {args.dataset}",
            fontsize=10,
        )
        ax.set_xlabel("Distance (meters)")
        ax.set_ylabel("Pixel Frequency (sampled)")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend()
        save_plot(fig, exporter.figures_dir / "depth_histogram.png")

    exporter.write_summary_md(
        title="EXP-06: Depth Characterization Summary",
        metrics_dict={
            "Frames Analyzed": f"{frames_processed} [MEASURED]",
            "Image Resolution": f"{frame_records[0]['resolution']} [MEASURED]",
            "Valid Pixel Coverage": f"{avg_valid_pct:.1f}% [MEASURED]",
            "Mean Detected Depth": f"{avg_mean_depth:.2f} m [MEASURED]",
            "Median Detected Depth": f"{avg_median_depth:.2f} m [MEASURED]",
            "Average Frame Size": f"{avg_frame_mb:.3f} MB [MEASURED]",
            "Mean Processing Latency": f"{avg_latency_ms:.2f} ms [MEASURED]",
            "P95 Processing Latency": f"{p95_latency_ms:.2f} ms [MEASURED]",
            "Host Processing Rate": f"{processing_fps:.1f} FPS [DERIVED]",
            "Host RAM Footprint": f"{process_ram_mb:.1f} MB [MEASURED]",
        },
        conclusions=[
            "Depth images provide dense per-pixel geometric distances in a structured 2D grid format.",
            "Valid pixel coverage highlights sensor dropouts (e.g., specular surfaces, sunlight wash-out, or objects beyond sensor range).",
            "Pinhole back-projection enables instantaneous conversion from 2D depth grids to 3D metric point clouds for navigation and obstacle avoidance.",
        ]
    )
    print(f"\n[DONE] Results and plots saved to {exporter.experiment_dir}")


if __name__ == "__main__":
    main()
