# 06 — Communication Architecture

## Design Principle

The communication link between the UAV and the ground station is for **mission-level commands and telemetry only**. The UAV must navigate autonomously without requiring ground computation.

## Communication Flow

```
GROUND STATION                              UAV
     │                                       │
     │──── Mission Commands (uplink) ───────►│
     │     TAKEOFF                           │
     │     SEARCH <area>                     │
     │     RETURN                            │
     │     ABORT                             │
     │     STATUS                            │
     │                                       │
     │◄─── Telemetry (downlink) ────────────│
     │     Position estimate                 │
     │     Battery status                    │
     │     Mission progress                  │
     │     System health                     │
     │     Alerts / warnings                 │
```

## What Travels Over the Link

### Uplink (Ground → UAV): LOW BANDWIDTH

- Mission commands (text-level commands, ~bytes)
- Parameter updates (configuration changes)
- Emergency abort signal

### Downlink (UAV → Ground): LOW-MEDIUM BANDWIDTH

- Position and attitude estimates (~100 bytes, 1-10 Hz)
- Battery voltage and current (~10 bytes, 1 Hz)
- Mission state and progress (~50 bytes, 1 Hz)
- System health / diagnostics (~100 bytes, 1 Hz)
- Compressed key images (if permitted and bandwidth allows)

### What Does NOT Travel Over the Link

- Raw LiDAR point clouds (too large)
- Raw camera frames (too large)
- Raw IMU data (too frequent)
- Navigation computation results (stays onboard)
- Control loop data (stays on Pixhawk)

## Bandwidth Estimation

> ⏳ **PENDING:** Exact bandwidth requirements will be determined by EXP-01 (LiDAR data rates) and EXP-02 (camera data rates), combined with compression analysis.

## Key Question

> **Q9:** What communication bandwidth is actually necessary?
> **Q10:** What information needs to be sent to the ground station?
> **Q11:** What information must remain onboard?

These are answered by experiments, not assumptions.

## Competition Constraint

> ⚠️ **IRoC-U 2026 rules state:** "No telemetry or remote piloting during the mission."
>
> This may mean the RF link can only be used for specific phases (e.g., pre-mission upload, post-mission download). **This must be verified for our competition year.**
