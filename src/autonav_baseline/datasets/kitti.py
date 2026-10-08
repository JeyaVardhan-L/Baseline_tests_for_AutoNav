"""
KITTI Odometry dataset adapter.
NOTE: Automotive reference dataset — optional computational baseline, NOT representative of UAV operation.
"""

from pathlib import Path
from typing import List, Optional, Generator, Dict, Any
import numpy as np
from autonav_baseline.datasets.base import (
    DatasetAdapter,
    SensorType,
    LiDARFrame,
    DatasetInspectionResult,
)


class KITTIAdapter(DatasetAdapter):
    """
    Adapter for the KITTI Odometry dataset.
    Preserved as an optional terrestrial automotive reference baseline.
    DO NOT use KITTI to make UAV sensor or UAV hardware claims.
    """

    @property
    def name(self) -> str:
        return "KITTI Odometry (Automotive Reference Only)"

    @property
    def sensor_types(self) -> List[SensorType]:
        return [SensorType.LIDAR]

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
                metadata={"status": "Automotive reference baseline only. Not downloaded."},
            )

        bin_files = sorted(self.root_path.glob("*.bin"))
        total_bytes = sum(f.stat().st_size for f in bin_files)

        return DatasetInspectionResult(
            name=self.name,
            root_path=str(self.root_path),
            sensor_types=self.sensor_types,
            total_files=len(bin_files),
            total_bytes=total_bytes,
            file_formats=[".bin"],
            available_streams=["velodyne_pointclouds"],
            frame_count=len(bin_files),
            approx_duration_s=len(bin_files) / 10.0 if bin_files else 0.0,
            nominal_rate_hz=10.0,
            observed_rate_hz=None,
            is_rate_measured=False,
            missing_frames_count=0,
            malformed_files_count=0,
            metadata={
                "sensor": "Velodyne HDL-64E (automotive, ~13 kg, ~60 W)",
                "note": "Terrestrial reference only. Not representative of UAV operation.",
            },
        )

    def get_lidar_frames(self, max_frames: Optional[int] = None) -> Generator[LiDARFrame, None, None]:
        if not self.root_path or not self.root_path.exists():
            raise FileNotFoundError(f"KITTI directory not found: {self.root_path}")

        bin_files = sorted(self.root_path.glob("*.bin"))
        if not bin_files:
            raise FileNotFoundError(f"No .bin files found in {self.root_path}")

        limit = min(len(bin_files), max_frames) if max_frames else len(bin_files)

        for i in range(limit):
            fpath = bin_files[i]
            pts = np.fromfile(str(fpath), dtype=np.float32).reshape(-1, 4)
            xyz = pts[:, :3]
            intensity = pts[:, 3]
            t = i * 0.10  # 10 Hz nominal
            yield LiDARFrame(
                index=i,
                timestamp=t,
                points=xyz,
                intensity=intensity,
                metadata={"filename": fpath.name},
            )
