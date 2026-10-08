# Concept: Sensor Fusion

**Sensor Fusion** is the mathematical combining of sensory data derived from disparate sources such that the resulting state estimation has less uncertainty than would be possible when these sources were used individually.

---

## 1. Loosely-Coupled vs. Tightly-Coupled Fusion

- **Loosely-Coupled**: Each sensor estimates its own pose independently (e.g. LiDAR odometry produces a pose, Camera odometry produces a pose), and an EKF fuses these full poses. Fast to implement, but fragile if one sensor temporarily degenerates (e.g. flying down a blank corridor).
- **Tightly-Coupled**: Raw sensor measurements (individual LiDAR point-to-plane residuals, raw visual image feature tracks, and raw IMU acceleration/gyro measurements) are optimized together inside a single nonlinear factor graph or iterated Kalman filter (e.g. LIO-SAM, FAST-LIO2). Extremely robust and resistant to single-modality dropouts.
