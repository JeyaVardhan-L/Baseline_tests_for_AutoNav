# Experiments Suite: Autonomous Navigation Feasibility Study

This directory contains the 10 experimental benchmarks for evaluating sensor data rates, point cloud density, memory footprints, processing latency, and computational bottlenecks.

## Core Principle

Every experiment adheres to strict engineering rigor:
- **Zero Robotics Knowledge Accessible**: Designed as an educational engineering laboratory.
- **Strict Evidence Tagging**: Every value is labeled `[MEASURED]`, `[DERIVED]`, `[ASSUMED]`, or `[ESTIMATED]`.
- **No Fabricated Data**: Runs against authentic downloaded datasets or clearly marked synthetic baseline streams.
- **Question-Driven Visualizations**: Every plot answers a specific technical question.

---

## Experiment Index

| ID | Name | Directory | Primary Question Answered | Status |
|:---:|---|---|---|:---:|
| **01** | [Dataset Inspection](01-data-inspection/) | `01-data-inspection/` | What data streams, files, frame counts, and formats exist in the dataset? | **READY** |
| **02** | [LiDAR Characterization](02-lidar-characterization/) | `02-lidar-characterization/` | What is the raw data volume, point density, and range distribution per scan? | **READY** |
| **03** | [Point Cloud Playback](03-pointcloud-playback/) | `03-pointcloud-playback/` | How do scans visually evolve frame-by-frame and what is the playback FPS? | **READY** |
| **04** | [Point Cloud Filtering](04-pointcloud-filtering/) | `04-pointcloud-filtering/` | How much memory and point volume is saved by range and voxel filtering? | **READY** |
| **05** | [Downsampling & Computational Load](05-downsampling/) | `05-downsampling/` | What is the execution latency distribution (P95/P99) of each pipeline stage? | **READY** |
| **06** | [Depth Characterization](06-depth-characterization/) | `06-depth-characterization/` | How dense are depth maps and what is the compute cost of 3D back-projection? | **READY** |
| **07** | [IMU Characterization](07-imu-characterization/) | `07-imu-characterization/` | Is the IMU arriving at a stable rate without timing jitter or dropped samples? | **READY** |
| **08** | [Timestamp Synchronization](08-timestamp-analysis/) | `08-timestamp-analysis/` | What is the nearest-neighbor temporal offset across LiDAR, Camera, and IMU? | **READY** |
| **09** | [Real-Time Pipeline Benchmark](09-realtime-processing/) | `09-realtime-processing/` | Does the complete end-to-end pipeline leave positive margin before the next frame? | **READY** |
| **10** | [Sensor Fusion Preparation](10-sensor-fusion-preparation/) | `10-sensor-fusion-preparation/` | What is the architectural boundary between mission, navigation, and flight control? | **READY** |

---

## How to Run Any Experiment

Every experiment can be executed immediately with the offline synthetic demonstration stream, or pointed to a locally downloaded dataset:

```bash
# 1. Inspect dataset structure
python experiments/01-data-inspection/run.py --dataset synthetic

# 2. Characterize LiDAR data rate
python experiments/02-lidar-characterization/run.py --dataset synthetic --max-frames 50

# 3. Interactive or CLI point cloud playback
python experiments/03-pointcloud-playback/run.py --dataset synthetic --cli

# 4. Filter and downsample comparison
python experiments/04-pointcloud-filtering/run.py --dataset synthetic --voxel-size 0.20

# 5. Measure computational stage breakdown & real-time status
python experiments/05-downsampling/run.py --dataset synthetic --max-frames 30

# 6. Characterize depth images & pinhole 3D back-projection
python experiments/06-depth-characterization/run.py --dataset synthetic --max-frames 30

# 7. Analyze IMU timing jitter & noise
python experiments/07-imu-characterization/run.py --dataset synthetic --max-samples 500

# 8. Cross-sensor timestamp synchronization analysis
python experiments/08-timestamp-analysis/run.py --dataset synthetic

# 9. Real-time pipeline timing breakdown & compute margin
python experiments/09-realtime-processing/run.py --dataset synthetic --max-frames 30

# 10. Architectural boundary & data flow verification
python experiments/10-sensor-fusion-preparation/run.py
```

---

## Result Artifacts Structure

Every experiment run automatically saves structured, machine-readable artifacts into `results/<dataset>/<experiment>/`:

```
results/
    <dataset>/
        <experiment>/
            metrics.csv       # Tabular per-frame measurements
            summary.json      # Machine-readable statistical summary
            metadata.json     # OS, CPU, RAM, Python versions, Git commit
            summary.md        # Formatted markdown summary report
            figures/          # Question-driven plots (PNG)
```
