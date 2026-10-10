"""
Common dataset adapter interface and normalized sensor records.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Generator, Any
import numpy as np


class SensorType(str, Enum):
    LIDAR = "LIDAR"
    DEPTH_CAMERA = "DEPTH_CAMERA"
    RGB_CAMERA = "RGB_CAMERA"
    IMU = "IMU"
    MULTI_MODAL = "MULTI_MODAL"


@dataclass
class LiDARFrame:
    """Normalized LiDAR scan."""
    index: int
    timestamp: Optional[float] = None  # seconds (Unix or sequence epoch, or None if unmeasured)
    points: np.ndarray = field(default_factory=lambda: np.zeros((0, 3), dtype=np.float32))  # (N, 3) float32 [x, y, z]
    intensity: Optional[np.ndarray] = None  # (N,) float32
    ring: Optional[np.ndarray] = None  # (N,) int32 laser ring/beam index
    point_timestamps: Optional[np.ndarray] = None  # (N,) float32 per-point time
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def num_points(self) -> int:
        return len(self.points)

    @property
    def byte_size(self) -> int:
        sz = self.points.nbytes
        if self.intensity is not None:
            sz += self.intensity.nbytes
        if self.ring is not None:
            sz += self.ring.nbytes
        return sz


@dataclass
class DepthFrame:
    """Normalized RGB + Depth frame."""
    index: int
    timestamp: Optional[float] = None  # seconds
    depth: np.ndarray = field(default_factory=lambda: np.zeros((0, 0), dtype=np.float32))  # (H, W) float32 in meters
    rgb: Optional[np.ndarray] = None  # (H, W, 3) uint8 RGB image
    camera_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def resolution(self) -> str:
        return f"{self.depth.shape[1]}x{self.depth.shape[0]}" if self.depth.ndim >= 2 else "0x0"

    @property
    def byte_size(self) -> int:
        sz = self.depth.nbytes
        if self.rgb is not None:
            sz += self.rgb.nbytes
        return sz


@dataclass
class IMUFrame:
    """Normalized IMU reading."""
    index: int
    timestamp: Optional[float] = None  # seconds
    accel: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))  # (3,) float32 [ax, ay, az] in m/s^2
    gyro: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))  # (3,) float32 [wx, wy, wz] in rad/s
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatasetInspectionResult:
    """Results of inspecting a local dataset directory."""
    name: str
    root_path: str
    sensor_types: List[SensorType]
    total_files: int
    total_bytes: int
    file_formats: List[str]
    available_streams: List[str]
    frame_count: int
    approx_duration_s: Optional[float] = None
    nominal_rate_hz: Optional[float] = None
    observed_rate_hz: Optional[float] = None
    is_rate_measured: bool = False
    missing_frames_count: Optional[int] = None
    malformed_files_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "root_path": self.root_path,
            "sensor_types": [s.value for s in self.sensor_types],
            "total_files": self.total_files,
            "total_bytes": self.total_bytes,
            "total_mb": round(self.total_bytes / (1024.0 * 1024.0), 2),
            "file_formats": self.file_formats,
            "available_streams": self.available_streams,
            "frame_count": self.frame_count,
            "approx_duration_s": round(self.approx_duration_s, 2) if self.approx_duration_s is not None else None,
            "nominal_rate_hz": self.nominal_rate_hz,
            "observed_rate_hz": round(self.observed_rate_hz, 3) if self.observed_rate_hz is not None else None,
            "is_rate_measured": self.is_rate_measured,
            "missing_frames_count": self.missing_frames_count,
            "malformed_files_count": self.malformed_files_count,
            "metadata": self.metadata,
        }


class DatasetAdapter(ABC):
    """Abstract base class for all dataset readers."""

    def __init__(self, root_path: Optional[Path] = None, config: Optional[Dict[str, Any]] = None):
        self.root_path = Path(root_path) if root_path else None
        self.config = config or {}

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def sensor_types(self) -> List[SensorType]:
        pass

    @abstractmethod
    def inspect(self) -> DatasetInspectionResult:
        """Inspects directory, files, formats, and structural health."""
        pass

    def get_lidar_frames(self, max_frames: Optional[int] = None) -> Generator[LiDARFrame, None, None]:
        raise NotImplementedError(f"{self.name} does not provide LiDAR streams.")

    def get_depth_frames(self, max_frames: Optional[int] = None) -> Generator[DepthFrame, None, None]:
        raise NotImplementedError(f"{self.name} does not provide depth streams.")

    def get_imu_frames(self, max_frames: Optional[int] = None) -> Generator[IMUFrame, None, None]:
        raise NotImplementedError(f"{self.name} does not provide IMU streams.")
