# Experiment 10: Preparing for Navigation (Architecture & Data Flow)

## 1. Objective
Establish and verify the conceptual architecture, data contracts, and transformation pipeline connecting raw sensor data to eventual autonomous UAV navigation:
$$\text{Sensor Data} \rightarrow \text{State Estimation} \rightarrow \text{Local Mapping} \rightarrow \text{Free-Space Detection} \rightarrow \text{Path Planning} \rightarrow \text{Flight Control}$$

## 2. Why This Matters
Building an autonomous UAV without explicit architectural boundaries leads to monolithic coupling where planning bugs crash the flight controller or sensor delays cause aerodynamic instability. Clear separation of concerns guarantees that even if higher-level vision or planning crashes or lags, the low-level flight controller continues to stabilize altitude and attitude safely.

## 3. Required Knowledge
- **High-Level Mission Control**: Strategic directive layer (e.g. "Survey designated polygon at 10m altitude"). Decides *where* to go.
- **Autonomous Navigation Layer**: Algorithmic intelligence running on the companion computer (e.g. Jetson/x86). Decides *how* to navigate safely without colliding.
- **Low-Level Flight Control**: Dedicated real-time microcontroller (e.g., PX4 on STM32) running fast rate dampers (250 - 1000 Hz) to keep the drone upright in the air.
- **Setpoints**: Position, velocity, acceleration, or attitude targets sent from the companion computer to the autopilot via MAVLink or microXRCE-DDS.

## 4. Dataset
Conceptual architectural verification and interface contract analysis.

## 5. Input
High-level mission objective and multi-modal sensor inputs.

## 6. Output
- `figures/navigation_architecture_hierarchy.png`: Three-tier architectural block diagram showing boundaries and protocols.
- `summary.json`: Formal interface specifications and expected message loop frequencies.
- `summary.md`: Standardized system architecture report.

## 7. Parameters
- `--verify-contracts`: Validates interface schema compliance.

## 8. Method
1. Trace the transformation of physical signals into spatial states and motor commands.
2. Formally demarcate the 3 tiers:
   - Tier 1: Mission Control
   - Tier 2: Autonomous Navigation
   - Tier 3: Low-Level Flight Control
3. Document message formats (e.g. `SET_POSITION_TARGET_LOCAL_NED`) and required publish frequencies.
4. Export architectural diagrams.

## 9. Equations
$$\mathbf{p}_{\text{error}} = \mathbf{p}_{\text{target}}(t) - \hat{\mathbf{p}}(t)$$
$$\mathbf{v}_{\text{command}} = \mathbf{K}_p \mathbf{p}_{\text{error}} + \dot{\mathbf{p}}_{\text{target}}$$
$$\boldsymbol{\tau}_{\text{motor}} = \mathbf{PID}_{\text{rate}}(\boldsymbol{\omega}_{\text{target}} - \boldsymbol{\omega}_{\text{measured}})$$

## 10. Command
```bash
python experiments/10-sensor-fusion-preparation/run.py
```

## 11. Expected Terminal Output
```
============================================================
  EXPERIMENT 10 - PREPARING FOR NAVIGATION
  Conceptual Architecture & Interface Contracts
============================================================

THREE-TIER SYSTEM ARCHITECTURE BOUNDARIES
------------------------------------------------------------
    +------------------------------------------------------------------------+
    | 1. HIGH-LEVEL MISSION CONTROL (Ground Station / Mission Supervisor)     |
    |    "Search this designated 50m x 50m sector at 10m altitude"            |
    +------------------------------------------------------------------------+
                                      |
                                      v
    +------------------------------------------------------------------------+
    | 2. AUTONOMOUS NAVIGATION (Onboard Companion Computer / GPU)             |
    |    State Estimation -> Local Mapping -> Free Space -> Path Planning    |
    |    Outputs: Target Position / Velocity / Yaw Rate Setpoints (e.g. 20Hz)|
    +------------------------------------------------------------------------+
                                      | (MAVLink / microXRCE-DDS)
                                      v
    +------------------------------------------------------------------------+
    | 3. LOW-LEVEL FLIGHT CONTROL (Autopilot: PX4 / ArduPilot / Micro)       |
    |    Attitude Loops (250-1000 Hz) | Rate Dampers | Motor ESC Signals     |
    +------------------------------------------------------------------------+
============================================================
```

## 12. Live Visualization
Outputs `figures/navigation_architecture_hierarchy.png` illustrating the data flow across the 3 tiers.

## 13. Graphs
- **`navigation_architecture_hierarchy.png`**: Answers *"What are the exact boundaries between mission control, autonomous navigation, and low-level stabilization?"*

## 14. Metrics
| Metric | Type | Unit | Description |
|---|---|---|---|
| Autopilot Loop Rate | `[SPECIFIED]` | Hz | Inner attitude feedback rate (250 - 1000 Hz) |
| Companion Guidance Rate | `[SPECIFIED]` | Hz | Setpoint transmission rate (10 - 50 Hz) |
| Protocol Interface | `[SPECIFIED]` | standard | MAVLink NED / microXRCE-DDS |

## 15. Interpretation
- The companion computer must NEVER attempt direct motor PWM mixing over USB/serial, as operating system jitter causes immediate aerodynamic loss of control.
- Autonomy software outputs trajectory setpoints; the flight controller translates setpoints into actuator forces.

## 16. Limitations
- Defines software interfaces; does not execute physical flight tests (reserved for subsequent phases).

## 17. Reproducibility Information
- All architectural specifications conform to standard robotics middleware conventions (ROS 2 / MAVLink).

## 18. What Decision This Experiment Can Inform
- Defines hardware communication bus requirements (UART / Ethernet / CAN) between companion computer and flight controller.
