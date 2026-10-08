# Timestamps and Synchronization in Robotics

This document explains what timestamps mean, why clock accuracy matters, and why microseconds determine safety for an autonomous UAV.

---

## 1. What is a Timestamp?

A **timestamp** is a numerical value attached to every sensor packet recording the precise moment the physical measurement was made by the hardware.

In robotics, timestamps are typically represented as **64-bit floating point seconds** since an epoch:
- **Unix Epoch**: Seconds elapsed since midnight January 1, 1970 UTC (e.g. `1685432100.123456` seconds).
- **Monotonic Clock**: Seconds elapsed since the computer or flight controller booted up (guaranteed never to jump backward, even during daylight savings adjustments).

---

## 2. Why Timestamps Matter: Drone Motion at Speed

Consider a quadcopter cruising through an indoor warehouse or obstacle course at **5 meters per second** ($5 \text{ m/s} = 18 \text{ km/h}$).

If the camera records an image at time $t = 10.000 \text{ s}$, but because of USB driver buffering, the image is stamped as $t = 10.050 \text{ s}$ (**a 50 millisecond error**):

### Spatial Position Error:
$$\text{Error} = \text{Speed} \times \Delta t = 5.0 \text{ m/s} \times 0.050 \text{ s} = 0.25 \text{ meters} = 25 \text{ cm}$$

A 25 cm position error is large enough to cause the drone's propeller tips to strike a doorway or support beam!

---

## 3. What is Sampling Jitter?

If a sensor is advertised as **200 Hz**, the ideal time interval between consecutive packets is:

$$\Delta t_{\text{ideal}} = \frac{1}{200} \text{ seconds} = 0.005 \text{ s} = 5.0 \text{ milliseconds}$$

In real systems, operating system scheduling, USB packet hubs, and thread context switches cause intervals to vary:
- Packet 1 arrives: $t = 0.000 \text{ s}$ ($\Delta t = 5.0 \text{ ms}$)
- Packet 2 arrives: $t = 0.007 \text{ s}$ ($\Delta t = 7.0 \text{ ms}$)
- Packet 3 arrives: $t = 0.010 \text{ s}$ ($\Delta t = 3.0 \text{ ms}$)

The standard deviation of these intervals is called **Timing Jitter**:
$$\text{Jitter} = \sigma(\Delta t)$$

Low jitter ($\sigma < 0.5 \text{ ms}$) indicates deterministic real-time communication. High jitter indicates operating system delays or buffer congestion.

---

## 4. Hardware vs. Software Synchronization

### Software Synchronization (Nearest Neighbor)
The companion computer receives sensor messages over USB/Ethernet and pairs them post-hoc by matching the closest timestamps:
$$\Delta t_{\text{sync}} = |t_{\text{lidar}} - t_{\text{imu, closest}}|$$
For a 200 Hz IMU (5 ms period), the maximum nearest-neighbor error is $\approx 2.5 \text{ ms}$.

### Hardware Synchronization (PPS / Triggering)
- **PPS (Pulse Per Second)**: A dedicated electrical wire carries a square-wave electrical pulse once every second.
- Sensors latch their internal clocks to the rising edge of the pulse with microsecond precision ($< 10 \mu\text{s}$), completely eliminating clock drift.
