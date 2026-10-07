# 05 — Computing Requirements

## Purpose

Determine the onboard computing requirements for the autonomous navigation stack. **All values are PENDING until experimentally measured.**

## Computational Tasks

| Task | Estimated Rate | Compute Intensity | Status |
|------|---------------|-------------------|--------|
| IMU integration | 200-1000 Hz | Low | ⚠️ ASSUMED |
| LiDAR preprocessing | 10 Hz | Medium-High | ⏳ PENDING (EXP-01) |
| LiDAR odometry | 10 Hz | High | ⏳ PENDING (EXP-03) |
| Visual odometry | 15-30 Hz | Medium-High | ⏳ PENDING (EXP-04) |
| Sensor fusion | 10-100 Hz | Medium | ⏳ PENDING (EXP-05) |
| Local mapping | 1-10 Hz | High | ⏳ PENDING (EXP-06) |
| Path planning | 1-5 Hz | Medium | ⏳ PENDING (EXP-08) |
| Mission management | < 1 Hz | Low | ⚠️ ASSUMED |

## Hardware Requirements (TO BE DETERMINED)

| Requirement | Value | Source | Status |
|-------------|-------|--------|--------|
| CPU cores | TBD | EXP-09 | ⏳ PENDING |
| CPU clock speed | TBD | EXP-09 | ⏳ PENDING |
| GPU | TBD (may not be required) | EXP-09 | ⏳ PENDING |
| RAM | TBD | EXP-01, EXP-09 | ⏳ PENDING |
| Storage | TBD | EXP-01 | ⏳ PENDING |
| Power consumption | TBD (must fit battery budget) | EXP-09 | ⏳ PENDING |
| Weight | TBD (must fit 2 kg UAV budget) | Competition | ⏳ PENDING |
| Thermal | TBD (passive cooling preferred) | Design constraint | ⏳ PENDING |

## Experiments That Feed This Document

| Experiment | What It Tells Us |
|-----------|-----------------|
| EXP-01 | Data rates, memory needed for LiDAR processing |
| EXP-02 | Data rates for camera processing |
| EXP-03 | CPU/GPU needed for LiDAR odometry |
| EXP-04 | CPU/GPU needed for visual odometry |
| EXP-05 | Combined processing requirements |
| EXP-09 | Full pipeline benchmark on candidate hardware |
| EXP-10 | End-to-end latency requirements |

## Decision

**FINAL COMPUTING SELECTION: PENDING EXPERIMENTAL RESULTS**

See: [`hardware/candidate-compute.md`](../hardware/candidate-compute.md)
