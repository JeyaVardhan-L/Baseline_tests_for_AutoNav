#!/usr/bin/env python3
"""
Validate a directory of PCD frames against a ground-truth pose file before it is used for odometry.

Checks (all measured, nothing assumed):
  1. frame spacing: gaps around the nominal period, longest consecutive run
  2. ground-truth timestamps cover the window, and every frame has a pose within --max-dt
  3. ground truth shows real motion (path length, rotation, speed, stationary segments)
  4. every PCD header is consistent (POINTS, payload size)
Writes <out>.json and <out>.md (no absolute paths).

Usage:
    python tools/validate_window.py --frames <dir> --gt <registered_poses.csv> --out <report-stem> [--period 0.1]
"""

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from autonav_baseline.datasets.groundtruth import load_pose_csv                # noqa: E402
from autonav_baseline.datasets.io import scan_sort_key, scan_timestamp_from_name        # noqa: E402
from autonav_baseline.metrics.trajectory_evaluation import associate_by_time   # noqa: E402

_NAME = re.compile(r"cloud_(\d+)_(\d+)\.pcd$")


def validate(frames_dir: Path, gt_csv: Path, period: float, max_dt: float, moving_speed: float):
    by_name = sorted(frames_dir.glob("*.pcd"))
    files = sorted(by_name, key=scan_sort_key)
    ts = np.array([t for t in (scan_timestamp_from_name(f) for f in files) if t is not None])
    report = {"frames_dir": frames_dir.name, "n_frames": int(len(files)), "nominal_period_s": period,
              "filename_order_is_chronological": by_name == files}
    if len(ts) != len(files) or len(ts) < 3:
        report["verdict"] = "FAIL: unparseable filenames or too few frames"
        return report, files, ts

    d = np.diff(ts)
    ok = np.abs(d - period) <= 0.012
    runs, start = [], 0
    for i, v in enumerate(ok):
        if not v:
            runs.append((start, i)); start = i + 1
    runs.append((start, len(ts) - 1))
    lengths = [e - s + 1 for s, e in runs]
    best = int(np.argmax(lengths))
    report["spacing"] = {
        "dt_min_s": float(d.min()), "dt_median_s": float(np.median(d)), "dt_max_s": float(d.max()),
        "gaps_near_nominal": int(ok.sum()), "gaps_other": int((~ok).sum()),
        "longest_consecutive_run_frames": int(lengths[best]),
        "longest_run_index_range": [int(runs[best][0]), int(runs[best][1])],
        "monotonic": bool(np.all(d > 0)),
    }
    report["window_s"] = [float(ts[0]), float(ts[-1])]

    gt_t, gt_poses = load_pose_csv(gt_csv)
    report["ground_truth"] = {
        "n_poses": int(len(gt_t)), "t_range_s": [float(gt_t[0]), float(gt_t[-1])],
        "median_dt_s": float(np.median(np.diff(gt_t))),
        "covers_window": bool(gt_t[0] <= ts[0] and ts[-1] <= gt_t[-1]),
    }
    ia, ib = associate_by_time(ts, gt_t, max_dt=max_dt)
    off = np.abs(ts[ia] - gt_t[ib]) if len(ia) else np.array([np.inf])
    report["association"] = {
        "max_dt_s": max_dt, "frames_with_pose": int(len(ia)),
        "frames_without_pose": int(len(ts) - len(ia)), "max_offset_s": float(off.max()),
    }

    # motion in the window (poses associated to frames)
    pos = gt_poses[ib, :3, 3]
    rot = gt_poses[ib, :3, :3]
    step = np.linalg.norm(np.diff(pos, axis=0), axis=1)
    dts = np.diff(ts[ia])
    speed = step / np.maximum(dts, 1e-9)
    rel = np.einsum("nij,njk->nik", np.transpose(rot[:-1], (0, 2, 1)), rot[1:])
    ang = np.degrees(np.arccos(np.clip((np.trace(rel, axis1=1, axis2=2) - 1) / 2, -1, 1)))
    moving = speed > moving_speed
    idx = np.flatnonzero(moving)
    report["motion"] = {
        "path_length_m": float(step.sum()), "net_displacement_m": float(np.linalg.norm(pos[-1] - pos[0])),
        "total_rotation_deg": float(ang.sum()),
        "speed_mps": {"median": float(np.median(speed)), "p95": float(np.percentile(speed, 95)), "max": float(speed.max())},
        "moving_fraction": float(moving.mean()), "moving_threshold_mps": moving_speed,
        "per_step_translation_m_max": float(step.max()),
        "per_step_rotation_deg_max": float(ang.max()),
    }
    if len(idx):
        first, last = int(idx[0]), int(idx[-1]) + 1   # step i joins frames i and i+1
        report["selected_window"] = {
            "rule": f"trim leading/trailing steps slower than {moving_speed} m/s",
            "first_frame_index": first, "last_frame_index": last, "n_frames": last - first + 1,
            "leading_stationary_frames": first, "trailing_stationary_frames": int(len(ts) - 1 - last),
        }
    ok_all = (report["spacing"]["gaps_other"] == 0 and report["ground_truth"]["covers_window"]
              and report["association"]["frames_without_pose"] == 0 and report["motion"]["path_length_m"] > 5.0)
    report["verdict"] = "PASS" if ok_all else "REVIEW"
    return report, files, ts


def _check_headers(files):
    bad, sizes = [], set()
    for f in files:
        head = f.read_bytes()[:700]
        try:
            end = head.index(b"DATA binary\n") + 12
        except ValueError:
            bad.append(f.name); continue
        n = int(re.search(rb"POINTS (\d+)", head).group(1))
        sizes.add(n)
        # packed 29-byte Ouster record
        if f.stat().st_size - end < n * 29:
            bad.append(f.name)
    return {"distinct_POINTS": sorted(int(s) for s in sizes), "bad_files": bad}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True, type=Path)
    ap.add_argument("--gt", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path, help="report path stem (writes .json and .md)")
    ap.add_argument("--period", type=float, default=0.1)
    ap.add_argument("--max-dt", type=float, default=0.02)
    ap.add_argument("--moving-speed", type=float, default=0.1)
    a = ap.parse_args()
    report, files, _ = validate(a.frames, a.gt, a.period, a.max_dt, a.moving_speed)
    report["headers"] = _check_headers(files)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = ["# Window validation", "", f"Verdict: **{report['verdict']}**", ""]
    for k in ("spacing", "ground_truth", "association", "motion", "selected_window", "headers"):
        if k in report:
            md += [f"## {k}", "", "```json", json.dumps(report[k], indent=2), "```", ""]
    a.out.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k in ("verdict", "n_frames", "spacing", "association", "motion", "selected_window")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())