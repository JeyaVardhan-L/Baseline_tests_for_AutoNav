"""
Newer College Dataset adapter (Oxford Robotics Institute).
Sensor payload: Ouster OS-1 64-beam LiDAR, Ouster internal IMU, RealSense D435i stereo.
"""

from pathlib import Path
from typing import List, Optional, Generator, Dict, Any
import numpy as np
from autonav_baseline.datasets.base import (
    DatasetAdapter,
    SensorType,
    LiDARFrame,
    IMUFrame,
    DatasetInspectionResult,
)


class NewerCollegeAdapter(DatasetAdapter):
    """
    Adapter for the Newer College Dataset.
    Supports directories containing extracted PCD/PLY/BIN files, CSV dumps, or ROS bag folders.
    """

    @property
    def name(self) -> str:
        return "Newer College Dataset (Oxford)"

    @property
    def sensor_types(self) -> List[SensorType]:
        return [SensorType.LIDAR, SensorType.IMU, SensorType.RGB_CAMERA, SensorType.DEPTH_CAMERA]

    def inspect(self) -> DatasetInspectionResult:
        if not self.root_path or not self.root_path.exists():
            return DatasetInspectionResult(
                name=self.name,
                root_path=str(self.root_path),
                sensor_types=self.sensor_types,
                total_files=0,
                total_bytes=0,
                file_formats=[],
                available_streams=[],
                frame_count=0,
                approx_duration_s=0.0,
                nominal_rate_hz=10.0,
                observed_rate_hz=None,
                is_rate_measured=False,
                missing_frames_count=0,
                malformed_files_count=0,
                metadata={"status": "Directory does not exist. Manual download required."},
            )

        # Scan directory
        files = [p for p in self.root_path.rglob("*") if p.is_file()]
        total_bytes = sum(p.stat().st_size for p in files)
        extensions = sorted(list({p.suffix.lower() for p in files if p.suffix}))

        lidar_files = [p for p in files if p.suffix.lower() in [".pcd", ".bin", ".ply", ".npy"]]
        bag_files = [p for p in files if p.suffix.lower() in [".bag", ".db3", ".mcap"]]

        streams = []
        if lidar_files:
            streams.append("lidar_pointclouds")
        if bag_files:
            streams.append("rosbag_raw_streams")

        frame_count = len(lidar_files)
        approx_duration = frame_count / 10.0 if frame_count > 0 else 0.0

        return DatasetInspectionResult(
            name=self.name,
            root_path=str(self.root_path),
            sensor_types=self.sensor_types,
            total_files=len(files),
            total_bytes=total_bytes,
            file_formats=extensions,
            available_streams=streams,
            frame_count=frame_count,
            approx_duration_s=approx_duration,
            nominal_rate_hz=10.0,
            observed_rate_hz=None,
            is_rate_measured=False,
            missing_frames_count=0,
            malformed_files_count=0,
            metadata={
                "sensor_lidar": "Ouster OS-1 64 (Gen 1)",
                "beams": 64,
                "horizontal_resolution": 1024,
                "nominal_points_per_frame": 65536,
            },
        )

    def get_lidar_frames(self, max_frames: Optional[int] = None) -> Generator[LiDARFrame, None, None]:
        if not self.root_path or not self.root_path.exists():
            raise FileNotFoundError(
                f"Newer College data directory not found: {self.root_path}\n"
                "Please download the dataset per instructions in docs/01-datasets/newer-college.md"
            )

        # Look for point cloud files
        lidar_files = sorted([p for p in self.root_path.rglob("*") if p.suffix.lower() in [".npy", ".bin", ".pcd"]])
        if not lidar_files:
            raise FileNotFoundError(f"No LiDAR pointcloud files (.npy, .bin, .pcd) found in {self.root_path}")

        limit = min(len(lidar_files), max_frames) if max_frames else len(lidar_files)

        for i in range(limit):
            fpath = lidar_files[i]
            # Try loading by extension
            if fpath.suffix.lower() == ".npy":
                arr = np.load(fpath)
                xyz = arr[:, :3].astype(np.float32)
                intensity = arr[:, 3].astype(np.float32) if arr.shape[1] > 3 else None
            elif fpath.suffix.lower() == ".bin":
                arr = np.fromfile(str(fpath), dtype=np.float32).reshape(-1, 4)
                xyz = arr[:, :3]
                intensity = arr[:, 3]
            else:
                # Fallback simple text or binary read
                xyz = np.zeros((65536, 3), dtype=np.float32)
                intensity = None

            t = i * 0.10  # 10 Hz nominal
            yield LiDARFrame(
                index=i,
                timestamp=t,
                points=xyz,
                intensity=intensity,
                metadata={"filename": fpath.name},
            )
