# EXP-01 — LiDAR Dataset Characterization

## Objective

Answer the question: **What does LiDAR data actually look like, and how much data does it generate?**

This is the first step before any algorithm development. We need to understand the raw data before we can process it.

### Specific Questions

1. How many points exist per LiDAR frame?
2. What is the frame rate?
3. What is the effective data rate (MB/s)?
4. What fields are present in each point?
5. What is the spatial distribution of points (range histogram)?
6. How much memory is required to load and process frames?
7. How long does it take to load and parse frames?
8. What CPU resources are needed for basic processing?
9. Can we estimate data bandwidth requirements for communication?

## Hypothesis

Based on the KITTI dataset specifications (Velodyne HDL-64E, nominal 10 Hz, nominal ~100,000 points/frame):

- Each frame size: ~100,000 × 16 bytes = ~1.6 MB (*DERIVED from 100k points and 4 × float32 fields*)
- Data rate: ~16 MB/s raw (*DERIVED using assumed 10.0 Hz nominal sensor rate*)
- Loading a frame into NumPy: < 10 ms on a modern CPU (*HYPOTHESIS / TO BE MEASURED*)
- Buffer memory for a single frame: ~2–5 MB (*ESTIMATED HYPOTHESIS / TO BE MEASURED*)

**These are hypotheses and derivations. They will be verified or refuted by actual measurement.**

## Why This Matters

- Establishes a **computational baseline** for point-cloud data rates and I/O load
- Determines the **memory footprint** needed for raw point-cloud buffers
- Provides an upper-bound baseline for evaluating future lightweight UAV LiDAR options
- Does **NOT** prove any specific UAV LiDAR or computer is suitable; it only establishes baseline processing limits

## Dataset

> ⚠️ **CRITICAL NOTE ON DATASET CONTEXT:**
> The KITTI dataset is a **terrestrial automotive dataset** recorded from a car driving through urban and suburban environments.
> It is **NOT** a UAV dataset, and the Velodyne HDL-64E (~13 kg, ~60 W) is **NOT** a UAV-mountable sensor for a < 2 kg micro-UAV.
> KITTI is used here exclusively as an established, publicly documented **data-volume and processing benchmark** to measure raw point-cloud ingestion, parsing speed, and memory usage.

| Field | Value | Classification |
|-------|-------|----------------|
| Name | KITTI Vision Benchmark Suite — Odometry | Sourced Fact |
| Type | Terrestrial Automotive (Roof-mounted on car) | Sourced Fact |
| Source | Karlsruhe Institute of Technology / Toyota Technological Institute at Chicago | Sourced Fact |
| URL | https://www.cvlibs.net/datasets/kitti/eval_odometry.php | Sourced Fact |
| Sensor | Velodyne HDL-64E (64-beam mechanical spinning LiDAR) | Sourced Fact |
| Sequence | 00 (residential loop, ~4,541 frames total) | Sourced Fact |
| Point format | Binary `.bin` — little-endian IEEE float32 (x, y, z, reflectance) | Sourced Fact |
| Nominal Frequency | 10.0 Hz | ASSUMED from manufacturer spec (unmeasured) |
| License | Creative Commons Attribution-NonCommercial-ShareAlike 3.0 | Sourced Fact |
| Download status | NOT YET DOWNLOADED (Local data required) | Operational Status |
| Evaluation subset | First 20–50 frames for initial test (configurable) | Experiment Parameter |

### Why KITTI for EXP-01 Baseline?

1. **Format simplicity**: Uniform binary `.bin` files (one per scan) allow direct parsing with NumPy without external ROS dependencies.
2. **Authoritative baseline**: Decades of literature use KITTI; sensor characteristics are thoroughly documented.
3. **Upper-bound processing load**: HDL-64E generates ~100k–120k points/scan, representing a heavy computational load compared to compact UAV LiDARs (~20k–50k points/scan). If our ingestion pipeline cannot handle KITTI, it will struggle with high-throughput streams.

### Limitations of KITTI for UAV Autonomy

- **Terrestrial vehicle perspective**: Ground-plane dominated, 2D planar motion bias, road surface features.
- **Sensor mass & power mismatch**: HDL-64E cannot fly on a micro-UAV (< 2 kg).
- **Does not represent UAV flight dynamics**: No 6-DoF aggressive pitch/roll, rotor vibrations, or aerial look-down angles.

### Download & Placement Instructions

The official KITTI Odometry dataset is hosted on the Karlsruhe Institute of Technology portal.

