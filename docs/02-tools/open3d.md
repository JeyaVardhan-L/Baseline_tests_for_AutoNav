# Open3D in Autonomous Robotics

## Why Does Open3D Exist in This Project?

**Open3D** is an open-source library that provides modern 3D data processing, geometric algorithms, and hardware-accelerated OpenGL/Metal visualization for point clouds and meshes.

---

## 1. Role in the Engineering Workflow

1. **Interactive 3D Inspection**: Providing an OpenGL render window where you can zoom, pan, rotate, and visually inspect 3D point clouds in real-time.
2. **Point Cloud Playback** (Exp 03): Displaying frame-by-frame LiDAR sequences with keyboard controls (Space to pause, N for next frame, ESC to exit).
3. **Advanced Geometry**: Fast k-d tree spatial indexing, normal estimation, ICP (Iterative Closest Point) registration, and statistical outlier removal.

---

## 2. Fallback Architecture in This Repository

While Open3D is an exceptional tool for Python 3.8 – 3.12, prebuilt binary wheels are sometimes unavailable for cutting-edge preview Python runtimes (e.g. Python 3.14).

To ensure complete robustness across all operating systems and Python versions:
- All core mathematics (NaN removal, range filtering, voxel downsampling, distance histograms) are implemented in pure, zero-dependency NumPy.
- Point cloud playback includes both an interactive GUI viewer and a pure `--cli` terminal streaming mode.
