# Assumptions Register

Every assumption in this project is tracked here. Assumptions are NOT facts. They must be validated, refuted, or accepted with evidence.

## Status Categories

| Status | Meaning |
|--------|---------|
| **UNPROVEN** | Not yet tested |
| **VALIDATED** | Confirmed by experiment or evidence |
| **REFUTED** | Disproven by experiment or evidence |
| **ACCEPTED** | Acknowledged as a reasonable working assumption |
| **SUPERSEDED** | Replaced by a new assumption |

---

## ASM-001 — Onboard Computation Required

| Field | Value |
|-------|-------|
| **Description** | Autonomous navigation requires onboard computation (not ground-station computation). |
| **Status** | ACCEPTED |
| **Source** | Competition rules (IRoC-U 2026) + architectural analysis |
| **Impact** | Drives onboard computer selection, weight/power budget |
| **Validation** | Verify against official rules for our competition year |
| **Related** | DEC-001 |

## ASM-002 — Low-Cost LiDAR May Be Sufficient

| Field | Value |
|-------|-------|
| **Description** | A low-cost LiDAR (e.g., < ₹50,000) may provide sufficient range, resolution, and update rate for local navigation in the competition environment. |
| **Status** | UNPROVEN |
| **Source** | Team hypothesis |
| **Impact** | Budget, sensor selection |
| **Validation** | EXP-01 (data characterization), EXP-03 (odometry performance) |

## ASM-003 — Multi-Sensor Fusion Outperforms Single Sensor

| Field | Value |
|-------|-------|
| **Description** | LiDAR + camera + IMU fusion provides better navigation performance than any single sensor alone. |
| **Status** | UNPROVEN |
| **Source** | Literature consensus (to be verified experimentally) |
| **Impact** | Sensor suite selection, complexity |
| **Validation** | EXP-05 (fusion experiments) |

## ASM-004 — IRoC-U Rules Consistent Across Years

| Field | Value |
|-------|-------|
| **Description** | The fundamental rules (GPS denial, < 2 kg, autonomous) from IRoC-U 2026 will remain broadly similar for our competition year. |
| **Status** | UNPROVEN |
| **Source** | Assumption based on competition theme continuity |
| **Impact** | All design decisions based on competition constraints |
| **Validation** | Official rules publication for our year |

## ASM-005 — 10 Hz LiDAR Update Rate Sufficient

| Field | Value |
|-------|-------|
| **Description** | A 10 Hz LiDAR update rate is sufficient for UAV navigation at typical flight speeds (1-5 m/s). |
| **Status** | UNPROVEN |
| **Source** | Common in literature; used by KITTI dataset (Velodyne HDL-64E at 10 Hz) |
| **Impact** | LiDAR selection, processing pipeline design |
| **Validation** | EXP-03 (odometry), EXP-10 (latency) |

## ASM-006 — Embedded Linux is the Onboard OS

| Field | Value |
|-------|-------|
| **Description** | The onboard computer will run a Linux-based OS (e.g., Ubuntu, Jetson Linux). |
| **Status** | ACCEPTED |
| **Source** | ROS 2, most robotics tools, and LiDAR drivers primarily support Linux |
| **Impact** | Software stack, driver compatibility |
| **Validation** | Confirmed when onboard computer is selected |

---

*New assumptions should be appended below with the next sequential ID (ASM-007, etc.)*
