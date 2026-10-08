"""
Synthetic dataset adapter for offline tutorials, smoke tests, and unit verification.
"""

from typing import List, Optional, Generator, Dict, Any
from pathlib import Path
import numpy as np
from autonav_baseline.datasets.base import (
    DatasetAdapter,
    SensorType,
    LiDARFrame,
    DepthFrame,
    IMUFrame,
    DatasetInspectionResult,
)


class SyntheticAdapter(DatasetAdapter):
    """
    Generates deterministic synthetic sensor data (LiDAR, Depth, IMU)
    so beginners can immediately test the entire software stack.
    """

    def __init__(self, root_path: Optional[Path] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(root_path, config)
        self.num_lidar_frames = self.config.get("num_frames", 100)
        self.points_per_frame = self.config.get("points_per_frame", 65536)  # Ouster OS-1 64 equivalent
        self.lidar_hz = self.config.get("lidar_hz", 10.0)
        self.imu_hz = self.config.get("imu_hz", 200.0)

    @property
    def name(self) -> str:
        return "Synthetic Demonstration Stream"

    @property
    def sensor_types(self) -> List[SensorType]:
        return [SensorType.LIDAR, SensorType.DEPTH_CAMERA, SensorType.IMU]

    def inspect(self) -> DatasetInspectionResult:
        approx_bytes = int(self.num_lidar_frames * self.points_per_frame * 16)
        duration_s = float(self.num_lidar_frames / self.lidar_hz)
        return DatasetInspectionResult(
            name=self.name,
            root_path="synthetic://in-memory",
            sensor_types=self.sensor_types,
            total_files=self.num_lidar_frames,
            total_bytes=approx_bytes,
            file_formats=[".synthetic", ".in-memory"],
            available_streams=["lidar_points", "depth_images", "imu_readings"],
            frame_count=self.num_lidar_frames,
            approx_duration_s=duration_s,
            nominal_rate_hz=self.lidar_hz,
            observed_rate_hz=self.lidar_hz,
            is_rate_measured=True,
            missing_frames_count=0,
            malformed_files_count=0,
            metadata={"source": "In-memory synthetic simulation", "purpose": "Tutorial and unit testing"},
        )

    def get_lidar_frames(self, max_frames: Optional[int] = None) -> Generator[LiDARFrame, None, None]:
        limit = min(self.num_lidar_frames, max_frames) if max_frames else self.num_lidar_frames
        rng = np.random.default_rng(42)

        for i in range(limit):
            t = i / self.lidar_hz
            # Generate structured scene: Ground plane (z = 0), four corridor walls, and a moving obstacle
            n_ground = self.points_per_frame // 3
            n_walls = self.points_per_frame // 3
            n_obstacle = self.points_per_frame - n_ground - n_walls

            # Ground plane
            x_g = rng.uniform(-10.0, 10.0, size=n_ground).astype(np.float32)
            y_g = rng.uniform(-10.0, 10.0, size=n_ground).astype(np.float32)
            z_g = rng.normal(-1.5, 0.02, size=n_ground).astype(np.float32)  # 1.5m below sensor

            # Corridor walls
            x_w = rng.uniform(-10.0, 10.0, size=n_walls).astype(np.float32)
            y_w = np.where(rng.uniform(size=n_walls) > 0.5, 4.0, -4.0).astype(np.float32) + rng.normal(0, 0.03, size=n_walls).astype(np.float32)
            z_w = rng.uniform(-1.5, 2.5, size=n_walls).astype(np.float32)

            # Obstacle
            theta = rng.uniform(0, 2 * np.pi, size=n_obstacle).astype(np.float32)
            r = rng.uniform(0.5, 1.0, size=n_obstacle).astype(np.float32)
            obs_center_x = 2.0 + np.sin(t * 0.5) * 2.0
            x_o = (obs_center_x + r * np.cos(theta)).astype(np.float32)
            y_o = (r * np.sin(theta)).astype(np.float32)
            z_o = rng.uniform(-1.5, 0.5, size=n_obstacle).astype(np.float32)

            xyz = np.vstack([
                np.column_stack([x_g, y_g, z_g]),
                np.column_stack([x_w, y_w, z_w]),
                np.column_stack([x_o, y_o, z_o]),
            ])

            intensity = rng.uniform(10.0, 255.0, size=len(xyz)).astype(np.float32)
            rings = rng.integers(0, 64, size=len(xyz)).astype(np.int32)

            yield LiDARFrame(
                index=i,
                timestamp=t,
                points=xyz,
                intensity=intensity,
                ring=rings,
                metadata={"synthetic": True, "frame_index": i},
            )

    def get_depth_frames(self, max_frames: Optional[int] = None) -> Generator[DepthFrame, None, None]:
        limit = min(self.num_lidar_frames, max_frames) if max_frames else self.num_lidar_frames
        height, width = 240, 320

        for i in range(limit):
            t = i / self.lidar_hz
            # Generate synthetic depth gradient with an obstacle
            u, v = np.meshgrid(np.arange(width), np.arange(height))
            depth = (2.0 + (v / float(height)) * 4.0).astype(np.float32)  # depth increasing from top to bottom
            # Add circular object
            cx, cy = int(160 + np.sin(t) * 50), 120
            mask = ((u - cx)**2 + (v - cy)**2) < 30**2
            depth[mask] = 1.2

            rgb = np.zeros((height, width, 3), dtype=np.uint8)
            rgb[:, :, 0] = (depth * 25).clip(0, 255).astype(np.uint8)
            rgb[:, :, 1] = 128
            rgb[mask, 2] = 255

            yield DepthFrame(
                index=i,
                timestamp=t,
                depth=depth,
                rgb=rgb,
                camera_metadata={"fx": 250.0, "fy": 250.0, "cx": 160.0, "cy": 120.0, "depth_scale": 1.0},
            )

    def get_imu_frames(self, max_frames: Optional[int] = None) -> Generator[IMUFrame, None, None]:
        total_samples = int(self.num_lidar_frames * (self.imu_hz / self.lidar_hz))
        limit = min(total_samples, max_frames) if max_frames else total_samples
        rng = np.random.default_rng(123)

        for i in range(limit):
            t = i / self.imu_hz
            # Gravity on Z (9.81 m/s^2), minor vibration noise on X, Y
            accel = np.array([
                rng.normal(0.0, 0.05) + np.sin(t * 5.0) * 0.2,
                rng.normal(0.0, 0.05),
                9.81 + rng.normal(0.0, 0.08),
            ], dtype=np.float32)

            gyro = np.array([
                rng.normal(0.0, 0.005),
                rng.normal(0.0, 0.005),
                np.sin(t * 0.5) * 0.1 + rng.normal(0.0, 0.005),
            ], dtype=np.float32)

            yield IMUFrame(
                index=i,
                timestamp=t,
                accel=accel,
                gyro=gyro,
                metadata={"synthetic": True},
            )
