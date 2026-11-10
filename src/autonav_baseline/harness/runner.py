"""
`autonav run`: orchestrates repeats, aggregates measurements and writes artifacts/runs/<run-id>/.

Each repeat is a whole run in a fresh worker process. Warm-up frames and the initial reference frame
are excluded from latency statistics (documented in run.json). The deadline is the sensor period.
"""

import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from autonav_baseline.datasets.groundtruth import load_pose_csv
from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.harness.config import (
    PROFILES, REPO_ROOT, VARIANTS, parse_window, profile_cpus, resolve_dataset,
)
from autonav_baseline.harness.env import collect_environment, git_info
from autonav_baseline.lidar.odometry import RegistrationGate
from autonav_baseline.metrics.trajectory_evaluation import evaluate_trajectory
from autonav_baseline.reporting.exporter import sanitize_paths

RUNS_DIR = REPO_ROOT / "artifacts" / "runs"
STAGES = ["load_ms", "preprocess_ms", "register_ms", "total_ms", "e2e_ms"]


def _dist(v: np.ndarray) -> Dict[str, float]:
    if len(v) == 0:
        return {"n": 0}
    p = np.percentile(v, [50, 90, 95, 99])  # linear interpolation
    return {"n": int(len(v)), "mean": float(v.mean()), "p50": float(p[0]), "p90": float(p[1]),
            "p95": float(p[2]), "p99": float(p[3]), "max": float(v.max()), "min": float(v.min()), "std": float(v.std())}


def _read_rows(path: Path) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _col(rows, name, mask=None) -> np.ndarray:
    vals = [float(r[name]) for r, m in zip(rows, mask if mask is not None else [True] * len(rows)) if m and r[name] != ""]
    return np.array(vals, dtype=float)


