# Beginner Tutorial: Running Your First Validated Research Pipeline

Welcome! This step-by-step guide is designed for beginners working in **Windows PowerShell**. It walks you through running, verifying, and interpreting the project's first complete research pipeline without needing external hardware or large gigabyte downloads.

---

## 1. Overview & The Research Goal

Before choosing an embedded computer (e.g. Raspberry Pi 5, Jetson Orin) or purchasing a 3D LiDAR, we must answer:
> *"How many milliseconds does it take to process a 3D LiDAR scan, and can our algorithm keep up with the sensor's arrival rate?"*

In this tutorial, you will:
1. Verify your local Python environment.
2. Inspect sensor data streams, file formats, and health checks.
3. Run scan-to-scan Iterative Closest Point (ICP) LiDAR odometry.
4. Open and interpret the resulting graphs and scientific reports.

---

## 2. Working Directory

All commands below must be executed from the **repository root directory**:

```powershell
# Verify your current working directory
pwd
# Expected: ...\Baseline_tests_for_AutoNav (or ...\IROC-U)
```

---

## 3. Step 1: Verify the Python Environment

Run the automated environment check tool:

```powershell
python tools/check_environment.py
```

### What This Command Does:
- Verifies Python version (3.10+).
- Checks required scientific packages (`numpy`, `matplotlib`, `pyyaml`, `psutil`, `scipy`, `pandas`).
- Confirms memory and CPU detection.

### Expected Output:
```
=================================================================
SYSTEM STATUS: ALL CORE REQUIREMENTS SATISFIED.
You are ready to run the experiments.
=================================================================
```

---

## 4. Step 2: Inspect Sensor Data & File Health (Experiment 01)

Before running any navigation algorithm on a dataset, we must inspect its file structure, frame count, storage size, and timestamp integrity:

```powershell
python experiments/01_inspect_dataset.py --dataset newer_college --path datasets/newer-college/01_short_experiment
```

### What the Major Parameters Control:
- `--dataset newer_college`: Selects the Oxford Newer College real dataset adapter.
- `--path <dir>`: Path to extracted sequence directory containing point clouds and timestamps.

### What to Look For in the Output:
- **Discovered Formats**: Confirms actual file extensions discovered on disk (.pcd, .bin, .ply, .npy).
- **Sensor Frequency**: Labeled `[MEASURED]` if derived from real recorded timestamps, or `[UNAVAILABLE]` if timestamps are absent.
- **Integrity & Health**: Reports verified missing frame drops and malformed files.

Output files are saved to `results/newer_college/01_data_inspection/`.

---

## 5. Step 3: Run the Minimal LiDAR Odometry Baseline (Experiment 02)

Now run the core navigation baseline: Iterative Closest Point (ICP) scan-to-scan odometry:

```powershell
python experiments/02_analyze_lidar_odometry.py --dataset newer_college --path datasets/newer-college/01_short_experiment --max-frames 50 --voxel-size 0.15
```

### What Each Major Parameter Controls:
- `--dataset newer_college`: Selects the Newer College dataset sequence.
- `--max-frames 50`: Restricts processing to 50 frames for fast initial evaluation.
- `--voxel-size 0.15`: Groups points into $15\text{ cm}$ cubic cells and computes cell centroids. This reduces input points by ~70–90%, dramatically speeding up computation while preserving wall geometry.
- `--max-distance 1.5`: Rejects point correspondences farther than $1.5\text{ meters}$, filtering out transient outliers.
- `--max-iterations 30`: Limits alignment iterations per scan to prevent infinite loops.

### Terminal Summary Breakdown:
```
------------------------------------------------------------
ODOMETRY & ALGORITHM RESULTS
------------------------------------------------------------
Frames Processed          : 20 frames          [MEASURED]
Successful Steps          : 20 steps           [MEASURED]
Registration Rate         : 100.0 %            [DERIVED]
Estimated Path Length     : 0.036 meters       [DERIVED]
Final Position [X,Y,Z]    : [0.033, 0.003, -0.005] meters [DERIVED]

------------------------------------------------------------
PROCESSING LATENCY PROFILER
------------------------------------------------------------
Mean Latency              : 286.09 ms          [MEASURED]
P95 Latency               : 308.90 ms          [MEASURED]
Sensor Arrival Period     : 100.0 ms           [ASSUMED]
Real-Time Margin          : -208.90 ms         [DERIVED]
Real-Time Check           : FAIL (CANNOT KEEP UP) [DERIVED]
```

