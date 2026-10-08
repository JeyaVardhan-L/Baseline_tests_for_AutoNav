"""
OpenLORIS-Scene dataset adapter.
Indoor mobile robot dataset providing RGB, Depth, IMU, wheel odometry, and 2D laser scans.
"""

from pathlib import Path
from typing import List, Optional, Generator, Dict, Any
from autonav_baseline.datasets.base import (
    DatasetAdapter,
    SensorType,
    DepthFrame,
    IMUFrame,
    DatasetInspectionResult,
)


class OpenLORISAdapter(DatasetAdapter):
    """
    Adapter for OpenLORIS-Scene indoor robotics dataset.
    Environments: office, corridor, home, cafe, supermarket.
    Sensors: RealSense T265 (stereo fisheye + IMU), RealSense D435i (RGB-D + IMU), wheel encoders.
    NOTE: This is NOT a LiDAR dataset; it provides RGB-D and 2D planar laser scans.
    """

    @property
    def name(self) -> str:
        return "OpenLORIS-Scene (Indoor Robot)"

    @property
    def sensor_types(self) -> List[SensorType]:
        return [SensorType.RGB_CAMERA, SensorType.DEPTH_CAMERA, SensorType.IMU]

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
                nominal_rate_hz=30.0,
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
            available_streams=["rgb_color", "depth_aligned", "imu_d435i", "imu_t265", "wheel_odom"],
            frame_count=len(files),
            approx_duration_s=len(files) / 30.0 if files else 0.0,
            nominal_rate_hz=30.0,
            observed_rate_hz=None,
            is_rate_measured=False,
            missing_frames_count=0,
            malformed_files_count=0,
            metadata={
                "dataset_type": "RGB-D + Inertial + Odometry (Indoor Mobile Robot)",
                "note": "Not a 3D LiDAR dataset. Ideal for indoor corridor/office geometry learning.",
            },
        )
