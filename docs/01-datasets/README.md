# Supported Benchmark Datasets

This directory documents the authentic robotics datasets supported by the autonomous navigation baseline study.

---

## Dataset Strategy: Why We Moved Beyond Automotive Baselines

Earlier robotics literature heavily centered around automotive datasets like KITTI. However, an autonomous UAV differs drastically from a 1.5-ton passenger car driving along paved German roads:

- **6-DoF Dynamics**: Drones pitch, roll, and heave aggressively in 3D space, introducing high rotational rates that cars never experience.
- **Payload & Power Limits**: Cars carry 500W computing racks and 12V lead-acid car batteries; UAVs operate under strict mass constraints (often $< 1.5\text{ kg}$ payload) and battery watt-hour limits.
- **Environments**: UAVs navigate indoor corridors, open fields, vegetation, and multi-level stairwells rather than flat 2D asphalt streets.

To gather realistic empirical evidence for UAV navigation feasibility, we prioritize datasets collected on **handheld or mobile robot platforms with aggressive 6-DoF motion**.

---

## Dataset Index

| Dataset | Platform / Modalities | Role in Project | Recommended Sequence |
|---|---|---|---|
| [**Oxford Newer College**](newer-college.md) | Ouster OS-1 64-beam LiDAR, IMU, RealSense D435i | **PRIMARY LiDAR Learning Dataset** | `short-experiment` / `collection-1` |
| [**Hilti SLAM 2023**](hilti-2023.md) | Robosense Bpearl LiDAR (10Hz), XSens IMU (200Hz), OAK-D | **Mobile Robot Platform Benchmark** | `Site_1_01_day` |
| [**OpenLORIS-Scene**](openloris-scene.md) | RealSense RGB-D, IMU, Wheel Odometry, 2D Laser | **Indoor Robot Depth/Camera Benchmark** | `office1` |
| [**TUM RGB-D**](tum-rgbd.md) | Kinect RGB-D, MoCap 6-DoF Ground Truth | **Beginner-Friendly Depth Dataset** | `rgbd_dataset_freiburg1_xyz` |
| [**Oxford Spires**](oxford-spires.md) | Multi-session LiDAR, Vision, mm-accurate RTK | **Advanced Long-Term Mapping Reference** | Advanced Phase Only |
| [**KITTI**](kitti.md) | Velodyne HDL-64E, Automotive Cameras, GPS/IMU | **Automotive Reference Baseline (Optional)** | `2011_09_26_drive_0001` |

---

## Dataset Download Policy

- **No Automatic Huge Downloads**: The repository does **NOT** automatically download multi-gigabyte files.
- **Manual User Acquisition**: The user downloads raw sequences directly from official institutional mirrors.
- **Clear File Organization**: Downloaded sequences belong in `datasets/<dataset_name>/` (which is `.gitignore`d to prevent accidental git bloat).
