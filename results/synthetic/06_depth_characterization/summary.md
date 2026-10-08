# EXP-06: Depth Characterization Summary

## Measured & Derived Metrics

| Metric | Value |
|---|---|
| Frames Analyzed | 10 [MEASURED] |
| Image Resolution | 320x240 [MEASURED] |
| Valid Pixel Coverage | 100.0% [MEASURED] |
| Mean Detected Depth | 3.89 m [MEASURED] |
| Median Detected Depth | 3.90 m [MEASURED] |
| Average Frame Size | 0.513 MB [MEASURED] |
| Mean Processing Latency | 11.46 ms [MEASURED] |
| P95 Processing Latency | 20.31 ms [MEASURED] |
| Host Processing Rate | 87.3 FPS [DERIVED] |
| Host RAM Footprint | 41.6 MB [MEASURED] |

## Key Observations & Conclusions

- Depth images provide dense per-pixel geometric distances in a structured 2D grid format.
- Valid pixel coverage highlights sensor dropouts (e.g., specular surfaces, sunlight wash-out, or objects beyond sensor range).
- Pinhole back-projection enables instantaneous conversion from 2D depth grids to 3D metric point clouds for navigation and obstacle avoidance.
