# Requirements Traceability Matrix

## Purpose

Trace each requirement to its source, the design response, the validating experiment, and the current status.

## Matrix

| Req ID | Requirement | Source | Priority | Design Response | Validating Experiment | Metric | Result | Status |
|--------|-------------|--------|----------|----------------|----------------------|--------|--------|--------|
| REQ-NAV-001 | Navigate without GPS/GNSS | Competition rules (TO BE VERIFIED) | CRITICAL | LiDAR+Camera+IMU navigation stack | EXP-03, EXP-05, EXP-07 | Position drift (m/100m) | TBD | OPEN |
| REQ-NAV-002 | All nav computation onboard | DEC-001, competition rules | CRITICAL | Onboard computer runs full pipeline | EXP-09, EXP-10 | Processing rate (Hz), latency (ms) | TBD | OPEN |
| REQ-SEN-001 | Total mass < 2 kg | Competition rules (TO BE VERIFIED) | CRITICAL | Lightweight sensor and compute selection | Physical measurement | Total mass (g) | TBD | OPEN |
| REQ-COM-001 | Mission-level communication only | DEC-001, competition rules | HIGH | Ground station sends commands, UAV navigates independently | Architecture review | Communication bandwidth (kbps) | TBD | OPEN |
| REQ-SAF-001 | Emergency safe landing | Competition rules (TO BE VERIFIED) | CRITICAL | Pixhawk failsafe + mission manager abort | Flight testing | Landing success rate | TBD | OPEN |
| REQ-SAF-002 | Return home on low battery | Competition rules (TO BE VERIFIED) | HIGH | Battery monitor → mission manager → return | Flight testing | Return success rate | TBD | OPEN |
| REQ-PWR-001 | Battery operation only | Competition rules (TO BE VERIFIED) | CRITICAL | LiPo battery, power-efficient components | Power budget analysis | Total power (W), flight time (min) | TBD | OPEN |

## Notes

- **TBD** = To Be Determined — experiment not yet run
- **TO BE VERIFIED** = Competition source not yet confirmed for our year
- Results will be populated as experiments are completed
- New rows should be added as requirements are identified
