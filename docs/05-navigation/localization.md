# Localization for Autonomous UAVs

**Localization** is the continuous process of determining where the drone is located in 3D space relative to a reference coordinate frame.

---

## 1. LiDAR-Inertial Odometry (LIO)

In GPS-denied environments, the primary localization engine is typically a **tightly-coupled LiDAR-Inertial Odometry** system (e.g. FAST-LIO2 or LIO-SAM):

1. **IMU Forward Propagation (100 – 500 Hz)**:
   - High-rate accelerometer and gyroscope readings are integrated to predict the drone's position, velocity, and orientation over the 100 ms interval between LiDAR frames.
2. **LiDAR Motion De-Skewing**:
   - Because a mechanical LiDAR takes 100 ms to rotate 360 degrees, the drone has moved while the scan was taking place. The predicted IMU trajectory is used to transform every individual point to the exact pose at the end of the scan.
3. **Scan-to-Map Matching (10 – 20 Hz)**:
   - The de-skewed points are registered against an incrementally updated local map (e.g. using an ik-d tree) using point-to-plane residual minimization.
4. **Kalman Update**:
   - Residual errors update the state estimate and correct IMU accelerometer and gyroscope bias estimates.
