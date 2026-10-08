# Concept: Latency

**Latency** is the time delay between the occurrence of a physical event in the real world and the moment the robotic software produces an action in response.

---

## 1. End-to-End Latency Chain

$$\text{Total Latency} = T_{\text{exposure}} + T_{\text{transfer}} + T_{\text{read}} + T_{\text{filtering}} + T_{\text{SLAM}} + T_{\text{planning}} + T_{\text{control}}$$

### Numerical Breakdown Example
- **Sensor Scan Time ($T_{\text{exposure}}$)**: $100 \text{ ms}$ (for a $10 \text{ Hz}$ spinning LiDAR).
- **Network Transfer ($T_{\text{transfer}}$)**: $2 \text{ ms}$ over Gigabit Ethernet.
- **Pre-processing / Filter ($T_{\text{filtering}}$)**: $8 \text{ ms}$ on host CPU.
- **Odometry & Mapping ($T_{\text{SLAM}}$)**: $30 \text{ ms}$.
- **Trajectory Planning ($T_{\text{planning}}$)**: $15 \text{ ms}$.
- **Autopilot Response ($T_{\text{control}}$)**: $5 \text{ ms}$.
- **Total Latency**: $100 + 2 + 8 + 30 + 15 + 5 = 160 \text{ milliseconds}$.

---

## 2. Impact on Flight Velocity

At $160\text{ ms}$ latency, a UAV flying at $4\text{ m/s}$ will travel:
$$\Delta d = 4.0 \text{ m/s} \times 0.160 \text{ s} = 0.64 \text{ meters} = 64 \text{ cm}$$
before its motors begin reacting to a newly detected obstacle!
