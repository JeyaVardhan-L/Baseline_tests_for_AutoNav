# Candidate LiDAR Sensors

## Status

```
FINAL SELECTION: PENDING EXPERIMENTAL RESULTS
```

## Evaluation Framework

Each candidate LiDAR will be evaluated against these criteria:

| Criterion | Unit | Why It Matters |
|-----------|------|---------------|
| Range | m | Maximum detection distance |
| Minimum range | m | Closest detectable distance (important for indoor/close obstacles) |
| FOV (horizontal) | ° | Coverage area per scan |
| FOV (vertical) | ° | Vertical coverage |
| Angular resolution | ° | Spatial detail |
| Update rate | Hz | Scan frequency |
| Points/sec | pts/s | Total data throughput |
| Accuracy | cm | Range measurement accuracy |
| Weight | g | Must fit within 2 kg UAV budget |
| Dimensions | mm | Must fit on UAV frame |
| Power consumption | W | Must fit within battery budget |
| Interface | — | USB, Ethernet, UART, etc. |
| Output format | — | Point cloud format |
| Driver support | — | Linux, ROS 2 compatibility |
| ROS 2 support | — | Native driver availability |
| Environmental | — | IP rating, temperature range |
| Price | ₹ | Budget constraint |
| Availability | — | Lead time, Indian availability |

## Candidates

> ⚠️ The table below contains **preliminary candidates only**. No evaluation has been performed. Specifications must be verified from official datasheets.

| # | Model | Type | Range | FOV (H×V) | Rate | Pts/s | Weight | Power | Price (est.) | Status |
|---|-------|------|-------|-----------|------|-------|--------|-------|-------------|--------|
| 1 | Livox Mid-360 | Non-repetitive | ~40 m | 360°×59° | 10 Hz | ~200k | ~265 g | ~9 W | ~₹70,000 | TO BE EVALUATED |
| 2 | Livox Avia | Non-repetitive | ~190 m | 70.4°×77.2° | 10 Hz | ~240k | ~498 g | ~10 W | ~₹80,000 | TO BE EVALUATED |
| 3 | Ouster OS0-32 | Spinning | ~50 m | 360°×90° | 10-20 Hz | ~655k | ~447 g | ~14 W | ~₹1,20,000 | TO BE EVALUATED |
| 4 | LD-19 / LD-06 | 2D | ~12 m | 360° (2D) | ~10 Hz | ~4.5k | ~50 g | ~1.5 W | ~₹3,000 | TO BE EVALUATED |
| 5 | Intel RealSense L515 | Solid-state depth | ~9 m | 70°×55° | 30 Hz | ~23M | ~100 g | ~3.5 W | Discontinued | TO BE EVALUATED |

> **Note:** All specifications above are approximate estimates from publicly available information. They must be verified from official vendor datasheets before any purchase decision.

## Evaluation Process

1. EXP-01 determines what data rates and processing loads look like
2. EXP-03 / EXP-06 determine minimum range, resolution, and FOV requirements
3. Weight and power budgets are finalized
4. Candidates are evaluated against measured requirements
5. Top candidates are shortlisted with justification
6. Director reviews evidence and approves purchase

## Key Trade-Offs

- **Range vs. Weight:** Longer-range LiDARs are typically heavier
- **Resolution vs. Data Rate:** More points = more processing = more compute needed
- **Cost vs. Capability:** High-end sensors may exceed budget
- **2D vs. 3D:** 2D LiDAR is much lighter/cheaper but provides less information