def _jsonable(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


def _spread(values: List[float]) -> Dict[str, float]:
    a = np.array(values, dtype=float)
    return {"min": float(a.min()), "median": float(np.median(a)), "max": float(a.max())}


def new_run_id(dataset: str, variant: str, profile: str, commit: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}_{dataset}_{variant}_{profile}_{commit[:7]}"


def execute(dataset_id: str, window: Optional[str], variant: str, profile: str, repeats: int = 3,
            warmup: int = 3, mode: str = "pipeline", voxel: float = 0.15, label: str = "",
            argv: Optional[List[str]] = None) -> Path:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}")
    if profile not in PROFILES:
        raise ValueError(f"profile must be one of {list(PROFILES)}")
    ds = resolve_dataset(dataset_id)
    if ds["frames"] and not Path(ds["frames"]).is_dir():
        raise FileNotFoundError(f"Frames directory for '{dataset_id}' not found. See docs/datasets.md for setup.")
    if mode == "pipeline" and not ds["consecutive"]:
        raise ValueError(f"'{dataset_id}' is NOT consecutive: odometry is not allowed. Use --mode single-frame.")

    adapter = get_adapter(ds["adapter"], root_path=Path(ds["frames"]) if ds["frames"] else None)
    n_total = adapter.inspect().frame_count
    start, stop = parse_window(window or ds["default_window"], n_total)

    git = git_info()
    run_id = new_run_id(dataset_id, f"{variant}{'-sf' if mode == 'single-frame' else ''}", profile, git["commit"])
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "logs").mkdir()
    print(f"run-id: {run_id}", flush=True)

    import psutil
    logical = psutil.cpu_count(logical=True)
    cpus = profile_cpus(profile, logical)
    prof = PROFILES[profile]
    params = {"voxel_size": voxel, "min_range": 0.5, "max_range": 50.0, "max_correspondence_distance": 1.5,
              "max_iterations": 30, "tolerance": 1e-4}
    child_env = dict(os.environ)
    if prof["threads"] is not None:
        for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
            child_env[k] = str(prof["threads"])
    child_env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + child_env.get("PYTHONPATH", "")
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"

    started = datetime.now(timezone.utc)
    rep_status = []
    for rep in range(repeats):
        rep_dir = run_dir / "repeats" / f"rep{rep}"
        rep_dir.mkdir(parents=True)
        spec = {"rep": rep, "adapter": ds["adapter"], "frames": ds["frames"], "window": [start, stop],
                "warmup": warmup, "mode": mode, "variant": variant, "params": params,
                "nominal_hz": ds["nominal_hz"], "cpus": cpus}
        (rep_dir / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
        (run_dir / "progress.json").write_text(json.dumps({"repeat": rep + 1, "repeats": repeats, "status": "running"}))
        with open(run_dir / "logs" / f"rep{rep}.log", "w", encoding="utf-8") as log:
            rc = subprocess.run([sys.executable, "-B", "-m", "autonav_baseline.harness.worker",
                                 "--spec", str(rep_dir / "spec.json"), "--out", str(rep_dir)],
                                env=child_env, stdout=log, stderr=subprocess.STDOUT).returncode
        rep_status.append(rc)
        if rc != 0:
            break
    ended = datetime.now(timezone.utc)
    ok = len(rep_status) == repeats and all(rc == 0 for rc in rep_status)

    summary = _aggregate(run_dir, ds, mode, repeats, warmup, ok)
    env_file = run_dir / "repeats" / "rep0" / "environment.json"
    env_info = json.loads(env_file.read_text(encoding="utf-8")) if env_file.is_file() else collect_environment()
    env_info["cpu_affinity_requested"] = cpus
    run_json = {
        "run_id": run_id, "label": label, "status": "completed" if ok else "failed",
        "command": "autonav " + " ".join(argv or []), "started_utc": started.isoformat(), "ended_utc": ended.isoformat(),
        "git": git, "mode": mode, "variant": variant,
        "dataset": {k: ds[k] for k in ("id", "sensor", "sequence", "licence", "evidence", "consecutive", "nominal_hz",
                                       "same_sensor_as_target")},
        "window": {"start": start, "stop": stop, "n_frames": stop - start, "of_total": n_total},
        "parameters": params, "registration_gate": RegistrationGate().to_dict() if mode == "pipeline" else None,
        "profile": {"id": profile, "claim": prof["claim"], "threads": prof["threads"]},
        "methodology": {"repeats": repeats, "warmup_frames_excluded": warmup, "initial_frame_excluded": True,
                        "deadline_ms": 1000.0 / ds["nominal_hz"], "percentile_method": "linear interpolation",
                        "timing": "time.perf_counter wall clock; total_ms = preprocess + register (frame in memory); e2e_ms adds file load",
                        "gc": "default (not disabled)"},
        "environment": env_info,
        "hardware_label": f"Measured on {env_info['cpu_model']} ({profile}); not a Raspberry Pi, not embedded hardware",
        "evidence_tags": {"latency": "MEASURED", "violation_percent": "DERIVED", "peak_rss": "MEASURED",
                          "ate_rpe": "DERIVED (ground truth)", "dataset": "DECLARED"},
    }
    (run_dir / "run.json").write_text(json.dumps(sanitize_paths(_jsonable(run_json)), indent=2), encoding="utf-8")
    (run_dir / "summary.json").write_text(json.dumps(sanitize_paths(_jsonable(summary)), indent=2), encoding="utf-8")
    (run_dir / "progress.json").write_text(json.dumps({"status": run_json["status"]}))
    if ok:  # canonical frames.csv = repeat 0
        (run_dir / "frames.csv").write_text((run_dir / "repeats" / "rep0" / "frames.csv").read_text(encoding="utf-8"), encoding="utf-8")
        from autonav_baseline.harness.verdict import generate_verdicts
        saved_run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        (run_dir / "verdicts.json").write_text(json.dumps(sanitize_paths(_jsonable(generate_verdicts(summary, saved_run))), indent=2), encoding="utf-8")
        try:
            from autonav_baseline.harness.viz import export_viz
            export_viz(run_dir, saved_run, summary)
        except Exception as exc:  # visuals must never invalidate a measurement
            (run_dir / "logs" / "viz_error.log").write_text(repr(exc), encoding="utf-8")
    return run_dir


def _aggregate(run_dir: Path, ds: Dict[str, Any], mode: str, repeats: int, warmup: int, ok: bool) -> Dict[str, Any]:
    if not ok:
        return {"status": "failed", "reason": "a worker repeat exited non-zero; see logs/"}
    deadline = 1000.0 / ds["nominal_hz"]
    per_rep, pooled_rows = [], []
    results = []
    for rep in range(repeats):
        rd = run_dir / "repeats" / f"rep{rep}"
        rows = _read_rows(rd / "frames.csv")
        results.append(json.loads((rd / "result.json").read_text()))
        first = 0 if mode == "single-frame" else 1   # initial reference frame has no registration
        stats_rows = [r for i, r in enumerate(rows) if i >= first and r["warmup"] == "0"]
        pooled_rows.extend(stats_rows)
        tot = _col(stats_rows, "total_ms"); e2e = _col(stats_rows, "e2e_ms")
        d = _dist(tot)
        per_rep.append({"rep": rep, "n": d["n"], "p50": d["p50"], "p95": d["p95"], "p99": d["p99"], "max": d["max"],
                        "violations_total": int((tot > deadline).sum()),
                        "violation_percent_total": float((tot > deadline).mean() * 100),
                        "violation_percent_e2e": float((e2e > deadline).mean() * 100),
                        "throughput_fps": results[rep]["n_frames"] / results[rep]["loop_wall_s"],
                        "peak_rss_mb": results[rep]["peak_rss_mb"]})
    lat = {s: _dist(_col(pooled_rows, s)) for s in STAGES}
    tot_all = _col(pooled_rows, "total_ms"); e2e_all = _col(pooled_rows, "e2e_ms")
    summary: Dict[str, Any] = {
        "status": "completed", "mode": mode, "evidence": ds["evidence"],
        "latency_ms": lat,
        "deadline": {"deadline_ms": deadline, "basis": "sensor period at nominal rate",
                     "pipeline_total_ms": {"violations": int((tot_all > deadline).sum()), "of": int(len(tot_all)),
                                           "violation_percent": float((tot_all > deadline).mean() * 100) if len(tot_all) else None},
                     "end_to_end_ms": {"violations": int((e2e_all > deadline).sum()), "of": int(len(e2e_all)),
                                       "violation_percent": float((e2e_all > deadline).mean() * 100) if len(e2e_all) else None},
                     "note": "A P95 below the deadline still allows up to 5 % of frames to miss it; the violation rate is the deadline statistic."},
        "throughput_fps": _spread([r["throughput_fps"] for r in per_rep]),
        "peak_rss_mb": _spread([r["peak_rss_mb"] for r in per_rep]),
        "per_repeat": per_rep,
        "repeat_spread": {k: _spread([r[k] for r in per_rep]) for k in ("p50", "p95", "p99", "violation_percent_total")},
    }
    if mode == "single-frame":
        for col in ("invalid_ms", "range_ms", "voxel_ms", "outlier_ms"):
            summary["latency_ms"][col] = _dist(_col(pooled_rows, col))
        summary["points"] = {c: _dist(_col(pooled_rows, c)) for c in ("points_raw", "points_range", "points_voxel", "points_outlier")}
        summary["labelling"] = "NON-CONSECUTIVE frames: single-frame preprocessing statistics only; no odometry, no accuracy."
        return summary

    rep0 = _read_rows(run_dir / "repeats" / "rep0" / "frames.csv")
    reg = rep0[1:]
    acc = np.array([int(r["accepted"]) for r in reg], dtype=bool)
    reasons: Dict[str, int] = {}
    for r in reg:
        if r["reject_reason"]:
            reasons[r["reject_reason"]] = reasons.get(r["reject_reason"], 0) + 1
    summary["registration"] = {
        "attempts": len(reg), "accepted": int(acc.sum()), "rejected": int((~acc).sum()),
        "rejected_by_reason": reasons, "accepted_percent": float(acc.mean() * 100) if len(reg) else None,
        "icp_iterations": _dist(_col(reg, "icp_iterations")), "inlier_ratio": _dist(_col(reg, "inlier_ratio")),
        "residual_m": _dist(_col(reg, "residual_m")), "path_length_estimated_m": float(_col(reg, "step_translation_m").sum()),
    }
    summary["points_per_frame"] = {c: _dist(_col(rep0, c)) for c in ("points_raw", "points_valid", "points_range", "points_voxel")}
    poses = [np.load(run_dir / "repeats" / f"rep{r}" / "poses.npy") for r in range(repeats)]
    summary["deterministic_across_repeats"] = bool(all(np.allclose(poses[0], p, atol=1e-9) for p in poses[1:]))
    gt_path = ds.get("gt")
    if gt_path and Path(gt_path).is_file():
        gt_t, gt = load_pose_csv(Path(gt_path))
        stamps = np.load(run_dir / "repeats" / "rep0" / "timestamps.npy")
        ev = evaluate_trajectory(poses[0], stamps, gt, gt_t, rpe_seconds=(1.0, 5.0), rpe_distances_m=(5.0, 10.0))
        summary["accuracy"] = ev["summary"]
        summary["accuracy_arrays"] = "see viz/ (trajectory_error.json)"
        np.savez_compressed(run_dir / "accuracy_per_pose.npz", **{k: v for k, v in ev["per_pose"].items()})
    else:
        summary["accuracy"] = {"status": "UNAVAILABLE", "reason": "no ground truth for this dataset/window"}
    summary["verdict_inputs"] = {
        "p95_total_ms": lat["total_ms"].get("p95"), "p99_total_ms": lat["total_ms"].get("p99"),
        "violation_percent_total": summary["deadline"]["pipeline_total_ms"]["violation_percent"],
        "accepted_percent": summary["registration"]["accepted_percent"],
        "ate_rmse_m": (summary["accuracy"].get("ate_m") or {}).get("rmse") if isinstance(summary["accuracy"], dict) else None,
        "gt_path_length_m": summary["accuracy"].get("gt_path_length_m") if isinstance(summary["accuracy"], dict) else None,
        "deadline_ms": deadline,
    }
    return summary