# Baseline Tests for Autonomous Navigation

[![Unit Tests](https://img.shields.io/badge/Unit%20Tests-Passing%20(12%2F12)-brightgreen)](#reproducibility)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue)](#installation)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

An empirical research laboratory, experiment framework, and zero-knowledge educational tutorial for evaluating sensor data rates, point cloud density, memory footprints, processing latency, and computational bottlenecks for a long-term autonomous UAV navigation feasibility study.

Repository: [https://github.com/JeyaVardhan-L/Baseline_tests_for_AutoNav.git](https://github.com/JeyaVardhan-L/Baseline_tests_for_AutoNav.git)

---

## What this project is

This repository is an offline research and evaluation laboratory for an autonomous UAV navigation feasibility study. We do not have the target LiDAR, onboard companion computer, or physical UAV airframe yet.

Our mission is to use publicly available sensor datasets and synthetic demonstration streams to:
1. **Characterize sensor data requirements**: Data rates, point densities, memory footprints, and storage bounds.
2. **Measure real-time processing costs**: Filtering latencies, downsampling overhead, algorithm execution time, and CPU/RAM usage.
3. **Evaluate baseline navigation algorithms**: Starting with a minimal, understandable LiDAR scan-to-scan odometry baseline.
4. **Gather empirical evidence**: Inform future hardware selection (communication buses, single-core CPU speeds, onboard RAM ceilings) based on measured facts rather than guesswork.

Repository: [https://github.com/JeyaVardhan-L/Baseline_tests_for_AutoNav.git](https://github.com/JeyaVardhan-L/Baseline_tests_for_AutoNav.git)

---

## Authoritative "Start Here" Guide for Beginners

If you are new to the repository, read this section first. It provides immediate answers to key architectural and workflow questions:

### 1. What problem is this repository solving?
Before purchasing an expensive UAV airframe, companion computer (e.g. Raspberry Pi 5, Jetson Orin), or 3D LiDAR, we must know if our computational algorithms can process incoming sensor scans within the sensor arrival period ($T_s = 1 / f_s$, e.g., 100 ms for 10 Hz LiDAR). This repository profiles those algorithms on recorded and synthetic data to establish empirical feasibility.

### 2. What is the complete data-to-results workflow?
Every valid experiment in this project follows an 8-step discipline:
```
1. Select Dataset  --> 2. Inspect Files  --> 3. Load Scans  --> 4. Run Navigation Method
                                                                          |
8. Hardware Sizing <-- 7. Compare Methods <-- 6. Generate Reports <-- 5. Profile Costs
```
1. **Select Dataset**: Pick an authentic public recording or in-memory synthetic stream.
2. **Inspect Files**: Measure file sizes, formats, sensor modalities, and verify file health.
3. **Load Scans**: Read actual 3D points and true timestamps through a normalized adapter interface.
4. **Run Navigation Method**: Execute an algorithm (e.g. scan-to-scan ICP odometry) on consecutive frames.
5. **Profile Costs**: Measure wall-clock latency per scan, process CPU %, and RAM consumption (RSS).
6. **Generate Reports**: Save machine-readable JSON/CSV, summary Markdown, and question-driven graphs.
7. **Compare Methods**: Repeat with different filtering, voxel sizes, or algorithms.
8. **Hardware Sizing**: Derive bus bandwidth, CPU IPC, and memory requirements from empirical measurements.

### 3. Which experiment should a beginner run first?
Beginners should run **two verified steps** in order:
1. **Step 1 — Dataset Inspection**:
   ```powershell
   python experiments/01-data-inspection/run.py --dataset synthetic
   ```
   *Inspects data format, total byte footprint, discovered streams, and frame counts.*
2. **Step 2 — Minimal LiDAR ICP Odometry**:
   ```powershell
   python experiments/02-lidar-odometry-icp/run.py --dataset synthetic --max-frames 20
   ```
   *Estimates vehicle motion between consecutive point clouds, computes drift, measures per-scan latency, and plots the estimated 3D trajectory.*

### 4. Which dataset is used first, and why?
- **Primary Public Dataset**: **Oxford Newer College Dataset**. It was recorded on a handheld rig moving through historic college quads with aggressive 6-DoF angular rates (pitch, roll, yaw) closely mimicking UAV flight turbulence. It provides 64-beam 3D LiDAR (Ouster OS-1-64), built-in IMU, and millimeter ground-truth laser maps.
- **Immediate Offline Testing**: **Synthetic Demonstration Stream**. Provides in-memory geometric corridors and obstacles without downloading gigabytes of external data, enabling immediate smoke testing.

### 5. Which navigation method is being evaluated first?
**LiDAR-Only Iterative Closest Point (ICP) Scan-to-Scan Odometry**.
It iteratively matches points between consecutive scans, computes the optimal rigid transformation ($R, t$) via Singular Value Decomposition (SVD), and accumulates relative transformations into an estimated vehicle trajectory. It serves as our understandable baseline before evaluating complex SLAM or sensor-fusion pipelines.

### 6. Where do the outputs and graphs appear?
All experiment runs write their artifacts to:
`results/<dataset>/<experiment_name>/`
- `summary.json`: Complete statistical dictionary with metric classifications and provenance.
- `metrics.csv`: Per-frame tabular measurements (latency, point count, translation step).
- `metadata.json`: Host machine OS, CPU, RAM, Python version, and execution timestamp.
- `summary.md`: Human-readable Markdown report with findings and observations.
- `figures/`: High-resolution PNG graphs answering specific engineering questions.

### 7. What do the principal evaluation metrics mean?
Every reported metric is categorized with an explicit scientific evidence tag:
- **Points per Frame** `[MEASURED]`: Total valid 3D $(x,y,z)$ coordinates in a scan.
- **Observed Frame Rate** `[MEASURED]`: $1 / \Delta t$ derived from actual recorded timestamps (if timestamps are missing, marked `[UNAVAILABLE]`).
- **Nominal Sensor Rate** `[ASSUMED]`: Manufacturer datasheet rate (e.g. 10.0 Hz).
- **Processing Latency** `[MEASURED]`: High-resolution wall-clock execution time for registering a scan.
- **Real-Time Margin** `[DERIVED]`: $T_{\text{deadline}} - \text{Latency}_{\text{P95}}$. Positive means host keeps up; negative means pipeline falls behind.
- **Process Memory (RSS)** `[MEASURED]`: Resident set size memory consumed by the Python process.
- **Process CPU %** `[MEASURED]`: Utilization percentage of host CPU during registration.

---

## Implementation Status Matrix

To prevent confusion, the components of this repository are classified explicitly:

| Component | File Path | Status | Role & Verification Level |
|---|---|---|---|
| **Base Dataset Adapter** | `src/autonav_baseline/datasets/base.py` | **IMPLEMENTED** | Normalized `LiDARFrame`, `DepthFrame`, `IMUFrame`, and inspection interfaces. |
| **Synthetic Stream** | `src/autonav_baseline/datasets/synthetic.py` | **IMPLEMENTED** | In-memory 3D corridor, ground plane, depth maps, and IMU. Fully verified in unit tests. |
| **Newer College Adapter** | `src/autonav_baseline/datasets/newer_college.py` | **IMPLEMENTED** | Validated inspection, `.npy`, `.bin`, `.pcd`, `.ply` parsing, honest timestamp reading. |
| **KITTI Adapter** | `src/autonav_baseline/datasets/kitti.py` | **PARTIAL** | Automotive baseline only; binary file reader. Not representative of UAV dynamics. |
| **Hilti SLAM Adapter** | `src/autonav_baseline/datasets/hilti.py` | **PARTIAL** | Directory inspection; full multi-modal streaming requires local dataset download. |
| **TUM RGB-D Adapter** | `src/autonav_baseline/datasets/tum_rgbd.py` | **PARTIAL** | Depth/RGB image reader for handheld indoor sequences. |
| **Oxford Spires Adapter** | `src/autonav_baseline/datasets/oxford_spires.py` | **PLACEHOLDER** | Advanced multi-session dataset reserved for later research phases. |
| **OpenLORIS Adapter** | `src/autonav_baseline/datasets/openloris.py` | **PLACEHOLDER** | Ground-robot multi-modal stream placeholder. |
| **LiDAR Preprocessing** | `src/autonav_baseline/lidar/filtering.py` | **IMPLEMENTED** | Invalid removal, range bounding, voxel downsampling, statistical outlier filtering. |
| **ICP Odometry (Core Baseline)** | `src/autonav_baseline/lidar/odometry.py` | **IMPLEMENTED** | Scan-to-scan 3D ICP odometry, SVD motion estimation, trajectory accumulation. |
| **Metrics & Profiler** | `src/autonav_baseline/timing/`, `metrics/` | **IMPLEMENTED** | Latency distributions (mean, median, P95), CPU/RAM monitoring, evidence classification. |
| **Reporting Exporter** | `src/autonav_baseline/reporting/exporter.py` | **IMPLEMENTED** | Standardized JSON, CSV, Markdown, and metadata export with sanitized paths. |
| **2D LiDAR Simulation** | `experiments/11-2d-lidar-slam-simulation/` | **SIMULATION ONLY** | Simplified 2D planar educational simulation. Not for 3D UAV evaluation. |
| **Pi 5 SLAM Benchmark** | `experiments/lidar-pi-slam-benchmark/` | **HARDWARE SPECIFIC** | Dedicated 2D benchmark scripts for Raspberry Pi 5. Non-core for desktop evaluation. |
| **Browser Live Viewer** | `experiments/lidar-pi-slam-benchmark/` | **EXPERIMENTAL** | Browser-based visualization helper. Non-core for beginner pipeline. |

---

## 7-Stage Research Roadmap

This roadmap defines the planned sequence of research activities. Stages marked **[IMPLEMENTED]** can be executed right now; future stages are explicitly marked **[PLANNED]**:

- **Stage 1: Validate Dataset Loading & Inspection** `[IMPLEMENTED]`  
  Inspect directory structure, file formats, frame counts, data rates, and verify that actual timestamps and point cloud coordinates load honestly without fake placeholders.
- **Stage 2: Establish LiDAR-Only Odometry Baseline** `[IMPLEMENTED]`  
  Implement and profile minimal 3D scan-to-scan ICP odometry. Measure per-scan registration time, CPU/RAM usage, and accumulate estimated trajectory.
- **Stage 3: Validate Baseline Against Ground Truth** `[PLANNED]`  
  Compute Absolute Trajectory Error (ATE) and Relative Pose Error (RPE) against millimeter Leica ground truth once recorded dataset poses are aligned.
- **Stage 4: Evaluate Preprocessing & Downsampling Trade-Offs** `[PLANNED]`  
  Measure how voxel grid size ($0.05\text{ m}$ vs $0.20\text{ m}$) impacts registration latency versus trajectory drift.
- **Stage 5: Evaluate Second Navigation Method (LiDAR-Inertial Fusion)** `[PLANNED]`  
  Integrate high-rate IMU angular rates with scan registration to handle fast rotational maneuvers.
- **Stage 6: Cross-Dataset Generalization** `[PLANNED]`  
  Benchmark identical algorithms across Hilti 2023, TUM RGB-D, and OpenLORIS to assess environmental robustness.
- **Stage 7: Empirical Hardware Sizing & Selection** `[PLANNED]`  
  Translate measured data rates and tail latencies (P95/P99) into formal specifications for communication buses, companion computer CPU cores, and onboard RAM.

---

## Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.14 on Windows, macOS, or Linux.
- Git.

### Setup
```bash
# Clone the repository
git clone https://github.com/JeyaVardhan-L/Baseline_tests_for_AutoNav.git
cd Baseline_tests_for_AutoNav

# Install requirements
pip install -r requirements/requirements.txt

# Verify your environment
python tools/check_environment.py
```

---

## First 10-minute experiment

You can run your first experiment in **under 10 seconds** without downloading gigabytes of external data using the built-in synthetic demonstration stream:

```bash
# Run Experiment 01: Inspect the synthetic sensor stream
python experiments/01-data-inspection/run.py --dataset synthetic

# Run Experiment 02: Characterize 100k-point LiDAR scans
python experiments/02-lidar-characterization/run.py --dataset synthetic --max-frames 30

# Run Experiment 05: Benchmark processing pipeline latency & real-time status
python experiments/05-downsampling/run.py --dataset synthetic --max-frames 20
```

---

## Dataset download instructions

To run experiments against authentic published datasets:

1. Consult [`docs/01-datasets/`](docs/01-datasets/) for official institutional download links.
2. Download a recommended small sequence (e.g. `01_short_experiment` for Newer College or `rgbd_dataset_freiburg1_xyz` for TUM RGB-D).
3. Place extracted files in the matching subdirectory inside `datasets/`:
   ```
   datasets/
       newer-college/01_short_experiment/
       tum-rgbd/rgbd_dataset_freiburg1_xyz/
   ```
4. Verify files using:
   ```bash
   python tools/inspect_dataset.py --path datasets/tum-rgbd/rgbd_dataset_freiburg1_xyz
   ```

*(Note: Raw dataset files are protected by `.gitignore` and are never committed to Git).*

---

## Running an experiment

Every experiment follows an identical execution pattern:

```bash
# Experiment 01: Dataset Inspection
python experiments/01-data-inspection/run.py --dataset synthetic

# Experiment 02: LiDAR Data Rate Characterization
python experiments/02-lidar-characterization/run.py --dataset synthetic --max-frames 50

# Experiment 03: Real-Time Point Cloud Playback (CLI or GUI)
python experiments/03-pointcloud-playback/run.py --dataset synthetic --cli

# Experiment 04: Point Cloud Filtering (Range Bounding & Voxel Grid)
python experiments/04-pointcloud-filtering/run.py --dataset synthetic --voxel-size 0.20

# Experiment 05: Pipeline Computational Load & Tail Latency (P95/P99)
python experiments/05-downsampling/run.py --dataset synthetic --max-frames 30

# Experiment 06: Depth Image Characterization & 3D Back-Projection
python experiments/06-depth-characterization/run.py --dataset synthetic --max-frames 30

# Experiment 07: High-Rate IMU Characterization & Timing Jitter
python experiments/07-imu-characterization/run.py --dataset synthetic --max-samples 500

# Experiment 08: Multi-Sensor Timestamp Synchronization
python experiments/08-timestamp-analysis/run.py --dataset synthetic

# Experiment 09: End-to-End Real-Time Pipeline Benchmark & Margin
python experiments/09-realtime-processing/run.py --dataset synthetic --max-frames 30

# Experiment 10: Sensor Fusion Architecture & Guidance Contracts
python experiments/10-sensor-fusion-preparation/run.py
```

---

## Understanding the output

Every value printed in terminal summaries carries an explicit evidence tag:

```
============================================================
AUTO NAV BASELINE
EXPERIMENT 02 - LIDAR CHARACTERIZATION
[Dataset: synthetic]
============================================================

SENSOR MEASUREMENTS
------------------------------------------------------------
Frames Processed          : 30 frames          [MEASURED]
Stream Duration           : 2.900 seconds      [MEASURED]
Observed Frame Rate       : 10.000 Hz          [MEASURED]   (1 / mean interval)
Average Points / Frame    : 100,000 pts        [MEASURED]
Average Frame Size        : 1.526 MB           [MEASURED]   (Binary MiB)

DATA RATE METRICS
------------------------------------------------------------
Point Generation Rate     : 1,000,000 pts/s    [DERIVED]    (points/frame * Hz)
Data Rate (Binary)        : 15.259 MiB/s       [DERIVED]
Data Rate (Decimal)       : 16.000 MB/s        [DERIVED]    (frame_size * Hz)
Projected Storage Rate    : 54.932 GiB/hour    [DERIVED]

REAL-TIME PROCESSING
------------------------------------------------------------
Mean Processing Latency   : 6.82 ms            [MEASURED]
P95 Processing Latency    : 8.10 ms            [MEASURED]
Real-Time Margin          : +91.90 ms          [DERIVED]    (100ms budget - P95)
Real-Time Status          : PASS               [DERIVED]
============================================================
```

- `[MEASURED]`: Measured directly from hardware or dataset files.
- `[DERIVED]`: Computed mathematically from measured values using documented equations.
- `[ASSUMED]`: Stated as nominal manufacturer spec without local empirical verification.
- `[ESTIMATED]`: Educated engineering projection.

---

## Understanding graphs

Every generated graph answers a specific engineering question:

| Figure | Question Answered |
|---|---|
| `point_count_vs_frame.png` | *"Does the sensor produce a stable amount of data per frame?"* |
| `range_histogram.png` | *"What distances are being observed in the environment?"* |
| `stage_latency_breakdown.png` | *"Which pipeline stage consumes the highest percentage of compute time?"* |
| `pipeline_latency_vs_frame.png` | *"Does processing remain stable and meet the sensor deadline across all frames?"* |
| `imu_interval_histogram.png` | *"Is the IMU arriving at a stable rate without timing jitter?"* |
| `cross_sensor_offset_vs_time.png`| *"How close in time is each LiDAR scan to the nearest IMU sample?"* |
| `available_margin_vs_frame.png` | *"Does the computer finish processing before the next scan arrives?"* |

---

## Result structure

Every experiment run automatically saves its outputs into `results/<dataset>/<experiment>/`:

```
results/
    synthetic/
        02_lidar_characterization/
            metrics.csv       # Frame-by-frame tabular metrics
            summary.json      # Structured statistical dictionary
            metadata.json     # OS, CPU, RAM, Python version, Git commit
            summary.md        # Human-readable summary report
            figures/          # Question-driven plots (PNG)
```

---

## Reproducibility

Unit tests verify numerical consistency across all metrics, geometries, and dataset adapters:

```bash
# Run unit test suite
python -m unittest discover -s tests
```

Expected result:
```
Ran 12 tests in 0.114s
OK
```

All system environment details (OS, Python version, CPU cores, RAM, GPU if detectable) are automatically captured in `metadata.json` for every run.

---

## Troubleshooting

See [`docs/08-troubleshooting/`](docs/08-troubleshooting/) for specific guides:
- [Windows UTF-8 Console Encoding](docs/08-troubleshooting/windows.md)
- [Python Dependencies](docs/08-troubleshooting/python.md)
- [Open3D & Headless Display Modes](docs/08-troubleshooting/open3d.md)
- [Missing Datasets](docs/08-troubleshooting/dataset.md)
- [ROS 2 & Bag File Compatibility](docs/08-troubleshooting/ros2.md)

---

## Hardware-selection methodology

Future flight hardware will **not** be chosen by intuition. Specifications will be derived systematically from the evidence collected in this laboratory:

1. **Sensor Data Rates** $\rightarrow$ Communication bus bandwidth (Gigabit Ethernet vs USB 3.0 vs CAN).
2. **Filtering Latency** $\rightarrow$ Required CPU single-core IPC and clock speed.
3. **Working Set Memory** $\rightarrow$ Minimum onboard RAM capacity without swapping.
4. **End-to-End Latency** $\rightarrow$ Maximum safe cruising speed of the UAV.
5. **Payload Mass & Power** $\rightarrow$ Airframe MTOW and LiPo battery drain limits.

See [`docs/06-hardware/hardware-requirements-methodology.md`](docs/06-hardware/hardware-requirements-methodology.md) for the full derivation methodology.

---

## Future phases

```
╔══════════════════════════════════════════════════════════════╗
║  PHASE 1: SENSOR & COMPUTATIONAL FEASIBILITY (Current)       ║
║  Ingest datasets, profile data rates, measure latencies.     ║
╠══════════════════════════════════════════════════════════════╣
║  PHASE 2: NAVIGATION ALGORITHM BENCHMARKING (Future)         ║
║  Evaluate LiDAR-Inertial Odometry, local mapping, and path   ║
║  planning algorithms against ground-truth trajectories.      ║
╠══════════════════════════════════════════════════════════════╣
║  PHASE 3: SOFTWARE-IN-THE-LOOP (SITL) SIMULATION (Future)    ║
║  Integrate Gazebo physics with PX4 autopilot firmware.       ║
╠══════════════════════════════════════════════════════════════╣
║  PHASE 4: ONBOARD HARDWARE INTEGRATION & FLIGHT (Future)     ║
║  Procure candidate computer, integrate sensors, flight test. ║
╚══════════════════════════════════════════════════════════════╝
```
