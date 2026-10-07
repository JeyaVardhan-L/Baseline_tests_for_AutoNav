# System Requirements

## Purpose

Capture system-level requirements derived from the mission, competition constraints, and engineering analysis.

## Requirement Categories

| Prefix | Category |
|--------|----------|
| REQ-NAV | Navigation |
| REQ-SEN | Sensors |
| REQ-COM | Communication |
| REQ-SAF | Safety |
| REQ-PWR | Power |
| REQ-SYS | System |

## Requirements

### REQ-NAV-001 — GPS-Denied Navigation

| Field | Value |
|-------|-------|
| **Requirement** | The system shall support autonomous navigation without relying on GPS/GNSS. |
| **Source** | Competition objective — TO BE VERIFIED AGAINST OFFICIAL RULES |
| **Priority** | CRITICAL |
| **Validation** | EXP-03, EXP-05, EXP-07, flight testing |
| **Status** | OPEN |

### REQ-NAV-002 — Onboard Processing

| Field | Value |
|-------|-------|
| **Requirement** | All navigation computation shall run onboard the UAV. |
| **Source** | DEC-001, competition constraints |
| **Priority** | CRITICAL |
| **Validation** | EXP-09, EXP-10 |
| **Status** | OPEN |

### REQ-SEN-001 — Mass Budget

| Field | Value |
|-------|-------|
| **Requirement** | Total UAV mass, including all sensors and computing, shall be less than 2 kg. |
| **Source** | Competition constraint — TO BE VERIFIED |
| **Priority** | CRITICAL |
| **Validation** | Physical measurement during integration |
| **Status** | OPEN |

### REQ-COM-001 — Mission-Level Communication

| Field | Value |
|-------|-------|
| **Requirement** | Communication link shall provide mission-level control. Navigation shall not depend on continuous ground communication. |
| **Source** | DEC-001, competition constraints |
| **Priority** | HIGH |
| **Validation** | Architecture review, integration testing |
| **Status** | OPEN |

### REQ-SAF-001 — Emergency Safe Landing

| Field | Value |
|-------|-------|
| **Requirement** | The system shall implement an emergency safe-landing mode triggered by low battery, lost link, or system malfunction. |
| **Source** | Competition constraint — TO BE VERIFIED |
| **Priority** | CRITICAL |
| **Validation** | Flight testing |
| **Status** | OPEN |

### REQ-SAF-002 — Return Home on Low Battery

| Field | Value |
|-------|-------|
| **Requirement** | The system shall detect low battery and autonomously navigate to the home position. |
| **Source** | Competition constraint — TO BE VERIFIED |
| **Priority** | HIGH |
| **Validation** | Flight testing |
| **Status** | OPEN |

### REQ-PWR-001 — Battery Operation

| Field | Value |
|-------|-------|
| **Requirement** | The system shall operate solely on battery power. |
| **Source** | Competition constraint — TO BE VERIFIED |
| **Priority** | CRITICAL |
| **Validation** | Power budget analysis + flight testing |
| **Status** | OPEN |

---

*New requirements should be appended with the next sequential ID.*