1. Navigate to: [http://www.cvlibs.net/datasets/kitti/eval_odometry.php](http://www.cvlibs.net/datasets/kitti/eval_odometry.php)
2. Register an academic/research account and log in.
3. Under **Download odometry data set (Velodyne laser data)**:
   - Download the laser archive (or sequence 00).
4. Extract sequence 00 into the repository under:
   `datasets/kitti/sequences/00/velodyne/`
5. Verify the files exist:
   `datasets/kitti/sequences/00/velodyne/000000.bin`
   `datasets/kitti/sequences/00/velodyne/000001.bin`
   ...

Expected directory structure:
```
datasets/kitti/sequences/00/velodyne/
├── 000000.bin
├── 000001.bin
├── 000002.bin
├── ...
└── 004540.bin
```

Each `.bin` file contains a sequence of float32 quadruplets (x, y, z, reflectance).

## Hardware / Software Environment

| Field | Value |
|-------|-------|
| Machine | NOT RECORDED (run `python tools/collect_sysinfo.py`) |
| OS | NOT RECORDED |
| CPU | NOT RECORDED |
| GPU | NOT RECORDED (not required for this experiment) |
| RAM | NOT RECORDED |
| Python | NOT RECORDED |
| Key libraries | numpy, matplotlib, pyyaml, psutil |
| Git commit | NOT RECORDED |

## Input

Binary `.bin` files from KITTI Velodyne directory. Each file is a single LiDAR frame.

## Method

1. Load configuration from `config/config.yaml`
2. Discover all `.bin` files in the data directory
3. For each frame (up to `max_frames`):
   a. Record file size in bytes
   b. Load binary data using `numpy.fromfile()`
   c. Reshape to (N, 4) — each row is (x, y, z, reflectance)
   d. Record load time
   e. Calculate point count
   f. Calculate range (√(x² + y² + z²)) for each point
   g. Record range statistics (min, max, mean, percentiles)
   h. Record reflectance statistics
   i. Record bounding box
   j. Measure memory usage
4. Aggregate statistics across all frames
5. Generate plots
6. Save results as CSV and JSON
7. Record system information and metadata

## Metrics

### Dataset-Level Metrics

| Metric | Unit | Why It Matters |
|--------|------|---------------|
| Total frames processed | count | Dataset scope |
| Total duration (derived) | seconds | Mission time reference |
| Sensor frequency (derived) | Hz | Validates expected rate |

### Per-Frame Metrics

| Metric | Unit | Why It Matters |
|--------|------|---------------|
| Points per frame | count | Processing load per cycle |
| Frame file size | bytes | Storage and I/O requirements |
| Point density | points/m³ | Spatial coverage |

### Aggregate Metrics

| Metric | Unit | Why It Matters |
|--------|------|---------------|
| Average points/frame | count | Typical processing load |
| Min/max points/frame | count | Variability |
| Std dev points/frame | count | Consistency |
| Average frame size | bytes | Storage/bandwidth planning |
| Data rate | MB/s | Bandwidth requirements |
| Data volume | GB/minute, GB/hour | Storage planning |

### Geometry Metrics

| Metric | Unit | Why It Matters |
|--------|------|---------------|
| Minimum range | m | Closest detection distance |
| Maximum range | m | Farthest detection distance |
| Average range | m | Typical operating range |
| Range percentiles (25/50/75/90/95) | m | Range distribution |
| Bounding box | m | Spatial extent |

### Computation Metrics

| Metric | Unit | Why It Matters |
|--------|------|---------------|
| Frame load time | ms | I/O performance |
| Processing time per frame | ms | CPU requirement |
| Total processing time | s | Experiment duration |
| Peak memory usage | MB | RAM requirements |

## Results

**Status: NOT YET RUN**

Results will be populated after running the experiment.

## Graphs

The experiment generates these plots:

1. **Points per frame** — bar/line chart over frame index
2. **Point count distribution** — histogram
3. **Frame size distribution** — histogram
4. **Range distribution** — histogram of all point ranges
5. **Processing time per frame** — line chart
6. **Range vs. point density** — scatter or 2D histogram
7. **Representative point cloud** — 2D projection (bird's-eye view)

All plots are saved to `figures/` with descriptive filenames.

## Interpretation

*To be written after results are available.*

## Limitations

- KITTI uses HDL-64E (64-beam, ~100k pts/frame) which is NOT representative of lightweight UAV LiDARs
- Ground-vehicle perspective differs from aerial perspective
- Single sequence may not represent all operating conditions
- Processing times measured on a desktop/laptop, not on embedded hardware

## Decision

This experiment informs:

- **Sensor requirements**: What data rate must the onboard computer handle?
- **Memory requirements**: How much RAM is needed for point-cloud buffers?
- **Communication bandwidth**: If we need to transmit any LiDAR data, how much bandwidth?
- **Downsampling feasibility**: Can we reduce data without destroying navigation utility?

## Reproduction

```bash
# 1. Ensure Python environment is set up
pip install -e .

# 2. Download KITTI sequence 00 Velodyne data (see download instructions above)

# 3. Run the experiment
python experiments/01-lidar-characterization/scripts/characterize_lidar.py \
    --config experiments/01-lidar-characterization/config/config.yaml

# Or with a custom data directory:
python experiments/01-lidar-characterization/scripts/characterize_lidar.py \
    --config experiments/01-lidar-characterization/config/config.yaml \
    --data-dir path/to/velodyne/directory
```

## Artifacts

| File | Description |
|------|-------------|
| `config/config.yaml` | Experiment configuration |
| `scripts/characterize_lidar.py` | Main experiment script |
| `results/frame_metrics.csv` | Per-frame measurements |
| `results/summary_metrics.json` | Aggregate statistics |
| `results/experiment_metadata.json` | Run metadata (system info, git, timestamps) |
| `figures/*.png` | Generated plots |

## Status

**NOT STARTED**
