# Dataset 4: TUM RGB-D Benchmark

**Official Website**: [https://vision.in.tum.de/data/datasets/rgbd-dataset](https://vision.in.tum.de/data/datasets/rgbd-dataset)  
**Institution**: Computer Vision Group, Technical University of Munich (TUM)  
**Role in Project**: **Beginner-Friendly Depth Dataset**

---

## 1. What the Dataset Is

The **TUM RGB-D Benchmark** is one of the most widely cited computer vision datasets in robotics history. It was recorded using a handheld Microsoft Kinect RGB-D sensor paired with an optical high-speed motion capture system (OptiTrack / Vicon) providing sub-millimeter ground-truth 6-DoF trajectory poses.

---

## 2. Why It Was Selected: The Simplest Depth Learning Path

Before wrestling with complex ROS bag unpacking, C++ compilation, or giant 50 GB archives, a beginner can download a **small 200 MB archive** of standard PNG files and immediately understand:

$$\text{RGB Image} + \text{Depth Image} + \text{Timestamp} + \text{Ground Truth Pose}$$

---

## 3. File Structure: Simple and Clean

Unlike binary bag files, TUM RGB-D sequences are extracted directly as simple directories:

```
rgbd_dataset_freiburg1_xyz/
    rgb/                  # Color PNG images (e.g. 1305031102.160407.png)
    depth/                # 16-bit Depth PNG images in mm (e.g. 1305031102.160430.png)
    accelerometer.txt     # IMU telemetry (timestamp, ax, ay, az)
    groundtruth.txt       # Millimeter motion capture 6-DoF poses
    depth.txt             # Timestamp index for depth images
    rgb.txt               # Timestamp index for color images
```

---

## 4. Recommended First Sequence

- **Sequence Name**: `rgbd_dataset_freiburg1_xyz`
- **Size**: ~250 MB compressed
- **Description**: Handheld camera moving along standard X, Y, and Z Cartesian axes over a typical office desk environment.
- **Where to Extract**:
  ```
  datasets/tum-rgbd/rgbd_dataset_freiburg1_xyz/
  ```

---

## 5. Instant 10-Second Command

Once extracted, you can immediately run Experiment 06 against the folder:

```bash
python experiments/06-depth-characterization/run.py --dataset tum_rgbd --path datasets/tum-rgbd/rgbd_dataset_freiburg1_xyz
```

You will immediately see:
- Image resolution ($640 \times 480$)
- Valid depth coverage percentage
- Minimum, maximum, and median detected depth in meters
- Uncompressed frame memory size
- 3D pinhole back-projection latency
- Depth histogram plot in `results/tum_rgbd/06_depth_characterization/figures/`
