"""
Pipeline stage profiler and latency distribution tools.
"""

import time
from typing import Dict, List, Any
import numpy as np
from autonav_baseline.metrics.classification import Classification, tag


def compute_distribution(samples: List[float]) -> Dict[str, float]:
    """Compute mean, median, p95, p99, min, max, std of a series in milliseconds."""
    if not samples:
        return {"mean": 0.0, "median": 0.0, "p95": 0.0, "p99": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}
    arr = np.asarray(samples, dtype=np.float64)
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "std": float(np.std(arr)),
    }


class StageTimer:
    """High-resolution wall-clock timer for pipeline stages using time.perf_counter()."""

    def __init__(self):
        self.stage_times: Dict[str, List[float]] = {}
        self._current_start = 0.0

    def start(self) -> None:
        self._current_start = time.perf_counter()

    def stop(self, stage_name: str) -> float:
        elapsed_ms = (time.perf_counter() - self._current_start) * 1000.0
        if stage_name not in self.stage_times:
            self.stage_times[stage_name] = []
        self.stage_times[stage_name].append(elapsed_ms)
        return elapsed_ms

    def record(self, stage_name: str, elapsed_ms: float) -> None:
        if stage_name not in self.stage_times:
            self.stage_times[stage_name] = []
        self.stage_times[stage_name].append(elapsed_ms)

    def summary(self) -> Dict[str, Dict[str, float]]:
        """Return distribution of all recorded stages."""
        out = {}
        for stage, times in self.stage_times.items():
            out[stage] = compute_distribution(times)
        return out


def evaluate_realtime_status(
    pipeline_latency_ms: float,
    sensor_period_ms: float,
) -> Dict[str, Any]:
    """
    Evaluates whether the host machine processing pipeline keeps up with the sensor frame rate.

    Args:
        pipeline_latency_ms: Mean or P95 total processing latency per frame.
        sensor_period_ms: 1000.0 / sensor_hz (e.g. 100 ms for 10 Hz).

    Returns:
        Dict with status, margin, and human explanation.
    """
    margin_ms = sensor_period_ms - pipeline_latency_ms
    can_keep_up = margin_ms > 0.0
    status_str = "PASS (CAN KEEP UP)" if can_keep_up else "FAIL (CANNOT KEEP UP)"

    return {
        "status": status_str,
        "can_keep_up": can_keep_up,
        "pipeline_latency_ms": tag(round(pipeline_latency_ms, 2), Classification.MEASURED, "ms", "Total processing latency"),
        "sensor_period_ms": tag(round(sensor_period_ms, 2), Classification.ASSUMED, "ms", "Sensor inter-frame arrival period"),
        "available_margin_ms": tag(round(margin_ms, 2), Classification.DERIVED, "ms", "sensor_period - pipeline_latency"),
        "processing_fps": tag(round(1000.0 / max(pipeline_latency_ms, 1e-6), 2), Classification.DERIVED, "FPS", "Max sustainable processing rate"),
    }
