# Concept: Point Density

**Point Density** measures how closely points are packed together in space. It is typically expressed as points per square meter ($\text{pts/m}^2$) or points per cubic meter ($\text{pts/m}^3$).

---

## 1. The Inverse Square Law in Point Clouds

Because LiDAR laser beams fan out angularly from the sensor, **point density decreases rapidly with distance**:

- At **$1\text{ meter}$**, consecutive laser beams are spaced millimeters apart $\rightarrow$ ultra-high point density.
- At **$30\text{ meters}$**, the same angular beam separation translates to points spaced meters apart $\rightarrow$ sparse point density.

---

## 2. Why Point Density Matters for UAV Navigation

1. **Obstacle Detection Reliability**: Thin obstacles like power lines, tree branches, and chain-link fences can slip between sparse laser beams if the drone is flying too far away.
2. **Registration Stability**: Scan-matching algorithms (ICP, NDT) require overlapping dense patches between consecutive frames to compute displacement without slipping along featureless corridors.
