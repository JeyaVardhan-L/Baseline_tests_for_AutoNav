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

        # Relative Pose Error (RPE) translation drift
        if n > 1:
            step_est = np.linalg.norm(np.diff(aligned_est, axis=0), axis=1)
            step_gt = np.linalg.norm(np.diff(gt, axis=0), axis=1)
            rpe_trans_errors = np.abs(step_est - step_gt)
            rpe_rmse = float(np.sqrt(np.mean(rpe_trans_errors ** 2)))
        else:
            rpe_rmse = 0.0

        return {
            "status": "MEASURED",
            "num_aligned_poses": n,
            "ate_rmse_m": tag(round(rmse, 4), Classification.DERIVED, "meters"),
            "ate_mean_m": tag(round(mean_err, 4), Classification.DERIVED, "meters"),
            "ate_median_m": tag(round(median_err, 4), Classification.DERIVED, "meters"),
            "ate_max_m": tag(round(max_err, 4), Classification.DERIVED, "meters"),
            "rpe_trans_rmse_m": tag(round(rpe_rmse, 4), Classification.DERIVED, "meters"),
        }
    except Exception as e:
        return {
            "status": "UNVERIFIED",
            "reason": f"Alignment calculation failed: {str(e)}",
            "ate_rmse_m": tag(None, Classification.UNAVAILABLE, "meters"),
        }
