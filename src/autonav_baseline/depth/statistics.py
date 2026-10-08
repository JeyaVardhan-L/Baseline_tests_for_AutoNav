"""
Depth image statistics and 3D back-projection.
"""

from typing import Dict, Any, Tuple
import numpy as np
from autonav_baseline.metrics.classification import Classification, tag


def compute_depth_statistics(
    depth_image: np.ndarray,
    min_depth_m: float = 0.2,
    max_depth_m: float = 10.0,
) -> Dict[str, Any]:
    """
    Computes statistical properties of a depth image.

    Args:
        depth_image: 2D array of depth values in meters (or millimeter integer array scaled to meters).
        min_depth_m: Minimum valid sensing range (sensor near clip).
        max_depth_m: Maximum valid sensing range (sensor far clip).
    """
    height, width = depth_image.shape[:2]
    total_pixels = height * width

    valid_mask = (depth_image > min_depth_m) & (depth_image < max_depth_m) & np.isfinite(depth_image)
    valid_count = int(np.sum(valid_mask))
    valid_percent = (valid_count / float(total_pixels)) * 100.0

    valid_depths = depth_image[valid_mask]
    if len(valid_depths) == 0:
        return {
            "resolution": f"{width}x{height}",
            "total_pixels": tag(total_pixels, Classification.MEASURED, "pixels"),
            "valid_pixels": tag(0, Classification.MEASURED, "pixels"),
            "valid_percent": tag(0.0, Classification.DERIVED, "%"),
            "min_depth_m": tag(0.0, Classification.MEASURED, "m"),
            "max_depth_m": tag(0.0, Classification.MEASURED, "m"),
            "mean_depth_m": tag(0.0, Classification.MEASURED, "m"),
            "median_depth_m": tag(0.0, Classification.MEASURED, "m"),
        }

    return {
        "resolution": f"{width}x{height}",
        "total_pixels": tag(total_pixels, Classification.MEASURED, "pixels", "Image resolution H x W"),
        "valid_pixels": tag(valid_count, Classification.MEASURED, "pixels", "Pixels with measurable depth return"),
        "valid_percent": tag(round(valid_percent, 2), Classification.DERIVED, "%", "Depth coverage percentage"),
        "min_depth_m": tag(round(float(np.min(valid_depths)), 3), Classification.MEASURED, "m", "Closest detected surface"),
        "max_depth_m": tag(round(float(np.max(valid_depths)), 3), Classification.MEASURED, "m", "Farthest detected surface"),
        "mean_depth_m": tag(round(float(np.mean(valid_depths)), 3), Classification.MEASURED, "m", "Average scene depth"),
        "median_depth_m": tag(round(float(np.median(valid_depths)), 3), Classification.MEASURED, "m", "Median scene depth"),
        "valid_depths": valid_depths,
    }


def depth_to_point_cloud(
    depth_image: np.ndarray,
    fx: float = 525.0,
    fy: float = 525.0,
    cx: float = 319.5,
    cy: float = 239.5,
    depth_scale: float = 1.0,
    min_depth: float = 0.2,
    max_depth: float = 10.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Back-projects a 2D depth image into a 3D metric point cloud using the pinhole camera model.

    Equations:
        Z = depth / depth_scale
        X = (u - cx) * Z / fx
        Y = (v - cy) * Z / fy

    Returns:
        points: (N, 3) point cloud array in camera optical coordinate frame.
        valid_indices: (N, 2) pixel coordinates (v, u) of the valid points.
    """
    height, width = depth_image.shape[:2]
    u, v = np.meshgrid(np.arange(width), np.arange(height))

    z = depth_image.astype(np.float64) / depth_scale
    valid = (z >= min_depth) & (z <= max_depth) & np.isfinite(z)

    z_valid = z[valid]
    u_valid = u[valid]
    v_valid = v[valid]

    x_valid = (u_valid - cx) * z_valid / fx
    y_valid = (v_valid - cy) * z_valid / fy

    points = np.stack((x_valid, y_valid, z_valid), axis=-1).astype(np.float32)
    indices = np.stack((v_valid, u_valid), axis=-1)
    return points, indices
