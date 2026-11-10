"""
Ground-truth trajectory loading.

Supported layouts (header lines start with '#'; delimiter is a comma or whitespace):
  * 9 columns: sec, nsec, x, y, z, qx, qy, qz, qw   (Newer College registered_poses.csv)
  * 8 columns: t, x, y, z, qx, qy, qz, qw           (TUM format)

Poses are returned as (N, 4, 4) matrices of the ground-truth body frame in the ground-truth world
frame, with float-second timestamps. Which physical frame that is (sensor, base, ...) comes from the
dataset documentation and is not assumed here.
"""

from pathlib import Path
from typing import Tuple
import numpy as np

from autonav_baseline.metrics.trajectory_evaluation import poses_from_xyz_quat


def load_pose_csv(path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """Returns (timestamps_s (N,), poses (N,4,4)). Raises ValueError on malformed content."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Ground-truth file not found: {path.name}")
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.replace(",", " ").split()
            rows.append([float(p) for p in parts])
    if not rows:
        raise ValueError(f"Ground-truth file {path.name} has no data rows.")
    data = np.asarray(rows, dtype=np.float64)
    if data.shape[1] == 9:
        t = data[:, 0] + data[:, 1] * 1e-9
        xyz, quat = data[:, 2:5], data[:, 5:9]
    elif data.shape[1] == 8:
        t = data[:, 0]
        xyz, quat = data[:, 1:4], data[:, 4:8]
    else:
        raise ValueError(f"Ground-truth file {path.name}: expected 8 or 9 columns, got {data.shape[1]}.")
    if not np.isfinite(data).all():
        raise ValueError(f"Ground-truth file {path.name} contains non-finite values.")
    if np.any(np.diff(t) <= 0):
        raise ValueError(f"Ground-truth timestamps in {path.name} are not strictly increasing.")
    norms = np.linalg.norm(quat, axis=1)
    if np.any(np.abs(norms - 1.0) > 1e-3):
        raise ValueError(f"Ground-truth quaternions in {path.name} are not unit length.")
    return t, poses_from_xyz_quat(xyz, quat)