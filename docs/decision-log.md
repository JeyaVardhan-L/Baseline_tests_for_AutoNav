# Decision Log

All significant design and engineering decisions are recorded here with context, rationale, and revisit conditions.

---

## DEC-001 — Navigation Computation Architecture

| Field | Value |
|-------|-------|
| **Date** | 2026-10-07 |
| **Status** | ACCEPTED |
| **Decision** | Navigation computation shall be designed as onboard computation rather than depending on ground-station computation. |
| **Context** | The UAV must navigate autonomously in a GPS-denied environment. The competition may restrict or prohibit telemetry during the mission. Even if communication is available, relying on it for navigation creates a single point of failure. |
| **Options considered** | 1. All computation onboard the UAV. 2. Offload heavy computation to the ground station via RF link. 3. Hybrid — critical path onboard, optional augmentation from ground. |
| **Evidence** | IRoC-U 2026 rules state "No telemetry or remote piloting during the mission." Latency over RF links would introduce unacceptable delays for real-time control. |
| **Reason** | Autonomous navigation must remain operational without ground computation. Competition rules prohibit remote piloting. Communication link failure must not cause navigation failure. |
| **Consequences** | The onboard computer must be powerful enough to run the full navigation stack. This increases weight and power requirements. |
| **Revisit condition** | If competition rules explicitly permit ground-station computation for navigation, this decision should be re-evaluated. |

---

## DEC-002 — Phase 1 Uses Public Datasets

| Field | Value |
|-------|-------|
| **Date** | 2026-10-07 |
| **Status** | ACCEPTED |
| **Decision** | Phase 1 experiments shall use publicly available sensor datasets rather than collecting our own data. |
| **Context** | We do not yet have a LiDAR sensor or finalized hardware. We need to understand sensor data characteristics before purchasing anything. |
| **Options considered** | 1. Purchase a LiDAR first and collect our own data. 2. Use public datasets to characterize data before purchasing. 3. Use only simulation data. |
| **Evidence** | Multiple high-quality public LiDAR datasets exist (KITTI, Newer College, MulRan, etc.) with known sensor specifications and ground truth. |
| **Reason** | Public datasets allow us to study real sensor data at zero cost and produce evidence to justify future hardware purchases. |
| **Consequences** | Our experiments will reflect the characteristics of the specific sensors used in those datasets, not necessarily the exact sensor we will purchase. Results must be interpreted accordingly. |
| **Revisit condition** | When we have our own hardware and can collect data. |

---

## DEC-003 — Python as Primary Phase 1 Language

| Field | Value |
|-------|-------|
| **Date** | 2026-10-07 |
| **Status** | ACCEPTED |
| **Decision** | Phase 1 experiments shall be implemented in Python. |
| **Context** | Phase 1 is about data analysis, characterization, and feasibility — not real-time performance. |
| **Options considered** | 1. Python (rapid development, rich ecosystem). 2. C++ (performance, ROS integration). 3. MATLAB (familiar to some team members, but proprietary). |
| **Evidence** | Python with NumPy/Matplotlib provides fast development for data analysis tasks. Open3D provides Python bindings for point-cloud processing. |
| **Reason** | Development speed is more important than execution speed in Phase 1. The team is familiar with Python. All tools are free and open-source. |
| **Consequences** | Performance measurements from Phase 1 Python code do not directly represent the performance of an optimized C++ navigation stack. Phase 2+ may require C++ for real-time components. |
| **Revisit condition** | If Python performance is insufficient even for offline analysis, or when transitioning to real-time implementation. |

---

*New decisions should be appended below with the next sequential ID (DEC-004, etc.)*
