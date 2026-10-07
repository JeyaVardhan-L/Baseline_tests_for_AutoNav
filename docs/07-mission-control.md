# 07 — Mission Control

## Concept

The mission control system bridges the gap between human intent and autonomous execution.

**The operator specifies WHAT mission to perform.**
**The autonomy system decides HOW to accomplish it.**

## Control Hierarchy

```
Human / Operator
      │
      ▼
Mission Command (e.g., SEARCH <area>)
      │
      ▼
Mission Manager (onboard)
      │  - interprets command
      │  - generates sub-goals
      │  - monitors progress
      │  - handles contingencies
      │
      ▼
Planner (onboard)
      │  - generates waypoints
      │  - avoids obstacles
      │  - optimizes trajectory
      │
      ▼
Trajectory / Setpoints
      │
      ▼
Pixhawk / PX4 / ArduPilot
      │  - attitude control
      │  - motor mixing
      │  - safety functions
      │
      ▼
Motors
```

## Example Mission Commands

| Command | Description |
|---------|-------------|
| `TAKEOFF` | Ascend to specified altitude |
| `SEARCH <area>` | Autonomously survey an area looking for targets |
| `SURVEY <area>` | Detailed survey of a specific region |
| `GOTO <x,y,z>` | Navigate to a local coordinate |
| `RETURN` | Navigate back to base station |
| `LAND` | Execute autonomous landing sequence |
| `ABORT` | Emergency — safe landing immediately |
| `STATUS` | Report current state |

> These are **conceptual examples only**. The actual command interface will be defined during implementation.

## Low-Level vs High-Level Control

| Level | Responsibility | Rate | Component |
|-------|---------------|------|-----------|
| **High** | Mission goals | < 1 Hz | Mission Manager |
| **Mid** | Path/trajectory | 1-10 Hz | Planner |
| **Low** | Attitude/motors | 100-400 Hz | Pixhawk |

**We do NOT implement low-level flight control.** That is handled by the Pixhawk firmware (PX4 or ArduPilot).

## Implementation Status

**NOT IMPLEMENTED.** This is documented for architectural clarity. Mission Manager implementation is planned for Phase 2+.
