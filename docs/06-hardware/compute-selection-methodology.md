# Onboard Compute Selection Methodology

## 1. Principles of Compute Evaluation

Selecting the companion computer that rides onboard the UAV requires balancing computational capacity against flight physics.

---

## 2. Key Criteria to Evaluate

1. **CPU IPC and Single-Thread Latency**:
   - Robotics algorithms (e.g. k-d tree point lookups, occupancy raycasting) are frequently single-threaded and memory-latency sensitive. High single-core IPC (Instructions Per Cycle) often outperforms high core-count low-clock designs.
2. **GPU / Tensor Accelerator**:
   - Required if dense depth estimation, neural point cloud feature extraction, or CNN obstacle classification is deployed. Optional if running lightweight LiDAR-inertial odometry (FAST-LIO2 runs on a single CPU core).
3. **RAM Bandwidth & Capacity**:
   - Must comfortably host OS kernel, ROS 2 middleware buffers, 3D volumetric map octree, and point cloud ring buffers without swapping to disk.
4. **Power Consumption (Watts TDP)**:
   - Must operate stably within the available 5V/12V step-down regulator without browning out the autopilot.
5. **Physical Mass (Grams)**:
   - Must include carrier board, heatsink, fan, and vibration dampeners.
6. **I/O Interfaces**:
   - Native Gigabit Ethernet for LiDAR, USB 3.0 for cameras, and hardware UART/CAN for flight controller communication.
