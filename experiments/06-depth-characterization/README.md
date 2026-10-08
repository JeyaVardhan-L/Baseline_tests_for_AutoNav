# Experiment 06: Depth Sensor Characterization

## 1. Objective
Experimentally evaluate RGB-D / depth camera data streams (TUM RGB-D, OpenLORIS, or Synthetic) to measure data volume, valid pixel return coverage, depth distribution, processing latency, and 3D back-projection geometry.

## 2. Why This Matters
For indoor, GPS-denied autonomous navigation, depth cameras (active stereo or time-of-flight) provide rich obstacle avoidance and dense mapping inputs. However, unlike LiDARs that emit active laser pulses in 360 degrees, depth cameras have a constrained field-of-view, drop out on reflective or dark surfaces, and require projective geometric transformation to become 3D coordinates.

## 3. Required Knowledge
- **Depth Image**: A 2D matrix where each pixel $(u, v)$ stores the distance $Z$ (in meters or millimeters) along the camera optical axis.
- **Pinhole Camera Model**: Geometric model relating 3D spatial points $(X, Y, Z)$ to 2D image coordinates $(u, v)$ via focal lengths $(f_x, f_y)$ and principal point $(c_x, c_y)$.
- **Valid Pixel Coverage**: Percentage of pixels with non-zero, finite depth values within the near and far clip range $[Z_{\min}, Z_{\max}]$.
- **LiDAR vs. Depth Camera**: LiDAR provides sparse/semi-dense 360-degree point clouds with high outdoor range; Depth cameras provide dense forward-facing regular grids with lower range (typically 0.2 m to 10 m).

## 4. Dataset
- TUM RGB-D (`tum_rgbd`) — recommended beginner-friendly depth benchmark
- OpenLORIS-Scene (`openloris`) — indoor robot navigation sequences
- Synthetic depth stream (`synthetic`)

## 5. Input
RGB-D image pairs containing 16-bit or 32-bit depth maps with associated RGB imagery.

## 6. Output
- `metrics.csv`: Per-frame statistics (valid pixels, coverage %, min/max/mean/median depth, frame size in bytes, latency).
- `summary.json`: Aggregated metrics and host machine processing performance.
- `figures/depth_histogram.png`: Histogram answering *"What range of distances is observed by the depth sensor?"*
- `summary.md`: Standardized engineering summary table.

## 7. Parameters
- `--dataset`: Dataset identifier (`synthetic`, `tum_rgbd`, `openloris`).
- `--max-frames`: Maximum frames to analyze (default: 30).
- `--min-depth`: Minimum valid range threshold in meters (default: 0.2 m).
- `--max-depth`: Maximum valid range threshold in meters (default: 10.0 m).
- `--save-pointcloud`: Flag to export generated 3D points.

## 8. Method
1. Load depth and color frames.
2. Filter out non-finite or out-of-range pixels.
3. Compute summary statistics: mean, median, min, max, and percentage coverage.
4. Apply the pinhole camera inverse projection formula to reconstruct 3D Cartesian coordinates $(X, Y, Z)$.
5. Profile execution latency and host RAM usage.

## 9. Equations
$$\text{Coverage } = \frac{N_{\text{valid}}}{H \times W} \times 100\%$$
$$X = \frac{(u - c_x) \times Z}{f_x}$$
$$Y = \frac{(v - c_y) \times Z}{f_y}$$
$$\text{Memory} = H \times W \times \text{bytes\_per\_pixel}$$

## 10. Command
```bash
# Synthetic demonstration
python experiments/06-depth-characterization/run.py --dataset synthetic --max-frames 30

# TUM RGB-D real sequence
python experiments/06-depth-characterization/run.py --dataset tum_rgbd --path datasets/tum-rgbd/rgbd_dataset_freiburg1_xyz
```

## 11. Expected Terminal Output
```
============================================================
  EXPERIMENT 06 - DEPTH CHARACTERIZATION
  Dataset: synthetic
============================================================

DEPTH SENSOR MEASUREMENTS
------------------------------------------------------------
Frames Analyzed         : 30 frames [MEASURED]
Resolution              : 640x480 WxH [MEASURED]
Average Valid Coverage  : 92.4 % [MEASURED] (Pixels with valid distance return)
Mean Detected Depth     : 3.42 m [MEASURED]
Median Detected Depth   : 3.10 m [MEASURED]
Average Frame Size      : 1.838 MB [MEASURED] (Depth + RGB uncompressed memory)

PROCESSING & COMPUTATIONAL LOAD
------------------------------------------------------------
Mean Processing Time    : 14.82 ms [MEASURED] (Stats + 3D back-projection)
P95 Processing Time     : 16.50 ms [MEASURED]
Processing Throughput   : 67.5 FPS [DERIVED] (Host single-core rate)
Process Memory (RAM)    : 84.2 MB [MEASURED]
============================================================
```

## 12. Live Visualization
Generates `figures/depth_histogram.png` illustrating distance distribution and cutoff thresholds.

## 13. Graphs
- **`depth_histogram.png`**: Answers *"What range of distances is observed by the depth sensor?"*

## 14. Metrics
| Metric | Type | Unit | Description |
|---|---|---|---|
| Valid Coverage | `[MEASURED]` | % | Proportion of image with valid returns |
| Mean Depth | `[MEASURED]` | m | Arithmetic mean of detected surfaces |
| Median Depth | `[MEASURED]` | m | Median surface distance |
| Frame Size | `[MEASURED]` | MB | Memory buffer footprint per frame |
| Latency | `[MEASURED]` | ms | 2D-to-3D projection and statistics compute time |

## 15. Interpretation
- If valid coverage drops below 70%, the sensor is struggling with absorption, high ambient sunlight, or out-of-range voids.
- Converting dense depth (e.g. 640x480 = 307,200 points) to 3D per frame requires significant CPU cycles unless downsampled or accelerated.

## 16. Limitations
- Pinhole projection assumes factory intrinsic calibration without non-linear radial lens distortion.
- Workstation execution does not include embedded memory bandwidth contention (e.g. unified memory bus on Jetson/SoC).

## 17. Reproducibility Information
- Intrinsic parameters $(f_x, f_y, c_x, c_y)$ documented in configuration or dataset metadata.

## 18. What Decision This Experiment Can Inform
- Informs whether depth camera data can be ingested at full resolution or if hardware decimation is mandatory for real-time UAV obstacle avoidance.
