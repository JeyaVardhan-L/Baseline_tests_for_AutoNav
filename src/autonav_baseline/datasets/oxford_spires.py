"""
Oxford Spires adapter (Oxford Robotics Institute; CC BY-NC-SA 4.0).

Sensor: Hesai QT64 (64 channels, 10 Hz, ~104 deg vertical field of view, 60 m range). This is NOT an
Ouster OS1-64: the beam layout, field of view and range differ, so results are never presented as
OS1-64 results. Frames are PCD files named `<sec>.<nsec>.pcd` in a single directory; timestamps come
only from those names.
"""

from pathlib import Path
from typing import Generator, List, Optional

from autonav_baseline.datasets.base import (
    DatasetAdapter, DatasetInspectionResult, LiDARFrame, SensorType,
)
from autonav_baseline.datasets.io import discover_timestamps, load_point_cloud_file, scan_sort_key


class OxfordSpiresAdapter(DatasetAdapter):
    @property
    def name(self) -> str:
        return "Oxford Spires (Hesai QT64)"

    @property
    def sensor_types(self) -> List[SensorType]:
        return [SensorType.LIDAR]

    def _files(self) -> List[Path]:
        if not self.root_path or not self.root_path.is_dir():
            return []
        return sorted((p for p in self.root_path.glob("*.pcd")), key=scan_sort_key)

    def inspect(self) -> DatasetInspectionResult:
        files = self._files()
        ts = discover_timestamps(self.root_path, files) if files else None
        rate, dur = None, None
        if ts and len(ts) > 1:
            span = ts[-1] - ts[0]
            dur = span
            rate = (len(ts) - 1) / span if span > 0 else None
        return DatasetInspectionResult(
            name=self.name, root_path=str(self.root_path), sensor_types=self.sensor_types,
            total_files=len(files), total_bytes=sum(f.stat().st_size for f in files),
            file_formats=[".pcd"] if files else [], available_streams=["lidar_pointclouds"] if files else [],
            frame_count=len(files), approx_duration_s=dur, nominal_rate_hz=10.0,
            observed_rate_hz=rate, is_rate_measured=rate is not None, missing_frames_count=None,
            malformed_files_count=None,
            metadata={"sensor_lidar": "Hesai QT64", "note": "differs from OS1-64 (beam layout, FOV, range)"},
        )

    def get_lidar_frames(self, max_frames: Optional[int] = None) -> Generator[LiDARFrame, None, None]:
        files = self._files()
        if not files:
            raise FileNotFoundError("No Spires PCD frames found. See docs/datasets.md (tools/fetch_spires.py).")
        ts = discover_timestamps(self.root_path, files)
        limit = len(files) if max_frames is None else min(len(files), max_frames)
        for i in range(limit):
            xyz, intensity, meta = load_point_cloud_file(files[i])
            yield LiDARFrame(index=i, timestamp=ts[i] if ts else None, points=xyz, intensity=intensity,
                             metadata={"filename": files[i].name, "format": meta.get("format")})