# Point Cloud Basics: Representation, Memory, and Math

This guide explains what a **point cloud** is, how computers store it in RAM, and how basic geometric operations work.

---

## 1. What is a 3D Point?

In a computer, a 3D point is a collection of 3 numbers representing Cartesian coordinates relative to a reference coordinate system:

$$\mathbf{p} = \begin{bmatrix} x \\ y \\ z \end{bmatrix}$$

- $x$: Distance forward (+) or backward (-) in meters.
- $y$: Distance left (+) or right (-) in meters.
- $z$: Distance up (+) or down (-) in meters.

In addition to coordinates, sensor points often carry auxiliary attributes:
- **Intensity ($i$)**: Reflectivity of the target surface (0.0 to 1.0 or 0 to 255).
- **Ring ($r$)**: Which laser beam produced this point (e.g. laser 0 through 63 on a 64-beam LiDAR).
- **Point Timestamp ($t_{\text{rel}}$)**: The fractional microsecond offset when this specific laser fired during the scan.

---

## 2. What is a Point Cloud?

A **Point Cloud** is an unordered collection of thousands or millions of 3D points recorded in a single temporal sweep of the sensor:

$$\mathcal{P} = \{ \mathbf{p}_1, \mathbf{p}_2, \mathbf{p}_3, \dots, \mathbf{p}_N \}$$

Where $N$ is the **point count** (typically 50,000 to 200,000 points per frame for an autonomous robot LiDAR).

---

## 3. How Much Memory Does a Point Cloud Occupy?

Computers store real numbers as **32-bit floating-point numbers (`float32`)**.
- $1 \text{ byte} = 8 \text{ bits}$
- A 32-bit float occupies **4 bytes** of memory.

### Step-by-Step Calculation for 1 Point
Each point has:
- $X$ coordinate $\rightarrow 4 \text{ bytes}$
- $Y$ coordinate $\rightarrow 4 \text{ bytes}$
- $Z$ coordinate $\rightarrow 4 \text{ bytes}$
- Intensity $\rightarrow 4 \text{ bytes}$
- Ring index $\rightarrow 4 \text{ bytes}$ (`int32`)
- **Total per point** = $4 + 4 + 4 + 4 + 4 = 20 \text{ bytes}$ (or $12 \text{ bytes}$ for minimal XYZ coordinates).

### Calculation for a Complete Frame (100,000 Points)
If one frame contains **100,000 points** and each point occupies **16 bytes** (X, Y, Z, Intensity):

$$100,000 \text{ points} \times 16 \text{ bytes/point} = 1,600,000 \text{ bytes}$$

To convert bytes to Megabytes (decimal):
$$\frac{1,600,000 \text{ bytes}}{1,000,000} = 1.6 \text{ MB per frame}$$

To convert bytes to Mebibytes (binary):
$$\frac{1,600,000 \text{ bytes}}{1,048,576} \approx 1.526 \text{ MiB per frame}$$

---

## 4. How Much Data Arrives Per Second (Data Rate)?

If the sensor fires **10 frames per second** (10 Hz):

$$\text{Data Rate} = 1.6 \text{ MB/frame} \times 10 \text{ frames/sec} = 16.0 \text{ MB/s}$$

### Storage Rate Over Time
- **Per Minute**: $16.0 \text{ MB/s} \times 60 \text{ s} = 960 \text{ MB/min} \approx 0.96 \text{ GB/min}$.
- **Per Hour**: $0.96 \text{ GB/min} \times 60 \text{ min} = 57.6 \text{ GB/hour}$.

This is why an autonomous drone **cannot simply record all raw point clouds to a slow micro-SD card**. The onboard computer must filter, downsample, and extract navigation features in RAM in real time.

---

## 5. Basic Math: Euclidean Range

How far is a point $(x, y, z)$ from the sensor? By the 3D Pythagorean theorem:

$$r = \sqrt{x^2 + y^2 + z^2}$$

### Numerical Example
A point has coordinates $x = 3.0 \text{ m}$, $y = 4.0 \text{ m}$, $z = 0.0 \text{ m}$:
$$r = \sqrt{3^2 + 4^2 + 0^2} = \sqrt{9 + 16 + 0} = \sqrt{25} = 5.0 \text{ meters}$$

---

## 6. What is Downsampling (Voxel Grid)?

A raw point cloud contains huge redundancy: thousands of points might be concentrated on a flat wall 1 meter away, while distant obstacles only have a few points.

A **Voxel Grid Filter** divides 3D space into small cubes called **voxels** (e.g. $0.2 \text{ m} \times 0.2 \text{ m} \times 0.2 \text{ m}$). All points that land inside the same voxel are averaged into a single centroid point.

### Why Downsample?
- Reduces point count from 100,000 down to 15,000 (an **85% reduction**).
- Reduces memory from 1.6 MB down to 0.24 MB.
- Speeds up nearest-neighbor search algorithms by a factor of 10x to 50x without losing the macro-geometry of obstacles!
