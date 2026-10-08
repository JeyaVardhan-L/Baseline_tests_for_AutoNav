# EXP-05: Data Rate + Computational Load Summary

## Measured & Derived Metrics

| Metric | Value |
|---|---|
| Frames Profiled | 10 |
| Nominal Sensor Hz | 10.0 Hz [ASSUMED] |
| Sensor Period | 100.00 ms [DERIVED] |
| Mean Pipeline Latency | 170.43 ms [MEASURED] |
| P95 Pipeline Latency | 172.80 ms [MEASURED] |
| P99 Pipeline Latency | 173.00 ms [MEASURED] |
| Max Pipeline Latency | 173.05 ms [MEASURED] |
| Host Real-Time Status | CANNOT KEEP UP (LAG OCCURS) [DERIVED] |

## Key Observations & Conclusions

- Stage timing breakdown reveals the primary computational bottleneck in the point cloud processing pipeline.
- Evaluating both mean and P95 latency demonstrates why average timing alone is insufficient for real-time robotic systems (tail latency causes buffer backlog).
- This result is a baseline measurement of the host CPU and must not be interpreted as final UAV companion computer capability.
