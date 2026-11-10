"""
One measured repeat of a run. Invoked by the runner in a fresh process so thread limits (env vars)
and CPU affinity take effect before NumPy does any work:

    python -m autonav_baseline.harness.worker --spec spec.json --out <dir>

Timing boundaries (all time.perf_counter, wall clock, single process):
  load_ms        reading one frame from disk (adapter generator step)
  preprocess_ms  invalid-point removal + range filter + voxel downsample
  register_ms    ICP + validity gate + pose update
  total_ms       preprocess_ms + register_ms   (pipeline latency; the frame is already in memory)
  e2e_ms         load_ms + total_ms            (includes file I/O, which a live sensor driver would not pay)
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.harness.env import collect_environment, peak_rss_mb
from autonav_baseline.harness.variants import make_odometry
from autonav_baseline.lidar.filtering import filter_by_range, remove_invalid_points, statistical_outlier_removal, voxel_downsample

FIELDS = [
    "rep", "frame_index", "timestamp", "warmup", "load_ms", "preprocess_ms", "register_ms", "total_ms", "e2e_ms",
    "points_raw", "points_valid", "points_range", "points_voxel", "icp_iterations", "num_inliers",
    "inlier_ratio", "residual_m", "accepted", "reject_reason", "step_translation_m", "step_rotation_deg",
    "invalid_ms", "range_ms", "voxel_ms", "outlier_ms", "points_outlier",
]


def _progress(out: Path, done: int, total: int, stage: str) -> None:
    (out / "progress.json").write_text(json.dumps({"frames_done": done, "frames_total": total, "stage": stage}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    spec = json.loads(a.spec.read_text(encoding="utf-8"))
    out = a.out
    out.mkdir(parents=True, exist_ok=True)

    if spec.get("cpus"):
        import psutil
        psutil.Process().cpu_affinity(spec["cpus"])

    # Record the environment AS SEEN BY THE WORKER (affinity and thread limits already applied).
    (out / "environment.json").write_text(json.dumps(collect_environment(), default=str), encoding="utf-8")

    adapter = get_adapter(spec["adapter"], root_path=Path(spec["frames"]) if spec.get("frames") else None,
                          config=spec.get("adapter_config"))
    start, stop = spec["window"]
    warmup = int(spec["warmup"])
    single_frame = spec["mode"] == "single-frame"
    odo = None if single_frame else make_odometry(spec["variant"], spec["params"])
    period_ms = 1000.0 / spec["nominal_hz"]
    params = spec["params"]

    rows, poses, stamps = [], [], []
    total = stop - start
    gen = adapter.get_lidar_frames(max_frames=stop)
    idx = -1
    t_loop0 = time.perf_counter()
    while True:
        t0 = time.perf_counter()
        try:
            frame = next(gen)
        except StopIteration:
            break
        load_ms = (time.perf_counter() - t0) * 1000.0
        idx += 1
        if idx < start:
            continue
        k = idx - start
        row = {f: "" for f in FIELDS}
        row.update(rep=spec["rep"], frame_index=idx, timestamp="" if frame.timestamp is None else repr(frame.timestamp),
                   warmup=int(0 < k <= warmup), load_ms=round(load_ms, 4), points_raw=len(frame.points))
        if single_frame:
            pts = frame.points
            t = time.perf_counter(); pts, _ = remove_invalid_points(pts); t_inv = time.perf_counter()
            pts, _ = filter_by_range(pts, params["min_range"], params["max_range"]); t_rng = time.perf_counter()
            n_range = len(pts)
            pts, _ = voxel_downsample(pts, params["voxel_size"]); t_vox = time.perf_counter()
            out_pts, _ = statistical_outlier_removal(pts, 16, 2.0); t_sor = time.perf_counter()
            pre = (t_vox - t) * 1000.0
            row.update(preprocess_ms=round(pre, 4), register_ms=0.0, total_ms=round(pre, 4), e2e_ms=round(load_ms + pre, 4),
                       invalid_ms=round((t_inv - t) * 1000, 4), range_ms=round((t_rng - t_inv) * 1000, 4),
                       voxel_ms=round((t_vox - t_rng) * 1000, 4), outlier_ms=round((t_sor - t_vox) * 1000, 4),
                       points_valid=len(pts) if False else "", points_range=n_range, points_voxel=len(pts),
                       points_outlier=len(out_pts), warmup=int(k < warmup))
        else:
            r = odo.process_frame(frame.points, idx, frame.timestamp)
            row.update(preprocess_ms=round(r.preprocess_ms, 4), register_ms=round(r.register_ms, 4),
                       total_ms=round(r.registration_latency_ms, 4),
                       e2e_ms=round(load_ms + r.registration_latency_ms, 4),
                       points_valid=r.points_after_valid, points_range=r.points_after_range,
                       points_voxel=r.downsampled_points_count, icp_iterations=r.icp_iterations,
                       num_inliers=r.num_inliers, inlier_ratio=round(r.inlier_ratio, 5),
                       residual_m="" if r.fitness_score == float("inf") else round(r.fitness_score, 5),
                       accepted=int(r.accepted), reject_reason=r.reject_reason,
                       step_translation_m=round(r.step_translation_m, 5), step_rotation_deg=round(r.step_rotation_deg, 4))
            poses.append(r.pose_4x4)
        stamps.append(np.nan if frame.timestamp is None else frame.timestamp)
        rows.append(row)
        if k % 5 == 0:
            _progress(out, k + 1, total, "processing")
    loop_wall = time.perf_counter() - t_loop0

    with open(out / "frames.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    if poses:
        np.save(out / "poses.npy", np.array(poses))
    np.save(out / "timestamps.npy", np.array(stamps))
    result = {"n_frames": len(rows), "loop_wall_s": loop_wall, "peak_rss_mb": peak_rss_mb(),
              "deadline_ms": period_ms, "gate": odo.gate.to_dict() if odo else None,
              "reject_counts": dict(odo.reject_counts) if odo else {}}
    (out / "result.json").write_text(json.dumps(result), encoding="utf-8")
    _progress(out, len(rows), total, "done")
    return 0


if __name__ == "__main__":
    sys.exit(main())