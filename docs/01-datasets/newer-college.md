# Dataset 1: Oxford Newer College Dataset

**Official Website**: [https://ori-drs.github.io/newer-college-dataset/](https://ori-drs.github.io/newer-college-dataset/)  
**Institution**: Oxford Robotics Institute, University of Oxford  
**Role in Project**: **PRIMARY LiDAR Learning Dataset**

---

## 1. What the Dataset Is

The **Newer College Dataset** is a multi-sensor dataset recorded by researchers walking and jogging around the historic New College campus in Oxford, UK. It covers historic stone quads, colonnades, open parkland, dense foliage, and aggressive handheld motions.

---

## 2. Why It Was Selected

1. **Realistic 6-DoF Dynamics**: Unlike automotive datasets where the vehicle moves mostly planar on asphalt, the Newer College handheld rig rotates rapidly across pitch, roll, and yaw, closely mimicking UAV flight turbulence and aggressive maneuvers.
2. **Dense Multibeam 3D LiDAR**: Equipped with an Ouster OS-1 64-beam LiDAR producing 131,072 points per scan.
3. **Centimeter Ground Truth**: Includes millimeter-accurate static terrestrial laser scanner (Leica BLK360) reference point clouds for benchmarking mapping accuracy.
4. **Rich Multi-Modal Sensors**: Carries an Ouster LiDAR, built-in IMU, stereo color cameras (Intel RealSense D435i), and external IMU.

---

## 3. Sensors and Hardware Specifications

| Sensor | Type | Sampling Rate | Measurement |
|---|---|---|---|
| **Ouster OS-1-64** | 64-beam mechanical LiDAR | 10 Hz / 20 Hz | Range, Intensity, Ring, Reflectivity, Ambient, Timestamp per point |
| **Ouster Internal IMU** | 6-axis MEMS IMU | 100 Hz | Linear Acceleration $[a_x, a_y, a_z]$, Angular Velocity $[\omega_x, \omega_y, \omega_z]$ |
| **Intel RealSense D435i** | Active stereo RGB-D | 30 Hz | Left/Right Infrared, RGB Color, Depth, Camera IMU |
| **Leica BLK360** | Terrestrial Laser Scanner | Static | Millimeter ground-truth point cloud map |

---

## 4. File Formats and ROS Topics

Available as ROS 1 `.bag` files (convertible to ROS 2 via `rosbags`):

| ROS Topic | Message Type | Rate | Description |
|---|---|---|---|
| `/os1_cloud_node/points` | `sensor_msgs/PointCloud2` | 10 Hz / 20 Hz | 64-ring 3D point cloud |
| `/os1_cloud_node/imu` | `sensor_msgs/Imu` | 100 Hz | High-rate linear acceleration & gyro |
| `/camera/color/image_raw` | `sensor_msgs/Image` | 30 Hz | 1920x1080 or 640x480 RGB image |
| `/camera/depth/image_rect_raw` | `sensor_msgs/Image` | 30 Hz | 16-bit depth image |

---

## 5. Sequence Selection, Formats, and Recommended Initial Subset

- **Target Sequence**: `01_short_experiment`
  - **Official Description**: 0.5 loop of quad, loop of mid-section, loop of parkland, loop of quad, loop of park.
  - **Duration**: 1,530 seconds (~25.5 minutes), generating ~15,300 LiDAR scans at 10 Hz.
  - **Published Formats**: ROS bag (`.bag`) and raw files (`.pcd` point clouds, `.png` stereo images, `.csv` timestamps/IMU).
  - **Full Sequence Size**: Tens of gigabytes (~25–50+ GB uncompressed across all streams; multi-gigabyte compressed). Note that "short" is the authors' relative designation compared to the 2,180-second `long experiment`.
- **Recommended Laptop Subset**:
  - Do **NOT** process all 15,300 frames on a standard laptop for initial baseline testing.
  - Extract an initial slice of **50 to 100 consecutive frames** (5 to 10 seconds of motion, ~100–250 MB) into `datasets/newer-college/01_short_experiment/point_clouds/`.
- **Official Download Portal**: [Newer College Downloads Page](https://ori-drs.github.io/newer-college-dataset/download/) (registration via Google Form).
- **License**: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).
- **Current Local Status**: The raw Newer College dataset is **currently absent locally**; real-data validation is pending dataset acquisition.
- **Where to Extract**: `datasets/newer-college/01_short_experiment/`

---

## 6. What Experiments Can and Cannot Be Performed With It

### What CAN Be Performed:
- LiDAR data rate, frame size, and point density characterization (Exp 02).
- Point cloud filtering and downsampling timing (Exp 04, Exp 05).
- LiDAR-IMU synchronization and cross-sensor timing analysis (Exp 07, Exp 08).
- End-to-end real-time pre-processing margin evaluation (Exp 09).

### What CANNOT Be Performed:
- Direct UAV aerodynamic rotor downwash vibration characterization (data was carried on a handheld stick, not a quadcopter frame).
- High-altitude thermal or barometric drift evaluation.
