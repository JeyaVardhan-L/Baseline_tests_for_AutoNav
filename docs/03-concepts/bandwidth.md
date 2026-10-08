# Concept: Bandwidth

**Bandwidth** is the maximum transmission capacity of a communication link or computer hardware bus, measured in bits per second (bps) or bytes per second (B/s).

---

## 1. Onboard Hardware Buses

On an autonomous UAV, sensor data must travel from the sensor physical port to the companion computer's RAM:

| Communication Bus | Theoretical Maximum | Practical Real-World | Suitable Sensors |
|---|---|---|---|
| **UART / Serial** | 115.2 kbps – 1 Mbps | ~100 kB/s | GPS, Telemetry, Autopilot setpoints |
| **CAN Bus** | 1 Mbps (CAN 2.0B) | ~80 kB/s | ESC motor telemetry, Smart batteries |
| **USB 2.0** | 480 Mbps | ~35 MB/s | Single depth camera or low-res camera |
| **USB 3.0 / 3.1** | 5 Gbps | ~400 MB/s | Multi-camera stereo pairs, RealSense |
| **Fast Ethernet (100Base-T)** | 100 Mbps | ~11.5 MB/s | Standard 16-beam / 32-beam LiDARs |
| **Gigabit Ethernet (1000Base-T)** | 1000 Mbps | ~115 MB/s | 64/128-beam LiDARs (Ouster, Hesai) |

---

## 2. Bandwidth Saturation Danger

If a 64-beam LiDAR generates $16\text{ MB/s}$ and an RGB camera generates $25\text{ MB/s}$, connecting both through an unpowered 100 Mbps switch or USB 2.0 hub will saturate the bus ($41\text{ MB/s} > 11.5\text{ MB/s}$ or $35\text{ MB/s}$), causing dropped packets and delayed frames.
