# Experiment 04 — Point Cloud Filtering & Downsampling

## 1. Objective
Understand how filtering and voxel downsampling reduce the geometric complexity of point clouds, and measure the computational cost of performing these operations.

## 2. Why This Matters
Downstream registration (ICP) and mapping (Octomap / Occupancy grids) have computational complexity scaling with point count ($O(N \log N)$ or $O(N^2)$). Downsampling reduces point counts by 70% to 90% while preserving geometric surface structure, drastically speeding up state estimation.

## 3. Required Knowledge
- **Voxel**: A 3D pixel (cubic volume with edge length $s$, e.g., 0.10 m or 0.20 m).
- **Centroid**: The mean coordinate of all points located inside a voxel cell.
- **Self-reflection Removal**: LiDARs often capture reflections from the drone frame or landing gear ($r < 0.5\text{ m}$); range clipping strips these false obstacles.

## 4. Dataset
Supports any registered dataset (`synthetic`, `newer_college`, `hilti_2023`, `kitti`).

## 5. Input
Single raw LiDAR frame ($N \approx 65\text{k}\text{ to }120\text{k}$ points).

## 6. Output
- Before vs. After point count and buffer size metrics.
- Side-by-side scatter comparison figure: `01_filtering_comparison.png`.
- Stage execution latencies (NaN drop, range clip, voxel downsampling).

## 7. Parameters
- `--voxel-size`: Cubic voxel dimension in meters (default: 0.20 m).
- `--min-range`: Near clipping boundary in meters (default: 0.5 m).
- `--max-range`: Far clipping boundary in meters (default: 30.0 m).

## 8. Command
```bash
python experiments/04-pointcloud-filtering/run.py --dataset synthetic --voxel-size 0.20
```

## 9. What Decision This Informs
Determines the optimal voxel resolution that removes point cloud redundancy without taking more CPU time than it saves in downstream SLAM.
