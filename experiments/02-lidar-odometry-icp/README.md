# Experiment: LiDAR-Only Iterative Closest Point (ICP) Odometry

## Purpose

This experiment establishes the project's **first minimal, understandable navigation baseline**:
estimating relative motion between consecutive 3D LiDAR scans using point-to-point Iterative Closest Point (ICP) registration.

It does **not** attempt a full SLAM system, bundle adjustment, or loop closure. It provides the reference baseline against which subsequent filtering methods, multi-sensor fusion, and hardware requirements will be compared.

---

## What the Algorithm Does

1. **Pre-processing**:
   - Removes non-finite coordinates (NaN, Inf) and self-reflections ($r < 0.5\text{ m}$).
   - Decimates the point cloud into a 3D voxel grid (default: $0.15\text{ m}$) to reduce registration cost while maintaining surface structure.
2. **Nearest-Neighbor Matching**:
   - Uses a SciPy $k\text{-d}$ tree to identify closest point pairs between the current scan and previous scan within `max_correspondence_distance` (default: $1.5\text{ m}$).
3. **Rigid Motion Estimation**:
   - Computes optimal rotation $R$ and translation $t$ using the Kabsch-Umeyama SVD algorithm.
4. **Trajectory Accumulation**:
   - Integrates relative step transformations into a global 6-DoF trajectory $T_0^k = T_0^{k-1} \cdot (T_{k-1}^k)^{-1}$.
5. **Empirical Cost Profiling**:
   - Measures per-scan wall-clock latency, host CPU percentage, and resident set size (RSS) RAM footprint.

---

## How to Run

### 1. Synthetic Demonstration (Fast Offline Verification)
```powershell
python experiments/02-lidar-odometry-icp/run.py --dataset synthetic --max-frames 20
```

### 2. Real Dataset (Oxford Newer College)
```powershell
python experiments/02-lidar-odometry-icp/run.py --dataset newer_college --path datasets/newer-college/01_short_experiment --max-frames 50
```

---

## Command-Line Arguments

| Argument | Default | Description |
|---|---|---|
| `--dataset` | `synthetic` | Dataset name (`synthetic`, `newer_college`) |
| `--path` | `None` | Custom local dataset directory |
| `--max-frames` | `20` | Maximum number of frames to process |
| `--voxel-size` | `0.15` | Voxel downsampling grid edge length in meters |
| `--max-distance`| `1.5` | Maximum Euclidean point correspondence threshold (meters) |
| `--max-iterations` | `30` | Maximum ICP alignment iterations per scan |

---

## Output Files

Artifacts are saved to `results/<dataset>/02_lidar_odometry_icp/`:
- `metrics.csv`: Tabular measurements per frame (latency, points, step distance, 3D pose, inlier ratio).
- `summary.json`: Complete dictionary with scientific evidence classifications (`[MEASURED]`, `[DERIVED]`, `[ASSUMED]`).
- `metadata.json`: Host machine OS, CPU, RAM, and run timestamp.
- `summary.md`: Human-readable summary report with findings and observations.
- `figures/trajectory_topdown.png`: Top-down and side profile of the estimated vehicle trajectory.
- `figures/registration_latency.png`: Registration latency per scan vs. sensor arrival deadline.
- `figures/point_decimation.png`: Comparison of raw vs. downsampled points per frame.

---

## Scientific Discipline & Evidence Classification

- **Host Latency & Memory** are labeled `[MEASURED]` on the test machine.
- **Estimated Path Length & Drift** are labeled `[DERIVED]` from registration steps.
- **Sensor Period** is labeled `[ASSUMED]` from datasheet nominal frequency unless authentic timestamps are verified.
- **Desktop measurements DO NOT represent Raspberry Pi 5 performance.** Embedded performance remains unverified until run directly on target hardware.
