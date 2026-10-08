"""
Synthetic test fixtures with deterministic numerical values for fast unit testing.
"""

import numpy as np

def create_tiny_point_cloud() -> np.ndarray:
    """
    Returns 100 known points:
      - 90 points on a grid with known coordinates (x: 0..9, y: 0..8, z: 1.0)
      - 5 points with NaN/Inf values
      - 5 points at extreme distance (range > 100m)
    """
    rng = np.random.default_rng(42)
    # 90 clean points
    clean = []
    for x in range(10):
        for y in range(9):
            clean.append([float(x), float(y), 1.0])
    pts = np.array(clean, dtype=np.float32)

    # 5 NaN/Inf points
    invalid = np.array([
        [np.nan, 0.0, 1.0],
        [0.0, np.nan, 1.0],
        [np.inf, 1.0, 1.0],
        [1.0, -np.inf, 1.0],
        [np.nan, np.nan, np.nan],
    ], dtype=np.float32)

    # 5 out-of-range points
    far = np.array([
        [150.0, 0.0, 0.0],
        [0.0, 200.0, 0.0],
        [300.0, 300.0, 0.0],
        [-150.0, 0.0, 0.0],
        [0.0, -200.0, 0.0],
    ], dtype=np.float32)

    return np.vstack([pts, invalid, far])


def create_known_timestamps(count: int = 10, rate_hz: float = 10.0) -> list:
    """Returns chronologically ordered timestamps at a constant rate."""
    dt = 1.0 / rate_hz
    return [round(i * dt, 4) for i in range(count)]


def create_known_imu_data(count: int = 100, rate_hz: float = 200.0):
    """Returns timestamps, stationary acceleration (gravity along Z), and zero gyro."""
    dt = 1.0 / rate_hz
    ts = [round(i * dt, 5) for i in range(count)]
    accel = np.zeros((count, 3), dtype=np.float32)
    accel[:, 2] = 9.81  # 1G gravity
    gyro = np.zeros((count, 3), dtype=np.float32)
    return ts, accel, gyro
