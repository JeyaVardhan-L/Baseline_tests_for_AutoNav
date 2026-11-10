"""
Results and reporting artifact exporter.
Exports metrics.csv, summary.json, metadata.json, run.log, and summary.md.
Sanitizes machine-specific absolute paths.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from autonav_baseline.system.monitor import get_system_snapshot

_REPO_ROOT = Path(__file__).resolve().parents[3]


def sanitize_text(text: str) -> str:
    """Replaces machine-specific absolute paths (repo root, home directory) with placeholders."""
    out = text
    for raw, placeholder in ((str(_REPO_ROOT), "<repo>"), (str(Path.home()), "<home>")):
        for variant in (raw, raw.replace("\\", "/"), raw.replace("\\", "\\\\")):
            out = out.replace(variant, placeholder)
    return out


def sanitize_paths(obj: Any) -> Any:
    """Recursively applies sanitize_text to every string in a JSON-like structure."""
    if isinstance(obj, str):
        return sanitize_text(obj)
    if isinstance(obj, dict):
        return {sanitize_text(str(k)): sanitize_paths(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_paths(v) for v in obj]
    return obj


class ExperimentExporter:
    """Exports structured results for an experiment execution run."""

    def __init__(self, dataset_name: str, experiment_name: str, base_results_dir: Optional[Path] = None):
        sanitized_ds = dataset_name.lower().replace(" ", "_").replace("-", "_")
        sanitized_exp = experiment_name.lower().replace(" ", "_").replace("-", "_")
        self.output_dir = (base_results_dir or Path("results")) / sanitized_ds / sanitized_exp
        self.experiment_dir = self.output_dir
        self.figures_dir = self.output_dir / "figures"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(self, rows: List[Dict[str, Any]], filename: str = "metrics.csv") -> Path:
        """Saves tabular frame-by-frame measurements."""
        path = self.output_dir / filename
        if not rows:
            return path
        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        return path

    def export_json(self, data: Dict[str, Any], filename: str = "summary.json") -> Path:
        """Saves structured summary data."""
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sanitize_paths(data), f, indent=2, default=str)
        return path

    def export_metadata(self, config: Dict[str, Any], filename: str = "metadata.json") -> Path:
        """Saves machine and environment metadata with relative paths."""
        path = self.output_dir / filename
        sys_snap = get_system_snapshot()
        meta = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "system": sys_snap,
            "configuration": config,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sanitize_paths(meta), f, indent=2, default=str)
        return path

    def export_summary_md(self, title: str, content: str, filename: str = "summary.md") -> Path:
        """Saves human-readable markdown summary."""
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(sanitize_text(f"# {title}\n\n{content}\n"))
        return path

    def write_summary_md(
        self,
        title: str,
        metrics_dict: Dict[str, str],
        conclusions: Optional[List[str]] = None,
        filename: str = "summary.md",
    ) -> Path:
        """Formats and saves a standardized markdown summary table and conclusions."""
        lines = [f"# {title}", "", "## Measured & Derived Metrics", "", "| Metric | Value |", "|---|---|"]
        for k, v in metrics_dict.items():
            lines.append(f"| {k} | {v} |")
        if conclusions:
            lines.extend(["", "## Key Observations & Conclusions", ""])
            for c in conclusions:
                lines.append(f"- {c}")
        lines.append("")
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(sanitize_text("\n".join(lines)))
        return path
