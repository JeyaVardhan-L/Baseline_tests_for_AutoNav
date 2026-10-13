# Dataset Registry and Selection Rationale

## Purpose

This registry evaluates candidate public datasets against the requirements of the ISRO autonomous navigation feasibility investigation.

---

## 1. Primary Selected Dataset: The Newer College Dataset

⭐ **SELECTED FOR REAL-DATA RESEARCH PIPELINE**

| Property | Value |
| :--- | :--- |
| **Dataset Name** | The Newer College Dataset |
| **Lead Organization** | Dynamic Robot Systems Group, Oxford Robotics Institute (ORI) |
| **Official Site** | [https://ori-drs.github.io/newer-college-dataset/](https://ori-drs.github.io/newer-college-dataset/) |
| **Download Portal** | [https://ori-drs.github.io/newer-college-dataset/download/](https://ori-drs.github.io/newer-college-dataset/download/) |
| **License** | Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0) |
| **Access Method** | Official Google Form email registration (free for non-commercial research) |
| **Selected Sequence** | `01_short_experiment` (1,530 seconds / ~25.5 minutes, ~15,300 LiDAR scans at 10 Hz) |
| **Primary LiDAR** | Ouster OS1-64 (Gen 1): 64 channels, 10 Hz nominal, 1024 horiz resolution, ~65,536 pts/frame |
| **IMU** | Internal Ouster 6-axis IMU (100 Hz nominal) |
| **Ground Truth** | Leica BLK360 terrestrial laser scanner millimeter reference trajectory |
| **Published Size & Formats** | Published as ROS bag and raw files (`.pcd`, `.png`, `.csv`). Full multi-sensor sequence is tens of gigabytes (~25–50+ GB uncompressed). |
| **Recommended Subset** | Initial slice of 50 to 100 consecutive frames (5 to 10 seconds, ~100–250 MB) for laptop-scale baseline ICP testing |
| **Local Status** | **ABSENT** — Directory is currently empty; real-data validation is pending download. |
| **Selection Rationale** | Handheld multi-axis motion matches UAV flight dynamics far better than automotive datasets. Provides survey-grade millimeter ground truth for trajectory validation. |

---

## 2. Secondary Evaluated Public Datasets

### KITTI Vision Benchmark (Odometry)
- **Sensor:** Velodyne HDL-64E (64-beam, 10 Hz, automotive roof-mounted)
- **Format:** Binary `.bin` float32 (x, y, z, reflectance)
- **Status:** Supported via generic `.bin` parser in `src/autonav_baseline/datasets/io.py`.
- **Limitation:** Automotive planar motion with constrained pitch/roll, unrepresentative of aerial dynamics.

### Hilti SLAM Challenge (2021 / 2023)
- **Sensor:** Robosense Bpearl dome LiDAR + Ouster OS0-128 + cameras + IMU
- **Status:** Candidate for aggressive multi-axis handheld / drone dynamics.

---

## 3. Strict Dataset Policy

1. **Real Data Exclusively:** Synthetic sensor generators and artificial point clouds are prohibited as evidence.
2. **Outside Git:** Raw archives and downloaded frames must never be committed to Git.
3. **Verifiable Parsing:** All dataset formats must be parsed via explicit, tested readers (`.pcd`, `.bin`, `.ply`, `.npy`) with authentic timestamps.
