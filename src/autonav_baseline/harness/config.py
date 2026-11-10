"""
Dataset ids, hardware profiles and window parsing for `autonav run`.

Dataset locations are repo-relative defaults. A git-ignored `config.local.yaml` may override them:

    dataset_roots:
      newer_college_bag9: D:/data/ncd/bag9/point_clouds
      newer_college_bag9_gt: D:/data/ncd/registered_poses.csv
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[3]

DATASETS: Dict[str, Dict[str, Any]] = {
    "newer_college_bag9": {
        "adapter": "newer_college",
        "frames": "datasets/newer-college/01_short_experiment/contiguous_bag9/point_clouds",
        "gt": "datasets/newer-college/01_short_experiment/contiguous/registered_poses.csv",
        "sensor": "Ouster OS1-64 Gen1 (64 beams, 1024 columns, 10 Hz)",
        "sequence": "Newer College 2020, 01_short_experiment, bag 9 (last 27 s)",
        "licence": "CC BY-NC-SA 4.0",
        "evidence": "REAL",
        "consecutive": True,
        "nominal_hz": 10.0,
        "default_window": "0:270",
        "same_sensor_as_target": True,
    },
    "newer_college_sparse": {
        "adapter": "newer_college",
        "frames": "datasets/newer-college/01_short_experiment/contiguous/point_clouds/ouster_scan",
        "gt": None,
        "sensor": "Ouster OS1-64 Gen1 (64 beams, 1024 columns, 10 Hz)",
        "sequence": "Newer College 2020, 01_short_experiment, thinned sample (11.3 % of scans)",
        "licence": "CC BY-NC-SA 4.0",
        "evidence": "REAL-NON-CONSECUTIVE",
        "consecutive": False,
        "nominal_hz": 10.0,
        "default_window": "0:200",
        "same_sensor_as_target": True,
    },
    "oxford_spires": {
        "adapter": "oxford_spires",
        "frames": "datasets/oxford-spires/window/lidar",
        "gt": "datasets/oxford-spires/window/gt.csv",
        "sensor": "Hesai QT64 (64 beams) - DIFFERENT from OS1-64 (beam layout, FOV, range)",
        "sequence": "Oxford Spires, one window",
        "licence": "see docs/decision-log.md",
        "evidence": "REAL",
        "consecutive": True,
        "nominal_hz": 10.0,
        "default_window": "0:300",
        "same_sensor_as_target": False,
    },
    "synthetic": {
        "adapter": "synthetic",
        "frames": None,
        "gt": None,
        "sensor": "none (SYNTHETIC room)",
        "sequence": "synthetic",
        "licence": "n/a",
        "evidence": "SYNTHETIC",
        "consecutive": True,
        "nominal_hz": 10.0,
        "default_window": "0:20",
        "same_sensor_as_target": False,
    },
}

# CPU affinity: one logical CPU per core, taking every other logical CPU from 0 (assumes SMT pairs are
# adjacent, true on Windows/Intel). Recorded exactly in run.json.
PROFILES: Dict[str, Dict[str, Any]] = {
    "laptop-full": {
        "threads": None, "n_cpus": None,
        "claim": "Development-laptop performance (no limits).",
    },
    "laptop-4c": {
        "threads": 4, "n_cpus": 4,
        "claim": "Scaling with core count on the development laptop. One-way inference only: a miss here makes a miss on a Raspberry Pi 5 very likely; a pass says nothing about the Pi.",
    },
    "laptop-1c": {
        "threads": 1, "n_cpus": 1,
        "claim": "Single-core scaling on the development laptop. One-way inference only (see laptop-4c).",
    },
}

PROFILES["arm-cloud"] = {
    "threads": None, "n_cpus": None,
    "claim": "Real ARM server-class shared cloud VM (GitHub Actions). Noisy. NOT a Raspberry Pi.",
}
PROFILES["pi5"] = {
    "threads": None, "n_cpus": None,
    "claim": "Raspberry Pi 5 measurement. Valid only when this profile is run on a real Pi 5; the CPU model recorded in run.json must say so.",
}

VARIANTS = ("baseline", "optimized", "p2plane")


def load_local_config() -> Dict[str, Any]:
    p = REPO_ROOT / "config.local.yaml"
    if not p.is_file():
        return {}
    import yaml
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def resolve_dataset(dataset_id: str) -> Dict[str, Any]:
    if dataset_id not in DATASETS:
        raise ValueError(f"Unknown dataset id '{dataset_id}'. Known: {', '.join(DATASETS)}")
    info = dict(DATASETS[dataset_id])
    over = (load_local_config().get("dataset_roots") or {})
    if dataset_id in over:
        info["frames"] = over[dataset_id]
    if f"{dataset_id}_gt" in over:
        info["gt"] = over[f"{dataset_id}_gt"]
    for key in ("frames", "gt"):
        if info.get(key):
            p = Path(info[key])
            info[key] = str(p if p.is_absolute() else REPO_ROOT / p)
    info["id"] = dataset_id
    return info


def parse_window(spec: str, n_total: int) -> Tuple[int, int]:
    """'0:270' -> frames [0, 270); 'first:50' -> [0, 50); 'all' -> everything."""
    spec = spec.strip().lower()
    if spec == "all":
        return 0, n_total
    if spec.startswith("first:"):
        return 0, min(int(spec.split(":")[1]), n_total)
    a, b = spec.split(":")
    start, stop = int(a), min(int(b), n_total)
    if not 0 <= start < stop:
        raise ValueError(f"Invalid window '{spec}' for {n_total} frames")
    return start, stop


def profile_cpus(profile_id: str, logical: int) -> Optional[List[int]]:
    n = PROFILES[profile_id]["n_cpus"]
    if n is None:
        return None
    cpus = list(range(0, min(2 * n, logical), 2))[:n]
    return cpus if len(cpus) == n else list(range(min(n, logical)))