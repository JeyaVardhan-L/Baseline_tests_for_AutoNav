# 01 — Mission Requirements

## Competition Source

**ISRO Robotics Challenge – URSC (IRoC-U)**
Theme: *ASCEND — Autonomous Surveyor Challenge for Exploration, Navigation and Dynamics*

> ⚠️ **ASSUMPTION (ASM-004):** Requirements below are derived from IRoC-U 2026 rules. Rules for our specific competition year must be re-verified when officially published.

## Mission Profile

The UAV must autonomously:

1. Depart from the base station
2. Acquire target characteristics
3. Search a designated area for features
4. Return to the base station
5. Perform data transfer
6. Execute autonomous landing
7. Power recharge

## Hard Constraints

| Constraint | Requirement | Source | Verified? |
|-----------|-------------|--------|-----------|
| UAV mass | < 2 kg | IRoC-U 2026 rules | FOR 2026 ONLY |
| Navigation | No GPS/GNSS, pseudolites, or reflector arrays | IRoC-U 2026 rules | FOR 2026 ONLY |
| Power | Battery-operated only | IRoC-U 2026 rules | FOR 2026 ONLY |
| Communication | RF radiation mode only | IRoC-U 2026 rules | FOR 2026 ONLY |
| Telemetry | No telemetry or remote piloting during autonomous mission | IRoC-U 2026 rules | FOR 2026 ONLY |
| Software | Indigenously developed algorithms | IRoC-U 2026 rules | FOR 2026 ONLY |
| Safety | Emergency "call off" mode required | IRoC-U 2026 rules | FOR 2026 ONLY |
| Safety | Safe landing on low battery / lost-link / malfunction | IRoC-U 2026 rules | FOR 2026 ONLY |
| Regulatory | Comply with Drone Rules-2021 (or latest) | IRoC-U 2026 rules | FOR 2026 ONLY |

## Derived Requirements

These are requirements we derive from the competition constraints. They are engineering decisions, not competition rules.

| ID | Requirement | Derived From | Status |
|----|-------------|-------------|--------|
| REQ-NAV-001 | System shall navigate without GPS/GNSS | Competition constraint | OPEN |
| REQ-NAV-002 | All navigation computation shall run onboard | Competition + design decision | OPEN |
| REQ-SEN-001 | Sensor suite shall fit within 2 kg total UAV mass budget | Competition constraint | OPEN |
| REQ-COM-001 | Communication shall provide mission-level control only | Competition constraint | OPEN |
| REQ-SAF-001 | System shall implement emergency safe-landing | Competition constraint | OPEN |
| REQ-SAF-002 | System shall detect low-battery and return home | Competition constraint | OPEN |
| REQ-PWR-001 | Total system power shall be within battery capacity | Competition + physics | OPEN |

## Open Questions

- What is the exact area of the search zone?
- What are the "target characteristics" to identify?
- What is the maximum flight time expected?
- What are the altitude constraints?
- What is the exact landing accuracy required?
- Are there obstacle specifications?

> These questions can only be answered when we obtain the official rules for our competition year.
