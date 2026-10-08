# EXP-09: End-to-End Real-Time Pipeline Summary

## Measured & Derived Metrics

| Metric | Value |
|---|---|
| Frames Benchmarked | 10 [MEASURED] |
| Sensor Frequency | 10.0 Hz [ASSUMED] |
| Sensor Period Budget | 100.00 ms [DERIVED] |
| Total Pipeline Mean | 164.49 ms [MEASURED] |
| Total Pipeline P95 | 167.28 ms [MEASURED] |
| Mean Available Margin | -64.49 ms [DERIVED] |
| P95 Available Margin | -67.28 ms [DERIVED] |
| Real-Time Pass Rate | 0.0% [DERIVED] |
| Host Real-Time Status | CANNOT KEEP UP (LAG OCCURS) [DERIVED] |

## Key Observations & Conclusions

- Sequential breakdown demonstrates exact execution latencies across Read, Decode, Validate, Filter, Downsample, and Visualize stages.
- Available Margin ($T_s - T_p$) proves whether spare CPU capacity exists for subsequent state estimation (odometry, mapping, and planning).
- This empirical measurement forms the host baseline required before conducting embedded hardware evaluations.
