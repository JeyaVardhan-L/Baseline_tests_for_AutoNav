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

## 5. Recommended Small Sequence for First Experiments

Do **NOT** download the full 100 GB multi-round sequence immediately.

- **Recommended Sequence**: `01_short_experiment` (~1.5 GB to 4.5 GB)
- **Official Download Link**: Available on the [Newer College Downloads Page](https://ori-drs.github.io/newer-college-dataset/download/).
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
