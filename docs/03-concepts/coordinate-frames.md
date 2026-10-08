# Concept: Coordinate Frames in Robotics

In autonomous robotics, numbers have no meaning without specifying **which coordinate frame** they belong to.

---

## 1. Standard Reference Frames (REP 103 / REP 105)

1. **`world` / `map` Frame**: An inertial, earth-fixed global Cartesian frame. Its origin $(0,0,0)$ is often the takeoff point or ground station antenna.
2. **`odom` Frame**: A smooth, continuous local odometry frame. It does not jump, but can drift slowly over time.
3. **`base_link` Frame**: Rigidly attached to the center of gravity of the drone. As the drone pitches forward, the $X$ axis tilts forward with the vehicle body.
4. **`lidar_link` / `camera_link`**: Attached to the physical optical center of the sensor. Points measured by LiDAR arrive in `lidar_link`.

---

## 2. Rigid Body Transformation

To transform a point $\mathbf{p}_{\text{lidar}}$ into the drone's body frame $\mathbf{p}_{\text{base}}$:

$$\mathbf{p}_{\text{base}} = \mathbf{R}_{\text{base}}^{\text{lidar}} \mathbf{p}_{\text{lidar}} + \mathbf{t}_{\text{base}}^{\text{lidar}}$$

Where $\mathbf{R}$ is a $3 \times 3$ Rotation Matrix and $\mathbf{t}$ is a $3 \times 1$ Translation Vector (the extrinsic sensor calibration).
