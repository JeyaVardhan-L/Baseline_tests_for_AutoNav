# 10 — Risk Register

## Purpose

Track identified risks, their likelihood, impact, and mitigation strategies.

## Risk Matrix

| Likelihood → | Low | Medium | High |
|:-------------|:----|:-------|:-----|
| **High Impact** | Monitor | Mitigate | Mitigate urgently |
| **Medium Impact** | Accept | Monitor | Mitigate |
| **Low Impact** | Accept | Accept | Monitor |

## Identified Risks

### RSK-001 — Insufficient onboard compute power

| Field | Value |
|-------|-------|
| **Description** | The navigation stack may require more computation than available on UAV-class hardware |
| **Likelihood** | Medium |
| **Impact** | High |
| **Category** | Technical |
| **Mitigation** | Phase 1 experiments will measure exact requirements before hardware selection. Algorithm optimization, downsampling, and GPU acceleration are fallback options. |
| **Status** | OPEN |
| **Owner** | Team |

### RSK-002 — Weight budget exceeded

| Field | Value |
|-------|-------|
| **Description** | Sensors + compute + structure may exceed 2 kg limit |
| **Likelihood** | Medium |
| **Impact** | High |
| **Category** | Design |
| **Mitigation** | Track weight budget continuously. Evaluate lighter sensor alternatives. Reduce sensor count if needed. |
| **Status** | OPEN |

### RSK-003 — LiDAR too expensive or unavailable

| Field | Value |
|-------|-------|
| **Description** | Suitable LiDAR may exceed budget or have long lead times |
| **Likelihood** | Medium |
| **Impact** | Medium |
| **Category** | Procurement |
| **Mitigation** | Evaluate multiple price tiers. Design architecture to potentially work without LiDAR (camera+IMU only as fallback). |
| **Status** | OPEN |

### RSK-004 — Odometry drift exceeds mission tolerance

| Field | Value |
|-------|-------|
| **Description** | Position estimate drift may accumulate beyond acceptable levels during mission |
| **Likelihood** | Medium |
| **Impact** | High |
| **Category** | Technical |
| **Mitigation** | Loop closure, multi-sensor fusion, landmark-based correction. Measure drift rates in Phase 1/2 experiments. |
| **Status** | OPEN |

### RSK-005 — Competition rules change

| Field | Value |
|-------|-------|
| **Description** | Rules for our competition year may differ from IRoC-U 2026 |
| **Likelihood** | Medium |
| **Impact** | Medium |
| **Category** | External |
| **Mitigation** | Design modular architecture. Document all rule-dependent assumptions. Re-evaluate when official rules are published. |
| **Status** | OPEN |

### RSK-006 — Power budget insufficient

| Field | Value |
|-------|-------|
| **Description** | Onboard compute power consumption may reduce flight time below mission requirements |
| **Likelihood** | Medium |
| **Impact** | High |
| **Category** | Design |
| **Mitigation** | Measure power consumption during compute benchmarks. Select power-efficient hardware. Optimize algorithms. |
| **Status** | OPEN |

## Risk Review Schedule

Risks should be reviewed:

- After each experiment completion
- At each phase transition
- When competition rules are published
- When hardware candidates are identified
