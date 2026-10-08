# Experiment 09: End-to-End Real-Time Pipeline

## 1. Objective
Benchmark the complete sequential sensor data processing pipeline:
$$\text{DATA} \rightarrow \text{READ} \rightarrow \text{DECODE} \rightarrow \text{VALIDATE} \rightarrow \text{FILTER} \rightarrow \text{DOWNSAMPLE} \rightarrow \text{VISUALIZE} \rightarrow \text{METRICS}$$
Measure exact wall-clock latency at each stage and compare total pipeline time against the sensor arrival budget ($T_s = 1000 / f_s$) to quantify the real-time available margin.

## 2. Why This Matters
On an autonomous UAV, LiDAR pre-processing is not the final objective; it is merely the first pre-requisite step for odometry, mapping, and collision avoidance. If pre-processing consumes 90 ms out of a 100 ms sensor period, only 10 ms remains for SLAM scan-matching and trajectory generation, which will inevitably overrun the deadline and trigger control lag.

## 3. Required Knowledge
- **Sensor Period Budget ($T_s$)**: The maximum allowable time before the next sensor packet arrives ($100 \text{ ms}$ for a $10 \text{ Hz}$ LiDAR).
- **Available Margin ($M$)**: Spare compute time remaining in the current cycle: $M = T_s - T_{\text{pipeline}}$.
- **Deadline Miss**: When $T_{\text{pipeline}} > T_s$, the queue backs up, accumulating latency until memory exhausts or frames are dropped.

## 4. Dataset
- Oxford Newer College (`newer_college`)
- Hilti SLAM 2023 (`hilti_2023`)
- Synthetic test stream (`synthetic`)

## 5. Input
Continuous sequence of raw 3D LiDAR point cloud scans.

## 6. Output
- `metrics.csv`: Per-frame stage timings (read, decode, validate, filter, downsample, visualize, total, margin, status).
- `summary.json`: Aggregated distributions for all stages.
- `figures/available_margin_vs_frame.png`: Timeline of spare compute margin with zero-margin threshold.
- `figures/stage_timing_stacked.png`: Stacked bar chart showing per-stage latency breakdown across frames.
- `summary.md`: Standardized summary report.

## 7. Parameters
- `--dataset`: Dataset identifier (`synthetic`, `newer_college`, `hilti_2023`).
- `--max-frames`: Number of frames to benchmark (default: 30).
- `--sensor-hz`: Target sensor publishing rate in Hz (default: 10.0 Hz).
- `--voxel-size`: Downsampling grid size in meters (default: 0.25 m).
- `--min-range`: Minimum sensor range filter in meters (default: 0.5 m).
- `--max-range`: Maximum sensor range filter in meters (default: 40.0 m).

## 8. Method
1. In a tight sequential loop, execute each pipeline stage consecutively.
2. Record microsecond wall-clock deltas using `time.perf_counter()`.
3. Compute available margin $M_i = T_s - T_{\text{total}, i}$.
4. Flag frames where $M_i > 0$ as `PASS` and $M_i \le 0$ as `FAIL`.
5. Aggregate statistical distributions (mean, P95).

## 9. Equations
$$T_s = \frac{1000}{f_s} \text{ ms}$$
$$T_{\text{total}} = T_{\text{read}} + T_{\text{decode}} + T_{\text{validate}} + T_{\text{filter}} + T_{\text{downsample}} + T_{\text{visualize}}$$
$$\text{Margin } M = T_s - T_{\text{total}}$$
$$\text{Pass Rate } = \frac{\sum [M_i > 0]}{N} \times 100\%$$

## 10. Command
```bash
# Benchmark with synthetic test stream
python experiments/09-realtime-processing/run.py --dataset synthetic --max-frames 30

# Benchmark with Oxford Newer College sequence
python experiments/09-realtime-processing/run.py --dataset newer_college --sensor-hz 10.0 --voxel-size 0.20
```

## 11. Expected Terminal Output
```
============================================================
  EXPERIMENT 09 - REAL-TIME PIPELINE BENCHMARK
  Dataset: synthetic
============================================================

AVERAGE PIPELINE TIMING BREAKDOWN (per frame)
------------------------------------------------------------
  READ           :   0.01 ms [MEASURED]
  DECODE         :   0.15 ms [MEASURED]
  VALIDATE       :   4.10 ms [MEASURED]
  FILTER         :   4.85 ms [MEASURED]
  DOWNSAMPLE     :  12.50 ms [MEASURED]
  VISUALIZE      :   0.65 ms [MEASURED]
  --------------------------------
  TOTAL PIPELINE :  22.26 ms [MEASURED] (P95: 25.10 ms)

REAL-TIME DEADLINE & MARGIN
------------------------------------------------------------
Sensor Frequency        : 10.0 Hz [ASSUMED] (Target sensor nominal rate)
Sensor Period Budget    : 100.0 ms [DERIVED] (1000 / Sensor Frequency)
Mean Pipeline Latency   : 22.26 ms [MEASURED]
P95 Pipeline Latency    : 25.10 ms [MEASURED]
Mean Available Margin   : 77.74 ms [DERIVED] (Budget - Mean Pipeline)
P95 Available Margin    : 74.90 ms [DERIVED] (Budget - P95 Pipeline)
Real-Time Pass Rate     : 100.0 % [DERIVED] (Frames meeting sensor deadline)

REAL-TIME STATUS        : PASS (CAN KEEP UP) [DERIVED]
  [NOTE]: Measured on host CPU. Serves as baseline benchmark.
============================================================
```

## 12. Live Visualization
Generates 2 diagnostic figures in `results/<dataset>/09_realtime_processing/figures/`.

## 13. Graphs
- **`available_margin_vs_frame.png`**: Answers *"Does the pipeline maintain positive compute margin on every frame?"*
- **`stage_timing_stacked.png`**: Answers *"Which stages dominate total processing time over the entire sequence?"*

## 14. Metrics
| Metric | Type | Unit | Description |
|---|---|---|---|
| Stage Latencies | `[MEASURED]` | ms | Microsecond timings per discrete stage |
| Total Pipeline | `[MEASURED]` | ms | Sum of stage times per scan |
| Available Margin | `[DERIVED]` | ms | $T_s - T_{\text{total}}$ |
| Real-Time Pass Rate | `[DERIVED]` | % | Percentage of scans completed before next arrival |

## 15. Interpretation
- A positive margin (e.g. 75 ms) indicates that 75% of the frame cycle is available for downstream SLAM, local costmap generation, and path planning.
- A negative margin indicates immediate sensor lag on the host CPU.

## 16. Limitations
- Benchmarked on workstation CPU, not onboard embedded hardware.
- Single-threaded sequential execution without pipelining across multiple CPU cores.

## 17. Reproducibility Information
- System hardware specs logged automatically to `metadata.json`.

## 18. What Decision This Experiment Can Inform
- Informs the computation budget available for onboard SLAM and obstacle avoidance algorithms.
