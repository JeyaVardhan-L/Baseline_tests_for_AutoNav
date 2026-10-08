"""
Oxford Spires dataset adapter (Oxford Robotics Institute, 2025).
Advanced dataset combining handheld multi-camera rigs and high-density LiDAR.
"""

from pathlib import Path
from typing import List, Optional, Generator, Dict, Any
from autonav_baseline.datasets.base import (
    DatasetAdapter,
    SensorType,
    DatasetInspectionResult,
)


class OxfordSpiresAdapter(DatasetAdapter):
    """
    Adapter for the Oxford Spires Dataset.
    Documented as an ADVANCED dataset for future multi-sensor localization and 3D reconstruction.
    """

    @property
    def name(self) -> str:
        return "Oxford Spires Dataset (Advanced Reference)"

    @property
    def sensor_types(self) -> List[SensorType]:
        return [SensorType.LIDAR, SensorType.RGB_CAMERA, SensorType.IMU]

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
                metadata={"status": "Advanced reference dataset. Not required for beginner tutorials."},
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
            available_streams=["spires_lidar", "multicam_color", "survey_gt"],
            frame_count=len(files),
            approx_duration_s=len(files) / 10.0 if files else 0.0,
            nominal_rate_hz=10.0,
            observed_rate_hz=None,
            is_rate_measured=False,
            missing_frames_count=0,
            malformed_files_count=0,
            metadata={"role": "Advanced benchmarking & long-term visual-inertial-LiDAR reference"},
        )
