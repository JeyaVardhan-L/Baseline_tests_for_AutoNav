"""
Point cloud filtering and downsampling algorithms.
"""

from typing import Tuple, Optional
import numpy as np


def remove_invalid_points(
    points: np.ndarray,
    intensity: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """Removes NaN, -Inf, and +Inf points from the cloud."""
    xyz = points[:, :3]
    mask = np.isfinite(xyz).all(axis=1)
    filtered_points = points[mask]
    filtered_intensity = intensity[mask] if intensity is not None else None
    return filtered_points, filtered_intensity


def filter_by_range(
    points: np.ndarray,
    min_range: float = 0.5,
    max_range: float = 100.0,
    intensity: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Filters points falling outside [min_range, max_range] Euclidean distance.
    Useful for removing UAV body self-reflections (< min_range) and distant noise (> max_range).
    """
    xyz = points[:, :3]
    ranges = np.linalg.norm(xyz, axis=1)
    mask = (ranges >= min_range) & (ranges <= max_range)
    return points[mask], (intensity[mask] if intensity is not None else None)


def voxel_downsample(
    points: np.ndarray,
    voxel_size: float = 0.10,
    intensity: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Voxel grid downsampling implemented using pure NumPy.
    Quantizes space into 3D grid cells of size `voxel_size` and computes the centroid of each cell.

    Args:
        points: np.ndarray of shape (N, 3).
        voxel_size: Edge length of cubic voxels in meters (e.g. 0.05m, 0.10m, 0.20m).
        intensity: Optional intensity array of shape (N,).

    Returns:
        Tuple of (downsampled_points, downsampled_intensity).
    """
    if len(points) == 0 or voxel_size <= 0:
        return points, intensity

    xyz = points[:, :3]
    # Compute 3D integer voxel coordinates
    voxel_coords = np.floor(xyz / voxel_size).astype(np.int64)

    # Use unique inverse mapping to calculate cell centroids
    _, inverse_indices, counts = np.unique(voxel_coords, axis=0, return_inverse=True, return_counts=True)
    num_voxels = len(counts)

    # Sum points inside each voxel
    sum_xyz = np.zeros((num_voxels, 3), dtype=np.float64)
    np.add.at(sum_xyz, inverse_indices, xyz)
    downsampled_xyz = sum_xyz / counts[:, np.newaxis]

    downsampled_intensity = None
    if intensity is not None:
        sum_int = np.zeros(num_voxels, dtype=np.float64)
        np.add.at(sum_int, inverse_indices, intensity)
        downsampled_intensity = (sum_int / counts).astype(intensity.dtype)

    return downsampled_xyz.astype(points.dtype), downsampled_intensity


def statistical_outlier_removal(
    points: np.ndarray,
    nb_neighbors: int = 16,
    std_ratio: float = 2.0,
    intensity: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Removes sparse statistical outliers based on mean distance to k-nearest neighbors.
    Uses KDTree if scipy is available, otherwise returns input.
    """
    try:
        from scipy.spatial import cKDTree
        if len(points) <= nb_neighbors:
            return points, intensity
        xyz = points[:, :3]
        tree = cKDTree(xyz)
        distances, _ = tree.query(xyz, k=nb_neighbors + 1)
        mean_dists = np.mean(distances[:, 1:], axis=1)  # exclude self
        global_mean = np.mean(mean_dists)
        global_std = np.std(mean_dists)
        threshold = global_mean + std_ratio * global_std
        mask = mean_dists <= threshold
        return points[mask], (intensity[mask] if intensity is not None else None)
    except ImportError:
        return points, intensity
