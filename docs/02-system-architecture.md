# 02 — System Architecture

## Design Principle

**All autonomous navigation computation runs onboard the UAV.**

The ground station provides mission-level commands and monitoring only. The UAV must be able to complete its mission even if ground communication is interrupted.

## Architecture Diagram

```
                         GROUND STATION
                              │
                    mission commands (RF)
                    telemetry / status
                              │
                              ▼
                 ┌────────────────────────┐
                 │         UAV            │
                 │                        │
  LiDAR ───────►│                        │
  Camera ──────►│   ONBOARD COMPUTATION  │
  IMU ─────────►│         │              │
                 │         ▼              │
                 │   Sensor Fusion        │
                 │         │              │
                 │         ▼              │
                 │   Pose Estimation      │
                 │         │              │
                 │         ▼              │
                 │   Local Mapping        │
                 │         │              │
                 │         ▼              │
                 │   Path Planning        │
                 │         │              │
                 │         ▼              │
                 │   Mission Manager      │
                 │         │              │
                 │         ▼              │
                 │   Pixhawk / PX4        │
                 │         │              │
                 │       Motors           │
                 └────────────────────────┘
```

## Layer Responsibilities

### 1. Sensor Layer

| Sensor | Purpose | Data Type |
|--------|---------|-----------|
| LiDAR | 3D environment geometry | Point clouds |
| Camera | Visual features, object detection | Images |
| IMU | High-rate attitude and acceleration | Inertial measurements |

### 2. Sensor Fusion

Combines complementary sensor data to produce a unified state estimate. Approaches to evaluate:

- Extended Kalman Filter (EKF)
- Unscented Kalman Filter (UKF)
- Factor graph optimization

### 3. Pose Estimation

Determines the UAV's 6-DoF pose (position + orientation) in a local reference frame.

Approaches to evaluate:

- LiDAR odometry (e.g., ICP, LOAM variants)
- Visual odometry (feature-based, direct methods)
- Visual-inertial odometry (VIO)
- LiDAR-inertial odometry (LIO)

### 4. Local Mapping

Builds a representation of the surrounding environment for obstacle avoidance and planning.

Approaches to evaluate:

- Occupancy grids (2D/3D)
- Octomap
- Point-cloud based maps
- Elevation maps

### 5. Path Planning

Generates collision-free trajectories from current position to goal.

Approaches to evaluate:

- A* / D* variants
- RRT / RRT*
- Potential fields
- Trajectory optimization

### 6. Mission Manager

Translates high-level mission commands into navigation goals.

```
Operator command:  SEARCH <area>
                       │
                       ▼
Mission Manager:   Generate search pattern (e.g., lawnmower)
                       │
                       ▼
Planner:           Compute waypoints and trajectories
                       │
                       ▼
Flight Controller: Execute trajectory
```

### 7. Flight Controller (Pixhawk / PX4 / ArduPilot)

Handles:

- Attitude stabilization
- Motor mixing
- Safety functions (failsafe, geofence)
- Low-level control loops (PID)

**This layer is NOT developed by us.** We use existing flight-controller firmware.

## Communication Architecture

```
Ground Station ◄──── RF Link ────► UAV Mission Manager
     │                                    │
     ▼                                    ▼
Mission commands                   Telemetry / status
(TAKEOFF, SEARCH,                  (position, battery,
 RETURN, ABORT, etc.)              mission progress, etc.)
```

**What is NOT sent over the link:**

- Raw sensor data (too high bandwidth)
- Navigation computation (runs onboard)
- Control loop data (stays on Pixhawk)

**What IS sent:**

- Mission commands (low bandwidth)
- Status telemetry (low bandwidth)
- Compressed summaries / key images (if permitted and bandwidth allows)

## Interface Between Layers

This architecture creates clear interfaces:

```
Sensor → Fusion:          Raw sensor readings
Fusion → Pose:            Fused sensor state
Pose → Mapping:           Estimated pose + registered point clouds
Mapping → Planning:       Occupancy / obstacle representation
Planning → Mission Mgr:   Planned trajectory / waypoints
Mission Mgr → FC:         Setpoints (position, velocity, attitude)
FC → Motors:              PWM signals
```

## Technology Candidates

| Layer | Candidates | Decision |
|-------|-----------|----------|
| Sensor Fusion | EKF, UKF, factor graph | PENDING |
| LiDAR Odometry | ICP, LOAM, KISS-ICP | PENDING |
| Visual Odometry | ORB-SLAM3, VINS-Fusion | PENDING |
| Mapping | Octomap, grid-based | PENDING |
| Planning | RRT*, A*, potential fields | PENDING |
| Flight Controller | PX4, ArduPilot | PENDING |
| Onboard Computer | TBD (Phase 4 decision) | PENDING |
| LiDAR | TBD (Phase 4 decision) | PENDING |

> All technology selections are **PENDING** experimental results from Phase 1.
