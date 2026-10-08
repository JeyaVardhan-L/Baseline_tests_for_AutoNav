#!/usr/bin/env python3
"""
Dataset inspection tool.
Analyzes local directories to identify formats, sensor streams, frame counts, and file health.

Usage:
    python tools/inspect_dataset.py --dataset synthetic
    python tools/inspect_dataset.py --dataset newer_college --path datasets/newer-college
    python tools/inspect_dataset.py --dataset tum_rgbd --path datasets/tum-rgbd/rgbd_dataset_freiburg1_xyz
"""

import argparse
import sys
from pathlib import Path

# Add src to python path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from autonav_baseline.datasets.registry import get_adapter, ADAPTERS


def main():
    parser = argparse.ArgumentParser(
        description="Inspect a local robotics dataset structure, streams, and health.",
        epilog="Supported datasets: " + ", ".join(sorted(set(ADAPTERS.keys()))),
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="synthetic",
        help="Canonical dataset name (e.g. synthetic, newer_college, hilti, tum_rgbd, openloris, kitti)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path to local dataset directory (optional for synthetic)",
    )
    args = parser.parse_args()

    root_path = Path(args.path) if args.path else None
    try:
        adapter = get_adapter(args.dataset, root_path=root_path)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    result = adapter.inspect()

    print("=" * 65)
    print("DATASET INSPECTION REPORT")
    print("=" * 65)
    print(f"Dataset Name          : {result.name}")
    print(f"Directory Path        : {result.root_path}")
    print(f"Sensor Modalities     : {', '.join([s.value for s in result.sensor_types])}")
    print(f"Total Files Found     : {result.total_files:,} files")
    print(f"Total Disk Footprint  : {result.total_bytes / (1024.0 * 1024.0):.2f} MB ({result.total_bytes:,} bytes)")
    print(f"File Formats          : {', '.join(result.file_formats) if result.file_formats else 'None found'}")
    print(f"Available Streams     : {', '.join(result.available_streams) if result.available_streams else 'None detected'}")
    print(f"Estimated Frames      : {result.frame_count:,} frames")
    print(f"Approximate Duration  : {result.approx_duration_s:.2f} seconds")

    freq_label = "MEASURED" if result.is_rate_measured else "ASSUMED NOMINAL"
    rate_val = result.observed_rate_hz if result.is_rate_measured else result.nominal_rate_hz
    print(f"Sensor Frame Rate     : {rate_val} Hz [{freq_label}]")

    print("-" * 65)
    print("STREAM HEALTH & INTEGRITY")
    print(f"Missing Frames Count  : {result.missing_frames_count}")
    print(f"Malformed Files Count : {result.malformed_files_count}")

    if result.metadata:
        print("\nMetadata & Hardware Specifications:")
        for k, v in result.metadata.items():
            print(f"  - {k}: {v}")

    print("=" * 65)


if __name__ == "__main__":
    main()
