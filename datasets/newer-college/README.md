# The Newer College Dataset — Acquisition and Organization Guide

**Official Source:** [Oxford Robotics Institute — The Newer College Dataset](https://ori-drs.github.io/newer-college-dataset/)  
**Download Portal:** [https://ori-drs.github.io/newer-college-dataset/download/](https://ori-drs.github.io/newer-college-dataset/download/)  
**License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)  
**Cost:** $0 (Free public research dataset)

---

## 1. Justification for Selection

The Newer College Dataset is selected as the primary real-world benchmark dataset for this autonomous navigation feasibility study because:

1. **Authentic 3D Multi-Beam LiDAR:** Recorded with an Ouster OS1-64 (64 channels, 10 Hz, 360° FOV, ~65,536 points/frame), representative of modern high-resolution robotic sensing.
2. **Sub-Centimeter Ground-Truth Trajectory:** Unlike datasets that rely on loose GNSS or unverified odometry, Newer College provides 6-DOF ground-truth poses registered against an optical millimeter-level Leica BLK360 terrestrial laser scan.
3. **Synchronized Multi-Modal Sensors:** Includes aligned LiDAR point clouds, 6-axis IMU readings (100 Hz), and stereo imagery.
4. **Appropriate Scale for Laptop Research:** The shortest recording, `01_short_experiment` (~160 meters, ~160 seconds), is compact enough (~1.5 GB compressed) to process on a standard laptop without enterprise server hardware.

---

## 2. Official Acquisition Procedure

The official Oxford distribution uses an email registration form to distribute download links:

1. Open the official download portal:
   ```text
   https://ori-drs.github.io/newer-college-dataset/download/
   ```
2. In the embedded Google Form, submit your email address.
3. Oxford will display or email the direct link to the dataset repository.
4. Select the sequence:
   ```text
   01_short_experiment.bag   (approx 1.5 GB compressed)
   ```
   Or download the pre-extracted point clouds if available.

---

## 3. Expected Local Directory Layout

Place the sequence files in `datasets/newer-college/01_short_experiment/` (which is excluded from Git via `.gitignore`):

```text
datasets/
└── newer-college/
    ├── manifest.json                  # Machine-readable metadata (tracked in git)
    ├── README.md                      # This guide (tracked in git)
    └── 01_short_experiment/           # Real data directory (git-ignored)
        ├── point_clouds/              # Directory of consecutive frames
        │   ├── frame_000000.pcd       # Supported formats: .pcd, .bin, .ply, .npy
        │   ├── frame_000001.pcd
        │   └── ...
        ├── timestamps.csv             # Monotonic timestamp per frame (seconds)
        └── ground_truth.csv           # Reference SE(3) poses (optional)
```

### Format Specifications:
- **`timestamps.csv`**: A CSV file containing a `timestamp` or `timestamp_sec` column (e.g. floating-point Unix timestamps).
- **Point Clouds**: Consecutive frames saved in standard ASCII or Binary PCD, PLY, binary float32 (`.bin`), or NumPy (`.npy`) format.
- **`ground_truth.csv`**: A CSV with columns `timestamp,tx,ty,tz,qx,qy,qz,qw` representing reference sensor position and orientation in the world frame.

---

## 4. Verification and Inspection Command

Once point clouds and timestamps are placed in the directory, verify the real data using PowerShell:

```powershell
python experiments/01_inspect_dataset.py --dataset newer_college --path datasets/newer-college/01_short_experiment
```

If files are present, the command measures:
- Exact valid point-cloud frame count (`MEASURED`).
- Coordinate bounding boxes and finite-value check (`MEASURED`).
- Observed frame interval and sensor frequency (`MEASURED`).
- Verification of IMU and ground-truth files (`MEASURED`).

If files are not yet downloaded, the inspection tool reports all metrics honestly as `UNAVAILABLE` without fabricating data.
