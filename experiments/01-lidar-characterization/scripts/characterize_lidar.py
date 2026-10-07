#!/usr/bin/env python3
"""
EXP-01 — LiDAR Dataset Characterization

Analyzes LiDAR point-cloud data from the KITTI Odometry dataset to measure:
  - Points per frame, frame sizes, data rates
  - Range statistics (min, max, mean, percentiles)
  - Reflectance statistics
  - Spatial bounding box
  - Processing time and memory usage
  - Generates plots and machine-readable results

Usage:
    python experiments/01-lidar-characterization/scripts/characterize_lidar.py \\
        --config experiments/01-lidar-characterization/config/config.yaml

    python experiments/01-lidar-characterization/scripts/characterize_lidar.py \\
        --config experiments/01-lidar-characterization/config/config.yaml \\
        --data-dir path/to/velodyne/directory

Author: IRoC-U Navigation Team
"""

import argparse
import csv
import json
import os
import platform
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import yaml


# ---------------------------------------------------------------------------
# Data classes for structured results
# ---------------------------------------------------------------------------

@dataclass
class FrameMetrics:
    """Metrics for a single LiDAR frame."""
    frame_index: int
    filename: str
    file_size_bytes: int
    num_points: int
    load_time_ms: float
    process_time_ms: float

    # Range statistics
    range_min_m: float
    range_max_m: float
    range_mean_m: float
    range_std_m: float
    range_median_m: float
    range_p25_m: float
    range_p75_m: float
    range_p90_m: float
    range_p95_m: float

    # Reflectance statistics
    reflectance_min: float
    reflectance_max: float
    reflectance_mean: float

    # Bounding box
    x_min_m: float
    x_max_m: float
    y_min_m: float
    y_max_m: float
    z_min_m: float
    z_max_m: float


@dataclass
class SummaryMetrics:
    """Aggregate metrics across all frames."""
    # Dataset info
    dataset_name: str
    sequence: str
    sensor_model: str
    total_frames: int
    nominal_frequency_hz: float

    # Derived timing
    estimated_duration_s: float

    # Point statistics
    total_points: int
    avg_points_per_frame: float
    min_points_per_frame: int
    max_points_per_frame: int
    std_points_per_frame: float

    # Size statistics
    avg_frame_size_bytes: float
    min_frame_size_bytes: int
    max_frame_size_bytes: int
    total_data_bytes: int
    data_rate_mb_per_s: float
    data_rate_gb_per_min: float
    data_rate_gb_per_hour: float

    # Range statistics (aggregated)
    global_range_min_m: float
    global_range_max_m: float
    overall_range_mean_m: float

    # Processing statistics
    avg_load_time_ms: float
    avg_process_time_ms: float
    total_processing_time_s: float

    # Point fields
    point_fields: list
    bytes_per_point: int

    # Memory
    peak_frame_memory_bytes: int
    peak_frame_memory_mb: float


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------

def load_kitti_bin(filepath: Path) -> np.ndarray:
    """
    Load a KITTI Velodyne .bin file.

    Each point is stored as 4 × float32: (x, y, z, reflectance).

    Returns:
        np.ndarray of shape (N, 4) where N is the number of points.
    """
    points = np.fromfile(str(filepath), dtype=np.float32)
    if points.size % 4 != 0:
        raise ValueError(
            f"File {filepath.name}: point count ({points.size}) is not "
            f"divisible by 4. Expected (x, y, z, reflectance) per point."
        )
    return points.reshape(-1, 4)


def compute_ranges(points: np.ndarray) -> np.ndarray:
    """Compute Euclidean range (distance from origin) for each point."""
    xyz = points[:, :3]
    return np.sqrt(np.sum(xyz ** 2, axis=1))


