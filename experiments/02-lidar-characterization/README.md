# Experiment 02 — LiDAR Point Cloud Characterization

## 1. Objective
Measure and understand the physical and computational properties of raw LiDAR streams:
- How many 3D points exist per scan?
- What is the raw data rate in MB/s?
- What memory footprint is required per frame?
- What are the observed Euclidean ranges in the environment?
- Can the host CPU process statistics faster than the sensor arrival period?

## 2. Why This Matters
Autonomous drones have finite onboard storage and limited compute power. Before selecting a LiDAR sensor or sizing an onboard flight computer, we must measure the baseline data volume and verify that our data pipeline does not bottleneck or drop scans.

## 3. Required Knowledge
- **Point Cloud**: A collection of 3D coordinates $(x, y, z)$ returned by laser reflections.
- **Euclidean Range**: Straight-line distance from sensor origin: $r = \sqrt{x^2 + y^2 + z^2}$.
- **Throughput vs. Sensor Period**: If a 10 Hz LiDAR produces a frame every 100 ms, processing that frame must take significantly less than 100 ms to leave computational margin for SLAM, mapping, and flight control.

## 4. Dataset
Supports:
- `synthetic` (default zero-download test stream)
- `newer_college` (Ouster OS-1 64-beam)
- `hilti_2023` (Robosense Bpearl)
- `kitti` (Automotive reference baseline)

## 5. Input
Stream of normalized `LiDARFrame` objects containing:
- `points`: $(N, 3)$ float32 array
- `intensity`: $(N,)$ float32 reflectance array
- `timestamp`: Float arrival time in seconds

## 6. Output
- `results/<dataset>/02_lidar_characterization/frame_metrics.csv`
- `results/<dataset>/02_lidar_characterization/summary.json`
- `results/<dataset>/02_lidar_characterization/metadata.json`
- Diagnostic Plots:
  1. `01_point_counts.png`: Point count stability over frame index
  2. `02_range_histogram.png`: Observed Euclidean range distribution
  3. `03_processing_latency.png`: Processing latency vs. 100 ms sensor deadline

## 7. Parameters
- `--dataset`: Target dataset name (`synthetic`, `newer_college`, etc.).
- `--frames`: Number of frames to evaluate (default: 50).
- `--path`: Optional custom filesystem path.

## 8. Method
1. Read frames sequentially via the dataset adapter.
2. Measure Euclidean point distances, spatial bounding box, and valid point counts.
3. Measure wall-clock latency using `time.perf_counter()`.
4. Derive throughput metrics ($MB/s$, $GiB/hour$) and margin against the sensor period.
5. Export structured CSV, JSON, and publication figures.

## 9. Equations
$$\text{Data Rate (bytes/sec)} = \text{Average Frame Size (bytes)} \times \text{Frame Rate (Hz)}$$

$$\text{Data Rate (MB/sec)} = \frac{\text{Data Rate (bytes/sec)}}{1{,}000{,}000}$$

$$\text{Available Margin (ms)} = \text{Sensor Period (ms)} - \text{Pipeline Processing Latency (ms)}$$

## 10. Command
```bash
# Run immediate benchmark using synthetic stream
python experiments/02-lidar-characterization/run.py --dataset synthetic --frames 50

# Run on downloaded Newer College sequence
python experiments/02-lidar-characterization/run.py --dataset newer_college --path datasets/newer-college --frames 100
```

## 11. Expected Terminal Output
```text
============================================================
AUTO NAV BASELINE
EXPERIMENT 02 - LIDAR CHARACTERIZATION
[Dataset: synthetic]
============================================================
------------------------------------------------------------
SENSOR MEASUREMENTS
------------------------------------------------------------
Frames Analyzed           : 50 frames          [MEASURED]
Average Points Per Frame  : 65,536 pts/frame   [MEASURED]
Points Per Second         : 655,360 pts/s      [DERIVED]
Average Frame Size        : 1.25 MB/frame      [MEASURED]
Observed Raw Data Rate    : 13.11 MB/s         [DERIVED]
Projected Storage Rate    : 43.95 GiB/hour     [DERIVED]
Mean Point Distance       : 6.0 m              [MEASURED]
P95 Point Distance        : 10.77 m            [MEASURED]
------------------------------------------------------------
HOST PROCESSING LATENCY
------------------------------------------------------------
Mean Latency              : 17.87 ms           [MEASURED]
P95 Latency               : 19.35 ms           [MEASURED]
Throughput Fps            : 56.0 FPS           [DERIVED]
------------------------------------------------------------
REAL-TIME REPLAY CHECK
------------------------------------------------------------
Target Sensor Period      : 100.0 ms           [ASSUMED]
Host Pipeline Time        : 17.87 ms           [MEASURED]
Processing Margin         : 82.13 ms           [DERIVED]
Status: PASS (CAN KEEP UP)
============================================================
```

## 12. Interpretation
- **Available Margin**: Positive margin indicates that the processor can keep up with the sensor stream without accumulating an in-memory queue.
- **P95 Latency**: Evaluates tail latencies caused by OS context switching or garbage collection.

## 13. Limitations
Does not benchmark point cloud registration (ICP/NDT) or SLAM pose optimization; measures only statistical characterization and array ingestion.

## 14. What Decision This Informs
Determines the raw I/O throughput and buffer allocation that the UAV autonomy stack must allocate for raw LiDAR packets.
