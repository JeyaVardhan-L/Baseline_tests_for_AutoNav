#!/usr/bin/env python3
"""
Experiment 01 — Dataset Inspection
Identifies dataset type, file formats, total size, streams, frame counts, and file health.
"""

import argparse
import sys
from pathlib import Path

# Add src to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from autonav_baseline.datasets.registry import get_adapter
from autonav_baseline.visualization.terminal import print_banner, print_field, print_section
from autonav_baseline.reporting.exporter import ExperimentExporter


def main():
    parser = argparse.ArgumentParser(description="EXP-01: Dataset Inspection")
    parser.add_argument("--dataset", type=str, default="synthetic", help="Dataset name")
    parser.add_argument("--path", type=str, default=None, help="Custom dataset path")
    args = parser.parse_args()

    print_banner("EXPERIMENT 01 - DATASET INSPECTION", f"Dataset: {args.dataset}")

    root_path = Path(args.path) if args.path else None
    adapter = get_adapter(args.dataset, root_path=root_path)
    result = adapter.inspect()

    print_section("INSPECTION SUMMARY")
    print_field("Dataset Name", result.name)
    print_field("Root Directory", result.root_path)
    print_field("Modalities", ", ".join([s.value for s in result.sensor_types]))
    print_field("Total Files", result.total_files, "files", "MEASURED")
    print_field("Total Footprint", round(result.total_bytes / (1024.0 * 1024.0), 2), "MB", "MEASURED")
    print_field("Discovered Formats", ", ".join(result.file_formats) if result.file_formats else "None")
    print_field("Available Streams", ", ".join(result.available_streams) if result.available_streams else "None")
    print_field("Total Frame Count", result.frame_count, "frames", "MEASURED")
    print_field("Approx Duration", round(result.approx_duration_s, 2), "seconds", "DERIVED")

    freq_label = "MEASURED" if result.is_rate_measured else "ASSUMED NOMINAL"
    rate = result.observed_rate_hz if result.is_rate_measured else result.nominal_rate_hz
    print_field("Sensor Frequency", rate, "Hz", freq_label)

    print()
    print_section("INTEGRITY & HEALTH")
    print_field("Missing Frames", result.missing_frames_count, "count", "DERIVED")
    print_field("Malformed Files", result.malformed_files_count, "count", "MEASURED")

    # Export results
    exporter = ExperimentExporter(args.dataset, "01_data_inspection")
    exporter.export_json(result.summary_dict(), "inspection_summary.json")
    exporter.export_metadata({"dataset": args.dataset, "path": args.path}, "metadata.json")
    exporter.export_summary_md(
        "Experiment 01 — Dataset Inspection",
        f"Inspected dataset `{result.name}`. Discovered {result.total_files} files ({round(result.total_bytes / 1e6, 2)} MB). "
        f"Available streams: {', '.join(result.available_streams)}.",
    )
    print(f"\n[+] Results saved to: {exporter.output_dir}/")


if __name__ == "__main__":
    main()
