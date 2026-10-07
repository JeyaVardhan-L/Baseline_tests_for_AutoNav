# 08 — Hardware Selection

## Status

```
╔══════════════════════════════════════════════════════════════╗
║  FINAL HARDWARE SELECTION: PENDING EXPERIMENTAL RESULTS      ║
╚══════════════════════════════════════════════════════════════╝
```

## Selection Process

Hardware will be selected based on **measured evidence**, not assumptions.

```
EXP-01 (LiDAR data)  ──┐
EXP-02 (Camera data)  ──┤
EXP-03 (LiDAR odom)  ──┤
EXP-04 (Visual odom)  ──┼──► Computing Requirements ──► Compute Selection
EXP-05 (Fusion)       ──┤
EXP-09 (Benchmark)    ──┤
EXP-10 (Latency)      ──┘
                          ├──► Sensor Requirements  ──► LiDAR Selection
                          └──► Weight/Power Budget  ──► Final BOM
```

## What We Need Before Selecting

### Before selecting a LiDAR:

- [ ] Measured data rates at various point densities (EXP-01)
- [ ] Minimum range requirements for our mission (EXP-06)
- [ ] Minimum angular resolution for mapping (EXP-06)
- [ ] Weight and power budget allocation

### Before selecting an onboard computer:

- [ ] Measured CPU requirements for LiDAR odometry (EXP-03)
- [ ] Measured CPU requirements for visual odometry (EXP-04)
- [ ] Measured GPU requirements (if any) (EXP-03/04)
- [ ] Measured RAM requirements (EXP-01/09)
- [ ] Measured end-to-end latency (EXP-10)
- [ ] Power budget allocation

## Current Candidate Documents

- [`hardware/candidate-lidars.md`](../hardware/candidate-lidars.md) — LiDAR comparison framework
- [`hardware/candidate-compute.md`](../hardware/candidate-compute.md) — Compute comparison framework
- [`hardware/preliminary-bom.md`](../hardware/preliminary-bom.md) — Bill of materials (draft)

## Decision Gate

Hardware purchase will be proposed only when:

1. Phase 1 experiments provide measured performance requirements
2. Candidate hardware is evaluated against measured requirements
3. Weight/power/thermal budgets are verified
4. A clear justification document is prepared for the Director
