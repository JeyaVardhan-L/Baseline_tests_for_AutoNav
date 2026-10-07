# 04 — Sensor Requirements

## Purpose

This document captures sensor requirements derived from the mission and architecture. **All values are PENDING until experimentally measured.**

## Sensor Modalities Under Consideration

### LiDAR

**Role:** Primary 3D range sensing for obstacle detection, mapping, and geometry-based localization.

| Parameter | Requirement | Source | Status |
|-----------|-------------|--------|--------|
| Range | TBD | To be determined by EXP-01, EXP-06 | ⏳ PENDING |
| Minimum range | TBD | To be determined by EXP-01 | ⏳ PENDING |
| FOV (horizontal) | TBD | Architecture decision | ⏳ PENDING |
| FOV (vertical) | TBD | Architecture decision | ⏳ PENDING |
| Angular resolution | TBD | To be determined by EXP-06 | ⏳ PENDING |
| Update rate | TBD | To be determined by EXP-01, EXP-09 | ⏳ PENDING |
| Points per second | TBD | To be determined by EXP-01 | ⏳ PENDING |
| Accuracy | TBD | To be determined by EXP-03 | ⏳ PENDING |
| Weight | < TBD g (within 2 kg UAV budget) | Competition constraint | ⏳ PENDING |
| Power consumption | < TBD W | Battery budget | ⏳ PENDING |
| Interface | TBD | Onboard computer compatibility | ⏳ PENDING |

### Camera

**Role:** Visual features for odometry, object detection for target identification.

| Parameter | Requirement | Source | Status |
|-----------|-------------|--------|--------|
| Resolution | TBD | To be determined by EXP-02, EXP-04 | ⏳ PENDING |
| Frame rate | TBD | To be determined by EXP-02 | ⏳ PENDING |
| FOV | TBD | Mission requirements | ⏳ PENDING |
| Type | Mono / Stereo / Depth — TBD | Architecture decision | ⏳ PENDING |
| Weight | < TBD g | Competition constraint | ⏳ PENDING |
| Power | < TBD W | Battery budget | ⏳ PENDING |

### IMU

**Role:** High-rate inertial measurements for attitude estimation and sensor fusion.

| Parameter | Requirement | Source | Status |
|-----------|-------------|--------|--------|
| Gyroscope rate | ≥ 200 Hz | Typical flight control requirement | ⚠️ ASSUMED |
| Accelerometer rate | ≥ 200 Hz | Typical flight control requirement | ⚠️ ASSUMED |
| Gyro bias stability | TBD | To be determined | ⏳ PENDING |

> **Note:** The Pixhawk flight controller includes an integrated IMU. Additional IMUs may be used for the navigation stack if needed.

## Key Experiments for Sensor Selection

| Sensor Parameter | Experiment | Status |
|-----------------|-----------|--------|
| LiDAR data rates | EXP-01 | NOT STARTED |
| LiDAR range requirements | EXP-01, EXP-06 | NOT STARTED |
| Camera data rates | EXP-02 | NOT STARTED |
| Minimum sensor suite | EXP-05 | NOT STARTED |

## Weight Budget (Preliminary)

> ⚠️ These are **estimated** allocations, not measured or final values.

| Component | Estimated Weight (g) | Status |
|-----------|---------------------|--------|
| Frame + motors + ESCs + props | ~800-1000 | 🔮 ESTIMATED |
| Battery | ~200-400 | 🔮 ESTIMATED |
| Flight controller (Pixhawk) | ~30-50 | 🔮 ESTIMATED |
| Onboard computer | TBD | ⏳ PENDING |
| LiDAR | TBD | ⏳ PENDING |
| Camera | ~10-50 | 🔮 ESTIMATED |
| Wiring, connectors, misc | ~50-100 | 🔮 ESTIMATED |
| **Total must be** | **< 2000** | Competition constraint |
| **Available for sensors + compute** | **~500-800** | 🔮 ESTIMATED |

> This budget will be refined as we select specific components.
