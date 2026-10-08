# Local Mapping for Obstacle Avoidance

An autonomous drone cannot plan a collision-free path without an accurate spatial model of its surroundings.

---

## 1. 3D Occupancy Grids (OctoMap / Voxel Grids)

A raw point cloud is just a list of points on surfaces. It does **not explicitly represent free space**. If there are no points in an area, is it open air, or an unobserved region behind a solid concrete wall?

An **Occupancy Grid** discretizes 3D space into small volumetric voxels (e.g. $0.1\text{ m} \times 0.1\text{ m} \times 0.1\text{ m}$ cubes):
- **Occupied Voxels**: Voxels containing detected LiDAR points (obstacles).
- **Free Voxels**: Voxels traversed by the laser ray from the sensor to the obstacle without hitting anything (safe open air for flying).
- **Unknown Voxels**: Occluded regions behind walls or beyond sensor range (forbidden to plan through).

---

## 2. Inflation and Safety Margins

A quadcopter is not a single infinitesimal point in space; it has physical body dimensions (e.g. $50\text{ cm}$ propeller-tip-to-tip diameter).

Before path planning, all occupied voxels are **inflated** by a safety radius:
$$R_{\text{inflation}} = R_{\text{drone}} + D_{\text{safety margin}}$$

For a 0.25 m drone radius and 0.25 m safety margin, obstacles are expanded by $0.5\text{ m}$. Any path planned through the remaining free space is mathematically guaranteed to keep the drone's propeller blades clear of physical contact.
