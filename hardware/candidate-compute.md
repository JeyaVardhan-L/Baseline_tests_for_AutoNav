# Candidate Compute Modules

## Status

```
FINAL SELECTION: PENDING EXPERIMENTAL RESULTS
```

## Evaluation Framework

| Criterion | Unit | Why It Matters |
|-----------|------|---------------|
| CPU | — | Core count, architecture, clock speed |
| GPU | — | CUDA cores, compute capability |
| RAM | GB | Must hold point clouds, maps, images in memory |
| AI acceleration | TOPS | For neural-network-based perception if needed |
| Storage | GB | For logging, maps |
| Power consumption | W | Must fit battery budget |
| Weight | g | Must fit 2 kg UAV budget |
| Thermal | — | Passive cooling preferred (no fan = less weight/power) |
| Interfaces | — | USB, UART, Ethernet, GPIO |
| ROS 2 support | — | Native Ubuntu/ROS 2 compatibility |
| CUDA / OpenCL | — | GPU compute framework support |
| Estimated throughput | — | Based on EXP-09 benchmarks |
| Price | ₹ | Budget constraint |
| Availability | — | Lead time, Indian availability |

## Candidates

> ⚠️ The table below contains **preliminary candidates only**. No benchmarking has been performed.

| # | Model | CPU | GPU | RAM | Power | Weight | Price (est.) | Status |
|---|-------|-----|-----|-----|-------|--------|-------------|--------|
| 1 | NVIDIA Jetson Orin Nano | 6-core Arm A78AE | 1024-core Ampere | 4/8 GB | 7-15 W | ~60 g (module) | ~₹20,000-30,000 | TO BE EVALUATED |
| 2 | NVIDIA Jetson Orin NX | 8-core Arm A78AE | 1024-core Ampere | 8/16 GB | 10-25 W | ~60 g (module) | ~₹40,000-60,000 | TO BE EVALUATED |
| 3 | Raspberry Pi 5 | 4-core Arm A76 | VideoCore VII | 4/8 GB | 5-12 W | ~45 g | ~₹6,000-8,000 | TO BE EVALUATED |
| 4 | Orange Pi 5 | RK3588S | Mali-G610 | 4-16 GB | 5-15 W | ~60 g | ~₹8,000-15,000 | TO BE EVALUATED |
| 5 | Khadas VIM4 | A311D2 | Mali-G52 | 8 GB | ~10 W | ~50 g | ~₹15,000-20,000 | TO BE EVALUATED |

> **Note:** All specifications are approximate. Carrier board adds weight and power. Must verify with official specifications.

## Evaluation Process

1. EXP-01 through EXP-08 determine computational requirements
2. EXP-09 benchmarks the full pipeline on available hardware
3. Requirements are compared against candidate specifications
4. Shortlist is prepared with justification
5. Director reviews evidence and approves purchase

## Key Trade-Offs

- **Performance vs. Power:** More compute = more watts = less flight time
- **GPU vs. CPU-only:** GPU enables neural-network inference but adds complexity and power
- **Weight:** Module alone is light; carrier board, heatsink, and cables add up
- **Cost:** Jetson provides best compute/watt but costs more
- **Ecosystem:** Jetson has best CUDA/ROS support; Pi has largest community
