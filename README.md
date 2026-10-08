# Baseline Tests for Autonomous Navigation

[![Unit Tests](https://img.shields.io/badge/Unit%20Tests-Passing%20(12%2F12)-brightgreen)](#reproducibility)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue)](#installation)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

An empirical research laboratory, experiment framework, and zero-knowledge educational tutorial for evaluating sensor data rates, point cloud density, memory footprints, processing latency, and computational bottlenecks for a long-term autonomous UAV navigation feasibility study.

Repository: [https://github.com/JeyaVardhan-L/Baseline_tests_for_AutoNav.git](https://github.com/JeyaVardhan-L/Baseline_tests_for_AutoNav.git)

---

## What this project is

This repository is simultaneously:
1. **An Engineering Laboratory**: A reproducible suite of empirical benchmarks measuring actual sensor data streams, buffer footprints, filtering latencies, and CPU bottlenecks.
2. **A Zero-Knowledge Tutorial**: A complete, step-by-step educational guide allowing anyone with zero prior robotics knowledge to understand how 3D point clouds, depth maps, and inertial sensors become autonomous navigation inputs.
3. **An Evidence Ledger**: A disciplined scientific record where every reported number is strictly categorized as `[MEASURED]`, `[DERIVED]`, `[ASSUMED]`, or `[ESTIMATED]`.

---

## Why this project exists

A common failure mode in student and amateur robotics projects is buying expensive hardware prematurely:
- Teams purchase an embedded computer before knowing whether their sensor data rate will saturate its USB bus.
- Teams buy a heavy LiDAR before knowing if its point processing latency will blow past real-time deadlines.
- Teams make architectural assumptions without empirical measurements.

Our engineering leadership has challenged us:
> *"Do not tell me you think you need a LiDAR or a Jetson. Show me you measured X, Y, and Z on authentic sensor streams — therefore you require a sensor and computer with these exact specifications."*

We cannot purchase hardware based on guesswork. This repository exists to produce the empirical evidence that justifies every hardware decision before spending money.

---

## The engineering question

The eventual engineering question this research will inform is:

> **"What sensor and onboard computing capability would an autonomous UAV need to navigate safely in GPS-denied environments?"**

**BUT WE DO NOT ANSWER THAT QUESTION YET.**  
We are currently in the evidence-gathering phase. We only collect empirical data, measure execution latencies, and isolate computational bottlenecks.

---

## Current scope

The scope of this repository is strictly limited to:
- Ingesting and characterizing authentic multi-modal robotics datasets (LiDAR, RGB-D, IMU).
- Profiling memory consumption and data rates (MB/s, GiB/hour).
- Measuring execution latencies for invalid point rejection, range bounding, and 3D voxel downsampling.
- Evaluating real-time compute margins against sensor arrival periods ($T_s = 1000 / f_s$).
- Benchmarking nearest-neighbor cross-sensor timestamp synchronization.
- Defining formal architectural data contracts between mission control, autonomous navigation, and low-level flight stabilization.

---

## What this project is NOT

To maintain absolute scientific discipline, this project is **NOT**:
- **NOT currently building the physical UAV airframe.**
- **NOT choosing or purchasing commercial flight hardware.**
- **NOT implementing PX4 or ArduPilot motor mixers or flight dynamics.**
- **NOT running live outdoor flight tests.**
- **NOT benchmarking or tuning complex SLAM algorithms.**
- **NOT training AI or machine learning models.**
- **NOT fabricating experimental results or assuming real-world performance without measurement.**

---

## Architecture

The system is organized into a clean, modular three-tier architecture:

```
+------------------------------------------------------------------------+
| TIER 1: HIGH-LEVEL MISSION CONTROL (Ground Station / Supervisor)       |
| Directives: "Survey designated 50m x 50m sector at 5m/s"               |
+------------------------------------------------------------------------+
                                  |
                                  v
+------------------------------------------------------------------------+
| TIER 2: AUTONOMOUS NAVIGATION (Companion Computer / GPU)               |
| - Sensor Ingestion (LiDAR 10Hz, Camera 30Hz, IMU 200Hz)                |
| - State Estimation (LiDAR-Inertial Odometry / EKF Pose)                |
| - Local Mapping (3D Volumetric Voxel Octree / Free Space Detection)   |
| - Trajectory Planning (3D Collision-Free Spline Generation)            |
| - Guidance Tracking (Position, Velocity, and Yaw Rate Setpoints)       |
+------------------------------------------------------------------------+
                                  | (MAVLink / microXRCE-DDS Setpoints)
                                  v
+------------------------------------------------------------------------+
| TIER 3: LOW-LEVEL FLIGHT CONTROL (Autopilot: PX4 / ArduPilot at 500Hz) |
| - Fast Inner Feedback Loops (Attitude & Rate Dampers)                  |
| - Motor ESC PWM / DShot Mixing                                         |
| - Failsafe Protection & Aerodynamic Stabilization                      |
+------------------------------------------------------------------------+
```

---

## Learning roadmap

For readers with zero prior background in robotics, follow this reading path:

1. [**Robotics Basics**](docs/00-start-here/robotics-basics.md): Coordinates, 6-DoF poses, and the 5 navigation questions.
2. [**Sensor Basics**](docs/00-start-here/sensor-basics.md): What are LiDARs, Depth Cameras, and IMUs?
3. [**Point Cloud Basics**](docs/00-start-here/point-cloud-basics.md): How 3D points are stored in computer memory.
4. [**Timestamps & Clocks**](docs/00-start-here/timestamps.md): Why microsecond timing determines flight safety.
5. [**Real-Time Processing**](docs/00-start-here/realtime-processing.md): Sensor deadlines, latency percentiles, and compute margins.
6. [**Tools Guide**](docs/02-tools/): Why we use Python, NumPy, Matplotlib, and Open3D.
7. [**Core Concepts**](docs/03-concepts/): Data rates, bandwidth, jitter, and coordinate transformations.

---

## Dataset roadmap

We replaced older automotive baselines with datasets recorded on **mobile robots and handheld 6-DoF platforms**:

| Dataset | Platform & Sensors | Role | Docs |
|---|---|---|---|
| **Oxford Newer College** | Ouster OS-1 64-beam LiDAR, IMU, RealSense D435i | **PRIMARY LiDAR Learning Dataset** | [`newer-college.md`](docs/01-datasets/newer-college.md) |
| **Hilti SLAM 2023** | Robosense Bpearl LiDAR (10Hz), XSens IMU (200Hz), OAK-D | **Mobile Robot Benchmark** | [`hilti-2023.md`](docs/01-datasets/hilti-2023.md) |
| **OpenLORIS-Scene** | RealSense RGB-D, IMU, Wheel Odometry, 2D Laser | **Indoor Robot Depth/Camera Benchmark** | [`openloris-scene.md`](docs/01-datasets/openloris-scene.md) |
| **TUM RGB-D** | Microsoft Kinect RGB-D, Optical MoCap 6-DoF | **Beginner-Friendly Depth Dataset** | [`tum-rgbd.md`](docs/01-datasets/tum-rgbd.md) |
| **Oxford Spires** | Multi-session LiDAR, Vision, mm RTK-GPS | **Advanced Reference (Later Phases)** | [`oxford-spires.md`](docs/01-datasets/oxford-spires.md) |
| **KITTI** | Velodyne HDL-64E, Automotive Cameras, GPS | **Automotive Reference Baseline (Optional)** | [`kitti.md`](docs/01-datasets/kitti.md) |

---

## Software roadmap

- **Phase 1 (Current)**: Pure Python / NumPy experiment framework, dataset adapters, synthetic streams, and metric profilers. (Zero external compilation required).
- **Phase 2**: Real-time C++ point cloud downsampling kernels, ROS 2 node wrappers, and SIMD/AVX acceleration.
- **Phase 3**: Software-In-The-Loop (SITL) simulation with Gazebo / PX4.
- **Phase 4**: Embedded hardware bench testing on physical companion computers.

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
