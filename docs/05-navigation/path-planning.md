# Path Planning for Autonomous UAVs

**Path Planning** is the computational process of finding a safe, smooth, and kinodynamically feasible 3D trajectory from the drone's current position to a target destination.

---

## 1. Global vs. Local Planning

- **Global Path Planner (Low Rate: 0.5 – 2 Hz)**:
  - Considers the entire explored map.
  - Finds a topological route through corridors and rooms (e.g. using A*, Dijkstra, or PRM).
  - Outputs a sequence of 3D waypoints $[W_1, W_2, \dots, W_k]$.

- **Local Trajectory Planner (High Rate: 10 – 20 Hz)**:
  - Operates over the immediate local sensor field (e.g. 5 to 10 meters around the drone).
  - Reacts instantly to newly detected dynamic obstacles (e.g. a moving person or swinging crane).
  - Optimizes a continuous polynomial or uniform B-spline curve minimizing snap/jerk while staying within aerodynamic velocity ($v_{\max}$) and acceleration ($a_{\max}$) constraints.
