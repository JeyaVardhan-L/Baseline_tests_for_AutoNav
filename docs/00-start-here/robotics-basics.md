# Robotics Basics for Autonomous Navigation

This document explains core concepts in plain English for someone with **zero prior robotics knowledge**.

---

## 1. What is an Autonomous UAV?

An **Unmanned Aerial Vehicle (UAV)** is an aircraft that flies without an onboard human pilot. A multicopter (e.g. quadcopter or hexacopter) stays aloft by spinning multiple propellers at high speeds.

- **Remote-Controlled (RC) Drone**: A human operator watches the drone and commands movements via radio transmitter.
- **Autonomous Drone**: An onboard computer reads sensors, plans a flight path, and navigates without human intervention, even in environments with **no GPS** (such as indoor warehouses, underground caves, or extraterrestrial planetary surfaces).

---

## 2. The Autonomy Pipeline: The 5 Questions

To fly autonomously, the drone's software must continuously answer five questions in real-time:

1. **"What is around me?"** $\rightarrow$ **Sensing**: Reading LiDAR beams, depth cameras, and inertial sensors.
2. **"Where am I?"** $\rightarrow$ **State Estimation & Localization**: Calculating position $(x, y, z)$, velocity $(v_x, v_y, v_z)$, and orientation (roll, pitch, yaw).
3. **"Where can I go?"** $\rightarrow$ **Mapping & Free Space Detection**: Building a 3D obstacle map and identifying open air vs. obstacles.
4. **"How do I get there?"** $\rightarrow$ **Path Planning**: Finding a smooth, collision-free curve from the current position to the destination.
5. **"How do I fly the path?"** $\rightarrow$ **Flight Control**: Calculating motor speeds hundreds of times per second to track the trajectory.

---

## 3. What is 6 Degrees of Freedom (6-DoF)?

In 3D space, an object can move and rotate in **6 independent ways**:

### 3 Translational Degrees (Position)
- **$X$ (Surge)**: Forward and backward along the flight path.
- **$Y$ (Sway)**: Left and right.
- **$Z$ (Heave)**: Up and down (altitude).

### 3 Rotational Degrees (Attitude / Orientation)
- **Roll ($\phi$)**: Tilting sideways (left wing up, right wing down).
- **Pitch ($\theta$)**: Tilting nose up or nose down.
- **Yaw ($\psi$)**: Turning the heading clockwise or counter-clockwise (compass direction).

Together, $[x, y, z, \phi, \theta, \psi]$ describe the **pose** of the drone at any single instant in time.

---

## 4. What is SLAM?

**SLAM** stands for **Simultaneous Localization and Mapping**.

- **The Chicken-and-Egg Problem**:
  - To know *where you are*, you need a *map* of your surroundings.
  - To build a *map*, you need to know *where you are* when taking each measurement.
- **SLAM solves both simultaneously**: It tracks how sensor measurements match consecutive observations (e.g. aligning LiDAR scans or tracking camera features) to estimate the drone's trajectory while incrementally building an accurate 3D map.

---

## 5. What is Sensor Fusion?

No individual sensor is perfect:
- **LiDAR**: Extremely accurate distances, but heavy, power-hungry, and updates slowly (10 to 20 times per second).
- **Cameras**: Rich color and visual textures, but fail in pitch darkness or bright glare and struggle with depth without motion.
- **IMU (Inertial Measurement Unit)**: Updates very fast (200 to 1000 times per second), but drifts rapidly over time due to sensor bias.

**Sensor Fusion** is the mathematical blending (using tools like Extended Kalman Filters or Factor Graphs) of fast IMU predictions with slower, highly accurate LiDAR/camera corrections to yield a reliable, high-rate state estimate.
