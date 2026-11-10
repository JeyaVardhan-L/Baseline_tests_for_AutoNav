"""
Faster implementation of the same voxel centroid filter (variant `optimized`).

Identical definition to filtering.voxel_downsample: voxel index = floor(p / size); each occupied voxel is
replaced by the centroid of its points. Only the implementation differs: the three integer voxel coordinates
are packed into one int64 key, so grouping sorts a 1-D integer array instead of calling np.unique(axis=0)
on an (N, 3) array, and centroids are summed with np.bincount instead of the unbuffered np.add.at.
Equivalence with the baseline is asserted in tests/unit/test_variants.py.
"""

from typing import Optional, Tuple
import numpy as np

_OFFSET = 1 << 20          # supports |index| < 2^20 voxels per axis (e.g. +-157 km at 0.15 m)
_BITS = 21


def voxel_downsample_fast(
    points: np.ndarray, voxel_size: float = 0.10, intensity: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    if len(points) == 0 or voxel_size <= 0:
        return points, intensity
    xyz = points[:, :3]
    idx = np.floor(xyz / voxel_size).astype(np.int64) + _OFFSET
    if idx.min() < 0 or idx.max() >= (1 << _BITS):
        raise ValueError("voxel index out of range for packed key; increase voxel_size")
    key = (idx[:, 0] << (2 * _BITS)) | (idx[:, 1] << _BITS) | idx[:, 2]
    _, inverse, counts = np.unique(key, return_inverse=True, return_counts=True)
    n = len(counts)
    out = np.empty((n, 3), dtype=np.float64)
    for axis in range(3):
        out[:, axis] = np.bincount(inverse, weights=xyz[:, axis], minlength=n) / counts
    out_int = None
    if intensity is not None:
        out_int = (np.bincount(inverse, weights=intensity, minlength=n) / counts).astype(intensity.dtype)
    return out.astype(points.dtype), out_int