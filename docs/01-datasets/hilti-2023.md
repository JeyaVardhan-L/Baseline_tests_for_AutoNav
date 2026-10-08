# Dataset 2: Hilti SLAM Challenge 2023 Robot Dataset

**Official Website**: [https://hilti-challenge.com/](https://hilti-challenge.com/)  
**Role in Project**: **Mobile Robot Payload Benchmark**

---

## 1. What the Dataset Is

The **Hilti SLAM Challenge 2023** dataset contains multi-sensor data collected on actual construction, industrial, and parking garage environments using real mobile robot platforms and handheld sensor rigs equipped with survey-grade ground truth.

---

## 2. Why It Was Selected

1. **True Robot Platform**: Represents an actual mobile robot moving in construction and industrial facilities rather than a highway car.
2. **Solid-State / Wide-FoV LiDAR**: Features a Robosense Bpearl dome-LiDAR specifically designed for near-field obstacle detection.
3. **Industrial High-Rate IMU**: Equipped with an XSens MTi-600 IMU operating at **200 Hz**, providing industrial-grade inertial data.
4. **Challenging Lighting & Structure**: Contains sequences in daylight, pitch darkness at night, and long multi-story parking structures.

---

## 3. Sensors and Specifications

| Sensor | Type | Rate | Description |
|---|---|---|---|
| **Robosense Bpearl** | Dome Solid-State LiDAR | 10 Hz | $360^\circ \times 90^\circ$ ultra-wide field of view |
| **XSens MTi-600** | Industrial MEMS IMU | 200 Hz | Low-noise, low-bias 6-axis inertial stream |
| **Luxonis OAK-D** | Stereo + RGB AI Camera | 15 – 30 Hz | High-resolution synchronized stereo |
| **Track Odometry** | Encoders | 50 Hz | Wheel / track kinematic displacement |

---

## 4. Topics and Formats

Available primarily as ROS 2 bags or ROS 1 bag files:

| Topic | Message Type | Rate |
|---|---|---|
| `/hesai/pandar` or `/rslidar_points` | `sensor_msgs/msg/PointCloud2` | 10 Hz |
| `/imu/data` or `/xsens/imu/data` | `sensor_msgs/msg/Imu` | 200 Hz |
| `/oak_d/left/image_raw` | `sensor_msgs/msg/Image` | 20 Hz |
| `/oak_d/right/image_raw` | `sensor_msgs/msg/Image` | 20 Hz |

---

## 5. Available Environments & Recommended Sequence

- `Site_1_01_day`: Large construction hall in daylight (Recommended first sequence)
- `Site_1_02_night`: Large construction hall in pitch darkness (evaluates low-light sensor degradation)
- `Site_2_01_garage`: Long multi-level underground parking structure

### Where to Place Downloaded Data:
```
datasets/hilti-2023/Site_1_01_day/
```

---

## 6. Expected Computational Experiments

- High-frequency (200 Hz) IMU jitter and timestamp delta profiling (Exp 07).
- Cross-sensor temporal alignment between 10 Hz Bpearl scans and 200 Hz IMU packets (Exp 08).
- Dome point cloud density characterization and near-field obstacle detection bounding (Exp 02, Exp 04).
