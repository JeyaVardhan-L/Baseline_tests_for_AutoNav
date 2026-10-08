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
            json.dump(data, f, indent=2, default=str)
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
            json.dump(meta, f, indent=2, default=str)
        return path

    def export_summary_md(self, title: str, content: str, filename: str = "summary.md") -> Path:
        """Saves human-readable markdown summary."""
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{content}\n")
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
            f.write("\n".join(lines))
        return path
