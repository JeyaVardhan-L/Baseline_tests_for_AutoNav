# Source Code

## Purpose

This directory will contain the production source code for the autonomous navigation stack.

## Planned Structure

```
src/
├── README.md            # This file
├── sensor_fusion/       # Sensor fusion module
├── odometry/            # Pose estimation (LiDAR + visual odometry)
├── mapping/             # Local mapping
├── planning/            # Path planning
├── mission/             # Mission manager
├── communication/       # Ground station communication
└── common/              # Shared utilities
```

## Status

**NOT YET IMPLEMENTED.** Production code is planned for Phase 2+.

Phase 1 experiment scripts are in `experiments/*/scripts/`, not here. Code will be promoted to `src/` when it matures from experimental to production quality.
