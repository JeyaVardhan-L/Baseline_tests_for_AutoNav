# NumPy in Autonomous Robotics

## Why Does NumPy Exist in This Project?

Standard Python lists (`[1.0, 2.0, 3.0]`) store numbers as individual dynamic objects with overhead pointers. When dealing with **100,000 points per frame at 10 Hz** (1,000,000 points per second), standard Python `for` loops take seconds to run, completely missing real-time deadlines.

**NumPy** provides contiguous, memory-efficient C-backed N-dimensional arrays (`ndarray`) and vectorized mathematical operations that run at near-hardware C/assembly speed.

---

## 1. How Point Clouds Are Represented in NumPy

A 3D LiDAR point cloud is stored as a 2D NumPy array:

```python
import numpy as np

# Shape: (N, 3), dtype: float32
points = np.zeros((100000, 3), dtype=np.float32)
```

- `points.shape[0]`: Point count ($N = 100,000$).
- `points.shape[1]`: Spatial dimensions ($3 \rightarrow X, Y, Z$).
- `points.nbytes`: Exact RAM footprint in bytes ($100,000 \times 3 \times 4 = 1,200,000\text{ bytes} \approx 1.2\text{ MB}$).

---

## 2. Fast Vectorized Math Examples

### Calculating Euclidean Distances for 100,000 Points
Instead of writing a slow loop:
```python
# SLOW (Python loop): ~120 ms
ranges = [math.sqrt(p[0]**2 + p[1]**2 + p[2]**2) for p in points]

# FAST (NumPy vectorized C code): ~1.2 ms (100x faster!)
ranges = np.linalg.norm(points, axis=1)
```

### Removing Invalid / NaN Points in One Line
```python
valid_mask = np.isfinite(points).all(axis=1)
clean_points = points[valid_mask]
```

### Pure-NumPy 3D Voxel Grid Downsampling
In this repository, we implemented a custom voxel grid downsampler using `np.floor` and `np.unique` that performs grid hashing in pure vectorized NumPy without requiring external compiled C++ binaries!
