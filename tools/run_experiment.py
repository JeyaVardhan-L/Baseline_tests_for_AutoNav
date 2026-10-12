#!/usr/bin/env python3
"""
Unified Experiment Runner for AutoNav Research Baseline.

Usage:
    python tools/run_experiment.py --exp 01 --dataset newer_college
    python tools/run_experiment.py --exp 02 --dataset newer_college --max-frames 50
"""

from __future__ import annotations

import argparse
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EXPERIMENT_RUNNERS = {
    "01": "experiments/01_inspect_dataset.py",
    "1": "experiments/01_inspect_dataset.py",
    "02": "experiments/02_analyze_lidar_odometry.py",
    "2": "experiments/02_analyze_lidar_odometry.py",
}


def main():
    parser = argparse.ArgumentParser(
        description="Unified launcher for autonav_baseline research experiments.",
    )
    parser.add_argument(
        "--exp",
        type=str,
        required=True,
        help="Experiment step number (e.g. 01, 02)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="newer_college",
        help="Dataset name (default: newer_college)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path to dataset directory",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=50,
        help="Maximum frames to process (Step 2)",
    )
    parser.add_argument(
        "--voxel-size",
        type=float,
        default=0.15,
        help="Voxel downsampling size in meters (Step 2)",
    )

    args, unknown = parser.parse_known_args()

    exp_key = args.exp.strip()
    if exp_key not in EXPERIMENT_RUNNERS:
        print(f"[!] Unknown experiment '{args.exp}'. Available experiments: 01, 02")
        sys.exit(1)

    runner_rel = EXPERIMENT_RUNNERS[exp_key]
    runner_path = REPO_ROOT / runner_rel

    if not runner_path.is_file():
        print(f"[!] Runner script not found: {runner_path}")
        sys.exit(1)

    cmd = [sys.executable, str(runner_path), "--dataset", args.dataset]
    if args.path:
        cmd.extend(["--path", args.path])
    if exp_key in ["02", "2"]:
        cmd.extend(["--max-frames", str(args.max_frames), "--voxel-size", str(args.voxel_size)])
    if unknown:
        cmd.extend(unknown)

    print(f"[*] Executing: {' '.join(cmd)}\n")
    proc = subprocess.run(cmd)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
