"""
Newer College Dataset adapter (Oxford Robotics Institute).
Sensor payload: Ouster OS-1 64-beam LiDAR, Ouster internal IMU, RealSense D435i stereo.

Supported recording formats:
  - Extracted point cloud files: .npy, .bin, .pcd (ASCII or binary), .ply (ASCII or binary).
  - Accompanying timestamp records: timestamps.csv, timestamps.txt, or filename-encoded timestamps.
  - ROS bag folders: Detected during inspection; requires offline extraction to point cloud files.

Limitations & Honest Reporting:
  - If timestamps are missing from disk, timestamps are reported as None / unmeasured rather than fabricated.
  - Modalities (IMU, Camera) are only reported if authentic matching data files exist on disk.
  - Malformed and missing frame counts are established empirically, never assumed to be zero.
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
from autonav_baseline.datasets.io import load_point_cloud_file, discover_timestamps


class NewerCollegeAdapter(DatasetAdapter):
    """
    Adapter for the Newer College Dataset.
    Supports directories containing extracted PCD/PLY/BIN/NPY files or ROS bag folders.
    Reads actual recorded point coordinates and authentic timestamps without synthetic fabrication.
    """

    SUPPORTED_LIDAR_EXTENSIONS = [".pcd", ".bin", ".ply", ".npy"]

    @property
    def name(self) -> str:
        return "Newer College Dataset (Oxford)"

    @property
    def sensor_types(self) -> List[SensorType]:
        # Evaluated dynamically in inspect() based on verified disk contents
        if not self.root_path or not self.root_path.exists():
            return [SensorType.LIDAR]
        return self._detect_modalities()

    def _detect_modalities(self) -> List[SensorType]:
        """Detects only modalities that genuinely exist on disk."""
        if not self.root_path or not self.root_path.exists():
            return [SensorType.LIDAR]

        types = []
        files = [p for p in self.root_path.rglob("*") if p.is_file()]

        has_lidar = any(p.suffix.lower() in self.SUPPORTED_LIDAR_EXTENSIONS for p in files)
        has_bags = any(p.suffix.lower() in [".bag", ".db3", ".mcap"] for p in files)
        if has_lidar or has_bags:
            types.append(SensorType.LIDAR)

        has_imu = any("imu" in p.name.lower() and p.suffix.lower() in [".csv", ".txt"] for p in files)
        if has_imu:
            types.append(SensorType.IMU)

        has_depth = any("depth" in p.name.lower() and p.suffix.lower() in [".png", ".npy", ".tiff"] for p in files)
        if has_depth:
            types.append(SensorType.DEPTH_CAMERA)

        has_rgb = any(
            ("color" in p.name.lower() or "rgb" in p.name.lower()) and p.suffix.lower() in [".png", ".jpg", ".jpeg"]
            for p in files
        )
        if has_rgb:
            types.append(SensorType.RGB_CAMERA)

        return types if types else [SensorType.LIDAR]

    def _find_lidar_files(self) -> List[Path]:
        """Finds and sorts supported point cloud files."""
        if not self.root_path or not self.root_path.exists():
            return []
        files = [
            p for p in self.root_path.rglob("*")
            if p.is_file() and p.suffix.lower() in self.SUPPORTED_LIDAR_EXTENSIONS
        ]
        return sorted(files)

    def inspect(self) -> DatasetInspectionResult:
        if not self.root_path or not self.root_path.exists():
            return DatasetInspectionResult(
                name=self.name,
                root_path=str(self.root_path),
                sensor_types=[SensorType.LIDAR],
                total_files=0,
                total_bytes=0,
                file_formats=[],
                available_streams=[],
                frame_count=0,
                approx_duration_s=None,
                nominal_rate_hz=10.0,
                observed_rate_hz=None,
                is_rate_measured=False,
                missing_frames_count=None,
                malformed_files_count=None,
                metadata={
                    "status": "Directory does not exist or contains no files. Please acquire data per datasets/newer-college/README.md",
                    "supported_formats": self.SUPPORTED_LIDAR_EXTENSIONS,
                },
            )

        all_files = [p for p in self.root_path.rglob("*") if p.is_file()]
        total_bytes = sum(p.stat().st_size for p in all_files)
        extensions = sorted(list({p.suffix.lower() for p in all_files if p.suffix}))

        lidar_files = self._find_lidar_files()
        bag_files = [p for p in all_files if p.suffix.lower() in [".bag", ".db3", ".mcap"]]
        imu_files = [p for p in all_files if "imu" in p.name.lower() and p.suffix.lower() in [".csv", ".txt"]]

        streams = []
        if lidar_files:
            streams.append("lidar_pointclouds")
        if bag_files:
            streams.append("rosbag_raw_streams")
        if imu_files:
            streams.append("imu_records")

        # Check file integrity empirically
        malformed_count = 0
        for lf in lidar_files:
            if lf.stat().st_size == 0:
                malformed_count += 1

        # Check authentic timestamps
        timestamps = discover_timestamps(self.root_path, lidar_files)
        is_rate_measured = False
        observed_rate_hz = None
        approx_duration = None
        missing_count = None

        if timestamps and len(timestamps) >= 2:
            intervals = np.diff(timestamps)
            positive_intervals = intervals[intervals > 0]
            if len(positive_intervals) > 0:
                mean_dt = float(np.mean(positive_intervals))
                if mean_dt > 0:
                    observed_rate_hz = 1.0 / mean_dt
                    is_rate_measured = True
                    approx_duration = float(timestamps[-1] - timestamps[0])

            # Check timestamp gaps exceeding 1.5x nominal period (150 ms at 10 Hz)
            nominal_dt = 1.0 / 10.0
            gap_threshold = 1.5 * nominal_dt
            missing_count = int(np.sum(intervals > gap_threshold))

        modalities = self._detect_modalities()

        return DatasetInspectionResult(
            name=self.name,
            root_path=str(self.root_path),
            sensor_types=modalities,
            total_files=len(all_files),
            total_bytes=total_bytes,
            file_formats=extensions,
            available_streams=streams,
            frame_count=len(lidar_files),
            approx_duration_s=approx_duration,
            nominal_rate_hz=10.0,
            observed_rate_hz=observed_rate_hz,
            is_rate_measured=is_rate_measured,
            missing_frames_count=missing_count,
            malformed_files_count=malformed_count,
            metadata={
                "sensor_lidar": "Ouster OS-1 64 (Gen 1)",
                "beams": 64,
                "horizontal_resolution": 1024,
                "nominal_points_per_frame": 65536,
                "timestamp_status": "Measured from recorded files" if is_rate_measured else "Unmeasured (No timestamp metadata file or timestamp-encoded filenames)",
                "supported_formats": self.SUPPORTED_LIDAR_EXTENSIONS,
            },
        )

    def get_lidar_frames(self, max_frames: Optional[int] = None) -> Generator[LiDARFrame, None, None]:
        if not self.root_path or not self.root_path.exists():
            raise FileNotFoundError(
                f"Newer College data directory not found: {self.root_path}\n"
                "Please acquire the dataset per instructions in datasets/newer-college/README.md"
            )

        lidar_files = self._find_lidar_files()
        if not lidar_files:
            bag_files = [p for p in self.root_path.rglob("*") if p.suffix.lower() in [".bag", ".db3", ".mcap"]]
            if bag_files:
                raise FileNotFoundError(
                    f"Directory contains ROS bags ({[b.name for b in bag_files]}) but no extracted point cloud files (.pcd, .bin, .npy, .ply).\n"
                    "Please extract point clouds from the ROS bag or supply an extracted point cloud directory."
                )
            raise FileNotFoundError(
                f"No supported LiDAR point cloud files ({', '.join(self.SUPPORTED_LIDAR_EXTENSIONS)}) found in {self.root_path}"
            )

        timestamps = discover_timestamps(self.root_path, lidar_files)
        limit = min(len(lidar_files), max_frames) if max_frames else len(lidar_files)

        for i in range(limit):
            fpath = lidar_files[i]
            xyz, intensity, meta = load_point_cloud_file(fpath)
            t = timestamps[i] if timestamps and i < len(timestamps) else None

            yield LiDARFrame(
                index=i,
                timestamp=t,
                points=xyz,
                intensity=intensity,
                metadata={
                    "filename": fpath.name,
                    "format": meta.get("format", fpath.suffix.lower()),
                    "timestamp_measured": t is not None,
                },
            )
