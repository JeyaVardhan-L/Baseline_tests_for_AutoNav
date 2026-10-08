# Real-Time Processing for Autonomous UAVs

This document explains what **real-time** means in robotics, why average processing speed is insufficient, and how compute margins prevent fatal control lag.

---

## 1. What Does "Real-Time" Actually Mean?

In everyday language, people often use "real-time" to mean "fast". In engineering and computer science, **real-time has a precise mathematical definition**:

> A real-time system is one whose correctness depends not only on the logical correctness of the computation, but also on the **time at which the result is produced**. If a correct calculation arrives after its deadline, the system has failed.

---

## 2. Sensor Period vs. Pipeline Latency

Every sensor publishes data at a fixed cadence called the **Sensor Period ($T_s$)**:

$$T_s = \frac{1000}{\text{Frequency (Hz)}} \text{ milliseconds}$$

### Examples:
- A $10 \text{ Hz}$ LiDAR produces a frame every **$100 \text{ ms}$**.
- A $30 \text{ Hz}$ camera produces a frame every **$33.3 \text{ ms}$**.
- A $200 \text{ Hz}$ IMU produces a packet every **$5.0 \text{ ms}$**.

The **Pipeline Latency ($T_{\text{pipeline}}$)** is the elapsed wall-clock time from the moment the computer receives the raw bytes until the point cloud is filtered and ready for navigation:

$$T_{\text{pipeline}} = T_{\text{read}} + T_{\text{decode}} + T_{\text{validate}} + T_{\text{filter}} + T_{\text{downsample}}$$

---

## 3. The Available Compute Margin

The spare time remaining before the next sensor measurement arrives is the **Available Margin ($M$)**:

$$M = T_s - T_{\text{pipeline}}$$

### Case 1: Positive Margin ($M > 0$) $\rightarrow$ PASS
- Sensor Period $T_s = 100 \text{ ms}$
- Pipeline Latency $T_{\text{pipeline}} = 25 \text{ ms}$
- **Margin $M = 100 - 25 = +75 \text{ ms}$**
- *Meaning*: The computer finishes processing with 75 ms to spare. It can safely run SLAM scan matching, local mapping, and path planning before the next LiDAR frame arrives.

### Case 2: Negative Margin ($M < 0$) $\rightarrow$ FAIL (Cannot Keep Up)
- Sensor Period $T_s = 100 \text{ ms}$
- Pipeline Latency $T_{\text{pipeline}} = 120 \text{ ms}$
- **Margin $M = 100 - 120 = -20 \text{ ms}$**
- *Meaning*: While processing frame 1, frame 2 arrives and waits in an operating system queue. Frame 2 will start 20 ms late. Frame 3 will start 40 ms late. Latency accumulates linearly until the queue overflows and frames are dropped.

---

## 4. Why Mean (Average) Latency is Dangerous: The P95/P99 Rule

In software engineering, developers often report **Mean Latency**:
$$\text{Mean} = \frac{1}{N}\sum_{i=1}^N T_i$$

### Why Mean Can Hide Fatal Bugs:
Suppose a drone processes 100 frames:
- 95 frames take **20 ms**.
- 5 frames encounter complex geometry or OS garbage collection and take **160 ms**.
- The **Mean** is:
  $$\text{Mean} = \frac{95 \times 20 + 5 \times 160}{100} = \frac{1900 + 800}{100} = 27.0 \text{ ms}$$

If you only look at the mean ($27 \text{ ms} < 100 \text{ ms}$), you might conclude the system is completely safe.

However, during those 5 slow frames, processing spiked to **160 ms**, blowing past the 100 ms deadline by 60 ms!

Therefore, robotics engineers always measure **Percentiles**:
- **P95 (95th Percentile)**: The latency below which 95% of frames fall.
- **P99 (99th Percentile)**: The latency below which 99% of frames fall.
- **Max**: The worst-case spike observed across the entire flight.

A robotic system is only certified real-time if its **P95/P99 latency** safely satisfies the sensor deadline with adequate margin.
