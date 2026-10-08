# From Sensing to Navigation: The Autonomy Data Pipeline

This document explains the end-to-end data flow that transforms raw photons and accelerations into physical UAV flight.

---

## 1. The Transformation Chain

$$\text{Raw Sensors} \longrightarrow \text{State Estimation} \longrightarrow \text{Mapping} \longrightarrow \text{Planning} \longrightarrow \text{Control} \longrightarrow \text{Actuators}$$

```
+------------------------------------------------------------------------+
| 0. SENSORS (Hardware)                                                  |
|    - LiDAR emits laser pulses -> measures time-of-flight               |
|    - Camera sensors expose CMOS arrays -> output RGB/Depth images      |
|    - MEMS IMU measures proof-mass deflection -> linear accel & gyro    |
+------------------------------------------------------------------------+
                                  |
                                  v
+------------------------------------------------------------------------+
| 1. STATE ESTIMATION & LOCALIZATION (Odometry / EKF / Factor Graph)     |
|    - Integrates high-rate IMU between scans                            |
|    - Aligns consecutive LiDAR scans (scan-to-map ICP)                  |
|    - Produces estimated 6-DoF vehicle pose [x, y, z, roll, pitch, yaw] |
+------------------------------------------------------------------------+
                                  |
                                  v
+------------------------------------------------------------------------+
| 2. LOCAL MAPPING & FREE-SPACE DETECTION (Voxel Grid / Costmap)         |
|    - Transforms LiDAR points into global world frame                   |
|    - Updates 3D occupancy grid (Occupied, Free, or Unknown voxels)    |
|    - Identifies obstacles and applies clearance inflation buffers      |
+------------------------------------------------------------------------+
                                  |
                                  v
+------------------------------------------------------------------------+
| 3. MOTION PLANNING (Global & Local Trajectory Generation)              |
|    - Global planner: Graph search (A* / Dijkstra) over waypoints       |
|    - Local planner: Generates kinodynamically feasible B-spline curves |
|    - Guarantees obstacle clearance and velocity/acceleration limits    |
+------------------------------------------------------------------------+
                                  |
                                  v
+------------------------------------------------------------------------+
| 4. GUIDANCE & TRAJECTORY TRACKING                                      |
|    - Samples the spline curve at 20 - 50 Hz                            |
|    - Computes desired position, velocity, and acceleration setpoints   |
|    - Transmits setpoints over MAVLink to the autopilot                 |
+------------------------------------------------------------------------+
                                  |
                                  v
+------------------------------------------------------------------------+
| 5. AUTOPILOT INNER-LOOP FLIGHT CONTROL (PX4 / ArduPilot at 500 Hz)     |
|    - Computes attitude error (quaternion PID)                          |
|    - Computes rate errors (p, q, r body rate dampers)                  |
|    - Motor mixer outputs DShot / PWM signals to motor ESCs             |
+------------------------------------------------------------------------+
```
