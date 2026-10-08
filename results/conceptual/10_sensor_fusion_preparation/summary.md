# EXP-10: Navigation Architecture & Data Flow Preparation

## Measured & Derived Metrics

| Metric | Value |
|---|---|
| Tier 1 Function | High-Level Strategic Mission Control [SPECIFIED] |
| Tier 2 Function | Autonomous Navigation & Trajectory Generation [SPECIFIED] |
| Tier 3 Function | Low-Level Flight Stabilization & Motor Mixing [SPECIFIED] |
| Companion-to-Autopilot Interface | MAVLink NED Setpoints (10-50 Hz) [SPECIFIED] |
| Flight Controller Loop Rate | 250 - 1000 Hz [SPECIFIED] |

## Key Observations & Conclusions

- Strict architectural boundary separates autonomous navigation (Tier 2) from attitude control (Tier 3).
- The flight controller remains unconditionally responsible for aerodynamic stabilization, failsafes, and motor mixing.
- The autonomous navigation computer provides target position, velocity, and yaw rate setpoints without bypassing inner-loop rate dampers.
