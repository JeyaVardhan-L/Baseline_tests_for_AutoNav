# ROS 2: Robot Operating System

## Why Does ROS 2 Exist in Robotics?

**ROS 2 (Robot Operating System 2)** is not an operating system like Windows or Linux; it is an open-source **robotics middleware** framework built on top of the Data Distribution Service (DDS) standard.

In a complex robot, many separate software programs (called **Nodes**) run simultaneously:
- Node 1: Talks to the LiDAR driver.
- Node 2: Talks to the IMU.
- Node 3: Computes SLAM odometry.
- Node 4: Plans flight trajectories.
- Node 5: Communicates with the ground station.

ROS 2 provides the standardized communication plumbing that allows these nodes to exchange timestamped data across memory or Ethernet buses.

---

## 1. Key ROS 2 Concepts

- **Topic**: A named channel over which nodes exchange messages (e.g. `/lidar/points` or `/imu/data`).
- **Publisher**: A node that sends messages onto a topic (e.g. the LiDAR driver).
- **Subscriber**: A node that listens for messages on a topic (e.g. the SLAM node).
- **Message (`msg`)**: Strongly typed data structure with standardized header timestamps (e.g. `sensor_msgs/PointCloud2`).
- **Quality of Service (QoS)**: Configurable delivery policies (e.g. "Best Effort" for high-rate sensor streams vs. "Reliable" for mission commands).

---

## 2. Policy in This Repository: Zero-Barrier Starting Path

Many robotics tutorials fail because they force beginners to install 20 GB of Ubuntu Linux, configure DDS domain IDs, and compile CMake workspaces before they can even see a single 3D point.

In this repository:
1. **The primary learning path is pure Python / NumPy**: You can clone the repo and run Experiments 01 through 10 in 60 seconds on any Windows, macOS, or Linux machine.
2. **ROS 2 is an optional advanced path**: Introduced after you already understand what a point cloud and timestamp mean mathematically.
