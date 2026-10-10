"""
Question-driven scientific plot generation using Matplotlib.
Every graph is designed to answer a specific engineering question.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np


def save_plot(fig, output_path: Path, dpi: int = 150) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)


def plot_point_counts(
    indices: List[int],
    point_counts: List[int],
    output_path: Path,
    dataset_name: str,
) -> None:
    """Question: Does the sensor produce a stable amount of data per frame?"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(indices, point_counts, color="#1976D2", linewidth=1.0, label="Points / frame")
    mean_val = float(np.mean(point_counts))
    ax.axhline(mean_val, color="#D32F2F", linestyle="--", linewidth=1.2, label=f"Mean: {mean_val:,.0f} pts")

    ax.set_title(
        f"Point Count Stability per Frame\nQuestion: Does the sensor produce a stable amount of data per frame?\nDataset: {dataset_name}",
        fontsize=10,
    )
    ax.set_xlabel("Frame Index (count)")
    ax.set_ylabel("Point Count (points/frame)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    save_plot(fig, output_path)


def plot_range_histogram(
    ranges: np.ndarray,
    output_path: Path,
    dataset_name: str,
) -> None:
    """Question: What distances are being observed?"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 4.5))
    r_sub = ranges if len(ranges) < 200_000 else np.random.default_rng(42).choice(ranges, size=200_000, replace=False)

    ax.hist(r_sub, bins=100, color="#388E3C", edgecolor="white", alpha=0.85)
    mean_r = float(np.mean(ranges))
    p95_r = float(np.percentile(ranges, 95))
    ax.axvline(mean_r, color="#1976D2", linestyle="--", label=f"Mean: {mean_r:.2f} m")
    ax.axvline(p95_r, color="#E64A19", linestyle=":", label=f"P95: {p95_r:.2f} m")

    ax.set_title(
        f"Spatial Range Distribution\nQuestion: What distances are being observed in the environment?\nDataset: {dataset_name}",
        fontsize=10,
    )
    ax.set_xlabel("Distance from Sensor (m)")
    ax.set_ylabel("Point Count Frequency")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    save_plot(fig, output_path)


def plot_processing_latency(
    indices: List[int],
    latencies_ms: List[float],
    sensor_period_ms: float,
    output_path: Path,
    dataset_name: str,
) -> None:
    """Question: Does processing remain stable and meet the sensor deadline?"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(indices, latencies_ms, color="#7B1FA2", linewidth=1.0, label="Host latency")
    mean_lat = float(np.mean(latencies_ms))
    p95_lat = float(np.percentile(latencies_ms, 95))

    ax.axhline(mean_lat, color="#0288D1", linestyle="--", label=f"Mean: {mean_lat:.2f} ms")
    ax.axhline(p95_lat, color="#F57C00", linestyle=":", label=f"P95: {p95_lat:.2f} ms")
    ax.axhline(sensor_period_ms, color="#D32F2F", linewidth=1.5, label=f"Sensor Period: {sensor_period_ms:.1f} ms")

    ax.set_title(
        f"Host Processing Latency vs. Sensor Deadline\nQuestion: Does processing remain stable and keep up with the sensor?\nDataset: {dataset_name}",
        fontsize=10,
    )
    ax.set_xlabel("Frame Index (count)")
    ax.set_ylabel("Host Pipeline Latency (ms)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    save_plot(fig, output_path)


def plot_imu_intervals(
    intervals_ms: List[float],
    expected_dt_ms: float,
    output_path: Path,
    dataset_name: str,
) -> None:
    """Question: Is the IMU stream arriving at a stable rate without timing jitter?"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.hist(intervals_ms, bins=50, color="#0097A7", edgecolor="white", alpha=0.85)
    mean_dt = float(np.mean(intervals_ms))
    std_dt = float(np.std(intervals_ms))

    ax.axvline(expected_dt_ms, color="#D32F2F", linestyle="--", label=f"Nominal: {expected_dt_ms:.2f} ms")
    ax.axvline(mean_dt, color="#1976D2", linestyle=":", label=f"Observed Mean: {mean_dt:.2f} ms (jitter: {std_dt:.2f} ms)")

    ax.set_title(
        f"IMU Sampling Interval Distribution\nQuestion: Is the stream arriving at a stable rate?\nDataset: {dataset_name}",
        fontsize=10,
    )
    ax.set_xlabel("Inter-Sample Delta Time dt (ms)")
    ax.set_ylabel("Sample Frequency")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    save_plot(fig, output_path)


def plot_odometry_trajectory(
    positions: np.ndarray,
    output_path: Path,
    dataset_name: str,
    path_length_m: float = 0.0,
) -> None:
    """Question: What 3D/2D trajectory is estimated by LiDAR scan-to-scan odometry?"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax_top, ax_side) = plt.subplots(1, 2, figsize=(12, 5))

    if len(positions) == 0:
        ax_top.text(0.5, 0.5, "No trajectory points", ha="center")
        ax_side.text(0.5, 0.5, "No trajectory points", ha="center")
        save_plot(fig, output_path)
        return

    x = positions[:, 0]
    y = positions[:, 1]
    z = positions[:, 2]

    # Top-Down view (X vs Y)
    ax_top.plot(x, y, color="#1976D2", linewidth=1.5, label="Estimated Path")
    ax_top.scatter(x[0], y[0], color="#388E3C", s=60, zorder=5, label="Start (0,0)")
    ax_top.scatter(x[-1], y[-1], color="#D32F2F", s=60, zorder=5, label=f"End ({x[-1]:.2f}, {y[-1]:.2f})")
    ax_top.set_title(f"Top-Down Trajectory (X-Y Plane)\nPath Length: {path_length_m:.2f} m\nDataset: {dataset_name}", fontsize=9)
    ax_top.set_xlabel("X (meters)")
    ax_top.set_ylabel("Y (meters)")
    ax_top.grid(True, linestyle=":", alpha=0.6)
    ax_top.legend(loc="best", fontsize=8)
    ax_top.axis("equal")

    # Side view (X vs Z)
    ax_side.plot(x, z, color="#7B1FA2", linewidth=1.5, label="Altitude Profile")
    ax_side.scatter(x[0], z[0], color="#388E3C", s=60, zorder=5)
    ax_side.scatter(x[-1], z[-1], color="#D32F2F", s=60, zorder=5)
    ax_side.set_title("Side Profile (X-Z Plane)\nElevation & Altitude Variation", fontsize=9)
    ax_side.set_xlabel("X (meters)")
    ax_side.set_ylabel("Z (meters)")
    ax_side.grid(True, linestyle=":", alpha=0.6)
    ax_side.legend(loc="best", fontsize=8)

    save_plot(fig, output_path)


def plot_dual_point_counts(
    indices: List[int],
    raw_counts: List[int],
    downsampled_counts: List[int],
    output_path: Path,
    dataset_name: str,
) -> None:
    """Question: How much did voxel grid decimation reduce computational input size?"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(indices, raw_counts, color="#78909C", linestyle="--", linewidth=1.0, label="Raw Points")
    ax.plot(indices, downsampled_counts, color="#1976D2", linewidth=1.2, label="Downsampled Points (ICP Input)")

    mean_raw = float(np.mean(raw_counts)) if raw_counts else 0.0
    mean_down = float(np.mean(downsampled_counts)) if downsampled_counts else 0.0
    reduction = ((mean_raw - mean_down) / max(mean_raw, 1.0)) * 100.0

    ax.set_title(
        f"Point Cloud Decimation per Frame\nQuestion: How much did voxel filtering reduce ICP input size? (Avg reduction: {reduction:.1f}%)\nDataset: {dataset_name}",
        fontsize=10,
    )
    ax.set_xlabel("Frame Index")
    ax.set_ylabel("Points Count")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    save_plot(fig, output_path)
