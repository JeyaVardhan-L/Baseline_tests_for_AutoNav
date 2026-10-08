# EXP-07: IMU Characterization Summary

## Measured & Derived Metrics

| Metric | Value |
|---|---|
| Samples Analyzed | 200 [MEASURED] |
| Duration | 0.995 s [MEASURED] |
| Nominal Rate | 200.0 Hz [ASSUMED] |
| Observed Frequency | 200.0 Hz [DERIVED] |
| Mean Sample Interval | 5.0 ms [MEASURED] |
| Timing Jitter | 0.0 ms [MEASURED] |
| Suspected Dropped Samples | 0 [DERIVED] |
| Mean Accel Magnitude | 9.8219 m/s^2 [MEASURED] |
| Mean Gyro Magnitude | 0.02594 rad/s [MEASURED] |

## Key Observations & Conclusions

- IMU sampling frequency is verified empirically against nominal manufacturer ratings.
- Timing jitter quantifies operating system bus latency or USB packet buffering delays.
- Accelerometer and gyroscope baseline offsets reveal stationary sensor bias that must be estimated during filter initialization.
