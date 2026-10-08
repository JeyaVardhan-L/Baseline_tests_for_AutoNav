#!/usr/bin/env python3
"""
Unified Experiment Runner for autonav_baseline.

Usage:
    python tools/run_experiment.py --exp 01 --dataset synthetic
    python tools/run_experiment.py --exp 02 --dataset synthetic --frames 50
    python tools/run_experiment.py --exp 03 --dataset synthetic --cli
    python tools/run_experiment.py --exp 04 --dataset synthetic
    python tools/run_experiment.py --exp 05 --dataset synthetic
    python tools/run_experiment.py --exp 06 --dataset synthetic
    python tools/run_experiment.py --exp 07 --dataset synthetic
    python tools/run_experiment.py --exp 08 --dataset synthetic
    python tools/run_experiment.py --exp 09 --dataset synthetic
    python tools/run_experiment.py --exp 10
"""

import argparse
import sys
import subprocess
from pathlib import Path

EXPERIMENT_DIRS = {
    "01": "experiments/01-data-inspection/run.py",
    "1": "experiments/01-data-inspection/run.py",
    "02": "experiments/02-lidar-characterization/run.py",
    "2": "experiments/02-lidar-characterization/run.py",
    "03": "experiments/03-pointcloud-playback/run.py",
    "3": "experiments/03-pointcloud-playback/run.py",
    "04": "experiments/04-pointcloud-filtering/run.py",
    "4": "experiments/04-pointcloud-filtering/run.py",
    "05": "experiments/05-downsampling/run.py",
    "5": "experiments/05-downsampling/run.py",
    "06": "experiments/06-depth-characterization/run.py",
    "6": "experiments/06-depth-characterization/run.py",
    "07": "experiments/07-imu-characterization/run.py",
    "7": "experiments/07-imu-characterization/run.py",
    "08": "experiments/08-timestamp-analysis/run.py",
    "8": "experiments/08-timestamp-analysis/run.py",
    "09": "experiments/09-realtime-processing/run.py",
    "9": "experiments/09-realtime-processing/run.py",
    "10": "experiments/10-sensor-fusion-preparation/run.py",
}


def main():
    parser = argparse.ArgumentParser(
        description="Unified launcher for autonav_baseline experiments (EXP-01 to EXP-10).",
    )
    parser.add_argument(
        "--exp",
        type=str,
        required=True,
        help="Experiment number (e.g. 01, 02, ..., 10)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="synthetic",
        help="Dataset name (e.g. synthetic, newer_college, hilti, tum_rgbd, openloris, kitti)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Custom dataset directory path (optional)",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=None,
        help="Maximum frames to process",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run interactive experiments in CLI streaming mode (headless friendly)",
    )

    args, unknown = parser.parse_known_args()

    exp_key = args.exp.strip().zfill(2)
    if exp_key not in EXPERIMENT_DIRS and args.exp not in EXPERIMENT_DIRS:
        print(f"Error: Unknown experiment '{args.exp}'. Available experiments: 01 to 10")
        sys.exit(1)

    script_path = Path(EXPERIMENT_DIRS.get(exp_key, EXPERIMENT_DIRS.get(args.exp)))
    if not script_path.exists():
        print(f"Error: Experiment script not found: {script_path}")
        sys.exit(1)

    cmd = [sys.executable, str(script_path), "--dataset", args.dataset]
    if args.path:
        cmd.extend(["--path", args.path])
    if args.frames:
        cmd.extend(["--frames", str(args.frames)])
    if args.cli:
        cmd.append("--cli")
    if unknown:
        cmd.extend(unknown)

    print(f"Launching {script_path.parent.name}...")
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
