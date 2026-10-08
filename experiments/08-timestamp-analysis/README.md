# Experiment 08: Timestamp & Sensor Synchronization

## 1. Objective
Measure and analyze multi-sensor timestamp synchronization between LiDAR scans, camera frames, and IMU telemetry by computing nearest-neighbor temporal offsets, assessing clock alignment, and evaluating synchronization requirements for state estimation.

## 2. Why This Matters
Autonomous UAV navigation depends on fusing multi-modal sensors. 
- **LiDAR + IMU**: A rotating or solid-state LiDAR scan takes 50 to 100 ms to acquire. If the UAV is pitching or rolling at $60^\circ/\text{s}$, points acquired at the end of the scan will be distorted relative to points at the start unless motion de-skewed using microsecond-synchronized IMU orientation integration.
- **Camera + IMU**: In Visual-Inertial Odometry (VIO), IMU integration predicts camera pose between frames. Timestamp desynchronization (even 5 to 10 ms) corrupts feature reprojection residuals and causes estimator divergence.
- **LiDAR + Camera**: Projecting 3D LiDAR points into 2D camera pixels requires both sensors to capture the world at identical poses.

## 3. Required Knowledge
- **Epoch / Timestamp ($t$)**: Time recorded when a physical measurement was sampled, expressed in UTC epoch or monotonic clock seconds.
- **Nearest-Neighbor Offset ($\Delta t_{\text{sync}}$)**: The temporal difference $|\,t_{\text{target}} - t_{\text{ref, closest}}\,|$.
- **Hard Hardware Sync (PPS / PTP)**: Hardware electrical pulse (Pulse Per Second) or IEEE 1588 Precision Time Protocol keeping clocks aligned within microseconds.
- **Soft Software Sync**: Associating frames post-hoc using closest timestamps or constant-offset interpolation.

## 4. Dataset
- Oxford Newer College (`newer_college`) — Ouster OS-1 LiDAR + RealSense D435i + IMU
- Hilti SLAM 2023 (`hilti_2023`) — Robosense Bpearl LiDAR + XSens MTi-600 IMU (200 Hz) + OAK-D
- OpenLORIS-Scene (`openloris`) — RealSense D435i RGB-D + IMU
- Synthetic multi-modal stream (`synthetic`)

## 5. Input
Multiple parallel time-series containing recorded timestamps from LiDAR, camera, and IMU streams.

## 6. Output
- `metrics.csv`: Time-series of nearest-neighbor offsets per frame.
- `summary.json`: Offset distribution metrics (mean, median, P95, max).
- `figures/cross_sensor_offset_vs_time.png`: Timeline of synchronization offsets.
- `figures/cross_sensor_offset_histogram.png`: Histogram answering *"What is the maximum temporal discrepancy before sensor fusion?"*
- `summary.md`: Standardized summary report.

## 7. Parameters
- `--dataset`: Dataset name (`synthetic`, `newer_college`, `hilti_2023`, `openloris`).
- `--max-lidar-frames`: Maximum LiDAR frames to evaluate (default: 50).
- `--max-imu-samples`: Maximum IMU packets to evaluate (default: 1000).

## 8. Method
1. Read timestamps from all available sensors into sorted arrays.
2. For each query sensor timestamp (e.g. LiDAR or Camera), perform binary search (`np.searchsorted`) to locate the temporally closest IMU sample.
3. Compute metric absolute differences $\Delta t = |t_{\text{query}} - t_{\text{ref, closest}}|$ in milliseconds.
4. Calculate mean, median, 95th percentile, and maximum synchronization offsets.
5. Plot temporal trajectory and histogram.

## 9. Equations
$$\Delta t_{\text{offset}, i} = \min_j \left| t_{\text{lidar}, i} - t_{\text{imu}, j} \right| \times 1000 \text{ ms}$$
$$\text{Spatial Motion Error } \Delta x \approx v_{\text{UAV}} \times \Delta t_{\text{offset}}$$

## 10. Command
```bash
# Run with synthetic multi-modal stream
python experiments/08-timestamp-analysis/run.py --dataset synthetic --max-lidar-frames 50

# Run with Oxford Newer College multi-sensor dataset
python experiments/08-timestamp-analysis/run.py --dataset newer_college
```

## 11. Expected Terminal Output
```
============================================================
  EXPERIMENT 08 - TIMESTAMP + SENSOR SYNCHRONIZATION
  Dataset: synthetic
============================================================

COLLECTED SENSOR STREAMS
------------------------------------------------------------
LiDAR Frames            : 50 scans [MEASURED]
LiDAR Epoch Span        : 0.000s -> 4.900s [MEASURED]
Camera Frames           : 50 frames [MEASURED]
Camera Epoch Span       : 0.000s -> 1.633s [MEASURED]
IMU Telemetry Packets   : 1000 packets [MEASURED]
IMU Epoch Span          : 0.000s -> 4.995s [MEASURED]

CROSS-SENSOR NEAREST-NEIGHBOR SYNCHRONIZATION OFFSETS (ms)
------------------------------------------------------------
  [LiDAR to Nearest IMU Sample]:
    Mean Offset         : 1.250 ms [MEASURED]
    Median Offset       : 1.250 ms [MEASURED]
    P95 Offset          : 2.375 ms [MEASURED]
    Max Offset          : 2.500 ms [MEASURED]

  [Camera to Nearest IMU Sample]:
    Mean Offset         : 1.248 ms [MEASURED]
    Median Offset       : 1.245 ms [MEASURED]
    P95 Offset          : 2.370 ms [MEASURED]
    Max Offset          : 2.498 ms [MEASURED]
============================================================
```

## 12. Live Visualization
Generates 2 synchronization diagnostic plots in `results/<dataset>/08_timestamp_analysis/figures/`.

## 13. Graphs
- **`cross_sensor_offset_vs_time.png`**: Answers *"Does synchronization drift or jump over the duration of the flight?"*
- **`cross_sensor_offset_histogram.png`**: Answers *"What is the distribution of temporal error between sensor pairs?"*

## 14. Metrics
| Metric | Type | Unit | Description |
|---|---|---|---|
| LiDAR-IMU Offset Mean | `[MEASURED]` | ms | Average time difference between closest scans |
| LiDAR-IMU Offset P95 | `[MEASURED]` | ms | 95th percentile worst-case offset |
| LiDAR-IMU Offset Max | `[MEASURED]` | ms | Peak discrepancy across the dataset |
| Cam-IMU Offset Mean | `[MEASURED]` | ms | Visual-inertial time delay baseline |

## 15. Interpretation
- For a 200 Hz IMU, samples arrive every 5 ms. The maximum theoretical nearest-neighbor error is $\frac{5}{2} = 2.5\text{ ms}$. If observed offsets exceed 2.5 ms, the IMU dropped samples or packets were delayed in transfer buffers.
- If the mean offset grows continuously over time, clock drift is present between distinct onboard sensor microcontrollers.

## 16. Limitations
- Nearest-neighbor evaluation demonstrates inter-sensor time gaps; it does not measure rolling-shutter CMOS readout delays within camera sensor rows.
- Software interpolation (B-splines or linear IMU preintegration) is required in actual SLAM backends to evaluate state at the exact fractional timestamp.

## 17. Reproducibility Information
- Analyzes recorded raw timestamps directly without synthesis or modification.

## 18. What Decision This Experiment Can Inform
- Determines whether software timestamp alignment is sufficient or whether hardware electrical synchronization (PPS/trigger cables) is strictly required for the UAV navigation payload.
