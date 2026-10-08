#!/usr/bin/env python3
"""
Experiment 03 — Real-Time Point Cloud Playback
Provides interactive and CLI playback of streaming LiDAR frames with telemetry overlays.
Controls:
    SPACE: Pause / Play
    N: Next frame
    B: Previous frame
    +: Speed up
    -: Slow down
    R: Reset
    ESC/Q: Exit
"""

import argparse
import sys
from pathlib import Path

# Add src to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.visualization.playback import PointCloudPlaybackViewer
from autonav_baseline.visualization.terminal import print_banner


def main():
    parser = argparse.ArgumentParser(description="EXP-03: Real-Time Point Cloud Playback")
    parser.add_argument("--dataset", type=str, default="synthetic", help="Dataset name")
    parser.add_argument("--path", type=str, default=None, help="Custom dataset path")
    parser.add_argument("--frames", "--max-frames", dest="frames", type=int, default=100, help="Max frames to load into playback buffer")
    parser.add_argument("--cli", action="store_true", help="Run in terminal CLI mode instead of GUI window")
    parser.add_argument("--fps", type=float, default=10.0, help="Target playback frame rate")
    args = parser.parse_args()

    print_banner("EXPERIMENT 03 - REAL-TIME POINT CLOUD PLAYBACK", f"Dataset: {args.dataset}")

    root_path = Path(args.path) if args.path else None
    adapter = get_adapter(args.dataset, root_path=root_path)

    print(f"Loading up to {args.frames} frames into playback buffer...")
    try:
        frames = list(adapter.get_lidar_frames(max_frames=args.frames))
    except FileNotFoundError as e:
        print(f"\n[ERROR]: {e}")
        sys.exit(1)

    if not frames:
        print("No frames available.")
        sys.exit(1)

    print(f"Buffered {len(frames)} frames. Starting playback viewer...")
    viewer = PointCloudPlaybackViewer(frames, fps=args.fps, cli_only=args.cli)

    if args.cli:
        viewer.run_cli()
    else:
        try:
            viewer.run_interactive()
        except Exception as e:
            print(f"GUI display unavailable ({e}). Falling back to CLI mode...")
            viewer.run_cli()


if __name__ == "__main__":
    main()
