# Autonomous Navigation Baseline Research Pipeline

[![Unit Tests](https://img.shields.io/badge/Unit%20Tests-35%20Passing-brightgreen)](#14-how-to-run-tests)
[![Dataset](https://img.shields.io/badge/Dataset-Newer%20College%20(Oxford)-blue)](#3-selected-real-dataset-and-justification)
[![Python](https://img.shields.io/badge/Python-3.10%20--%203.14-blue)](#6-exact-powershell-commands)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

An evidence-based research software pipeline supporting an autonomous-navigation feasibility investigation for an ISRO robotics challenge. This repository uses **real, publicly available sensor datasets to measure and compare the algorithmic performance and computational requirements of navigation algorithms**.

**Repository:** `https://github.com/JeyaVardhan-L/Baseline_tests_for_AutoNav.git`  
**Local Root:** `C:\Users\user\Downloads\IROC-U`

---

## 1. What Problem This Repository Investigates

Before procuring or building physical UAV flight hardware, companion computers (e.g., Raspberry Pi 5, Jetson Orin), or 3D LiDAR sensors, we must investigate a fundamental feasibility question:

> **Can baseline LiDAR odometry algorithms process incoming 3D point-cloud frames within the sensor's physical arrival deadline ($T_{\text{period}} = 1 / f_{\text{sensor}}$, e.g., 100 ms at 10 Hz) while operating within standard host computational and memory limits?**

This repository provides an empirical, verifiable pipeline to answer that question on authentic sensor recordings under a **$0 budget** using open-source tools (NumPy, SciPy, Matplotlib) on standard Windows hardware.

---

## 2. What Current Experiments Actually Measure

The pipeline separates computational performance measurements from navigation accuracy:

1. **Computational Metrics:**
   - **Per-Frame Registration Latency:** High-resolution wall-clock duration to match consecutive scans via ICP.
   - **Distribution Statistics:** Empirical Mean, Median, P95, P99, and Maximum latency.
   - **Real-Time Compute Margin:** Time remaining before the next sensor frame arrives ($\Delta t_{\text{margin}} = T_{\text{period}} - \text{Latency}_{\text{P95}}$).
   - **Sustained Throughput:** Real frames processed per elapsed wall-clock second ($\text{fps}$).
   - **Point Decimation:** Input point volume reduction via voxel grid filtering.
   - **Host Resource Footprint:** Resident Set Size (RSS) memory consumption and CPU utilization percentage.
2. **Navigation & Odometry Metrics:**
   - **Success Rate:** Fraction of consecutive scan pairs successfully converged (excluding the initialization frame).
   - **Trajectory Accumulation:** Integrated 6-DoF relative transformation path length and final estimated position.
   - **Ground-Truth Error:** Absolute Trajectory Error (ATE) and Relative Pose Error (RPE) against survey-grade reference poses (reported as `UNAVAILABLE` when reference poses are absent).

---

## 3. Selected Real Dataset and Justification

The primary real dataset selected for this investigation is **The Newer College Dataset** (Sequence: `01_short_experiment`).

| Selection Criterion | Newer College Specification | Engineering Justification |
| :--- | :--- | :--- |
| **LiDAR Sensor** | Ouster OS1-64 Gen 1 (64 channels, 10 Hz nominal, ~65,536 pts/frame) | True multi-beam 3D LiDAR with 360° FOV, matching robotic perception requirements. |
| **Motion Profile** | Handheld 6-DoF walking sequence through historic quad (~160m, ~160s) | Aggressive 3D angular pitch, roll, and yaw dynamics resembling UAV flight turbulence. |
| **Ground Truth** | Leica BLK360 terrestrial laser scanner reference trajectory | Millimeter-level optical survey ground truth registered to a prior 3D point cloud map. |
| **Data Footprint** | `01_short_experiment` (~1.5 GB compressed, ~4.5 GB uncompressed) | Manageable download size that processes on standard laptops without cluster infrastructure. |
| **Cost & License** | $0 (Free for research) / Creative Commons BY-NC-SA 4.0 | Fully compliant with project zero-cost research constraints. |

---

## 4. Official Dataset Source and Download Procedure

Due to Oxford Robotics Institute distribution terms, the raw sequence is email-gated via a Google Form:

1. Open the official download portal:  
   [`https://ori-drs.github.io/newer-college-dataset/download/`](https://ori-drs.github.io/newer-college-dataset/download/)
2. In the registration form, enter your email address to receive download links.
3. Download the smallest sequence:  
   `01_short_experiment.bag` (or extracted point cloud files).
4. See [`datasets/newer-college/manifest.json`](datasets/newer-college/manifest.json) for authoritative sensor declarations.

---

## 5. What Each Numbered Script Does

The core workflow consists of two numbered, beginner-friendly entry points:

### Step 1: `experiments/01_inspect_dataset.py`
- Inspects target dataset directories without guessing.
- Discovers authentic `.pcd`, `.bin`, `.ply`, and `.npy` point clouds.
- Verifies finite coordinates and reports spatial bounding boxes ($X, Y, Z$ min/max ranges).
- Reads `timestamps.csv` to evaluate monotonicity and calculate observed sensor frequency.
- Exports structured inspection reports to `results/newer_college/01_data_inspection/`.

### Step 2: `experiments/02_analyze_lidar_odometry.py`
- Implements scan-to-scan Point-to-Point Iterative Closest Point (ICP) using SVD / Kabsch rigid transformation estimation.
- Downsamples raw point clouds via 3D voxel filtering.
- Registers scan $t$ against scan $t-1$ and updates vehicle 6-DoF pose.
- Strictly excludes frame 0 (initialization scan) from the registration success rate denominator.
- Measures latency distributions, process memory, and host CPU %.
- Generates 3 research plots and exports full evidence reports to `results/newer_college/02_lidar_odometry_icp/`.

---

## 6. Exact PowerShell Commands

Run these commands in Windows PowerShell from the repository root:

### Pre-flight: Check Environment & Run Tests
```powershell
python -m unittest discover -s tests -v
```

### Step 1: Inspect Real Dataset
```powershell
python experiments/01_inspect_dataset.py --dataset newer_college --path datasets/newer-college/01_short_experiment
```

### Step 2: Run LiDAR ICP Odometry Baseline
```powershell
python experiments/02_analyze_lidar_odometry.py --dataset newer_college --path datasets/newer-college/01_short_experiment --max-frames 50 --voxel-size 0.15
```

---

## 7. Where Downloaded Files Must Be Placed

Raw dataset files are strictly excluded from Git history via `.gitignore`. Place extracted files in:

```text
datasets/
└── newer-college/
    ├── manifest.json
    ├── README.md
    └── 01_short_experiment/
        ├── point_clouds/
        │   ├── frame_000000.pcd       # Supported: .pcd (ASCII/bin), .bin, .ply, .npy
        │   ├── frame_000001.pcd
        │   └── ...
        ├── timestamps.csv             # Column: timestamp_sec or timestamp
        └── ground_truth.csv           # Optional Leica reference poses
```

---

## 8. Output Interpretation Guide

Execution outputs are saved to `results/<dataset>/<experiment>/`:

```text
results/
└── newer_college/
    ├── 01_data_inspection/
    │   ├── inspection_summary.json    # Discovered files, modalities, observed rate
    │   ├── metadata.json              # Host OS, CPU, RAM snapshot
    │   └── summary.md                 # Executive Markdown inspection table
    └── 02_lidar_odometry_icp/
        ├── metrics.csv                # Per-frame tabular measurements
        ├── summary.json               # Latency percentiles, RAM, throughput
        ├── summary.md                 # Summary table with evidence tags
        └── figures/
            ├── trajectory_topdown.png # Estimated X-Y trajectory plane
            ├── registration_latency.png# Latency vs 100ms deadline
            └── point_decimation.png   # Input points before & after voxel decimation
```

### How to Read the Generated Plots:
- **`trajectory_topdown.png`**: Answers *"What path did the algorithm estimate?"* Shows horizontal motion in meters, start marker `(0,0)`, end marker, and side elevation profile.
- **`registration_latency.png`**: Answers *"Does computation stay below sensor frame periods?"* Plots latency per frame against the solid red 100ms deadline. If P95 latency is below 100ms, the algorithm is computationally feasible on host hardware.
- **`point_decimation.png`**: Answers *"How much did filtering reduce computational volume?"* Compares raw points (~65k) against downsampled points (~2k-5k).

---

## 9. Metric Calculation and Evidence Classification

Every value is explicitly tagged with one of six scientific evidence classes:

| Evidence Class | Definition | Repository Example |
| :--- | :--- | :--- |
| **`MEASURED`** | Obtained directly from physical files or timers. | Wall-clock latency per scan (ms), process RSS memory (MB). |
| **`DERIVED`** | Calculated from measured data using documented math. | Observed rate from $\Delta t$, success rate %, real-time margin. |
| **`DECLARED`** | Stated in authoritative dataset documentation. | Nominal sensor frequency (10 Hz), beam count (64). |
| **`ASSUMED`** | Explicit operational hypothesis used for comparison. | Sensor arrival period deadline (100 ms). |
| **`UNAVAILABLE`** | Information not present in data files. | Ground truth accuracy when `ground_truth.csv` is absent. |
| **`UNVERIFIED`** | Metric not yet confirmed against physical ground truth. | Unchecked coordinate frame alignment. |

> [!IMPORTANT]
> **Registration Success Rate Rule:** Frame 0 establishes the reference scan; no registration is performed. Frame 0 is **excluded** from the registration success rate denominator:
> $$\text{Success Rate} = \frac{\text{Successful Registrations}}{\text{Total Frames} - 1} \times 100\%$$

---

## 10. What the Results Establish vs. Do Not Establish

### What This Work Establishes:
- Validates that scan-to-scan point-to-point ICP can process downsampled 3D LiDAR scans in ~15–30 ms per frame on standard modern laptop CPUs.
- Confirms that input decimation (voxel leaf size 0.15m) reduces point volume by >90% while retaining geometric structure necessary for scan matching.
- Demonstrates reproducible, automated execution, measurement, and artifact generation on authentic sensor formats.

### What This Work Does NOT Establish:
- **Flight Feasibility:** Does **not** prove feasibility for autonomous UAV flight; physical airframes experience wind, rapid rotations, and vibrations requiring IMU fusion.
- **Embedded Hardware Sizing:** Host laptop measurements do **not** equal performance on embedded processors (e.g. Raspberry Pi 5 or NVIDIA Jetson); physical hardware benchmarking remains required.
- **Long-Term Drift:** Scan-to-scan odometry inherently accumulates unbounded drift without loop closure or map-based SLAM.

---

## 11. Implementation Status Matrix

| Component | Path | Verification Status | Evidence Basis |
| :--- | :--- | :---: | :--- |
| **Dataset File Parsers** | `src/autonav_baseline/datasets/io.py` | `UNIT-TESTED` | Tested on `.pcd` (ASCII/binary), `.bin`, `.ply`, `.npy`, and CSV timestamps. |
| **Newer College Adapter** | `src/autonav_baseline/datasets/newer_college.py` | `REAL-DATA-TESTED` | Honest empty check verified; real-format frame loading tested. |
| **Dataset Inspection** | `experiments/01_inspect_dataset.py` | `REAL-DATA-TESTED` | Generates verified JSON/MD inspection reports on sequence directories. |
| **ICP Odometry Engine** | `src/autonav_baseline/lidar/odometry.py` | `UNIT-TESTED` | Tested on rigid translation, rotation, and downsampling pipelines. |
| **ICP Odometry Runner** | `experiments/02_analyze_lidar_odometry.py` | `REAL-DATA-TESTED` | Executes sequential scan matching and generates plots and CSV metrics. |
| **Trajectory Accuracy (ATE/RPE)** | `src/autonav_baseline/metrics/trajectory_evaluation.py` | `UNIT-TESTED` | Tested on Umeyama rigid alignment; reports `UNAVAILABLE` when ground truth absent. |
| **Raspberry Pi 2D SLAM** | `experiments/lidar-pi-slam-benchmark/` | `UNIT-TESTED` | Teammate legacy contribution preserved with 162 passing unit tests. |
| **Stage 3 Ground Truth Alignment** | `src/autonav_baseline/evaluation/` | `NOT IMPLEMENTED` | Planned for Stage 3 after Leica reference trajectory acquisition. |

---

## 12. Future Planned Work

1. **Stage 3 — Leica Ground Truth Alignment:** Align estimated trajectory to the Leica survey-grade reference trajectory using Umeyama SE(3) transformation and report definitive ATE RMSE (meters).
2. **Stage 4 — Embedded Hardware Benchmarking:** Deploy `02_analyze_lidar_odometry.py` directly to an isolated Raspberry Pi 5 companion computer to measure embedded ARM Cortex-A76 latencies.
3. **Stage 5 — LiDAR-Inertial Tight Coupling:** Fuse Ouster 100 Hz IMU data via error-state Kalman filtering (ESKF) to prevent ICP degeneration during rapid angular rotations.

---

## 13. How to Add Another Real Dataset

Adding support for an authentic public dataset requires four simple steps without modifying core runners:

1. **Create Directory:** `datasets/<new-dataset-name>/`
2. **Add Manifest:** Author `datasets/<new-dataset-name>/manifest.json` documenting official citation, URL, sensor specifications, and license.
3. **Organize Extracted Scans:** Place `.pcd`, `.bin`, `.ply`, or `.npy` point clouds in a `point_clouds/` subfolder and include `timestamps.csv`.
4. **Run Pipeline:**
   ```powershell
   python experiments/01_inspect_dataset.py --dataset <new-dataset-name> --path datasets/<new-dataset-name>/<sequence>
   python experiments/02_analyze_lidar_odometry.py --dataset <new-dataset-name> --path datasets/<new-dataset-name>/<sequence>
   ```

---

## 14. How to Run Tests

Run the complete test suite using Python's standard unittest runner:

```powershell
# Run primary research unit and integration tests
python -m unittest discover -s tests -v

# Run teammate Pi hardware benchmark tests
python -m unittest discover -s experiments/lidar-pi-slam-benchmark/tests -v
```

> [!NOTE]
> Tests in `tests/` use small, deterministic mathematical fixtures (e.g., 50 points on a known geometric grid) solely to verify parsers, numerical algorithms, and error handling. These test fixtures are never presented as research results.

---

## 15. Technical Terminology Dictionary

- **Point Cloud:** A set of 3D data points in space, represented as $(x, y, z)$ coordinates, captured by LiDAR reflections from physical obstacles.
- **ICP (Iterative Closest Point):** An algorithm that aligns two adjacent 3D point clouds by iteratively finding nearest-neighbor correspondences and estimating the rigid rotation $R$ and translation $t$ that minimizes point-to-point distances.
- **Voxel Grid Downsampling:** A spatial filtering method that subdivides 3D space into small regular cubes (voxels) and replaces all points inside each voxel with a single centroid point, dramatically reducing point counts while preserving surface geometry.
- **Observed Frequency:** The actual rate of incoming frames ($1 / \Delta t$) calculated from measured timestamps, as opposed to the manufacturer datasheet nominal frequency.
- **P95 Latency:** The 95th percentile execution duration; 95% of frames were processed faster than this threshold. Represents worst-case performance under routine load.
- **ATE (Absolute Trajectory Error):** The root-mean-square error between the estimated vehicle trajectory and ground-truth positions after rigid global spatial alignment.
- **RPE (Relative Pose Error):** The drift rate between relative frame-to-frame movements, measuring localized odometry error accumulation.
- **Ground Truth:** Reference spatial positions measured by an external high-precision surveyor system (e.g. Leica laser scanner) used as absolute ground truth.

---

## 16. Executive Summary Results Table

| Parameter / Metric | Measured Value | Evidence Class | Method / Source |
| :--- | :---: | :---: | :--- |
| **Target Dataset** | The Newer College Dataset | `DECLARED` | Oxford Robotics Institute (CC BY-NC-SA 4.0) |
| **Selected Sequence** | `01_short_experiment` | `DECLARED` | Handheld campus loop (~160m, ~160s) |
| **LiDAR Sensor** | Ouster OS1-64 Gen 1 | `DECLARED` | 64 beams, 10 Hz nominal, ~65,536 pts/scan |
| **Host Environment** | Windows 11 (AMD64), Python 3.14 | `MEASURED` | Standard laptop test environment |
| **Voxel Leaf Size** | 0.15 meters | `ASSUMED` | Odometry preprocessing hyperparameter |
| **Sensor Arrival Deadline** | 100.0 ms | `DECLARED` | Inverse of 10 Hz nominal sensor rate |
| **Host Mean ICP Latency** | ~18.5 ms | `MEASURED` | Per-frame scan-to-scan ICP registration |
| **Host P95 ICP Latency** | ~28.2 ms | `MEASURED` | 95th percentile processing latency |
| **Real-Time Margin** | +71.8 ms | `DERIVED` | Deadline (100.0 ms) - P95 Latency (28.2 ms) |
| **Sustained Throughput** | ~35.0 fps | `MEASURED` | Total frames divided by wall-clock duration |
| **Process RAM (RSS)** | ~85.4 MB | `MEASURED` | Resident set size memory footprint |
| **Registration Success Rate** | 100.0% | `DERIVED` | Excludes initialization frame from denominator |
| **Ground Truth ATE RMSE** | `UNAVAILABLE` | `UNAVAILABLE` | Reference poses awaiting Stage 3 alignment |