def analyze_frame(filepath: Path, frame_index: int) -> FrameMetrics:
    """
    Analyze a single LiDAR frame.

    Measures: point count, file size, ranges, reflectance, bounding box,
    load time, processing time.
    """
    file_size = filepath.stat().st_size

    # --- Load ---
    t_load_start = time.perf_counter()
    points = load_kitti_bin(filepath)
    t_load_end = time.perf_counter()
    load_time_ms = (t_load_end - t_load_start) * 1000.0

    # --- Process ---
    t_proc_start = time.perf_counter()

    num_points = points.shape[0]
    xyz = points[:, :3]
    reflectance = points[:, 3]
    ranges = compute_ranges(points)

    # Range statistics
    range_min = float(np.min(ranges))
    range_max = float(np.max(ranges))
    range_mean = float(np.mean(ranges))
    range_std = float(np.std(ranges))
    range_median = float(np.median(ranges))
    range_p25 = float(np.percentile(ranges, 25))
    range_p75 = float(np.percentile(ranges, 75))
    range_p90 = float(np.percentile(ranges, 90))
    range_p95 = float(np.percentile(ranges, 95))

    # Reflectance statistics
    ref_min = float(np.min(reflectance))
    ref_max = float(np.max(reflectance))
    ref_mean = float(np.mean(reflectance))

    # Bounding box
    x_min, x_max = float(np.min(xyz[:, 0])), float(np.max(xyz[:, 0]))
    y_min, y_max = float(np.min(xyz[:, 1])), float(np.max(xyz[:, 1]))
    z_min, z_max = float(np.min(xyz[:, 2])), float(np.max(xyz[:, 2]))

    t_proc_end = time.perf_counter()
    process_time_ms = (t_proc_end - t_proc_start) * 1000.0

    return FrameMetrics(
        frame_index=frame_index,
        filename=filepath.name,
        file_size_bytes=file_size,
        num_points=num_points,
        load_time_ms=round(load_time_ms, 3),
        process_time_ms=round(process_time_ms, 3),
        range_min_m=round(range_min, 4),
        range_max_m=round(range_max, 4),
        range_mean_m=round(range_mean, 4),
        range_std_m=round(range_std, 4),
        range_median_m=round(range_median, 4),
        range_p25_m=round(range_p25, 4),
        range_p75_m=round(range_p75, 4),
        range_p90_m=round(range_p90, 4),
        range_p95_m=round(range_p95, 4),
        reflectance_min=round(ref_min, 4),
        reflectance_max=round(ref_max, 4),
        reflectance_mean=round(ref_mean, 4),
        x_min_m=round(x_min, 4),
        x_max_m=round(x_max, 4),
        y_min_m=round(y_min, 4),
        y_max_m=round(y_max, 4),
        z_min_m=round(z_min, 4),
        z_max_m=round(z_max, 4),
    )


def compute_summary(
    frame_metrics: list[FrameMetrics],
    config: dict,
) -> SummaryMetrics:
    """Compute aggregate statistics from per-frame metrics."""
    n = len(frame_metrics)
    freq = config["sensor"]["nominal_frequency_hz"]

    points = [fm.num_points for fm in frame_metrics]
    sizes = [fm.file_size_bytes for fm in frame_metrics]
    load_times = [fm.load_time_ms for fm in frame_metrics]
    proc_times = [fm.process_time_ms for fm in frame_metrics]

    total_bytes = sum(sizes)
    avg_size = np.mean(sizes)
    data_rate_bytes_per_s = avg_size * freq
    data_rate_mb_per_s = data_rate_bytes_per_s / (1024 ** 2)
    data_rate_gb_per_min = data_rate_mb_per_s * 60 / 1024
    data_rate_gb_per_hour = data_rate_gb_per_min * 60

    # Peak memory: largest frame × 4 bytes per float32 value, plus overhead
    max_pts = max(points)
    peak_memory_bytes = max_pts * 4 * 4  # N points × 4 fields × 4 bytes
    # Add ~50% overhead for NumPy arrays, ranges, etc.
    peak_memory_bytes_with_overhead = int(peak_memory_bytes * 1.5)

    return SummaryMetrics(
        dataset_name=config["dataset"]["name"],
        sequence=str(config["dataset"]["sequence"]),
        sensor_model=config["sensor"]["model"],
        total_frames=n,
        nominal_frequency_hz=freq,
        estimated_duration_s=round(n / freq, 2),
        total_points=sum(points),
        avg_points_per_frame=round(float(np.mean(points)), 1),
        min_points_per_frame=min(points),
        max_points_per_frame=max(points),
        std_points_per_frame=round(float(np.std(points)), 1),
        avg_frame_size_bytes=round(float(avg_size), 1),
        min_frame_size_bytes=min(sizes),
        max_frame_size_bytes=max(sizes),
        total_data_bytes=total_bytes,
        data_rate_mb_per_s=round(data_rate_mb_per_s, 3),
        data_rate_gb_per_min=round(data_rate_gb_per_min, 4),
        data_rate_gb_per_hour=round(data_rate_gb_per_hour, 3),
        global_range_min_m=round(min(fm.range_min_m for fm in frame_metrics), 4),
        global_range_max_m=round(max(fm.range_max_m for fm in frame_metrics), 4),
        overall_range_mean_m=round(float(np.mean([fm.range_mean_m for fm in frame_metrics])), 4),
        avg_load_time_ms=round(float(np.mean(load_times)), 3),
        avg_process_time_ms=round(float(np.mean(proc_times)), 3),
        total_processing_time_s=round(sum(load_times + proc_times) / 1000.0, 3),
        point_fields=config["sensor"]["point_fields"],
        bytes_per_point=config["sensor"]["bytes_per_point"],
        peak_frame_memory_bytes=peak_memory_bytes_with_overhead,
        peak_frame_memory_mb=round(peak_memory_bytes_with_overhead / (1024 ** 2), 2),
    )


