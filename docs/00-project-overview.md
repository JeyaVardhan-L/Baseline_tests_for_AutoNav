# 00 — Project Overview

## What We Are Building

An autonomous micro-UAV (< 2 kg) capable of GPS/GNSS-denied navigation for the ISRO Robotics Challenge – URSC (IRoC-U).

## The Problem

Traditional UAV navigation relies on GPS/GNSS for position estimation. The IRoC-U competition explicitly prohibits satellite-based navigation, simulating the challenges of planetary exploration (e.g., Mars surface operations) where GPS infrastructure does not exist.

We must navigate using **onboard sensors only**: LiDAR, cameras, and IMU.

## Our Approach

A layered architecture where:

1. **Sensors** (LiDAR, camera, IMU) provide raw environmental data
2. **Sensor fusion** combines complementary sensor modalities
3. **State estimation** determines the UAV's pose (position + orientation)
4. **Local mapping** builds a representation of the surrounding environment
5. **Path planning** generates collision-free trajectories
6. **Mission manager** translates high-level commands into navigation goals
7. **Flight controller** (Pixhawk) handles low-level stabilization and motor control

All autonomous navigation computation runs **onboard** the UAV.

## Current Phase

**Phase 1 — Sensor and Computational Feasibility**

We are answering: *Can we prove, using publicly available sensor datasets, that this architecture is computationally feasible?*

## Team Background

Our team has practical experience with:

- Drone construction and flight
- Pixhawk flight controllers
- Motors, ESCs, power systems
- Raspberry Pi / embedded computing
- Telemetry systems
- Camera systems
- Drone electronics and wiring

The drone hardware is **not** the primary uncertainty. The primary uncertainty is **autonomous navigation without GPS**.

## What This Repository Contains

| Section | Purpose |
|---------|---------|
| `docs/` | Engineering documentation and design decisions |
| `experiments/` | Reproducible experiments with datasets |
| `datasets/` | Dataset documentation and download instructions |
| `benchmarks/` | Hardware performance benchmarks |
| `hardware/` | Hardware candidate evaluation |
| `src/` | Production software (future phases) |
| `results/` | Aggregated experimental results |
| `reports/` | Formal reports for stakeholders |

## Environment

| Item | Value |
|------|-------|
| Machine | NOT RECORDED |
| OS | NOT RECORDED |
| CPU | NOT RECORDED |
| GPU | NOT RECORDED |
| RAM | NOT RECORDED |
| Storage | NOT RECORDED |
| Python | NOT RECORDED |
| Git | NOT RECORDED |
| ROS | NOT INSTALLED (Phase 1 does not require ROS) |
| Docker | NOT RECORDED |

> Run `python tools/collect_sysinfo.py` to populate these values automatically.
