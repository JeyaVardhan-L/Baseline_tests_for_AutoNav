# EXP-08: Timestamp & Synchronization Summary

## Measured & Derived Metrics

| Metric | Value |
|---|---|
| LiDAR Scans Count | 10 [MEASURED] |
| IMU Samples Count | 1000 [MEASURED] |
| LiDAR-IMU Mean Offset | 0.000 ms [MEASURED] |
| LiDAR-IMU P95 Offset | 0.000 ms [MEASURED] |
| LiDAR-IMU Max Offset | 0.000 ms [MEASURED] |
| Cam-IMU Mean Offset | 0.000 ms [MEASURED] |
| LiDAR-Cam Mean Offset | 0.000 ms [MEASURED] |

## Key Observations & Conclusions

- LiDAR+IMU synchronization: At UAV cruise speeds (e.g., 5 m/s), a 20 ms time offset causes a 10 cm spatial state estimation error if uncompensated.
- High-frequency IMU telemetry (>= 200 Hz) ensures the maximum temporal distance to any visual or LiDAR frame is bounded within half the IMU sample period (<= 2.5 ms).
- Hardware triggering (PTP / PPS / hardware sync pulse) minimizes clock drift across distinct embedded microcontrollers.
