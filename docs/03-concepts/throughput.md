# Concept: Throughput

**Throughput** is the rate at which a computer system successfully processes frames or points, typically measured in **Frames Per Second (FPS)** or points per second.

---

## 1. Latency vs. Throughput

It is essential not to confuse **Latency** and **Throughput**:
- **Latency**: How long a *single* frame takes to travel through the pipeline (e.g. $25\text{ ms}$).
- **Throughput**: How many frames can be completed per second (e.g. $40\text{ FPS}$).

### Equation:
$$\text{Max Throughput (FPS)} = \frac{1000}{\text{Per-Frame Execution Latency (ms)}}$$

If an algorithm takes $20\text{ ms}$ on average:
$$\text{Throughput} = \frac{1000}{20} = 50\text{ FPS}$$
