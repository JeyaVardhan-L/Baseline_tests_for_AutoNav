# Hardware Requirements Methodology: Evidence-Driven Engineering

> [!CRITICAL]
> **DO NOT PREMATURELY SELECT OR PURCHASE HARDWARE.**  
> In this repository, we do **not** write:  
> - *"Therefore we need a Jetson Orin Nano."*  
> - *"Therefore we need a LiDAR under 15 Watts."*  
> - *"Therefore we need 16 GB of RAM."*  
>  
> Any such claims made prior to experimental evidence are unsubstantiated speculation. The purpose of Phase 1 is **strictly evidence gathering**.

---

## 1. The Evidence-to-Hardware Derivation Chain

Future hardware specifications for the autonomous UAV will be derived systematically through empirical measurements across 12 criteria:

$$\text{Experimental Measurements} \xrightarrow{\text{Analysis}} \text{Payload Specifications} \xrightarrow{\text{Trade Study}} \text{Hardware Selection}$$

```
+-------------------------------------------------------------------------+
| EMPIRICAL EXPERIMENTAL MEASUREMENTS (Phase 1 Laboratory)                |
| 1. Sensor Data Rate (MB/s)              -> Communication bus selection  |
| 2. Per-Scan Processing Time (ms)        -> CPU core frequency & IPC     |
| 3. Downsampling / Voxel Latency (ms)    -> Single-thread vs SIMD / GPU  |
| 4. Peak Memory Working Set (MB)         -> Minimum RAM & swap overhead  |
| 5. End-to-End Latency (ms)              -> Maximum safe flight velocity |
| 6. Sensor Timing Jitter (ms)            -> Hardware vs software sync    |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| PHYSICAL UAV CONSTRAINTS (Aeronautical Limits)                          |
| 7. Mass & Weight Budget (grams)         -> Airframe payload capacity    |
| 8. Electrical Power Budget (Watts)      -> LiPo battery watt-hour drain |
| 9. Thermal Dissipation Limits (Celsius) -> Enclosed chassis cooling     |
| 10. Flight Controller Interface         -> UART / CAN / Ethernet bus    |
| 11. Shock & Vibration Resistance        -> Rotor harmonic isolation     |
| 12. Mission Operational Duration (mins) -> Flight endurance trade-off   |
+-------------------------------------------------------------------------+
```

---

## 2. Why Premature Hardware Purchases Fail

1. **Purchasing before understanding data rates**: A team buys an embedded board only to discover its USB 2.0 bus drops camera frames or its single-core CPU cannot sustain 10 Hz voxelization.
2. **Ignoring thermal and power constraints**: A team buys a 60W compute module that draws so much current it overheats inside an enclosed drone frame within 90 seconds and cuts flight time from 20 minutes to 4 minutes.
3. **Ignoring weight limits**: Adding a 500-gram LiDAR and 300-gram computer pushes the drone past its Maximum Takeoff Weight (MTOW), causing motor saturation and loss of control authority.

---

## 3. Decision Boundary: When Will Hardware Be Selected?

Hardware selection occurs **only after**:
- Experiments 01 through 09 establish empirical data rates, memory footprints, and pipeline latencies across multiple candidate sensor modalities.
- Algorithmic profiling identifies whether GPU acceleration is strictly necessary or if CPU SIMD vectorization satisfies the real-time deadline.
- A formal multi-criteria trade matrix ranks candidate devices against verified empirical evidence.
