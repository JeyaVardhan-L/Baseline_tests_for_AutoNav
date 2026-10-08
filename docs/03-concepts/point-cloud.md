# Concept: Point Cloud

A **Point Cloud** is a discrete geometric representation of the physical world consisting of thousands or millions of individual 3D coordinate points measured by an active sensor.

---

## 1. Structure

Each point $\mathbf{p}_i$ is represented as:
$$\mathbf{p}_i = [x_i, y_i, z_i, \dots]$$

Where:
- $x$: Longitudinal axis (meters forward).
- $y$: Lateral axis (meters left).
- $z$: Vertical axis (meters upward).

---

## 2. Numerical Memory Example

If a LiDAR produces **100,000 points** per scan:
- Each coordinate is a 32-bit float ($4 \text{ bytes}$).
- Coordinates $[x, y, z]$ occupy: $3 \times 4 = 12 \text{ bytes}$.
- Intensity adds: $1 \times 4 = 4 \text{ bytes}$.
- Total per point: $16 \text{ bytes}$.

### Total Frame Memory:
$$100,000 \times 16 \text{ bytes} = 1,600,000 \text{ bytes} = 1.6 \text{ MB}$$

In binary units:
$$\frac{1,600,000}{1,048,576} \approx 1.526 \text{ MiB}$$
