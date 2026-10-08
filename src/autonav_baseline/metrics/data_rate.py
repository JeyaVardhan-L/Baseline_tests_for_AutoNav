"""
Data rate and bandwidth computation utilities.

Formulas:
    points_per_sec = avg_points_per_frame * frame_rate_hz
    bytes_per_sec  = avg_frame_size_bytes * frame_rate_hz
    mib_per_sec    = bytes_per_sec / 2^20  (binary MiB/s)
    mb_per_sec     = bytes_per_sec / 10^6  (decimal MB/s)
    gib_per_min    = (bytes_per_sec * 60) / 2^30
    gib_per_hour   = gib_per_min * 60
"""

from dataclasses import dataclass
from typing import Dict, Any
from autonav_baseline.metrics.classification import Classification, tag


@dataclass
class DataRateMetrics:
    avg_frame_size_bytes: float
    frame_rate_hz: float
    is_frame_rate_measured: bool

    @property
    def bytes_per_sec(self) -> float:
        return self.avg_frame_size_bytes * self.frame_rate_hz

    @property
    def mib_per_sec(self) -> float:
        """Binary mebibytes per second (1 MiB = 1,048,576 bytes)."""
        return self.bytes_per_sec / (1024.0 ** 2)

    @property
    def mb_per_sec(self) -> float:
        """Decimal megabytes per second (1 MB = 1,000,000 bytes)."""
        return self.bytes_per_sec / 1_000_000.0

    @property
    def gib_per_min(self) -> float:
        """Binary gibibytes per minute."""
        return (self.bytes_per_sec * 60.0) / (1024.0 ** 3)

    @property
    def gib_per_hour(self) -> float:
        """Binary gibibytes per hour."""
        return self.gib_per_min * 60.0

    def to_dict(self) -> Dict[str, Any]:
        rate_classification = Classification.MEASURED if self.is_frame_rate_measured else Classification.ASSUMED
        return {
            "avg_frame_size_bytes": tag(round(self.avg_frame_size_bytes, 1), Classification.MEASURED, "bytes", "Average raw frame size"),
            "frame_rate_hz": tag(round(self.frame_rate_hz, 3), rate_classification, "Hz", "Observed or reference frame rate"),
            "bytes_per_sec": tag(round(self.bytes_per_sec, 1), Classification.DERIVED, "bytes/s", "avg_frame_size * frame_rate"),
            "mib_per_sec": tag(round(self.mib_per_sec, 3), Classification.DERIVED, "MiB/s", "Binary throughput"),
            "mb_per_sec": tag(round(self.mb_per_sec, 3), Classification.DERIVED, "MB/s", "Decimal throughput"),
            "gib_per_min": tag(round(self.gib_per_min, 4), Classification.DERIVED, "GiB/min", "Projected storage rate"),
            "gib_per_hour": tag(round(self.gib_per_hour, 3), Classification.DERIVED, "GiB/hour", "Projected storage rate"),
        }
