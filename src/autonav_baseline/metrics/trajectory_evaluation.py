"""
Trajectory accuracy evaluation against ground truth.
Computes Absolute Trajectory Error (ATE) via rigid SE(3) Umeyama alignment
and Relative Pose Error (RPE) translation drift.
Reports UNAVAILABLE honestly when ground truth poses are absent.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import numpy as np

from autonav_baseline.metrics.classification import Classification, tag


def align_umeyama_rigid(
    model: np.ndarray,
    data: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Computes optimal rigid transformation (R, t) aligning 'model' to 'data' in least-squares sense:
    data_approx = R @ model + t.
    Does NOT estimate scale (rigid SE(3) constraint).
    """
    if len(model) != len(data) or len(model) < 3:
        raise ValueError("Umeyama alignment requires at least 3 corresponding points with equal lengths.")

    mu_m = np.mean(model, axis=0)
    mu_d = np.mean(data, axis=0)

    m_centered = model - mu_m
    d_centered = data - mu_d

    # Covariance matrix H = D_centered^T * M_centered / N
    h = (d_centered.T @ m_centered) / len(model)
    u, s, vt = np.linalg.svd(h)

    r = u @ vt
    # Ensure proper rotation (det(R) == +1)
    if np.linalg.det(r) < 0:
        vt[-1, :] *= -1
        r = u @ vt

    t = mu_d - (r @ mu_m)
    aligned_model = (r @ model.T).T + t
    return r, t, aligned_model


def compute_trajectory_accuracy(
    estimated_positions: np.ndarray,
    ground_truth_positions: Optional[np.ndarray],
) -> Dict[str, Any]:
    """
    Evaluates trajectory accuracy against reference ground truth.
    If ground truth is absent or insufficient, returns an honest UNAVAILABLE status.
    """
    if ground_truth_positions is None or len(ground_truth_positions) == 0:
        return {
            "status": "UNAVAILABLE",
            "reason": "Ground truth reference trajectory file is not present or not loaded.",
            "ate_rmse_m": tag(None, Classification.UNAVAILABLE, "meters", "Ground truth reference absent"),
            "ate_mean_m": tag(None, Classification.UNAVAILABLE, "meters"),
            "ate_median_m": tag(None, Classification.UNAVAILABLE, "meters"),
        }

    n_est = len(estimated_positions)
    n_gt = len(ground_truth_positions)
    n = min(n_est, n_gt)

    if n < 3:
        return {
            "status": "UNAVAILABLE",
            "reason": f"Insufficient corresponding poses for 3D alignment (estimated={n_est}, ground_truth={n_gt}).",
            "ate_rmse_m": tag(None, Classification.UNAVAILABLE, "meters"),
            "ate_mean_m": tag(None, Classification.UNAVAILABLE, "meters"),
            "ate_median_m": tag(None, Classification.UNAVAILABLE, "meters"),
        }

    est = estimated_positions[:n]
    gt = ground_truth_positions[:n]

    try:
        r, t, aligned_est = align_umeyama_rigid(est, gt)
        errors = np.linalg.norm(aligned_est - gt, axis=1)

        rmse = float(np.sqrt(np.mean(errors ** 2)))
        mean_err = float(np.mean(errors))
        median_err = float(np.median(errors))
        max_err = float(np.max(errors))

        # NOTE: legacy index-paired ATE only. Real RPE and timestamp association live in
        # evaluate_trajectory() below; the old "RPE" here compared step lengths, which is not RPE.
        return {
            "status": "MEASURED",
            "num_aligned_poses": n,
            "ate_rmse_m": tag(round(rmse, 4), Classification.DERIVED, "meters"),
            "ate_mean_m": tag(round(mean_err, 4), Classification.DERIVED, "meters"),
            "ate_median_m": tag(round(median_err, 4), Classification.DERIVED, "meters"),
            "ate_max_m": tag(round(max_err, 4), Classification.DERIVED, "meters"),
        }
    except Exception as e:
        return {
            "status": "UNVERIFIED",
            "reason": f"Alignment calculation failed: {str(e)}",
            "ate_rmse_m": tag(None, Classification.UNAVAILABLE, "meters"),
        }


# ----------------------------------------------------------------------------------------------
# Timestamp-associated ATE and real RPE
# ----------------------------------------------------------------------------------------------

