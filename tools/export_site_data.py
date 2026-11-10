#!/usr/bin/env python3
"""
Export published runs to the static site: site/public/data/.

The site never recomputes anything. It renders what this script copies from artifacts/runs/<id>/ plus a
dataset catalogue and metric definitions derived from the harness configuration. SYNTHETIC runs are
refused. Every exported file is scanned for private paths and secrets; the export aborts if any is found.

Usage:  python tools/export_site_data.py [--out site/public/data]
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
from autonav_baseline.harness.config import DATASETS, PROFILES  # noqa: E402
from autonav_baseline.harness.verdict import compare_profiles    # noqa: E402

RUNS = REPO / "artifacts" / "runs"
COPY = ["run.json", "summary.json", "verdicts.json", "frames.csv"]

METRICS = [
    {"id": "total_ms", "name": "Pipeline latency", "unit": "ms", "evidence": "MEASURED",
     "definition": "Wall-clock time to process one frame that is already in memory: invalid-point removal, range filter, voxel downsample, ICP registration, validity gate and pose update.",
     "calculation": "time.perf_counter around each stage in the worker process; total = preprocess + register. Warm-up frames and the initial reference frame are excluded.",
     "interpretation": "Compare with the sensor period (100 ms at 10 Hz). Single-machine software timing; not a hard real-time guarantee."},
    {"id": "e2e_ms", "name": "End-to-end latency", "unit": "ms", "evidence": "MEASURED",
     "definition": "Pipeline latency plus the time to read the frame from disk.",
     "calculation": "load_ms + total_ms.", "interpretation": "A live sensor driver delivers frames in memory, so total_ms is the primary number; e2e shows the file-I/O cost of offline replay."},
    {"id": "percentiles", "name": "P50 / P90 / P95 / P99 / max", "unit": "ms", "evidence": "DERIVED",
     "definition": "Order statistics of per-frame latency pooled over all repeats.", "calculation": "numpy.percentile, linear interpolation.",
     "interpretation": "P99 and max describe the tail that causes missed frames."},
    {"id": "violation_percent", "name": "Deadline violation rate", "unit": "% of frames", "evidence": "DERIVED",
     "definition": "Share of measured frames whose pipeline latency is strictly greater than the sensor period.",
     "calculation": "count(total_ms > deadline) / frames measured.",
     "interpretation": "The deadline statistic. A P95 below the deadline still allows 5 % of frames to miss it."},
    {"id": "throughput_fps", "name": "Sustained throughput", "unit": "frames/s", "evidence": "MEASURED",
     "definition": "Frames processed per second of wall-clock time over the whole loop, file loading included.",
     "calculation": "frames / loop wall time per repeat (min, median, max over repeats).", "interpretation": "Must exceed the sensor rate (10 fps) to keep up in steady state."},
    {"id": "peak_rss_mb", "name": "Peak memory", "unit": "MB", "evidence": "MEASURED",
     "definition": "Peak resident (working-set) memory of the worker process.", "calculation": "psutil peak_wset (Windows) or ru_maxrss.",
     "interpretation": "Process peak; machine RAM is a separate specification, not a measurement."},
    {"id": "accepted_percent", "name": "Accepted registrations", "unit": "%", "evidence": "DERIVED",
     "definition": "Registrations that pass the validity gate (inlier ratio, residual, plausible motion) divided by attempts.",
     "calculation": "Frame 0 is excluded (it has no registration). Thresholds are in run.json.", "interpretation": "Rejections are counted by reason, never silently accepted."},
    {"id": "ate_rmse_m", "name": "Absolute trajectory error (RMSE)", "unit": "m", "evidence": "DERIVED",
     "definition": "RMS position error between the estimated and ground-truth trajectories after a rigid SE(3) Umeyama alignment (no scale), using timestamp-associated poses.",
     "calculation": "Association within 20 ms, one-to-one.", "interpretation": "Needs ground truth. Without loop closure error grows with distance. It also includes any unmodelled sensor-to-body offset (lever arm) between the estimated sensor positions and the ground-truth body positions, so it mixes drift with extrinsic bias."},
    {"id": "rpe", "name": "Relative pose error (position)", "unit": "m, % of segment", "evidence": "DERIVED",
     "definition": "Error of the displacement over fixed time or path-length windows, in the aligned world frame.",
     "calculation": "Rotation RPE is UNAVAILABLE because the ground-truth body frame differs from the sensor frame (DEC-012). Position RPE removes the step-direction (yaw) offset but not a lever arm, and the global alignment is fitted over the whole window, so it is mildly optimistic.",
     "interpretation": "Drift per unit motion; less sensitive to a single bad alignment than ATE."},
    {"id": "icp_iterations", "name": "ICP iterations", "unit": "count", "evidence": "MEASURED",
     "definition": "Iterations before the convergence rule stopped (cap 30).", "calculation": "Per registration.", "interpretation": "Drives register_ms; hitting the cap flags poor initial alignment."},
    {"id": "inlier_ratio", "name": "Inlier ratio", "unit": "fraction", "evidence": "MEASURED",
     "definition": "Source points with a target neighbour within 1.5 m, divided by source points.", "calculation": "Last ICP iteration.", "interpretation": "Low values mean little scan overlap or a wrong match."},
    {"id": "residual_m", "name": "Registration residual", "unit": "m", "evidence": "MEASURED",
     "definition": "Mean distance of inlier correspondences at the start of the last iteration.", "calculation": "Point-to-point distance for all variants.", "interpretation": "Included in the validity gate."},
]


def scan(text: str, where: str):
    """Abort the export if a file contains a machine path, e-mail address, Drive link or Drive-id-like token."""
    home = Path.home().name
    pats = [r"[A-Za-z]:[\\/]+Users[\\/]", r"/home/[a-z]", r"/Users/[A-Za-z]", r"drive\.google\.com",
            r"[\w.+-]+@[\w-]+\.[\w.-]+", r"(?<![A-Za-z0-9_-])(?=[A-Za-z0-9_-]*[A-Z])(?=[A-Za-z0-9_-]*[a-z])(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]{33}(?![A-Za-z0-9_-])"]
    if home and len(home) > 3:
        pats.append(re.escape(home))
    bad = [p for p in pats if re.search(p, text)]
    if bad:
        raise SystemExit(f"refusing to export: {where} matches private-data pattern {bad}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=REPO / "site" / "public" / "data")
    a = ap.parse_args()
    pub_file = REPO / "artifacts" / "published.json"
    ids = json.loads(pub_file.read_text())["runs"] if pub_file.is_file() else []
    if a.out.exists():
        shutil.rmtree(a.out)          # generated output only
    (a.out / "runs").mkdir(parents=True)
    index = []
    for rid in ids:
        src = RUNS / rid
        run = json.loads((src / "run.json").read_text(encoding="utf-8"))
        if run["dataset"]["evidence"] == "SYNTHETIC":
            raise SystemExit(f"refusing to publish SYNTHETIC run {rid}")
        dst = a.out / "runs" / rid
        dst.mkdir()
        for f in COPY:
            if (src / f).is_file():
                shutil.copy2(src / f, dst / f)
        if (src / "viz").is_dir():
            shutil.copytree(src / "viz", dst / "viz")
        s = json.loads((src / "summary.json").read_text(encoding="utf-8"))
        item = {"run_id": rid, "dataset": run["dataset"]["id"], "evidence": run["dataset"]["evidence"], "variant": run["variant"],
                "profile": run["profile"]["id"], "mode": run["mode"], "label": run.get("label", ""),
                "window": run["window"], "commit": run["git"]["commit"][:7], "git_dirty": run["git"]["dirty"],
                "started_utc": run["started_utc"], "cpu_model": run["environment"]["cpu_model"],
                "hardware_label": run["hardware_label"]}
        if s.get("status") == "completed":
            t = s["latency_ms"]["total_ms"]
            item.update(p50_ms=t["p50"], p90_ms=t["p90"], p95_ms=t["p95"], p99_ms=t["p99"], max_ms=t["max"],
                        violation_percent=s["deadline"]["pipeline_total_ms"]["violation_percent"])
            if s.get("accuracy", {}).get("status") == "MEASURED":
                item["ate_rmse_m"] = s["accuracy"]["ate_m"]["rmse"]
            if "registration" in s:
                item["accepted_percent"] = s["registration"]["accepted_percent"]
        index.append(item)

    groups = {}
    for it in index:
        if it["mode"] == "pipeline":
            groups.setdefault((it["dataset"], it["variant"], it["label"]), {})[it["profile"]] = json.loads(
                (a.out / "runs" / it["run_id"] / "summary.json").read_text(encoding="utf-8"))
    comparisons = [{"dataset": k[0], "variant": k[1], "label": k[2], **compare_profiles(v)} for k, v in groups.items() if len(v) > 1]
    datasets = {k: {kk: v[kk] for kk in ("sensor", "sequence", "licence", "evidence", "consecutive", "nominal_hz", "same_sensor_as_target")}
                for k, v in DATASETS.items() if k != "synthetic"}
    (a.out / "index.json").write_text(json.dumps({"runs": index}, indent=2), encoding="utf-8")
    (a.out / "metrics.json").write_text(json.dumps(METRICS, indent=2), encoding="utf-8")
    (a.out / "datasets.json").write_text(json.dumps(datasets, indent=2), encoding="utf-8")
    (a.out / "profiles.json").write_text(json.dumps({k: v["claim"] for k, v in PROFILES.items()}, indent=2), encoding="utf-8")
    (a.out / "comparisons.json").write_text(json.dumps(comparisons, indent=2), encoding="utf-8")
    for f in a.out.rglob("*"):
        if f.is_file() and f.suffix in (".json", ".csv"):
            scan(f.read_text(encoding="utf-8"), f.relative_to(a.out).as_posix())
    print(f"exported {len(index)} published run(s) to {a.out.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())