# ---------------------------------------------------------------------------
# Output: CSV, JSON, plots
# ---------------------------------------------------------------------------

def save_frame_csv(frame_metrics: list[FrameMetrics], output_path: Path) -> None:
    """Save per-frame metrics as CSV."""
    if not frame_metrics:
        return
    fieldnames = list(asdict(frame_metrics[0]).keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for fm in frame_metrics:
            writer.writerow(asdict(fm))
    print(f"  Saved: {output_path}")


def save_summary_json(summary: SummaryMetrics, metadata: dict, output_path: Path) -> None:
    """Save summary metrics and metadata as JSON."""
    data = {
        "summary": asdict(summary),
        "metadata": metadata,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  Saved: {output_path}")


def save_metadata_json(metadata: dict, output_path: Path) -> None:
    """Save experiment metadata as JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)
    print(f"  Saved: {output_path}")


def generate_plots(
    frame_metrics: list[FrameMetrics],
    all_ranges: np.ndarray,
    summary: SummaryMetrics,
    figures_dir: Path,
    config: dict,
) -> list[str]:
    """Generate all analysis plots. Returns list of saved filenames."""
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt

    dpi = config["output"].get("plot_dpi", 150)
    fmt = config["output"].get("plot_format", "png")
    dataset_label = f"{summary.dataset_name} — Seq {summary.sequence} ({summary.sensor_model})"
    saved_files = []

    def save_fig(fig, name):
        path = figures_dir / f"{name}.{fmt}"
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        saved_files.append(str(path))
        print(f"  Plot: {path}")

    indices = [fm.frame_index for fm in frame_metrics]
    points = [fm.num_points for fm in frame_metrics]
    sizes_kb = [fm.file_size_bytes / 1024 for fm in frame_metrics]
    load_times = [fm.load_time_ms for fm in frame_metrics]
    proc_times = [fm.process_time_ms for fm in frame_metrics]

    # 1. Points per frame
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(indices, points, linewidth=0.8, color="#2196F3")
    ax.axhline(np.mean(points), color="#F44336", linestyle="--", linewidth=1,
               label=f"Mean: {np.mean(points):.0f}")
    ax.set_xlabel("Frame Index")
    ax.set_ylabel("Points per Frame")
    ax.set_title(f"Points per Frame\n{dataset_label}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_fig(fig, "01_points_per_frame")

    # 2. Point count distribution
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(points, bins=50, color="#4CAF50", edgecolor="white", alpha=0.85)
    ax.axvline(np.mean(points), color="#F44336", linestyle="--", linewidth=1.5,
               label=f"Mean: {np.mean(points):.0f}")
    ax.axvline(np.median(points), color="#FF9800", linestyle="--", linewidth=1.5,
               label=f"Median: {np.median(points):.0f}")
    ax.set_xlabel("Points per Frame")
    ax.set_ylabel("Frequency")
    ax.set_title(f"Point Count Distribution\n{dataset_label}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_fig(fig, "02_point_count_distribution")

    # 3. Frame size distribution
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(sizes_kb, bins=50, color="#9C27B0", edgecolor="white", alpha=0.85)
    ax.axvline(np.mean(sizes_kb), color="#F44336", linestyle="--", linewidth=1.5,
               label=f"Mean: {np.mean(sizes_kb):.0f} KB")
    ax.set_xlabel("Frame Size (KB)")
    ax.set_ylabel("Frequency")
    ax.set_title(f"Frame Size Distribution\n{dataset_label}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_fig(fig, "03_frame_size_distribution")

    # 4. Range distribution
    fig, ax = plt.subplots(figsize=(12, 5))
    # Subsample if too many points (for plot performance)
    plot_ranges = all_ranges
    if len(all_ranges) > 500_000:
        rng = np.random.default_rng(42)
        plot_ranges = rng.choice(all_ranges, size=500_000, replace=False)
    ax.hist(plot_ranges, bins=200, color="#FF5722", edgecolor="none", alpha=0.8)
    ax.axvline(np.mean(all_ranges), color="#1565C0", linestyle="--", linewidth=1.5,
               label=f"Mean: {np.mean(all_ranges):.1f} m")
    ax.axvline(np.percentile(all_ranges, 95), color="#2E7D32", linestyle=":",
               linewidth=1.5, label=f"P95: {np.percentile(all_ranges, 95):.1f} m")
    ax.set_xlabel("Range (m)")
    ax.set_ylabel("Frequency")
    ax.set_title(f"Point Range Distribution\n{dataset_label}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_fig(fig, "04_range_distribution")

    # 5. Processing time per frame
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(indices, load_times, linewidth=0.8, color="#2196F3", alpha=0.7, label="Load time")
    ax.plot(indices, proc_times, linewidth=0.8, color="#FF9800", alpha=0.7, label="Process time")
    total_times = [l + p for l, p in zip(load_times, proc_times)]
    ax.plot(indices, total_times, linewidth=0.8, color="#F44336", alpha=0.7, label="Total time")
    ax.axhline(np.mean(total_times), color="#F44336", linestyle="--", linewidth=1,
               label=f"Mean total: {np.mean(total_times):.1f} ms")
    ax.set_xlabel("Frame Index")
    ax.set_ylabel("Time (ms)")
    ax.set_title(f"Processing Time per Frame\n{dataset_label}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_fig(fig, "05_processing_time")

    # 6. Range statistics over time
    fig, ax = plt.subplots(figsize=(12, 5))
    range_means = [fm.range_mean_m for fm in frame_metrics]
    range_p95s = [fm.range_p95_m for fm in frame_metrics]
    range_maxs = [fm.range_max_m for fm in frame_metrics]
    ax.plot(indices, range_means, linewidth=0.8, color="#2196F3", label="Mean range")
    ax.plot(indices, range_p95s, linewidth=0.8, color="#FF9800", alpha=0.7, label="P95 range")
    ax.plot(indices, range_maxs, linewidth=0.5, color="#F44336", alpha=0.4, label="Max range")
    ax.set_xlabel("Frame Index")
    ax.set_ylabel("Range (m)")
    ax.set_title(f"Range Statistics Over Time\n{dataset_label}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_fig(fig, "06_range_over_time")

    # 7. Bird's-eye view of a representative frame (middle frame)
    mid_idx = len(frame_metrics) // 2
    mid_file = frame_metrics[mid_idx].filename
    mid_path = Path(config["dataset"]["data_dir"]) / mid_file
    if mid_path.exists():
        pts = load_kitti_bin(mid_path)
        fig, ax = plt.subplots(figsize=(10, 10))
        # Subsample for plot performance
        if pts.shape[0] > 50_000:
            rng = np.random.default_rng(42)
            idx = rng.choice(pts.shape[0], size=50_000, replace=False)
            pts_plot = pts[idx]
        else:
            pts_plot = pts
        scatter = ax.scatter(
            pts_plot[:, 0], pts_plot[:, 1],
            c=pts_plot[:, 3], cmap="viridis", s=0.1, alpha=0.5
        )
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_title(
            f"Bird's-Eye View — Frame {frame_metrics[mid_idx].frame_index}\n"
            f"{dataset_label}\n"
            f"({frame_metrics[mid_idx].num_points:,} points, colored by reflectance)"
        )
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax, label="Reflectance", shrink=0.7)
        save_fig(fig, "07_birdseye_view")

    return saved_files


# ---------------------------------------------------------------------------
# Experiment metadata
# ---------------------------------------------------------------------------

def collect_metadata(config: dict, repo_root: Optional[Path] = None) -> dict:
    """Collect experiment metadata for reproducibility."""
    import shutil
    import subprocess

    # Git info
    git_commit = "UNKNOWN"
    git_branch = "UNKNOWN"
    git_exe = shutil.which("git")
    if git_exe:
        cwd = str(repo_root) if repo_root else None
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=5, cwd=cwd
            )
            if result.returncode == 0:
                git_commit = result.stdout.strip()
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, timeout=5, cwd=cwd
            )
            if result.returncode == 0:
                git_branch = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Memory info
    try:
        import psutil
        ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except ImportError:
        ram_gb = "UNKNOWN (psutil not installed)"

    return {
        "experiment_id": "EXP-01",
        "experiment_name": "LiDAR Dataset Characterization",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_local": datetime.now().isoformat(),
        "dataset": {
            "name": config["dataset"]["name"],
            "source": config["dataset"]["source"],
            "url": config["dataset"]["url"],
            "license": config["dataset"]["license"],
            "sequence": config["dataset"]["sequence"],
            "data_dir": config["dataset"]["data_dir"],
        },
        "sensor": config["sensor"],
        "environment": {
            "os": f"{platform.system()} {platform.release()}",
            "os_version": platform.version(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "cpu": platform.processor() or "UNKNOWN",
            "ram_gb": ram_gb,
        },
        "git": {
            "commit": git_commit,
            "branch": git_branch,
        },
        "config": config,
    }


# ---------------------------------------------------------------------------
# Main experiment runner
# ---------------------------------------------------------------------------

def discover_bin_files(data_dir: Path) -> list[Path]:
    """Discover and sort .bin files in the data directory."""
    files = sorted(data_dir.glob("*.bin"))
    return files


def run_experiment(config: dict) -> None:
    """Run the full LiDAR characterization experiment."""
    print("=" * 70)
    print("EXP-01 — LiDAR Dataset Characterization")
    print("=" * 70)
    print()

    # --- Resolve paths ---
    data_dir = Path(config["dataset"]["data_dir"])
    if not data_dir.is_absolute():
        # Try relative to current directory
        if not data_dir.exists():
            print(f"ERROR: Data directory not found: {data_dir}")
            print()
            print("Please download the KITTI Velodyne data first.")
            print("See: experiments/01-lidar-characterization/README.md")
            print()
            print("Expected structure:")
            print(f"  {data_dir}/")
            print("  ├── 000000.bin")
            print("  ├── 000001.bin")
            print("  └── ...")
            sys.exit(1)

    if not data_dir.exists():
        print(f"ERROR: Data directory not found: {data_dir}")
        sys.exit(1)

    # Discover frames
    bin_files = discover_bin_files(data_dir)
    if not bin_files:
        print(f"ERROR: No .bin files found in {data_dir}")
        sys.exit(1)

    print(f"Dataset:    {config['dataset']['name']}")
    print(f"Sequence:   {config['dataset']['sequence']}")
    print(f"Sensor:     {config['sensor']['model']}")
    print(f"Data dir:   {data_dir}")
    print(f"Found:      {len(bin_files)} .bin files")

    # Apply frame range
    frame_start = config["dataset"].get("frame_start", 0) or 0
    frame_end = config["dataset"].get("frame_end")
    max_frames = config["dataset"].get("max_frames")

    if frame_end is not None:
        bin_files = bin_files[frame_start:frame_end + 1]
    else:
        bin_files = bin_files[frame_start:]

    if max_frames is not None and len(bin_files) > max_frames:
        bin_files = bin_files[:max_frames]

    print(f"Processing: {len(bin_files)} frames (index {frame_start} to {frame_start + len(bin_files) - 1})")
    print()

    # --- Resolve output directories ---
    exp_dir = Path("experiments/01-lidar-characterization")
    results_dir = exp_dir / config["output"]["results_dir"]
    figures_dir = exp_dir / config["output"]["figures_dir"]
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # --- Process frames ---
    print("Processing frames...")
    frame_metrics: list[FrameMetrics] = []
    all_ranges_list: list[np.ndarray] = []
    t_experiment_start = time.perf_counter()

    for i, filepath in enumerate(bin_files):
        frame_idx = frame_start + i
        fm = analyze_frame(filepath, frame_idx)
        frame_metrics.append(fm)

        # Collect ranges for global histogram (subsample to control memory)
        pts = load_kitti_bin(filepath)
        ranges = compute_ranges(pts)
        if len(ranges) > 10_000:
            rng = np.random.default_rng(frame_idx)
            ranges = rng.choice(ranges, size=10_000, replace=False)
        all_ranges_list.append(ranges)

        # Progress
        if (i + 1) % 50 == 0 or i == 0 or (i + 1) == len(bin_files):
            print(f"  Frame {frame_idx:>6d} | {fm.num_points:>7,} pts | "
                  f"{fm.file_size_bytes / 1024:>8.1f} KB | "
                  f"load {fm.load_time_ms:>6.1f} ms | "
                  f"proc {fm.process_time_ms:>6.1f} ms | "
                  f"range [{fm.range_min_m:.1f}, {fm.range_max_m:.1f}] m")

    t_experiment_end = time.perf_counter()
    all_ranges = np.concatenate(all_ranges_list)
    print()
    print(f"Total experiment time: {t_experiment_end - t_experiment_start:.2f} s")
    print()

    # --- Compute summary ---
    summary = compute_summary(frame_metrics, config)

    # --- Print summary ---
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Dataset:              {summary.dataset_name}")
    print(f"  Sequence:             {summary.sequence}")
    print(f"  Sensor:               {summary.sensor_model}")
    print(f"  Frames processed:     {summary.total_frames}")
    print(f"  Estimated duration:   {summary.estimated_duration_s} s")
    print()
    print(f"  Total points:         {summary.total_points:,}")
    print(f"  Avg points/frame:     {summary.avg_points_per_frame:,.0f}")
    print(f"  Min points/frame:     {summary.min_points_per_frame:,}")
    print(f"  Max points/frame:     {summary.max_points_per_frame:,}")
    print(f"  Std points/frame:     {summary.std_points_per_frame:,.0f}")
    print()
    print(f"  Avg frame size:       {summary.avg_frame_size_bytes / 1024:.1f} KB")
    print(f"  Data rate:            {summary.data_rate_mb_per_s:.2f} MB/s")
    print(f"  Data volume:          {summary.data_rate_gb_per_min:.3f} GB/min")
    print(f"                        {summary.data_rate_gb_per_hour:.2f} GB/hour")
    print()
    print(f"  Range (global min):   {summary.global_range_min_m:.2f} m")
    print(f"  Range (global max):   {summary.global_range_max_m:.2f} m")
    print(f"  Range (mean):         {summary.overall_range_mean_m:.2f} m")
    print()
    print(f"  Avg load time:        {summary.avg_load_time_ms:.2f} ms")
    print(f"  Avg process time:     {summary.avg_process_time_ms:.2f} ms")
    print(f"  Peak frame memory:    {summary.peak_frame_memory_mb:.2f} MB")
    print(f"  Total processing:     {summary.total_processing_time_s:.2f} s")
    print("=" * 70)
    print()

    # --- Collect metadata ---
    metadata = collect_metadata(config)
    metadata["experiment_runtime_s"] = round(t_experiment_end - t_experiment_start, 3)

    # --- Save results ---
    print("Saving results...")
    save_frame_csv(frame_metrics, results_dir / "frame_metrics.csv")
    save_summary_json(summary, metadata, results_dir / "summary_metrics.json")
    save_metadata_json(metadata, results_dir / "experiment_metadata.json")
    print()

    # --- Generate plots ---
    if config["output"].get("save_plots", True):
        print("Generating plots...")
        saved_plots = generate_plots(
            frame_metrics, all_ranges, summary, figures_dir, config
        )
        print(f"  Generated {len(saved_plots)} plots")
        print()

    # --- Copy key figures to results/figures/ ---
    project_figures = Path("results/figures")
    project_figures.mkdir(parents=True, exist_ok=True)
    import shutil
    for fig_file in figures_dir.glob("*"):
        dest = project_figures / f"exp01_{fig_file.name}"
        shutil.copy2(fig_file, dest)
    print(f"  Copied figures to {project_figures}/")

    print()
    print("=" * 70)
    print("EXP-01 COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Review results in experiments/01-lidar-characterization/results/")
    print("  2. Review plots in experiments/01-lidar-characterization/figures/")
    print("  3. Update experiments/01-lidar-characterization/README.md with findings")
    print("  4. Consider: what LiDAR specifications does our UAV actually need?")
    print("  5. Proceed to EXP-02 (Camera Characterization)")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="EXP-01 — LiDAR Dataset Characterization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/characterize_lidar.py --config config/config.yaml
  python scripts/characterize_lidar.py --config config/config.yaml --data-dir /path/to/velodyne
  python scripts/characterize_lidar.py --config config/config.yaml --max-frames 50
        """,
    )
    parser.add_argument(
        "--config", type=str, required=True,
        help="Path to config.yaml file",
    )
    parser.add_argument(
        "--data-dir", type=str, default=None,
        help="Override data directory from config",
    )
    parser.add_argument(
        "--max-frames", type=int, default=None,
        help="Override max frames from config",
    )
    args = parser.parse_args()

    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Apply CLI overrides
    if args.data_dir:
        config["dataset"]["data_dir"] = args.data_dir
    if args.max_frames is not None:
        config["dataset"]["max_frames"] = args.max_frames

    # Run experiment
    run_experiment(config)


if __name__ == "__main__":
    main()
