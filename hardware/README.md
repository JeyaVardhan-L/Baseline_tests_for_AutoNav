# Hardware Selection Methodology & Evidence Boundary

> [!CRITICAL]
> **NO HARDWARE IS SELECTED OR PURCHASED IN PHASE 1.**  
> We do NOT assume or claim that a particular companion computer (e.g. Jetson Orin Nano, Raspberry Pi) or LiDAR sensor is required until empirical experiments provide concrete measurements.

---

## Purpose of This Directory

This directory will eventually store the formal Bill of Materials (BOM), electrical wiring diagrams, power distribution architecture, and mass budget spreadsheets.

However, during Phase 1, **this directory serves as the boundary guarding against premature hardware decisions**.

---

## How Hardware Specifications Will Be Derived

Future hardware requirements will be derived directly from experimental findings:

1. **Sensor Processing Rate**: Established in EXP-02, EXP-05, EXP-09.
2. **Algorithm Execution Latency**: Established in EXP-04, EXP-05, EXP-09.
3. **RAM Memory Footprint**: Established in EXP-02, EXP-06.
4. **Communication Bandwidth**: Established in EXP-02, EXP-06, EXP-07.
5. **Synchronization Requirements**: Established in EXP-07, EXP-08.
6. **Aeronautical Constraints**: Maximum Takeoff Weight (MTOW), available flight battery Watt-hours, and thermal cooling limits.

See [`docs/06-hardware/hardware-requirements-methodology.md`](../docs/06-hardware/hardware-requirements-methodology.md) for the complete engineering methodology.
