# 03 — The Navigation Problem

## Problem Statement

Navigate a UAV autonomously through an unknown environment **without GPS/GNSS** — using only onboard sensors and computation.

## Why This Is Hard

### 1. No Global Position Reference

GPS provides an absolute position fix (~2-5 m accuracy) at ~1-10 Hz. Without it, the UAV must estimate its own position relative to a local reference frame. This is the **localization** problem.

### 2. Drift Accumulation

Odometry-based methods (integrating sensor measurements over time) accumulate **drift**. Without corrections, position error grows unboundedly. Over a 10-minute mission, even small angular errors compound into large position offsets.

### 3. Computational Constraints

Unlike a self-driving car, a UAV has severe constraints:

| Constraint | Car | UAV (< 2 kg) |
|-----------|-----|---------------|
| Power budget | ~kW available | ~10-50 W total |
| Compute weight | Not a concern | Every gram matters |
| Cooling | Active cooling available | Limited airflow |
| Failure mode | Pull over | **Crash** |

### 4. Real-Time Requirements

The navigation stack must produce outputs **fast enough** for stable flight:

- IMU integration: ~200-1000 Hz
- Attitude control: ~100-400 Hz
- Position control: ~10-50 Hz
- LiDAR processing: ~10 Hz
- Path planning: ~1-10 Hz

If processing takes too long, the UAV flies blind.

### 5. Sensor Limitations

| Sensor | Strengths | Weaknesses |
|--------|-----------|------------|
| LiDAR | Precise range, geometry | Weight, power, cost, limited FOV (some) |
| Camera | Lightweight, cheap, rich information | Scale ambiguity, lighting sensitivity |
| IMU | Very high rate, no external dependency | Drift (gyro bias, accelerometer noise) |

No single sensor is sufficient. Fusion is required.

## What We Need to Demonstrate

Before we can claim this architecture is feasible, we must show:

1. **Data feasibility:** We can handle the data rates from chosen sensors
2. **Algorithmic feasibility:** Navigation algorithms can produce usable outputs
3. **Computational feasibility:** The full pipeline can run in real-time on hardware that fits on a UAV
4. **Accuracy feasibility:** Position estimates are accurate enough for the mission
5. **Robustness feasibility:** The system degrades gracefully under sensor failure

## Relevant Research Areas

- Simultaneous Localization and Mapping (SLAM)
- Visual-Inertial Odometry (VIO)
- LiDAR-Inertial Odometry (LIO)
- Multi-sensor fusion
- Occupancy grid mapping
- Motion planning under uncertainty
- Embedded real-time systems

## Key Metrics

| Metric | Why It Matters |
|--------|---------------|
| Position drift (m / 100 m) | Determines if we can complete the mission |
| Processing latency (ms) | Determines if control loop is stable |
| CPU/GPU utilization (%) | Determines hardware requirements |
| Memory usage (MB) | Determines RAM requirements |
| Power consumption (W) | Determines battery requirements |
| Data rate (MB/s) | Determines bandwidth and storage needs |

All values above are **PENDING measurement** in Phase 1 experiments.
