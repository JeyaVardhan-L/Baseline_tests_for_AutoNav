# Experiment 05: Data Rate + Computational Load

## 1. Objective
Measure and profile the actual wall-clock execution time of each discrete stage in the LiDAR processing pipeline (Read, Decode, Validate, Range Filter, Voxel Downsample, Visualization Prep) across multiple frames to determine computational bottlenecks and evaluate host real-time feasibility.

## 2. Why This Matters
An autonomous UAV cannot pause reality while an onboard computer finishes calculating. If incoming sensor data arrives at 10 Hz (every 100 ms) and the pipeline takes 120 ms to process each frame, sensor queues will overflow, latency will accumulate, and the UAV will navigate using stale state estimates, leading to catastrophic drift or collision.

## 3. Required Knowledge
- **Sensor Period ($\Delta t$)**: The time between consecutive sensor measurements ($T = 1 / f$).
- **Pipeline Latency**: Total elapsed wall-clock time from raw packet arrival to ready representation.
- **Percentiles (P95, P99)**: The value below which 95% or 99% of observations fall. Mean latency hides worst-case spikes.
- **Real-Time Margin**: $T_{\text{margin}} = T_{\text{sensor}} - T_{\text{pipeline}}$. Positive margin means the processor finishes before the next frame arrives.

## 4. Dataset
Supports all registered LiDAR datasets:
- Oxford Newer College (`newer_college`)
- Hilti SLAM 2023 (`hilti_2023`)
- Synthetic benchmark stream (`synthetic`)

## 5. Input
Sequence of timestamped 3D point cloud frames.

## 6. Output
- `stage_latency_breakdown.png`: Bar chart of mean execution time per pipeline stage.
- `pipeline_latency_vs_frame.png`: Frame-by-frame latency trajectory with sensor period threshold.
- `summary.json`: Detailed distributions (mean, median, p95, p99, min, max, std) for each stage.
- `summary.md`: Human-readable summary table.

## 7. Parameters
- `--dataset`: Dataset name (`synthetic`, `newer_college`, `hilti_2023`).
- `--max-frames`: Number of frames to benchmark (default: 50).
- `--voxel-size`: Voxel grid leaf size in meters (default: 0.20 m).
- `--min-range`: Minimum range cutoff (default: 0.5 m).
- `--max-range`: Maximum range cutoff (default: 30.0 m).
- `--sensor-hz`: Nominal sensor publishing rate (default: 10.0 Hz).

## 8. Method
1. Iterate through consecutive frames using high-resolution hardware counters (`time.perf_counter()`).
2. Isolate and measure:
   - `Read`: Buffer memory access.
   - `Decode`: Float32 point array parsing.
   - `Validate`: NaN / Inf point rejection.
   - `Filter`: Distance range bounding.
   - `Downsample`: 3D voxel grid aggregation.
   - `Vis Prep`: Intensity/depth color indexing.
3. Compute summary statistics across all frames.
4. Compare $T_{\text{P95}}$ against $T_{\text{sensor}}$ to determine if the pipeline sustains real-time playback.

## 9. Equations
$$\text{Sensor Period } T_s = \frac{1000}{f_s} \text{ ms}$$
$$T_{\text{pipeline}} = T_{\text{read}} + T_{\text{decode}} + T_{\text{validate}} + T_{\text{filter}} + T_{\text{downsample}} + T_{\text{vis\_prep}}$$
$$\text{Margin } M = T_s - T_{\text{pipeline}}$$
$$\text{Processing FPS} = \frac{1000}{T_{\text{pipeline}}}$$

## 10. Command
```bash
# Run with synthetic test stream
python experiments/05-downsampling/run.py --dataset synthetic --max-frames 50

# Run with Newer College dataset
python experiments/05-downsampling/run.py --dataset newer_college --max-frames 100 --voxel-size 0.20
```

