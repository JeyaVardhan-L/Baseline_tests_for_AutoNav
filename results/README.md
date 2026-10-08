# Experimental Results Directory

This directory stores structured artifacts generated from reproducible experimental runs.

> [!WARNING]
> **DO NOT COMMIT REAL RAW SENSOR DATASETS TO GIT.**  
> Only machine-readable metrics, lightweight summary tables, JSON configurations, and vector/raster figures belong in this directory.

---

## Directory Organization

Results are partitioned by dataset name and experiment identifier:

```
results/
    <dataset>/
        <experiment>/
            metrics.csv       # Tabular frame-by-frame measurements
            summary.json      # Structured statistical distribution
            metadata.json     # OS, Python, CPU, RAM, Git commit snapshot
            summary.md        # Formatted markdown summary
            figures/          # Question-driven generated plots (PNG)
```

### Examples:
- `results/synthetic/02_lidar_characterization/`
- `results/newer_college/05_downsampling_computational_load/`
- `results/tum_rgbd/06_depth_characterization/`

---

## Rules for Results

1. **No Absolute Paths**: All paths in `metadata.json` and `summary.md` are sanitized relative paths.
2. **Deterministic Evidence Tagging**: Values must carry their evidence label: `[MEASURED]`, `[DERIVED]`, `[ASSUMED]`, `[ESTIMATED]`.
3. **Reproducibility**: Any team member running the identical command on identical data must obtain statistically equivalent results.
