#!/usr/bin/env python3
"""
Step 1: Inspect Real Sensor Dataset
Identifies dataset sequence, file formats, frame counts, timestamp health,
and point cloud spatial characteristics without synthetic fabrication.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure src is on python path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np

from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.datasets.newer_college import NewerCollegeAdapter
from autonav_baseline.datasets.io import load_point_cloud_file, discover_timestamps
from autonav_baseline.visualization.terminal import print_banner, print_field, print_section
from autonav_baseline.reporting.exporter import ExperimentExporter


def inspect_dataset_workflow(
    dataset_name: str = "newer_college",
    root_path_str: Optional[str] = None,
    output_dir_str: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes the dataset inspection workflow and exports structured evidence."""
    default_root = REPO_ROOT / "datasets" / "newer-college" / "01_short_experiment"
    target_path = Path(root_path_str) if root_path_str else default_root

    print_banner("STEP 1: REAL DATASET INSPECTION", f"Dataset: {dataset_name} | Path: {target_path}")

    adapter = get_adapter(dataset_name, root_path=target_path)
    result = adapter.inspect()

    print_section("DATASET & SEQUENCE IDENTIFICATION")
    print_field("Dataset Name", result.name)
    print_field("Directory Path", str(result.root_path))
    print_field("Path Exists", str(target_path.exists()))

    is_populated = result.total_files > 0
    status_label = "POPULATED" if is_populated else "NOT DOWNLOADED / EMPTY"
    print_field("Dataset Status", status_label)

    print()
    print_section("FILE DISCOVERY & TIMING METRICS")
    print_field("Total Files", result.total_files, "files", "MEASURED")
    footprint_mb = round(result.total_bytes / (1024.0 * 1024.0), 2)
    print_field("Disk Footprint", footprint_mb, "MB", "MEASURED")
    print_field("Discovered Formats", ", ".join(result.file_formats) if result.file_formats else "None")
    print_field("Available Modalities", ", ".join([s.value for s in result.sensor_types]))
    print_field("Point Cloud Frames", result.frame_count, "frames", "MEASURED" if result.frame_count > 0 else "UNAVAILABLE")

    if result.is_rate_measured and result.observed_rate_hz is not None:
        print_field("Observed Frequency", f"{result.observed_rate_hz:.2f}", "Hz", "MEASURED")
    elif result.nominal_rate_hz is not None:
        print_field("Nominal Frequency", f"{result.nominal_rate_hz:.2f}", "Hz", "DECLARED NOMINAL")
    else:
        print_field("Sensor Frequency", "UNAVAILABLE", "", "UNAVAILABLE")

    duration_str = f"{result.approx_duration_s:.2f}" if result.approx_duration_s is not None else "UNAVAILABLE"
    duration_tag = "DERIVED" if result.approx_duration_s is not None else "UNAVAILABLE"
    print_field("Sequence Duration", duration_str, "seconds" if result.approx_duration_s else "", duration_tag)

    print()
    print_section("DATA INTEGRITY & SPATIAL CHECKS")
    missing_tag = "DERIVED" if result.missing_frames_count is not None else "UNAVAILABLE"
    print_field("Missing Frames", str(result.missing_frames_count) if result.missing_frames_count is not None else "UNAVAILABLE", "frames", missing_tag)
    malformed_tag = "MEASURED" if result.malformed_files_count is not None else "UNAVAILABLE"
    print_field("Malformed Files", str(result.malformed_files_count) if result.malformed_files_count is not None else "UNAVAILABLE", "files", malformed_tag)

    # Detailed inspection if frames are present
    spatial_stats: Dict[str, Any] = {}
    if is_populated and result.frame_count > 0 and isinstance(adapter, NewerCollegeAdapter):
        lidar_files = adapter._find_lidar_files()
        if lidar_files:
            sample_file = lidar_files[0]
            try:
                pts = load_point_cloud_file(sample_file)
                spatial_stats = {
                    "sample_frame_file": sample_file.name,
                    "sample_point_count": int(len(pts)),
                    "all_finite": bool(np.isfinite(pts).all()),
                    "x_min": float(np.min(pts[:, 0])),
                    "x_max": float(np.max(pts[:, 0])),
                    "y_min": float(np.min(pts[:, 1])),
                    "y_max": float(np.max(pts[:, 1])),
                    "z_min": float(np.min(pts[:, 2])),
                    "z_max": float(np.max(pts[:, 2])),
                }
                print_field("Sample Point Count", spatial_stats["sample_point_count"], "points", "MEASURED")
                print_field("Finite Coordinates", str(spatial_stats["all_finite"]), "", "MEASURED")
                print_field("X Range [min, max]", f"[{spatial_stats['x_min']:.2f}, {spatial_stats['x_max']:.2f}]", "m", "MEASURED")
                print_field("Y Range [min, max]", f"[{spatial_stats['y_min']:.2f}, {spatial_stats['y_max']:.2f}]", "m", "MEASURED")
                print_field("Z Range [min, max]", f"[{spatial_stats['z_min']:.2f}, {spatial_stats['z_max']:.2f}]", "m", "MEASURED")
            except Exception as e:
                spatial_stats["error"] = str(e)
                print_field("Sample Read Error", str(e), "", "MEASURED")

    # Export results
    base_results = Path(output_dir_str).parent.parent if output_dir_str else (REPO_ROOT / "results")
    exporter = ExperimentExporter(dataset_name, "01_data_inspection", base_results_dir=base_results)

    summary_payload = result.summary_dict()
    summary_payload["spatial_checks"] = spatial_stats
    summary_payload["populated_on_disk"] = is_populated

    exporter.export_json(summary_payload, "inspection_summary.json")
    exporter.export_metadata(
        {
            "dataset": dataset_name,
            "target_path": str(target_path),
            "populated": is_populated,
        },
        "metadata.json",
    )

    findings = [
        f"Dataset `{result.name}` target directory is `{target_path}`.",
        f"Files discovered: {result.total_files} ({footprint_mb} MB).",
        f"Point cloud frames available: {result.frame_count}.",
    ]
    if not is_populated:
        findings.append("Action required: Sequence files are not yet in directory. See datasets/newer-college/README.md for download steps.")
    else:
        findings.append("Point cloud files verified and available for odometry analysis.")

    exporter.write_summary_md(
        "Experiment 01 — Dataset Inspection",
        metrics_dict={
            "Dataset Status": status_label,
            "Total Files": f"{result.total_files} [MEASURED]",
            "Frames Found": f"{result.frame_count} [MEASURED]",
            "Observed Frequency": f"{result.observed_rate_hz:.2f} Hz [MEASURED]" if result.observed_rate_hz else "UNAVAILABLE",
            "Nominal Frequency": f"{result.nominal_rate_hz:.2f} Hz [DECLARED]" if result.nominal_rate_hz else "UNAVAILABLE",
        },
        conclusions=findings,
    )

    print()
    print(f"[+] Inspection artifacts saved to: {exporter.output_dir.resolve()}")
    return summary_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 1: Inspect Real Sensor Dataset")
    parser.add_argument(
        "--dataset",
        type=str,
        default="newer_college",
        help="Dataset adapter name (default: newer_college)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path to dataset directory (default: datasets/newer-college/01_short_experiment)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory for inspection results",
    )
    args = parser.parse_args()

    inspect_dataset_workflow(
        dataset_name=args.dataset,
        root_path_str=args.path,
        output_dir_str=args.output_dir,
    )


if __name__ == "__main__":
    main()
