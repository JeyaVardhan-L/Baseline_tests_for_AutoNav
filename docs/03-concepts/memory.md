# Concept: Memory (RAM) Requirements

**Random Access Memory (RAM)** stores operating system state, active processes, and sensor buffer queues.

---

## 1. Static vs. Dynamic Memory Allocation

In an autonomous navigation software stack:
1. **Raw Sensor Ring Buffers**: Circular FIFO queues holding recent incoming frames (e.g. 10 frames of 1.6 MB $\approx 16\text{ MB}$).
2. **Intermediate Point Cloud Copies**: Read buffer $\rightarrow$ Valid array $\rightarrow$ Range filtered array $\rightarrow$ Downsampled array $\approx 10\text{ MB}$ per frame during processing.
3. **Local Volumetric Map**: 3D voxel grid or octree storing observed obstacles over the past 100 meters $\approx 100\text{ MB}$ to $500\text{ MB}$.
4. **Trajectory Optimization Trees**: A* / RRT* search nodes $\approx 50\text{ MB}$.

---

## 2. Embedded RAM Constraints

While desktop PCs have 16 GB to 64 GB of RAM, embedded single-board computers often have **4 GB or 8 GB of unified memory** shared between CPU and GPU. Memory leaks or unbounded map accumulation will trigger the Linux Out-Of-Memory (OOM) Killer, terminating the navigation process mid-flight!