## 11. Expected Terminal Output
```
============================================================
  EXPERIMENT 05 - DATA RATE + COMPUTATIONAL LOAD
  Dataset: synthetic
============================================================

STAGE TIMING BREAKDOWN (DISTRIBUTION ACROSS FRAMES in ms)
----------------------------------------------------------------------------
Stage                Mean     Median   P95      P99      Min      Max      Std     
read                 0.01     0.01     0.02     0.02     0.01     0.02     0.00    
decode               0.02     0.02     0.03     0.04     0.01     0.04     0.01    
validate             0.45     0.42     0.68     0.75     0.35     0.80     0.09    
filter               0.82     0.78     1.15     1.30     0.65     1.42     0.14    
downsample           8.20     7.95     11.10    12.40    6.80     13.10    1.12    
visualization_prep   0.65     0.60     0.90     1.05     0.50     1.15     0.11    
total_pipeline       10.15    9.80     13.80    15.50    8.40     16.20    1.45    
============================================================================

REAL-TIME SYSTEM COMPARISON
----------------------------------------------------------------------------
Sensor Frequency        : 10.0 Hz [ASSUMED] (Target sensor nominal rate)
Sensor Arrival Period   : 100.0 ms [DERIVED] (1000 / Sensor Frequency)
Mean Pipeline Latency   : 10.15 ms [MEASURED]
P95 Pipeline Latency    : 13.80 ms [MEASURED] (Tail latency threshold)
Mean Processing FPS     : 98.5 FPS [DERIVED]
P95 Processing FPS      : 72.5 FPS [DERIVED]

Mean Real-Time Margin   : 89.85 ms [DERIVED]
P95 Real-Time Margin    : 86.20 ms [DERIVED]

REAL-TIME STATUS (P95)  : PASS (CAN KEEP UP) [DERIVED]
  [NOTE]: Evaluated strictly against host machine CPU baseline.
          Does NOT represent onboard UAV embedded compute capability.
============================================================================
```

## 12. Live Visualization
The experiment provides a terminal breakdown and generates two figures in the results directory:
1. Stage latency comparative bar chart
2. Frame-by-frame latency timeline relative to the sensor arrival limit

## 13. Graphs
- **`stage_latency_breakdown.png`**: Answers *"Which pipeline stage consumes the highest percentage of compute time?"*
- **`pipeline_latency_vs_frame.png`**: Answers *"Does processing remain stable across all frames, or are there severe spikes that violate the sensor period?"*

## 14. Metrics
| Metric | Type | Unit | Description |
|---|---|---|---|
| Stage Mean/P95 | `[MEASURED]` | ms | Execution latency per stage |
| Total Pipeline P95 | `[MEASURED]` | ms | 95th percentile total latency |
| Sensor Period | `[DERIVED]` | ms | Inter-frame arrival budget |
| Real-Time Margin | `[DERIVED]` | ms | Spare processing time before next frame |
| Real-Time Status | `[DERIVED]` | text | `PASS` or `CANNOT KEEP UP` |

## 15. Interpretation
- If downsampling consumes >70% of total pipeline time, optimizing the spatial indexing data structure or adjusting leaf size yields the highest return on engineering effort.
- If $T_{\text{P95}} > T_s$, the system fails real-time processing under peak loads, even if the mean latency is within budget.

## 16. Limitations
- Measured on a workstation x86_64 CPU, not an embedded ARM processor (Jetson, Raspberry Pi).
- Does not include OS context switching, hardware interrupts, or competition from odometry/mapping algorithms running concurrently.

## 17. Reproducibility Information
- Random seed fixed where applicable.
- Operating system, Python version, CPU, and RAM captured automatically in `metadata.json`.

## 18. What Decision This Experiment Can Inform
- Determines whether a chosen voxel resolution allows real-time execution.
- Informs whether CPU downsampling is viable or if GPU/SIMD acceleration will be needed on embedded hardware.
