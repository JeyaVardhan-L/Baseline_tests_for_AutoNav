# 09 — Development Roadmap

## Phase Overview

| Phase | Name | Goal | Status |
|-------|------|------|--------|
| 0 | Requirements & Mission Definition | Define what we're building and why | COMPLETE |
| **1** | **Sensor & Computational Feasibility** | **Prove architecture is feasible using datasets** | **IN PROGRESS** |
| 2 | Navigation Algorithms | Implement and benchmark navigation stack | NOT STARTED |
| 3 | Simulation | Validate in simulated environment | NOT STARTED |
| 4 | Onboard Computing Selection | Select and procure hardware | NOT STARTED |
| 5 | Hardware Integration | Integrate sensors + compute + airframe | NOT STARTED |
| 6 | Ground Testing | Test navigation on static/moving platform | NOT STARTED |
| 7 | Flight Testing | Test navigation on actual UAV | NOT STARTED |
| 8 | Mission Validation | Full mission rehearsal | NOT STARTED |
| 9 | Competition Preparation | Final tuning and documentation | NOT STARTED |

## Phase 1 — Detailed Plan

### Objective

Answer: *"Can our proposed LiDAR/camera/IMU architecture run in real-time on hardware that fits on a < 2 kg UAV?"*

### Experiments

| Order | Experiment | Dependency | Status |
|-------|-----------|-----------|--------|
| 1 | EXP-01: LiDAR Characterization | None | NOT STARTED |
| 2 | EXP-02: Camera Characterization | None | NOT STARTED |
| 3 | EXP-03: LiDAR Odometry | EXP-01 | NOT STARTED |
| 4 | EXP-04: Visual Odometry | EXP-02 | NOT STARTED |
| 5 | EXP-05: LiDAR-Camera Fusion | EXP-03, EXP-04 | NOT STARTED |
| 6 | EXP-06: Local Mapping | EXP-03 | NOT STARTED |
| 7 | EXP-07: Localization | EXP-05, EXP-06 | NOT STARTED |
| 8 | EXP-08: Path Planning | EXP-06 | NOT STARTED |
| 9 | EXP-09: Compute Benchmark | EXP-03 through EXP-08 | NOT STARTED |
| 10 | EXP-10: End-to-End Latency | EXP-09 | NOT STARTED |

### Phase 1 Deliverable

A report containing:

1. Measured data rates for LiDAR and camera
2. Measured computational requirements for each pipeline stage
3. Measured end-to-end latency
4. Hardware specifications derived from measurements
5. Specific hardware purchase recommendation with justification

## Phase 2 — Preview

Implement and benchmark the core navigation algorithms:

- LiDAR odometry (ICP / LOAM / KISS-ICP)
- Visual odometry (feature-based or direct)
- Sensor fusion (EKF or factor graph)
- Local mapping
- Path planning

> Phase 2 is NOT started. This preview is for planning purposes only.

## Phase Dependencies

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4
                                                    │
                                                    ▼
                                            Phase 5 ──► Phase 6 ──► Phase 7 ──► Phase 8 ──► Phase 9
```

Phases 0-3 require no hardware purchases.
Phase 4 produces the hardware purchase decision.
Phases 5+ require hardware.
