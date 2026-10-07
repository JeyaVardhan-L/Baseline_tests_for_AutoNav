# Experiments

## Purpose

This directory contains all experiments performed as part of the IRoC-U autonomous navigation project. Each experiment follows a standardized structure to ensure reproducibility and clear documentation.

## Experiment Index

| ID | Name | Directory | Purpose | Status |
|----|------|-----------|---------|--------|
| EXP-01 | LiDAR Dataset Characterization | `01-lidar-characterization/` | Understand LiDAR data rates, sizes, and properties | NOT STARTED |
| EXP-02 | Camera Data Characterization | `02-camera-characterization/` | Understand camera data rates and properties | NOT STARTED |
| EXP-03 | LiDAR Odometry | `03-lidar-odometry/` | Test LiDAR-based pose estimation | NOT STARTED |
| EXP-04 | Visual Odometry | `04-visual-odometry/` | Test camera-based pose estimation | NOT STARTED |
| EXP-05 | LiDAR-Camera Fusion | `05-lidar-camera-fusion/` | Test multi-sensor fusion | NOT STARTED |
| EXP-06 | Local Mapping | `06-local-mapping/` | Test environment representation | NOT STARTED |
| EXP-07 | Localization | `07-localization/` | Test localization accuracy | NOT STARTED |
| EXP-08 | Path Planning | `08-path-planning/` | Test planning algorithms | NOT STARTED |
| EXP-09 | Compute Benchmark | `09-compute-benchmark/` | Profile full pipeline performance | NOT STARTED |
| EXP-10 | End-to-End Latency | `10-end-to-end-latency/` | Measure sensor-to-actuator latency | NOT STARTED |

## Experiment Standard

Every experiment must follow the template in [`TEMPLATE.md`](TEMPLATE.md).

### Required Deliverables

1. **README.md** — Objective, method, results, interpretation
2. **config/** — Configuration files (YAML)
3. **scripts/** — Reproducible Python scripts
4. **results/** — Machine-readable output (CSV, JSON)
5. **figures/** — Generated plots (PNG/SVG)

### Evidence Categories

Every value reported must be labeled:

- 📏 **Measured** — experimentally measured from actual data
- 📐 **Derived** — mathematically calculated from measured values
- ⚠️ **Assumed** — not yet validated
- 🔮 **Estimated** — educated estimate
- ⏳ **Pending** — not yet measured

## Failed Experiments

**Failed experiments are valuable evidence and must NOT be deleted.**

If an experiment fails, document:

1. What was expected
2. What was observed
3. What caused the failure
4. What impact this has on the design
5. What the next action is

Example:

```
## FAILED: EXP-XX — Name

Expected: 10 Hz processing rate
Observed: 3.2 Hz
Cause:    CPU bottleneck during point-cloud nearest-neighbor search
Impact:   Current hardware candidate insufficient for real-time operation
Action:   Test downsampling / GPU acceleration / alternative algorithm
```

## Reproducibility

Every experiment must be reproducible by running:

```bash
# Ensure dataset is available (see experiment README for download instructions)
python experiments/<experiment>/scripts/<main_script>.py
```

Results should be identical (or statistically equivalent) across runs.
