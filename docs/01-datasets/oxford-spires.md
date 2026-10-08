# Dataset 5: Oxford Spires Dataset (Advanced Reference)

**Official Website**: Oxford Robotics Institute  
**Role in Project**: **Advanced Long-Term Mapping & Reconstruction Reference**

---

## 1. What the Dataset Is

The **Oxford Spires Dataset** is a high-precision multi-session dataset captured across the city of Oxford, designed specifically for investigating long-term localization, seasonal appearance change, multi-year map maintenance, and large-scale 3D city reconstruction.

---

## 2. Why It Is an Advanced Reference

> [!NOTE]
> **NOT MANDATORY FOR THE FIRST TUTORIAL.**  
> Oxford Spires is reserved for advanced subsequent project phases. Beginners should start with **Newer College** for LiDAR and **TUM RGB-D** for depth.

It provides:
- Multi-modal sensor suites (multibeam LiDAR, panoramic cameras, industrial IMU, dual-antenna RTK-GPS).
- Multi-session repeated trajectories over identical geographic routes.
- Centimeter-accurate survey control networks.

---

## 3. Potential Future Use Cases in Later Phases

1. **LiDAR-Visual Map Prior Localization**: Testing whether a UAV can localize itself against a pre-existing 3D geometric map built during a previous mission.
2. **Dense Volumetric Reconstruction**: Benchmarking 3D TSDF (Truncated Signed Distance Function) and neural implicit surface reconstruction algorithms.
3. **Multi-Sensor Extrinsic Calibration Stability**: Measuring long-term mechanical calibration drift between cameras and LiDAR.
