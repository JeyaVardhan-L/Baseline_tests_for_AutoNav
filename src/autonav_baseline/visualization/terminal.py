"""
Terminal output formatting for autonav_baseline experiments.
Clean, beginner-friendly format with clear section dividers and classification tags.
"""

from typing import Dict, Any, Optional


def print_banner(experiment_title: str, subtitle: Optional[str] = None) -> None:
    print("=" * 60)
    print("AUTO NAV BASELINE")
    print(experiment_title)
    if subtitle:
        print(f"[{subtitle}]")
    print("=" * 60)
    print()


def print_section(title: str) -> None:
    print("-" * 60)
    print(title)
    print("-" * 60)


def print_field(label: str, value: Any, unit: str = "", classification: str = "", note: str = "") -> None:
    val_str = f"{value} {unit}".strip()
    tag_str = f"[{classification}]" if classification else ""
    if note:
        print(f"{label:<26}: {val_str:<18} {tag_str:<12} ({note})")
    else:
        print(f"{label:<26}: {val_str:<18} {tag_str}")


def print_experiment_summary(
    dataset_name: str,
    sequence_name: str,
    frames_count: int,
    sensor_metrics: Dict[str, Any],
    processing_metrics: Dict[str, Any],
    system_metrics: Dict[str, Any],
    realtime_check: Dict[str, Any],
) -> None:
    """Prints the standardized beginner-friendly experiment summary."""
    print()
    print_section("DATASET & RUN INFO")
    print_field("Dataset", dataset_name)
    print_field("Sequence / Scope", sequence_name)
    print_field("Frames Processed", frames_count, "frames", "MEASURED")
    print()

    print_section("SENSOR MEASUREMENTS")
    for key, item in sensor_metrics.items():
        if isinstance(item, dict) and "value" in item:
            print_field(
                key.replace("_", " ").title(),
                item["value"],
                item.get("unit", ""),
                item.get("classification", ""),
                item.get("note", ""),
            )
        else:
            print_field(key.replace("_", " ").title(), item)
    print()

    print_section("HOST PROCESSING LATENCY")
    for key, item in processing_metrics.items():
        if isinstance(item, dict) and "value" in item:
            print_field(
                key.replace("_", " ").title(),
                item["value"],
                item.get("unit", ""),
                item.get("classification", ""),
            )
        else:
            print_field(key.replace("_", " ").title(), item)
    print()

    print_section("HOST SYSTEM UTILIZATION")
    for key, item in system_metrics.items():
        if isinstance(item, dict) and "value" in item:
            print_field(
                key.replace("_", " ").title(),
                item["value"],
                item.get("unit", ""),
                item.get("classification", ""),
            )
        else:
            print_field(key.replace("_", " ").title(), item)
    print()

    print_section("REAL-TIME REPLAY CHECK")
    status = realtime_check.get("status", "TBD")
    period = realtime_check.get("sensor_period_ms", {}).get("value", 0.0)
    lat = realtime_check.get("pipeline_latency_ms", {}).get("value", 0.0)
    margin = realtime_check.get("available_margin_ms", {}).get("value", 0.0)

    print_field("Target Sensor Period", period, "ms", "ASSUMED")
    print_field("Host Pipeline Time", lat, "ms", "MEASURED")
    print_field("Processing Margin", margin, "ms", "DERIVED")
    print()
    print(f"Status: {status}")
    if margin > 0:
        print("  -> PASS: Host processor completes computation faster than sensor produces frames.")
    else:
        print("  -> WARNING: Processing latency exceeds arrival rate (buffer backlog will accumulate).")
    print("=" * 60)
    print()
