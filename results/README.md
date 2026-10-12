# Research Results Directory

This directory stores structured artifacts generated from real sensor experimental runs.

> [!IMPORTANT]
> **Strict Evidence Rules:**
> - Only results obtained from verified real-sensor datasets belong here.
> - Synthetic data generation and simulated scans are prohibited from serving as feasibility evidence.
> - Do not commit machine-specific raw sensor logs or heavy binary datasets to Git history.
> - Every numerical metric must carry its evidence classification (`MEASURED`, `DERIVED`, `DECLARED`, `ASSUMED`, `UNAVAILABLE`, `UNVERIFIED`).

---

## Output Organization

Outputs are structured by dataset and experiment:

```text
results/
    <dataset>/
        <experiment>/
            metrics.csv       # Measured frame-by-frame computational and navigation metrics
            summary.json      # Structured statistical distribution and metadata
            metadata.json     # Host machine, OS, CPU, RAM, and Git commit hash
            summary.md        # Human-readable summary report
            figures/          # Focused, question-driven plots (PNG)
```
