# Experiment 01 — Dataset Inspection

## 1. Objective
Before writing code or attempting complex SLAM algorithms, we must answer fundamental data-hygiene questions:
- What files actually exist in this dataset?
- How much total disk space does it occupy?
- What sensory modalities (LiDAR, camera, IMU) are present?
- What are the frame rates and timestamps?
- Are there missing frames or corrupt files?

## 2. Why This Matters
Robotics algorithms fail silently or produce erratic trajectory drift when fed incomplete datasets, dropped frames, or incorrect sensor frequency assumptions. Inspecting the dataset verifies data integrity before downstream compute pipelines run.

## 3. Required Knowledge
- **Sensor Modality**: The physical measurement channel (e.g., optical depth, laser time-of-flight, inertial accelerations).
- **Frame Rate (Hz)**: Samples per second ($1\text{ Hz} = 1\text{ frame per second}$).
- **Nominal vs. Observed Rate**: Manufacturer specifications state nominal rates (e.g., 10.0 Hz). Real-world data may arrive with slight jitter (e.g., 9.98 Hz).

## 4. Dataset
Supports any registered dataset:
- `synthetic` (default zero-download test stream)
- `newer_college`
- `hilti_2023`
- `openloris`
- `tum_rgbd`
- `kitti` (automotive reference)

## 5. Input
Directory containing dataset files (e.g., ROS bags, raw point clouds, PNG images, or metadata text files).

## 6. Output
- `results/<dataset>/01_data_inspection/inspection_summary.json`
- `results/<dataset>/01_data_inspection/metadata.json`
- `results/<dataset>/01_data_inspection/summary.md`

## 7. Parameters
- `--dataset`: Dataset identifier (`synthetic`, `newer_college`, etc.).
- `--path`: Custom local path if extracted outside standard folders.

## 8. Method
1. Recursively discover files and catalog extensions.
2. Calculate total byte footprint on disk.
3. Identify sensory topics and file streams.
4. Check timestamp monotonic progression and identify dropped frames.
5. Generate standardized JSON and terminal summary.

## 9. Equations
$$\text{Observed Frequency (Hz)} = \frac{\text{Total Frames} - 1}{t_{\text{last}} - t_{\text{first}}}$$

$$\text{Data Footprint (MB)} = \frac{\sum \text{File Sizes (bytes)}}{1{,}048{,}576}$$

## 10. Command
```bash
# Test on synthetic dataset immediately
python experiments/01-data-inspection/run.py --dataset synthetic

# Inspect downloaded Newer College dataset
python experiments/01-data-inspection/run.py --dataset newer_college --path datasets/newer-college
```

## 11. Expected Terminal Output
```text
============================================================
AUTO NAV BASELINE
EXPERIMENT 01 - DATASET INSPECTION
[Dataset: synthetic]
============================================================
------------------------------------------------------------
INSPECTION SUMMARY
------------------------------------------------------------
Dataset Name              : Synthetic Demonstration Stream
Modalities                : LIDAR, DEPTH_CAMERA, IMU
Total Files               : 100 files          [MEASURED]
Total Footprint           : 100.0 MB           [MEASURED]
Total Frame Count         : 100 frames         [MEASURED]
Approx Duration           : 10.0 seconds       [DERIVED]
Sensor Frequency          : 10.0 Hz            [MEASURED]
------------------------------------------------------------
INTEGRITY & HEALTH
Missing Frames            : 0 count            [DERIVED]
Malformed Files           : 0 count            [MEASURED]
```

## 12. Interpretation
- If observed rate matches nominal rate, sensor stream timing is healthy.
- If missing frames count > 0, down-stream filters must handle irregular sample intervals.

## 13. Limitations
Inspection does not check point cloud geometric calibration or sensor noise; it only audits file and stream health.

## 14. What Decision This Informs
Determines whether a downloaded dataset slice is intact and sufficient for algorithmic characterization.
