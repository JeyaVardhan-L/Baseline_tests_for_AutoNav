# LiDAR-Only ICP Odometry Baseline Report

## Measured & Derived Metrics

| Metric | Value |
|---|---|
| Dataset | Synthetic Demonstration Stream |
| Frames Processed | 20 frames |
| Path Length | 0.036 m |
| Registration Success Rate | 100.0% |
| P95 Latency | 308.90 ms |
| Real-Time Status | FAIL (CANNOT KEEP UP) |
| Host Process RAM | 67.68 MB |

## Key Observations & Conclusions

- Processed 20 LiDAR frames with 100.0% successful scan registrations.
- Estimated total trajectory length of 0.036 meters.
- P95 registration latency was 308.90 ms vs 100.0 ms arrival deadline (FAIL (CANNOT KEEP UP)).
- Process memory stabilized at 67.68 MB RSS with no memory leakage.
- Measurements were recorded on host test machine; target embedded hardware (Raspberry Pi 5) remains unverified until deployed.
