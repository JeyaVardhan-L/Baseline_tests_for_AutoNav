"""
Point-to-plane ICP with an optional initial guess (variant `p2plane`).

Error metric: sum_i ((R p_i + t - q_i) . n_i)^2, where q_i is the nearest target point and n_i the
target surface normal (PCA over the k nearest target neighbours, smallest-eigenvalue eigenvector).
Each iteration solves the linearised 6x6 system for a small rotation vector w and translation t:

    A_i = [ (p_i x n_i)^T , n_i^T ],   b_i = -(p_i - q_i) . n_i,   (A^T A) x = A^T b,   x = [w, t]

and applies the update through the exact rotation (Rodrigues), so large-ish rotations stay a valid SO(3).
The 6x6 condition number of A^T A is reported as a degeneracy indicator (very large = some motion
direction is unconstrained, e.g. a featureless corridor).

Conventions match icp_point_to_point: the returned transformation maps SOURCE points into the TARGET frame.
"""

from typing import Optional, Tuple
import numpy as np
from scipy.spatial import cKDTree

from autonav_baseline.lidar.odometry import ICPResult, _compose


def estimate_normals(points: np.ndarray, tree: cKDTree, k: int = 10) -> np.ndarray:
    """Unit normals by PCA over the k nearest neighbours (sign is arbitrary; only n n^T is used)."""
    _, nn = tree.query(points, k=min(k, len(points)), workers=1)
    nb = points[nn]                                   # (N, k, 3)
    centred = nb - nb.mean(axis=1, keepdims=True)
    cov = np.einsum("nki,nkj->nij", centred, centred) / nb.shape[1]
    _, vecs = np.linalg.eigh(cov)                     # ascending eigenvalues
    return vecs[:, :, 0]


def _exp_so3(w: np.ndarray) -> np.ndarray:
    theta = np.linalg.norm(w)
    if theta < 1e-12:
        return np.eye(3)
    k = w / theta
    kx = np.array([[0.0, -k[2], k[1]], [k[2], 0.0, -k[0]], [-k[1], k[0], 0.0]])
    return np.eye(3) + np.sin(theta) * kx + (1.0 - np.cos(theta)) * (kx @ kx)


def icp_point_to_plane(
    source_points: np.ndarray,
    target_points: np.ndarray,
    target_normals: np.ndarray,
    target_tree: cKDTree,
    max_correspondence_distance: float = 1.5,
    max_iterations: int = 30,
    tolerance: float = 1e-4,
    initial_transform: Optional[np.ndarray] = None,
    min_inliers: int = 20,
) -> Tuple[ICPResult, float]:
    """Returns (ICPResult, condition number of the last normal-equation matrix)."""
    if len(source_points) < min_inliers or len(target_points) < min_inliers:
        return ICPResult(False, np.eye(4), np.eye(3), np.zeros(3), float("inf"), 0.0, 0, 0, "INSUFFICIENT_POINTS"), float("nan")

    start = np.eye(4) if initial_transform is None else np.array(initial_transform, dtype=np.float64)
    r, t = start[:3, :3].copy(), start[:3, 3].copy()
    src = np.asarray(source_points, dtype=np.float64)
    tgt = np.asarray(target_points, dtype=np.float64)
    history = []
    converged, inliers_n, err, cond = False, 0, float("inf"), float("nan")
    iters = 0
    for it in range(max_iterations):
        iters = it + 1
        moved = src @ r.T + t
        dist, nn = target_tree.query(moved, k=1, workers=1)
        mask = dist <= max_correspondence_distance
        inliers_n = int(np.count_nonzero(mask))
        if inliers_n < min_inliers:
            return ICPResult(False, _compose(r, t), r, t, float("inf"), inliers_n / len(src), inliers_n, iters,
                             "DEGENERATE_MATCHES_UNDER_THRESHOLD", history), cond
        p = moved[mask]
        q = tgt[nn[mask]]
        n = target_normals[nn[mask]]
        err = float(np.mean(dist[mask]))
        history.append(err)
        a = np.hstack([np.cross(p, n), n])            # (M, 6)
        b = -np.einsum("ij,ij->i", p - q, n)          # (M,)
        ata = a.T @ a
        cond = float(np.linalg.cond(ata))
        try:
            x = np.linalg.solve(ata, a.T @ b)
        except np.linalg.LinAlgError:
            return ICPResult(False, _compose(r, t), r, t, float("inf"), inliers_n / len(src), inliers_n, iters, "SINGULAR_SYSTEM", history), cond
        dr = _exp_so3(x[:3])
        dt = x[3:]
        r = dr @ r
        t = dr @ t + dt
        if np.linalg.norm(dt) < tolerance and np.linalg.norm(x[:3]) < tolerance:
            converged = True
            break
    return ICPResult(True, _compose(r, t), r, t, err, inliers_n / len(src), inliers_n, iters,
                     "CONVERGED" if converged else "MAX_ITERATIONS", history), cond