---

## 6. How to Open the Generated Graphs

All output artifacts are saved in:  
`results/synthetic/02_lidar_odometry_icp/`

In Windows PowerShell, open the generated graphs directly in your default image viewer:

```powershell
# 1. Open the estimated 3D vehicle trajectory
Start-Process results/synthetic/02_lidar_odometry_icp/figures/trajectory_topdown.png

# 2. Open the per-scan processing latency graph
Start-Process results/synthetic/02_lidar_odometry_icp/figures/registration_latency.png

# 3. Open the point cloud decimation graph
Start-Process results/synthetic/02_lidar_odometry_icp/figures/point_decimation.png
```

---

## 7. How to Interpret Each Graph and Metric

### 1. `trajectory_topdown.png` (Estimated Motion)
- **Top-Down Plot ($X\text{ vs }Y$)**: Displays the vehicle's position over time starting at $(0, 0)$.
- **Side Profile ($X\text{ vs }Z$)**: Shows elevation changes and vertical drift.
- **What it tells you**: Whether the odometry maintains a smooth continuous trajectory or jumps erratically due to registration divergence.

### 2. `registration_latency.png` (Real-Time Feasibility)
- **Purple Line**: Wall-clock execution time for each individual scan.
- **Red Line (100 ms)**: The sensor arrival deadline ($1 / 10\text{ Hz} = 100\text{ ms}$).
- **Orange Dotted Line (P95)**: 95th percentile latency (95% of scans completed faster than this time).
- **What it tells you**: If the purple line is above the red line, the host computer cannot process scans as fast as the LiDAR produces them. Scans will queue up in memory, causing dangerous lag on an autonomous drone.

### 3. `point_decimation.png` (Computational Input Size)
- **Dashed Gray Line**: Raw points emitted by the sensor (~65,000 points).
- **Solid Blue Line**: Points after $15\text{ cm}$ voxel filtering (~5,000 to ~15,000 points).
- **What it tells you**: Shows the exact data volume entering the nearest-neighbor search. Voxel downsampling is the single most effective way to improve processing speed.

### 4. `metrics.csv` & `summary.json`
- `metrics.csv`: Contains exact per-frame measurements (latency in ms, coordinates $X, Y, Z$, translation step, fitness residual).
- `summary.json`: Contains full scientific metadata with explicit provenance tags (`[MEASURED]`, `[DERIVED]`, `[ASSUMED]`).

---

## 8. What Conclusions Are Justified vs. NOT Justified

| Conclusion | Valid? | Why? |
|---|---|---|
| *"Scan-to-scan ICP successfully registered 20 frames with 0 divergences."* | **YES** | Empirically verified by convergence status and residual fitness scores. |
| *"On this host computer, pure Python ICP took ~280 ms per scan."* | **YES** | Measured directly with `time.perf_counter()`. |
| *"This pure Python implementation would fail to run in real time on a 10 Hz LiDAR without C++ acceleration or coarser voxel grids."* | **YES** | $280\text{ ms} > 100\text{ ms}$ arrival budget. |
| *"This algorithm will run at the same speed on a Raspberry Pi 5."* | **NO!** | Desktop x86 CPU performance does not represent ARM Cortex-A76 cores. Hardware must be benchmarked directly. |
| *"This odometry has sub-centimeter global accuracy."* | **NO!** | We have not yet aligned with Leica ground truth (planned for Stage 3). Scan-to-scan odometry drifts over time. |

---

## 9. How to Run on Real Newer College Data

When you have downloaded the Oxford Newer College `01_short_experiment` slice:

1. Extract the point cloud files (`.pcd`, `.bin`, or `.npy`) to:
   ```
   datasets/newer-college/01_short_experiment/
   ```
2. Run inspection on the real folder:
   ```powershell
   python experiments/01-data-inspection/run.py --dataset newer_college --path datasets/newer-college/01_short_experiment
   ```
3. Run the ICP odometry baseline on the real folder:
   ```powershell
   python experiments/02-lidar-odometry-icp/run.py --dataset newer_college --path datasets/newer-college/01_short_experiment --max-frames 50
   ```
4. Compare the measured latencies and trajectories against the synthetic baseline!
