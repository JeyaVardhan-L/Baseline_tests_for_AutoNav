"""
Hilti SLAM Challenge 2023 dataset adapter.
Sensors: Robosense Bpearl LiDAR (dome FOV), Xsens MTi-600 IMU (200 Hz), OAK-D cameras.
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


class HiltiAdapter(DatasetAdapter):
    """
    Adapter for the Hilti SLAM Challenge 2023 dataset.
    Features a mobile robotic base with Robosense Bpearl wide-angle dome LiDAR (10 Hz)
    and Xsens MTi-600 IMU (200 Hz).
    """

    @property
    def name(self) -> str:
        return "Hilti SLAM Challenge 2023 (Mobile Robot)"

    @property
    def sensor_types(self) -> List[SensorType]:
        return [SensorType.LIDAR, SensorType.IMU, SensorType.RGB_CAMERA]

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
                metadata={"status": "Directory not found. Manual download required."},
            )

        files = [p for p in self.root_path.rglob("*") if p.is_file()]
        total_bytes = sum(p.stat().st_size for p in files)
        extensions = sorted(list({p.suffix.lower() for p in files if p.suffix}))

        return DatasetInspectionResult(
            name=self.name,
            root_path=str(self.root_path),
            sensor_types=self.sensor_types,
            total_files=len(files),
            total_bytes=total_bytes,
            file_formats=extensions,
            available_streams=["bpearl_lidar", "xsens_imu_200hz", "oak_d_images"],
            frame_count=len(files),
            approx_duration_s=len(files) / 10.0 if files else 0.0,
            nominal_rate_hz=10.0,
            observed_rate_hz=None,
            is_rate_measured=False,
            missing_frames_count=0,
            malformed_files_count=0,
            metadata={
                "platform": "Wheeled ground mobile robot",
                "lidar": "Robosense Bpearl (super wide FOV 90x360 deg, 10 Hz)",
                "imu": "Xsens MTi-600 (200 Hz)",
            },
        )
