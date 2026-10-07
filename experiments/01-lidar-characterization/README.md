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

Based on the KITTI dataset using a Velodyne HDL-64E at 10 Hz with ~100,000 points/frame:

- Each frame should be approximately 100,000 × 16 bytes = ~1.6 MB
- Data rate should be approximately 16 MB/s raw
- Loading a frame into NumPy should take < 10 ms on a modern CPU
- Total memory for a single frame should be ~2-5 MB including overhead

**These are hypotheses. They will be verified or refuted by measurement.**

## Why This Matters

- Determines the **data rate** our onboard computer must handle
- Determines the **memory** needed for point-cloud buffers
- Determines the **communication bandwidth** if any data is transmitted
- Provides **baseline understanding** for all subsequent LiDAR experiments
- Helps evaluate whether **low-cost LiDARs** (with fewer points) are feasible

## Dataset

| Field | Value |
|-------|-------|
| Name | KITTI Odometry |
| Source | Karlsruhe Institute of Technology |
| URL | https://www.cvlibs.net/datasets/kitti/eval_odometry.php |
| Sensor | Velodyne HDL-64E |
| Sequence | 00 (or configurable) |
| Point format | Binary `.bin` — float32 (x, y, z, reflectance) |
| Frequency | 10 Hz (nominal) |
| License | CC BY-NC-SA 3.0 |
| Download date | NOT YET DOWNLOADED |
| Subset size | First 200 frames (configurable) |

### Why KITTI?

1. **Simple format**: Binary `.bin` files, one per frame — easy to parse with NumPy
2. **Well-documented sensor**: Velodyne HDL-64E specifications are publicly available
3. **Known characteristics**: ~100k points/frame at 10 Hz — allows verification
4. **Large community**: Published benchmarks for cross-reference
5. **Individual sequences**: Can download one sequence (~2-4 GB) instead of full 80 GB
6. **Outdoor environment**: Relevant to outdoor UAV operation

### KITTI Limitations (for our use case)

- **Ground vehicle**: Data collected from a car, not a UAV
- **Expensive sensor**: HDL-64E is a large, high-end, 64-beam LiDAR — not representative of UAV-class sensors
- **Ground perspective**: Viewpoint is from road level, not aerial

These limitations are acceptable for EXP-01 because we are characterizing **data properties**, not testing navigation algorithms.

### Download Instructions

1. Go to https://www.cvlibs.net/datasets/kitti/eval_odometry.php
2. Register / log in
3. Download "Velodyne point clouds" (80 GB for all, or find individual sequence links)
4. For a minimal test, download only sequence 00
5. Extract to: `datasets/kitti/sequences/00/velodyne/`

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
