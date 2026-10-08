# Automotive Reference Dataset: KITTI Vision Benchmark Suite

> [!WARNING]
> **AUTOMOTIVE REFERENCE DATASET — OPTIONAL COMPUTATIONAL BASELINE, NOT REPRESENTATIVE OF UAV OPERATION.**  
> Do **NOT** use KITTI to make UAV sensor requirements, power budgets, or hardware selection claims.

---

## 1. What KITTI Is

The **KITTI Vision Benchmark Suite** (Karlsruhe Institute of Technology and Toyota Technological Institute at Chicago) was collected in 2011 using a modified Volkswagen Passat station wagon driving through Karlsruhe, Germany.

Sensors on the station wagon:
- **Velodyne HDL-64E** mechanical 64-beam LiDAR (10 Hz, ~120,000 points/frame)
- 2 $\times$ Color and 2 $\times$ Grayscale point Grey Flea2 stereo cameras
- OXTS RT3003 GPS/IMU navigation system

---

## 2. Why KITTI Is NOT Representative of an Autonomous UAV

| Characteristic | KITTI Automotive Platform | Autonomous UAV Platform |
|---|---|---|
| **Motion Constraints** | Planar 2D driving on flat asphalt road | Unconstrained 6-DoF 3D flight (pitch, roll, heave) |
| **Angular Velocity** | Mostly yaw turns ($< 30^\circ/\text{s}$) | Aggressive rotation rates ($> 120^\circ/\text{s}$ during wind gusts) |
| **Mass & Payload** | 1,500 kg automobile payload | $< 1.5\text{ kg}$ total sensor and compute payload |
| **Power Budget** | Continuous alternator / 12V battery ($> 500\text{ W}$) | Strictly limited LiPo flight battery ($< 40\text{ W}$ for autonomy stack) |
| **Field-of-View** | Forward and 360-horizontal ring | Omnidirectional spherical / hemispherical awareness for vertical obstacles |

---

## 3. How KITTI May Be Used in This Repository

KITTI is retained purely as a **computational volume baseline**:
- Verifying that LiDAR binary format parsers (`.bin` float arrays) correctly handle 120,000-point frames.
- Comparing raw point density between automotive mechanical LiDARs (Velodyne HDL-64E) and modern UAV-grade solid-state/MEMS LiDARs (Livox Mid-360, Ouster OS-1).
