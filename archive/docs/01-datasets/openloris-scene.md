# Dataset 3: OpenLORIS-Scene Dataset

**Official Website**: [https://lifelong-robotic-vision.github.io/dataset/scene](https://lifelong-robotic-vision.github.io/dataset/scene)  
**Role in Project**: **Indoor Robot RGB-D / Camera / IMU Benchmark**

> [!IMPORTANT]
> **DO NOT CALL THIS A 3D LIDAR DATASET.**  
> OpenLORIS-Scene is strictly an **indoor robot vision, depth, and inertial dataset** (with an optional 2D single-line planar laser rangefinder). It does not contain 3D multi-beam LiDAR point clouds.

---

## 1. What the Dataset Is

The **OpenLORIS-Scene** dataset was recorded using an indoor wheeled mobile robot navigating typical real-world indoor facilities across multiple days and varying human clutter levels:
- Offices
- Narrow Corridors
- Cafés
- Supermarkets
- Residential Homes

---

## 2. Why It Was Selected

Indoor UAV flight inside buildings, tunnels, or subterranean structures requires navigating narrow corridors, glass partitions, and featureless white walls:
1. **Corridor and Room Geometry**: Captures real indoor room layouts where GPS is completely unavailable.
2. **Camera Data Volume**: Teaches raw RGB and 16-bit depth image bandwidth and memory footprint.
3. **Multi-Rate Synchronization**: Combines 30 Hz RGB-D cameras with a 200 Hz / 400 Hz RealSense IMU.
4. **Lighting Variations**: Tests sensor degradation under dim indoor lighting, fluorescent flicker, and daylight window glare.

---

## 3. Sensors and Hardware Specifications

| Sensor | Type | Rate | Output Format |
|---|---|---|---|
| **Intel RealSense D435i** | Active Stereo Camera | 30 Hz | $640 \times 480$ RGB + 16-bit Depth image in millimeters |
| **RealSense IMU** | 6-Axis MEMS IMU | 200 Hz / 400 Hz | Accelerometer $[a_x, a_y, a_z]$ and Gyroscope $[\omega_x, \omega_y, \omega_z]$ |
| **Wheel Odometry** | Robot Base Encoders | 20 Hz | 2D Linear and angular velocity |
| **2D Laser Scanner** | Single-line planar scanner | 10 Hz | 2D range array in polar coordinates |

---

## 4. Topics and File Formats

Available as ROS `.bag` files or unpacked image/timestamp folders:

| Topic / Stream | Rate | Description |
|---|---|---|
| `/color/image_raw` | 30 Hz | 24-bit RGB visual stream |
| `/depth/image_raw` | 30 Hz | 16-bit depth stream (distance in mm) |
| `/imu/data_raw` | 200 Hz | Accelerometer and Gyroscope telemetry |
| `/odom` | 20 Hz | Ground robot planar odometry |

---

## 5. Recommended Small Sequence

- **Recommended Sequence**: `office1-1` or `corridor1-1`
- **Where to Extract**: `datasets/openloris/office1/`

---

## 6. What Experiments Can Be Performed With It

- **Depth Image Data Volume & Coverage** (Exp 06): Measure valid depth pixels, detect voids on specular desks and windows.
- **Pinhole 3D Back-Projection** (Exp 06): Project 2D depth matrices into 3D metric coordinate frames.
- **IMU High-Rate Characterization** (Exp 07): Profile RealSense IMU noise and sample rate stability.
- **Visual-Inertial Timestamp Alignment** (Exp 08): Measure camera-to-IMU temporal offsets.
