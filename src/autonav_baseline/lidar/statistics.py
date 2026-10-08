"""
LiDAR point cloud statistics calculation.
"""

from typing import Dict, Any, Optional
import numpy as np
from autonav_baseline.metrics.classification import Classification, tag


def compute_point_cloud_statistics(
    points: np.ndarray,
    intensity: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """
    Computes spatial, range, and validity statistics for an N x 3 (or N x 4) point cloud.

    Args:
        points: np.ndarray of shape (N, 3) representing (x, y, z).
        intensity: Optional np.ndarray of shape (N,) representing return intensity.

    Returns:
        Structured dictionary of measured and derived statistics.
    """
    total_points = len(points)
    if total_points == 0:
        return {
            "total_points": tag(0, Classification.MEASURED, "count"),
            "finite_points": tag(0, Classification.MEASURED, "count"),
            "finite_percent": tag(0.0, Classification.DERIVED, "%"),
            "range_min_m": tag(0.0, Classification.MEASURED, "m"),
            "range_max_m": tag(0.0, Classification.MEASURED, "m"),
            "range_mean_m": tag(0.0, Classification.MEASURED, "m"),
            "range_median_m": tag(0.0, Classification.MEASURED, "m"),
            "range_p95_m": tag(0.0, Classification.MEASURED, "m"),
            "bbox_extents_m": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }

    # Validity checks (NaN and Inf)
    xyz = points[:, :3]
    valid_mask = np.isfinite(xyz).all(axis=1)
    finite_count = int(np.sum(valid_mask))
    finite_percent = (finite_count / float(total_points)) * 100.0

    valid_xyz = xyz[valid_mask]
    if len(valid_xyz) == 0:
        return {
            "total_points": tag(total_points, Classification.MEASURED, "count"),
            "finite_points": tag(0, Classification.MEASURED, "count"),
            "finite_percent": tag(0.0, Classification.DERIVED, "%"),
            "range_min_m": tag(0.0, Classification.MEASURED, "m"),
            "range_max_m": tag(0.0, Classification.MEASURED, "m"),
            "range_mean_m": tag(0.0, Classification.MEASURED, "m"),
            "range_median_m": tag(0.0, Classification.MEASURED, "m"),
            "range_p95_m": tag(0.0, Classification.MEASURED, "m"),
            "bbox_extents_m": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }

    # Euclidean Range: r = sqrt(x^2 + y^2 + z^2)
    ranges = np.linalg.norm(valid_xyz, axis=1)

    r_min = float(np.min(ranges))
    r_max = float(np.max(ranges))
    r_mean = float(np.mean(ranges))
    r_median = float(np.median(ranges))
    r_p25 = float(np.percentile(ranges, 25))
    r_p75 = float(np.percentile(ranges, 75))
    r_p90 = float(np.percentile(ranges, 90))
    r_p95 = float(np.percentile(ranges, 95))

    # Bounding box
    x_min, x_max = float(np.min(valid_xyz[:, 0])), float(np.max(valid_xyz[:, 0]))
    y_min, y_max = float(np.min(valid_xyz[:, 1])), float(np.max(valid_xyz[:, 1]))
    z_min, z_max = float(np.min(valid_xyz[:, 2])), float(np.max(valid_xyz[:, 2]))

    stats = {
        "total_points": tag(total_points, Classification.MEASURED, "count", "Total points in scan"),
        "finite_points": tag(finite_count, Classification.MEASURED, "count", "Points with valid coordinates"),
        "finite_percent": tag(round(finite_percent, 2), Classification.DERIVED, "%", "Percentage of finite points"),
        "range_min_m": tag(round(r_min, 3), Classification.MEASURED, "m", "Closest detected point"),
        "range_max_m": tag(round(r_max, 3), Classification.MEASURED, "m", "Farthest detected point"),
        "range_mean_m": tag(round(r_mean, 3), Classification.MEASURED, "m", "Mean Euclidean distance"),
        "range_median_m": tag(round(r_median, 3), Classification.MEASURED, "m", "Median Euclidean distance"),
        "range_p25_m": tag(round(r_p25, 3), Classification.MEASURED, "m", "25th percentile range"),
        "range_p75_m": tag(round(r_p75, 3), Classification.MEASURED, "m", "75th percentile range"),
        "range_p90_m": tag(round(r_p90, 3), Classification.MEASURED, "m", "90th percentile range"),
        "range_p95_m": tag(round(r_p95, 3), Classification.MEASURED, "m", "95th percentile range"),
        "bbox": {
            "x_min_m": round(x_min, 2), "x_max_m": round(x_max, 2),
            "y_min_m": round(y_min, 2), "y_max_m": round(y_max, 2),
            "z_min_m": round(z_min, 2), "z_max_m": round(z_max, 2),
        },
        "ranges": ranges,
    }

    if intensity is not None and len(intensity) == total_points:
        valid_int = intensity[valid_mask]
        stats["intensity"] = {
            "min": round(float(np.min(valid_int)), 3),
            "max": round(float(np.max(valid_int)), 3),
            "mean": round(float(np.mean(valid_int)), 3),
            "median": round(float(np.median(valid_int)), 3),
        }

    return stats


compute_lidar_statistics = compute_point_cloud_statistics

