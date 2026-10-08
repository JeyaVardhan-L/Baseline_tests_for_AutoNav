"""
Inertial Measurement Unit (IMU) data characterization and statistics.
"""

from typing import Dict, Any, List
import numpy as np
from autonav_baseline.metrics.classification import Classification, tag


def compute_imu_statistics(
    timestamps: List[float],
    accel: np.ndarray,
    gyro: np.ndarray,
) -> Dict[str, Any]:
    """
    Computes statistical and timing properties of an IMU stream.

    Args:
        timestamps: (N,) timestamps in seconds.
        accel: (N, 3) linear acceleration [ax, ay, az] in m/s^2.
        gyro: (N, 3) angular velocity [wx, wy, wz] in rad/s.
    """
    num_samples = len(timestamps)
    if num_samples < 2:
        return {"num_samples": num_samples}

    ts = np.asarray(timestamps, dtype=np.float64)
    dt = np.diff(ts)
    dt_ms = dt * 1000.0

    mean_dt_ms = float(np.mean(dt_ms))
    jitter_ms = float(np.std(dt_ms))
    min_dt_ms = float(np.min(dt_ms))
    max_dt_ms = float(np.max(dt_ms))

    observed_hz = 1000.0 / mean_dt_ms if mean_dt_ms > 0 else 0.0

    # Accelerometer stats
    acc_norm = np.linalg.norm(accel, axis=1)
    acc_mean = np.mean(accel, axis=0)
    acc_std = np.std(accel, axis=0)

    # Gyroscope stats
    gyro_norm = np.linalg.norm(gyro, axis=1)
    gyro_mean = np.mean(gyro, axis=0)
    gyro_std = np.std(gyro, axis=0)

    # Missing sample detection: any dt > 1.8 * mean_dt is flagged as a likely dropped packet
    dropped_mask = dt_ms > (1.8 * mean_dt_ms)
    dropped_count = int(np.sum(dropped_mask))

    return {
        "num_samples": tag(num_samples, Classification.MEASURED, "samples"),
        "duration_s": tag(round(float(ts[-1] - ts[0]), 3), Classification.MEASURED, "s"),
        "observed_frequency_hz": tag(round(observed_hz, 2), Classification.DERIVED, "Hz", "1000 / mean_dt_ms"),
        "mean_interval_ms": tag(round(mean_dt_ms, 3), Classification.MEASURED, "ms"),
        "jitter_ms": tag(round(jitter_ms, 3), Classification.MEASURED, "ms", "Std dev of sample intervals"),
        "min_interval_ms": tag(round(min_dt_ms, 3), Classification.MEASURED, "ms"),
        "max_interval_ms": tag(round(max_dt_ms, 3), Classification.MEASURED, "ms"),
        "suspected_dropped_packets": tag(dropped_count, Classification.DERIVED, "packets", "Intervals > 1.8x mean interval"),
        "accel": {
            "mean_xyz_mps2": [round(float(v), 4) for v in acc_mean],
            "std_xyz_mps2": [round(float(v), 4) for v in acc_std],
            "mean_norm_mps2": round(float(np.mean(acc_norm)), 4),
        },
        "gyro": {
            "mean_xyz_radps": [round(float(v), 5) for v in gyro_mean],
            "std_xyz_radps": [round(float(v), 5) for v in gyro_std],
            "mean_norm_radps": round(float(np.mean(gyro_norm)), 5),
        },
        "dt_ms_series": dt_ms.tolist(),
        "timestamps": ts.tolist(),
        "accel_norm_series": acc_norm.tolist(),
        "gyro_norm_series": gyro_norm.tolist(),
    }
