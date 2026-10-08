# Start Here: Zero-Knowledge Autonomous Robotics Guide

Welcome to the autonomous navigation engineering laboratory. This guide is written specifically for students and engineers with **zero prior robotics knowledge**.

---

## 1. Why Does Autonomous Navigation Exist?

When a human pilots an Unmanned Aerial Vehicle (drone or UAV), the human's eyes observe obstacles, the human's brain calculates where to steer, and the human's fingers move joysticks to command the drone.

In an **autonomous UAV**, there is no human pilot in real-time. The drone must:
1. **Sense** the world using physical devices (LiDAR, cameras, IMUs).
2. **Estimate** where it is in 3D space (State Estimation / Localization).
3. **Map** obstacles and structures around it (Local Mapping).
4. **Plan** a safe trajectory through open air (Path Planning).
5. **Command** its motors to fly that path without crashing (Flight Control).

---

## 2. The Fundamental Engineering Challenge: Computing vs. Reality

Sensors generate continuous torrents of digital numbers. Reality does not pause while computers process those numbers:

- If a LiDAR produces **10 frames per second** (10 Hz), a new frame arrives every **100 milliseconds** ($0.1\text{ s}$).
- If our algorithms take **150 milliseconds** to process one frame, the drone is falling **50 milliseconds behind** on every single scan.
- Within 10 seconds, the software is processing data from 5 seconds in the past. If a wall appears in front of the drone, it will collide with the wall before the computer realizes the wall is there.

Before buying expensive flight computers or drone frames, we must experimentally understand:
- How big is the sensor data?
- How much memory does it need?
- How many CPU milliseconds does each step take?
- Can our algorithms keep up in real time?

---

## 3. Reading Roadmap

Start reading in this exact order:

1. [`robotics-basics.md`](robotics-basics.md): Coordinates, frames of reference, and navigation terms.
2. [`sensor-basics.md`](sensor-basics.md): What are LiDAR, Cameras, and IMUs?
3. [`point-cloud-basics.md`](point-cloud-basics.md): What is a 3D point and how is it stored in memory?
4. [`timestamps.md`](timestamps.md): Why clocks and microsecond timing determine safety.
5. [`realtime-processing.md`](realtime-processing.md): Deadlines, margins, latency, and CPU capacity.

---

## 4. Evidence Classification Rules

In this laboratory, every numerical statement is labeled with its evidence category:

- `[MEASURED]`: Measured directly from physical hardware or authentic recorded data.
- `[DERIVED]`: Calculated mathematically from measured numbers using explicit equations.
- `[ASSUMED]`: Stated as a baseline assumption or manufacturer nominal spec without local empirical validation.
- `[ESTIMATED]`: Educated engineering projection.

Never present an assumption as a measurement. Never invent a specification.
