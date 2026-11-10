"""
Deterministic SYNTHETIC LiDAR scene, for unit tests only.

SYNTHETIC data must never be published as experimental evidence. Every frame carries
metadata["synthetic"] = True and the adapter name says so. The scene is a closed room with two
pillars, sampled once in the world frame; each frame is that same static point set seen from a known
sensor pose, so the exact trajectory is known analytically.
"""

from typing import Generator, List, Optional, Tuple
import numpy as np

from autonav_baseline.datasets.base import (
    DatasetAdapter, SensorType, LiDARFrame, DatasetInspectionResult,
)


def make_room_points(n: int = 20000, seed: int = 7) -> np.ndarray:
    """Static world-frame points on a 20 x 16 x 6 m room (floor, ceiling, 4 walls) and two pillars."""
    rng = np.random.default_rng(seed)
    sx, sy, sz = 20.0, 16.0, 6.0
    areas = np.array([sx * sy, sx * sy, sx * sz, sx * sz, sy * sz, sy * sz], dtype=float)
    per_face = (areas / areas.sum() * (n - 2000)).astype(int)
    faces = []
    for face, m in enumerate(per_face):
        u = rng.uniform(0, 1, m)
        v = rng.uniform(0, 1, m)
        if face in (0, 1):   # floor / ceiling
            faces.append(np.column_stack([-10 + sx * u, -8 + sy * v, np.full(m, 0.0 if face == 0 else sz)]))
        elif face in (2, 3):  # y = +-8 walls
            faces.append(np.column_stack([-10 + sx * u, np.full(m, -8.0 if face == 2 else 8.0), sz * v]))
        else:                # x = +-10 walls
            faces.append(np.column_stack([np.full(m, -10.0 if face == 4 else 10.0), -8 + sy * u, sz * v]))
    for cx, cy in ((-2.0, 3.0), (3.0, -4.0)):
        ang = rng.uniform(0, 2 * np.pi, 1000)
        z = rng.uniform(0, sz, 1000)
        faces.append(np.column_stack([cx + 0.5 * np.cos(ang), cy + 0.5 * np.sin(ang), z]))
    return np.vstack(faces)


def _rot_z(yaw: float) -> np.ndarray:
    c, s = np.cos(yaw), np.sin(yaw)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


class SyntheticAdapter(DatasetAdapter):
    """Known-trajectory synthetic scene. Config: num_frames, step_m, yaw_step_deg, seed."""

    @property
    def name(self) -> str:
        return "SYNTHETIC room (tests only, not evidence)"

    @property
    def sensor_types(self) -> List[SensorType]:
        return [SensorType.LIDAR]

    def _params(self):
        c = self.config
        return int(c.get("num_frames", 20)), float(c.get("step_m", 0.1)), float(c.get("yaw_step_deg", 0.5))

    def ground_truth(self) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (timestamps (N,), sensor poses (N,4,4)) in the room (world) frame."""
        n, step, yaw_deg = self._params()
        poses = np.tile(np.eye(4), (n, 1, 1))
        pos = np.array([-6.0, 0.0, 1.5])
        yaw = 0.0
        for k in range(n):
            poses[k, :3, :3] = _rot_z(yaw)
            poses[k, :3, 3] = pos
            pos = pos + _rot_z(yaw) @ np.array([step, 0.0, 0.0])  # move forward in the body frame
            yaw += np.radians(yaw_deg)
        return np.arange(n) * 0.1, poses

    def inspect(self) -> DatasetInspectionResult:
        n, _, _ = self._params()
        return DatasetInspectionResult(
            name=self.name, root_path="<synthetic>", sensor_types=self.sensor_types,
            total_files=0, total_bytes=0, file_formats=[], available_streams=["synthetic_points"],
            frame_count=n, approx_duration_s=(n - 1) * 0.1, nominal_rate_hz=10.0,
            observed_rate_hz=10.0, is_rate_measured=False, missing_frames_count=0,
            malformed_files_count=0, metadata={"synthetic": True},
        )

    def get_lidar_frames(self, max_frames: Optional[int] = None) -> Generator[LiDARFrame, None, None]:
        t, poses = self.ground_truth()
        world = make_room_points(seed=int(self.config.get("seed", 7)))
        limit = len(t) if max_frames is None else min(len(t), max_frames)
        for k in range(limit):
            r, p = poses[k, :3, :3], poses[k, :3, 3]
            pts_sensor = (world - p) @ r  # p_s = R^T (p_w - t)
            yield LiDARFrame(index=k, timestamp=float(t[k]), points=pts_sensor.astype(np.float32),
                             metadata={"synthetic": True})