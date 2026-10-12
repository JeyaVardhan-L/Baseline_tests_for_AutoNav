# Research Experiments Walkthrough

This directory contains the core numbered research workflow for evaluating real sensor datasets and benchmarking LiDAR odometry algorithms.

```text
experiments/
├── 01_inspect_dataset.py          # Step 1: Inspect and validate real sensor datasets
├── 02_analyze_lidar_odometry.py    # Step 2: Measure scan-to-scan ICP performance and host compute
└── README.md                      # This walkthrough
```

---

## Non-Negotiable Research Principles

1. **Real Data Exclusively:** Synthetic data generators and simulation raycasters are prohibited from serving as navigation feasibility evidence.
2. **Deterministic Evidence Tagging:** Every metric is explicitly classified:
   - `[MEASURED]`: Derived directly from sensor recordings or timer measurements.
   - `[DERIVED]`: Computed via mathematical formulas from measured data.
   - `[DECLARED]`: Extracted from authoritative sensor datasheets or publication specifications.
   - `[ASSUMED]`: Explicitly stated parameters used for comparison.
   - `[UNAVAILABLE]`: Data or ground truth not available.
   - `[UNVERIFIED]`: Algorithm or metric not validated against ground truth.
3. **Reproducibility:** Experiments export structured CSV, JSON, Markdown, and PNG figures to `results/<dataset>/<experiment>/`.

---

## Step 1: Inspect Real Sensor Dataset

**Script:** `experiments/01_inspect_dataset.py`  
**Purpose:** Answers the fundamental research question: *"What sensors, files, and timestamps does this dataset contain, and is it suitable for odometry analysis?"*

### Windows PowerShell Execution:
```powershell
python experiments/01_inspect_dataset.py --dataset newer_college --path datasets/newer-college/01_short_experiment
```

### What It Measures and Reports:
- **Discovered Files & Size:** Total count of raw files and disk footprint (`MEASURED`).
- **Discovered Formats:** `.pcd`, `.bin`, `.ply`, `.npy`, `.bag` files present on disk.
- **Valid Point Cloud Frames:** Number of consecutive readable 3D point cloud scans (`MEASURED`).
- **Timestamp Integrity:** Reads `timestamps.csv` or filename timestamps; checks monotonicity and derives observed sensor frequency (`MEASURED`).
- **Spatial Bounding Checks:** Reads coordinate ranges (X, Y, Z min/max) and verifies all coordinates are finite numbers without NaN/Inf values (`MEASURED`).
- **Honest Missing Data:** If files or timestamps are missing, reports `UNAVAILABLE` rather than fabricating numbers.

### Generated Artifacts (`results/newer_college/01_data_inspection/`):
- `inspection_summary.json`: Complete machine-readable summary.
- `metadata.json`: Host machine OS, CPU, RAM, and Git commit hash.
- `summary.md`: Clean Markdown report with measured metrics table.

---

## Step 2: Run LiDAR Odometry Baseline (Scan-to-Scan ICP)

**Script:** `experiments/02_analyze_lidar_odometry.py`  
**Purpose:** Answers the core computational question: *"How long does scan-to-scan ICP take to process each frame on host hardware, and can it keep up with real-time sensor arrival rates?"*

### Algorithm Overview:
- **Method:** Rigid 3D point-to-point Iterative Closest Point (SVD / Kabsch alignment).
- **Previous & Current Frame Pairing:** Consecutive temporal scans: frame $t$ is registered against frame $t-1$.
- **Coordinate Conventions:** Right-handed sensor frame ($X$ forward, $Y$ left, $Z$ up).
- **Preprocessing:** Voxel downsampling decimation to reduce point counts while preserving geometry.
- **Registration Success Rate:** Frame 0 is the reference initialization frame and is **strictly excluded** from the registration success rate denominator:
  $$\text{Success Rate} = \frac{\text{Successful Registrations}}{\text{Total Frames} - 1} \times 100\%$$

### Windows PowerShell Execution:
```powershell
python experiments/02_analyze_lidar_odometry.py --dataset newer_college --path datasets/newer-college/01_short_experiment --max-frames 50 --voxel-size 0.15
```

### Key Parameters:
- `--max-frames`: Limit number of frames processed (default: 50).
- `--voxel-size`: Downsampling voxel leaf size in meters (default: 0.15m).
- `--max-distance`: Correspondence rejection distance threshold in meters (default: 1.5m).
- `--max-iterations`: Maximum ICP iteration steps per scan (default: 30).

### Generated Artifacts (`results/newer_college/02_lidar_odometry_icp/`):
- `metrics.csv`: Tabular frame-by-frame data (latencies, point counts, 3D positions, inlier ratios).
- `summary.json`: Latency distribution (Mean, Median, P95, P99), RSS RAM, and throughput.
- `summary.md`: Executive summary table with scientific evidence tags.
- `figures/trajectory_topdown.png`: Top-down X-Y plane estimated trajectory with start/end markers.
- `figures/registration_latency.png`: Per-frame registration latency plotted against the 100ms sensor deadline.
- `figures/point_decimation.png`: Raw vs downsampled point counts illustrating compute decimation.
