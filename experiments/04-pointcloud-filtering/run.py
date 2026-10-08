#!/usr/bin/env python3
"""
Experiment 04 — Point Cloud Filtering
Measures the reduction in point counts, memory footprint, and CPU processing cost
across:
  1. Invalid / NaN point removal
  2. Range bounding [min_range, max_range]
  3. Voxel grid downsampling
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
from autonav_baseline.visualization.terminal import print_banner, print_section, print_field
from autonav_baseline.visualization.plots import save_plot
from autonav_baseline.reporting.exporter import ExperimentExporter


def main():
    parser = argparse.ArgumentParser(description="EXP-04: Point Cloud Filtering")
    parser.add_argument("--dataset", type=str, default="synthetic", help="Dataset name")
    parser.add_argument("--path", type=str, default=None, help="Custom dataset path")
    parser.add_argument("--voxel-size", type=float, default=0.20, help="Voxel size in meters (e.g. 0.10, 0.20)")
    parser.add_argument("--min-range", type=float, default=0.5, help="Minimum range in meters")
    parser.add_argument("--max-range", type=float, default=30.0, help="Maximum range in meters")
    args = parser.parse_args()

    print_banner("EXPERIMENT 04 - POINT CLOUD FILTERING", f"Dataset: {args.dataset}")

    root_path = Path(args.path) if args.path else None
    adapter = get_adapter(args.dataset, root_path=root_path)

    try:
        frames = list(adapter.get_lidar_frames(max_frames=1))
    except FileNotFoundError as e:
        print(f"\n[ERROR]: {e}")
        sys.exit(1)

    if not frames:
        print("No frames available.")
        sys.exit(1)

    raw_frame = frames[0]
    raw_pts = raw_frame.points

    # Stage 1: Measure raw state
    raw_count = len(raw_pts)
    raw_bytes = raw_pts.nbytes

    # Stage 2: Execute filtering steps with timing
    t0 = time.perf_counter()
    valid_pts, _ = remove_invalid_points(raw_pts)
    t_valid_ms = (time.perf_counter() - t0) * 1000.0

    t1 = time.perf_counter()
    range_pts, _ = filter_by_range(valid_pts, min_range=args.min_range, max_range=args.max_range)
    t_range_ms = (time.perf_counter() - t1) * 1000.0

    t2 = time.perf_counter()
    voxel_pts, _ = voxel_downsample(range_pts, voxel_size=args.voxel_size)
    t_voxel_ms = (time.perf_counter() - t2) * 1000.0

    total_filter_time_ms = t_valid_ms + t_range_ms + t_voxel_ms

    filtered_count = len(voxel_pts)
    filtered_bytes = voxel_pts.nbytes
    reduction_pct = ((raw_count - filtered_count) / float(raw_count)) * 100.0

    print_section("FILTERING BEFORE vs. AFTER COMPARISON")
    print_field("RAW Input Points", raw_count, "points", "MEASURED")
    print_field("RAW Buffer Memory", round(raw_bytes / (1024.0 * 1024.0), 3), "MB", "MEASURED")
    print()
    print_field("FILTERED Points", filtered_count, "points", "MEASURED")
    print_field("FILTERED Buffer Memory", round(filtered_bytes / (1024.0 * 1024.0), 3), "MB", "MEASURED")
    print_field("Point Cloud Reduction", round(reduction_pct, 1), "%", "DERIVED", "Removed redundancy")
    print()

    print_section("FILTERING EXECUTION LATENCY")
    print_field("NaN Removal Latency", round(t_valid_ms, 2), "ms", "MEASURED")
    print_field("Range Bounding Latency", round(t_range_ms, 2), "ms", "MEASURED")
    print_field("Voxel Grid Latency", round(t_voxel_ms, 2), "ms", "MEASURED", f"Grid={args.voxel_size}m")
    print_field("Total Filter Pipeline", round(total_filter_time_ms, 2), "ms", "MEASURED")
    print("=" * 60)

    # Export results and before/after plot
    exporter = ExperimentExporter(args.dataset, "04_pointcloud_filtering")
    exporter.export_json({
        "raw_points": raw_count,
        "filtered_points": filtered_count,
        "reduction_percent": round(reduction_pct, 2),
        "voxel_size_m": args.voxel_size,
        "total_latency_ms": round(total_filter_time_ms, 3),
    }, "summary.json")

    # Generate Comparison Plot
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    sub_raw = raw_pts[::max(1, len(raw_pts) // 4000)]
    sub_vox = voxel_pts[::max(1, len(voxel_pts) // 4000)]

    ax1.scatter(sub_raw[:, 0], sub_raw[:, 1], c=sub_raw[:, 2], cmap="coolwarm", s=1.0)
    ax1.set_title(f"RAW Point Cloud\n({raw_count:,} points, {raw_bytes/1024:.0f} KB)")
    ax1.set_xlabel("X (m)")
    ax1.set_ylabel("Y (m)")
    ax1.set_aspect("equal")
    ax1.grid(True, linestyle=":", alpha=0.5)

    ax2.scatter(sub_vox[:, 0], sub_vox[:, 1], c=sub_vox[:, 2], cmap="coolwarm", s=1.0)
    ax2.set_title(f"FILTERED & DOWNSAMPLED (Voxel={args.voxel_size}m)\n({filtered_count:,} points, {reduction_pct:.1f}% reduction)")
    ax2.set_xlabel("X (m)")
    ax2.set_ylabel("Y (m)")
    ax2.set_aspect("equal")
    ax2.grid(True, linestyle=":", alpha=0.5)

    plot_path = exporter.figures_dir / "01_filtering_comparison.png"
    save_plot(fig, plot_path)

    print(f"\n[+] Before/After comparison plot saved to: {plot_path}")


if __name__ == "__main__":
    main()
