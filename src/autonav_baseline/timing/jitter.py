"""
Timestamp delta and jitter analysis.
"""

from typing import List, Dict, Any
import numpy as np
from autonav_baseline.metrics.classification import Classification, tag


def analyze_timestamp_intervals(timestamps: List[float]) -> Dict[str, Any]:
    """
    Computes inter-frame timestamp intervals (dt), mean frequency, and jitter.

    Args:
        timestamps: Chronologically ordered timestamps in seconds.
    """
    if len(timestamps) < 2:
        return {
            "num_samples": len(timestamps),
            "observed_frequency_hz": tag(0.0, Classification.MEASURED, "Hz"),
            "mean_dt_ms": tag(0.0, Classification.MEASURED, "ms"),
            "jitter_std_ms": tag(0.0, Classification.MEASURED, "ms"),
            "min_dt_ms": tag(0.0, Classification.MEASURED, "ms"),
            "max_dt_ms": tag(0.0, Classification.MEASURED, "ms"),
            "intervals_ms": [],
        }

    ts = np.asarray(timestamps, dtype=np.float64)
    dt_seconds = np.diff(ts)
    dt_ms = dt_seconds * 1000.0

    mean_dt = float(np.mean(dt_ms))
    std_jitter = float(np.std(dt_ms))
    min_dt = float(np.min(dt_ms))
    max_dt = float(np.max(dt_ms))

    observed_freq = float(1.0 / np.mean(dt_seconds)) if np.mean(dt_seconds) > 0 else 0.0

    return {
        "num_samples": len(timestamps),
        "observed_frequency_hz": tag(round(observed_freq, 3), Classification.DERIVED, "Hz", "1 / mean_dt"),
        "mean_dt_ms": tag(round(mean_dt, 3), Classification.MEASURED, "ms", "Average inter-sample interval"),
        "jitter_std_ms": tag(round(std_jitter, 3), Classification.MEASURED, "ms", "Standard deviation of intervals (timing jitter)"),
        "min_dt_ms": tag(round(min_dt, 3), Classification.MEASURED, "ms", "Minimum observed interval"),
        "max_dt_ms": tag(round(max_dt, 3), Classification.MEASURED, "ms", "Maximum observed interval"),
        "intervals_ms": dt_ms.tolist(),
    }


def compute_cross_sensor_offsets(
    query_timestamps: List[float],
    reference_timestamps: List[float],
) -> Dict[str, Any]:
    """
    Computes nearest-neighbor timestamp synchronization offsets between two sensor streams.

    Args:
        query_timestamps: List of timestamps for the query sensor (e.g. LiDAR or Camera).
        reference_timestamps: List of timestamps for the reference sensor (e.g. IMU).

    Returns:
        Dict with mean, median, p95, max offset in milliseconds, and the per-query offset series.
    """
    if not query_timestamps or not reference_timestamps:
        return {"mean_ms": 0.0, "median_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0, "offsets_ms": []}

    ref = np.sort(np.asarray(reference_timestamps, dtype=np.float64))
    query = np.asarray(query_timestamps, dtype=np.float64)

    # Use searchsorted for fast nearest neighbor lookup
    idx = np.searchsorted(ref, query)
    idx_clamped = np.clip(idx, 0, len(ref) - 1)
    idx_prev = np.clip(idx - 1, 0, len(ref) - 1)

    diff1 = np.abs(query - ref[idx_clamped])
    diff2 = np.abs(query - ref[idx_prev])
    nearest_diff_s = np.minimum(diff1, diff2)
    nearest_diff_ms = nearest_diff_s * 1000.0

    return {
        "mean_offset_ms": float(np.mean(nearest_diff_ms)),
        "median_offset_ms": float(np.median(nearest_diff_ms)),
        "p95_offset_ms": float(np.percentile(nearest_diff_ms, 95)),
        "max_offset_ms": float(np.max(nearest_diff_ms)),
        "offsets_ms": nearest_diff_ms.tolist(),
    }

