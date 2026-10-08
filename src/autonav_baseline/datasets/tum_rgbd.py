"""
TUM RGB-D Benchmark dataset adapter (Technical University of Munich).
The standard beginner-friendly RGB-D dataset: RGB images, 16-bit depth PNGs, and timestamp associations.
"""

from pathlib import Path
from typing import List, Optional, Generator, Dict, Any, Tuple
import numpy as np
from autonav_baseline.datasets.base import (
    DatasetAdapter,
    SensorType,
    DepthFrame,
    DatasetInspectionResult,
)


def parse_tum_txt(filepath: Path) -> List[Tuple[float, str]]:
    """Parses standard TUM association file (e.g. rgb.txt or depth.txt)."""
    records = []
    if not filepath.exists():
        return records
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    ts = float(parts[0])
                    rel_path = parts[1]
                    records.append((ts, rel_path))
                except ValueError:
                    continue
    return records


class TUMRGBDAdapter(DatasetAdapter):
    """
    Adapter for the TUM RGB-D dataset (e.g. freiburg1_xyz, freiburg1_desk).
    Reads RGB images, 16-bit millimeter depth PNG files, and timestamps.
    """

    @property
    def name(self) -> str:
        return "TUM RGB-D Benchmark"

    @property
    def sensor_types(self) -> List[SensorType]:
        return [SensorType.RGB_CAMERA, SensorType.DEPTH_CAMERA]

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

        depth_records = parse_tum_txt(self.root_path / "depth.txt")
        rgb_records = parse_tum_txt(self.root_path / "rgb.txt")
        frame_count = max(len(depth_records), len(rgb_records))

        duration_s = 0.0
        observed_hz = None
        is_measured = False
        if len(depth_records) >= 2:
            duration_s = depth_records[-1][0] - depth_records[0][0]
            if duration_s > 0:
                observed_hz = round(float(len(depth_records) / duration_s), 2)
                is_measured = True

        return DatasetInspectionResult(
            name=self.name,
            root_path=str(self.root_path),
            sensor_types=self.sensor_types,
            total_files=len(files),
            total_bytes=total_bytes,
            file_formats=extensions,
            available_streams=["rgb_png", "depth_16bit_png", "groundtruth_trajectory"],
            frame_count=frame_count,
            approx_duration_s=duration_s,
            nominal_rate_hz=30.0,
            observed_rate_hz=observed_hz,
            is_rate_measured=is_measured,
            missing_frames_count=abs(len(depth_records) - len(rgb_records)),
            malformed_files_count=0,
            metadata={
                "camera": "Microsoft Kinect v1",
                "depth_scale": 5000.0,  # 5000 units = 1 meter
                "fx": 525.0, "fy": 525.0, "cx": 319.5, "cy": 239.5,
            },
        )

    def get_depth_frames(self, max_frames: Optional[int] = None) -> Generator[DepthFrame, None, None]:
        if not self.root_path or not self.root_path.exists():
            raise FileNotFoundError(f"TUM RGB-D directory not found: {self.root_path}")

        depth_records = parse_tum_txt(self.root_path / "depth.txt")
        if not depth_records:
            # Fallback search for pngs
            pngs = sorted((self.root_path / "depth").glob("*.png"))
            depth_records = [(i * (1.0 / 30.0), str(p.relative_to(self.root_path))) for i, p in enumerate(pngs)]

        limit = min(len(depth_records), max_frames) if max_frames else len(depth_records)
        import matplotlib.image as mpimg

        for i in range(limit):
            ts, rel_depth = depth_records[i]
            depth_file = self.root_path / rel_depth
            if not depth_file.exists():
                continue

            try:
                # Read 16-bit depth png (scaled to float meters)
                raw_depth = mpimg.imread(str(depth_file))
                # If image is float in [0, 1] or uint16
                if raw_depth.dtype == np.uint16 or raw_depth.max() > 1.0:
                    depth_m = raw_depth.astype(np.float32) / 5000.0
                else:
                    depth_m = (raw_depth * 65535.0).astype(np.float32) / 5000.0
            except Exception:
                depth_m = np.zeros((480, 640), dtype=np.float32)

            yield DepthFrame(
                index=i,
                timestamp=ts,
                depth=depth_m,
                rgb=None,
                camera_metadata={"fx": 525.0, "fy": 525.0, "cx": 319.5, "cy": 239.5, "depth_scale": 5000.0},
            )
