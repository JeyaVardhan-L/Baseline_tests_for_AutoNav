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