def quat_xyzw_to_rotation(quats: np.ndarray) -> np.ndarray:
    """(N,4) quaternions [qx,qy,qz,qw] -> (N,3,3) rotation matrices (normalised first)."""
    q = np.asarray(quats, dtype=np.float64).reshape(-1, 4)
    q = q / np.linalg.norm(q, axis=1, keepdims=True)
    x, y, z, w = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    r = np.empty((len(q), 3, 3))
    r[:, 0, 0] = 1 - 2 * (y * y + z * z)
    r[:, 0, 1] = 2 * (x * y - z * w)
    r[:, 0, 2] = 2 * (x * z + y * w)
    r[:, 1, 0] = 2 * (x * y + z * w)
    r[:, 1, 1] = 1 - 2 * (x * x + z * z)
    r[:, 1, 2] = 2 * (y * z - x * w)
    r[:, 2, 0] = 2 * (x * z - y * w)
    r[:, 2, 1] = 2 * (y * z + x * w)
    r[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return r


def poses_from_xyz_quat(xyz: np.ndarray, quats_xyzw: np.ndarray) -> np.ndarray:
    """(N,3) positions and (N,4) quaternions -> (N,4,4) homogeneous poses."""
    xyz = np.asarray(xyz, dtype=np.float64).reshape(-1, 3)
    poses = np.tile(np.eye(4), (len(xyz), 1, 1))
    poses[:, :3, :3] = quat_xyzw_to_rotation(quats_xyzw)
    poses[:, :3, 3] = xyz
    return poses


def associate_by_time(t_a: np.ndarray, t_b: np.ndarray, max_dt: float = 0.02) -> Tuple[np.ndarray, np.ndarray]:
    """
    One-to-one nearest-timestamp association. Both arrays must be sorted ascending.
    Returns index arrays (ia, ib) with |t_a[ia] - t_b[ib]| <= max_dt, each b used at most once.
    """
    t_a = np.asarray(t_a, dtype=np.float64)
    t_b = np.asarray(t_b, dtype=np.float64)
    if len(t_a) == 0 or len(t_b) == 0:
        return np.zeros(0, dtype=int), np.zeros(0, dtype=int)
    pos = np.clip(np.searchsorted(t_b, t_a), 1, len(t_b) - 1) if len(t_b) > 1 else np.zeros(len(t_a), dtype=int)
    if len(t_b) > 1:
        left_closer = np.abs(t_b[pos - 1] - t_a) <= np.abs(t_b[pos] - t_a)
        nearest = np.where(left_closer, pos - 1, pos)
    else:
        nearest = pos
    dt = np.abs(t_b[nearest] - t_a)
    ok = dt <= max_dt
    ia = np.flatnonzero(ok)
    ib = nearest[ok]
    # enforce uniqueness: keep the closest a for each b
    best: Dict[int, int] = {}
    for a_idx, b_idx in zip(ia, ib):
        cur = best.get(int(b_idx))
        if cur is None or dt[a_idx] < dt[cur]:
            best[int(b_idx)] = int(a_idx)
    pairs = sorted((a_idx, b_idx) for b_idx, a_idx in best.items())
    if not pairs:
        return np.zeros(0, dtype=int), np.zeros(0, dtype=int)
    arr = np.array(pairs, dtype=int)
    return arr[:, 0], arr[:, 1]


def relative_pose_errors(
    est_poses: np.ndarray, gt_poses: np.ndarray, idx_i: np.ndarray, idx_j: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Relative pose error (Sturm et al. 2012) for index pairs (i, j):
        E_ij = (Q_i^-1 Q_j)^-1 (P_i^-1 P_j)     Q = ground truth, P = estimate
    Returns (translation error in metres, rotation error in degrees). Independent of any global
    alignment between the estimate and ground-truth world frames; it assumes both poses describe
    the SAME body frame (the sensor).
    """
    rel_gt = np.linalg.inv(gt_poses[idx_i]) @ gt_poses[idx_j]
    rel_est = np.linalg.inv(est_poses[idx_i]) @ est_poses[idx_j]
    err = np.linalg.inv(rel_gt) @ rel_est
    trans = np.linalg.norm(err[:, :3, 3], axis=1)
    cos_theta = (np.trace(err[:, :3, :3], axis1=1, axis2=2) - 1.0) / 2.0
    rot = np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))
    return trans, rot


def _stats(values: np.ndarray) -> Dict[str, float]:
    v = np.asarray(values, dtype=np.float64)
    if len(v) == 0:
        return {"n": 0}
    return {
        "n": int(len(v)),
        "rmse": float(np.sqrt(np.mean(v ** 2))),
        "mean": float(np.mean(v)),
        "median": float(np.median(v)),
        "p95": float(np.percentile(v, 95)),
        "max": float(np.max(v)),
    }


def evaluate_trajectory(
    est_poses: np.ndarray,
    est_t: np.ndarray,
    gt_poses: np.ndarray,
    gt_t: np.ndarray,
    max_dt: float = 0.02,
    rpe_seconds: Tuple[float, ...] = (1.0, 10.0),
    rpe_distances_m: Tuple[float, ...] = (10.0, 50.0),
    body_frames_match: bool = False,
) -> Dict[str, Any]:
    """
    Evaluates an estimated trajectory against ground truth.

    1. Poses are associated by timestamp (nearest, within max_dt seconds, one-to-one).
    2. ATE: position error after a rigid SE(3) Umeyama alignment (no scale) of the estimate to GT.
    3. RPE over fixed time windows and fixed GT path-length windows (no alignment needed).

    Assumption (UNVERIFIED unless the dataset documents it): the ground-truth poses describe the
    same body frame as the estimate, i.e. the LiDAR/sensor frame.

    Returns {"summary": {...JSON-safe...}, "per_pose": {...numpy arrays...}}.
    """
    est_t = np.asarray(est_t, dtype=np.float64)
    gt_t = np.asarray(gt_t, dtype=np.float64)
    ia, ib = associate_by_time(est_t, gt_t, max_dt=max_dt)
    if len(ia) < 3:
        return {
            "summary": {
                "status": "UNAVAILABLE",
                "reason": f"fewer than 3 poses associated within {max_dt}s (got {len(ia)}).",
                "n_estimated": int(len(est_t)), "n_ground_truth": int(len(gt_t)),
            },
            "per_pose": {},
        }

    P = np.asarray(est_poses)[ia]
    Q = np.asarray(gt_poses)[ib]
    tt = est_t[ia]
    est_xyz = P[:, :3, 3]
    gt_xyz = Q[:, :3, 3]

    r_align, t_align, est_aligned = align_umeyama_rigid(est_xyz, gt_xyz)
    ate = np.linalg.norm(est_aligned - gt_xyz, axis=1)

    gt_step = np.linalg.norm(np.diff(gt_xyz, axis=0), axis=1)
    gt_cum = np.concatenate([[0.0], np.cumsum(gt_step)])
    gt_path = float(gt_cum[-1])
    ate_s = _stats(ate)

    def _window_errors(i, j):
        """Per-window errors. SE(3) RPE if the body frames are known to match, else world-frame
        position RPE after the global alignment (independent of any sensor-to-body extrinsic)."""
        if body_frames_match:
            return relative_pose_errors(P, Q, i, j)
        d_est = est_aligned[j] - est_aligned[i]
        d_gt = gt_xyz[j] - gt_xyz[i]
        return np.linalg.norm(d_est - d_gt, axis=1), None

    rpe: Dict[str, Any] = {}
    for sec in rpe_seconds:
        target = tt + sec
        j = np.searchsorted(tt, target)
        valid = j < len(tt)
        i = np.flatnonzero(valid)
        j = j[valid]
        close = np.abs(tt[j] - target[i]) <= max_dt
        i, j = i[close], j[close]
        if len(i) == 0:
            rpe[f"time_{sec:g}s"] = {"n": 0}
            continue
        te, re_ = _window_errors(i, j)
        seg = gt_cum[j] - gt_cum[i]
        rpe[f"time_{sec:g}s"] = {
            "translation_m": _stats(te),
            "rotation_deg": _stats(re_) if re_ is not None else "UNAVAILABLE",
            "mean_segment_length_m": float(np.mean(seg)),
            "translation_percent_of_length": float(np.mean(te) / max(np.mean(seg), 1e-9) * 100.0),
        }
    for d in rpe_distances_m:
        j = np.searchsorted(gt_cum, gt_cum + d)
        i = np.flatnonzero(j < len(gt_cum))
        j = j[i]
        if len(i) == 0:
            rpe[f"distance_{d:g}m"] = {"n": 0}
            continue
        te, re_ = _window_errors(i, j)
        seg = gt_cum[j] - gt_cum[i]
        rpe[f"distance_{d:g}m"] = {
            "translation_m": _stats(te),
            "rotation_deg": _stats(re_) if re_ is not None else "UNAVAILABLE",
            "mean_segment_length_m": float(np.mean(seg)),
            "translation_percent_of_length": float(np.mean(te) / max(np.mean(seg), 1e-9) * 100.0),
        }

    summary = {
        "status": "MEASURED",
        "evidence": "DERIVED",
        "n_estimated": int(len(est_t)), "n_ground_truth": int(len(gt_t)), "n_associated": int(len(ia)),
        "association_max_dt_s": max_dt,
        "ate_m": ate_s,
        "ate_alignment": "rigid SE(3) Umeyama on positions, no scale",
        "gt_path_length_m": gt_path,
        "final_position_error_after_alignment_m": float(ate[-1]),
        "rpe": rpe,
        "rpe_mode": ("se3_body_frame" if body_frames_match else "world_position_after_umeyama_alignment"),
        "assumptions": (["Ground-truth poses are in the same body frame as the estimate (sensor frame): caller-asserted"] if body_frames_match else ["Sensor and ground-truth body frames may differ (extrinsic not calibrated): RPE is world-frame position error after global alignment; rotation RPE UNAVAILABLE"]),
    }
    per_pose = {"t": tt, "ate_m": ate, "gt_xyz": gt_xyz, "est_aligned_xyz": est_aligned,
                "alignment_R": r_align, "alignment_t": t_align}
    return {"summary": summary, "per_pose": per_pose}
