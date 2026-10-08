# Sensor Basics for Autonomous Navigation

This guide explains the three primary sensors used in GPS-denied autonomous UAV navigation: **LiDAR**, **Depth Cameras**, and **Inertial Measurement Units (IMUs)**.

---

## 1. What is a Sensor?

A **sensor** is an electronic device that measures a physical property of the world (e.g. distance, light, acceleration) and converts it into digital numbers that an onboard computer can read.

Every sensor has:
- **Sampling Rate (Frequency in Hertz / Hz)**: How many times per second it produces a new measurement.
  - $10\text{ Hz} = 10\text{ times per second}$ (once every $100\text{ ms}$).
  - $200\text{ Hz} = 200\text{ times per second}$ (once every $5\text{ ms}$).
- **Data Volume**: How many bytes are transmitted with each measurement.
- **Range & Field-of-View (FoV)**: How far and in which directions it can see.

---

## 2. Sensor 1: LiDAR (Light Detection and Ranging)

### How It Works
A LiDAR emits millions of invisible laser pulses per second. When a laser pulse strikes an obstacle (a wall, a tree, a rock), the light bounces back. The LiDAR's photodetector measures the **time-of-flight** ($\Delta t$) of the pulse.

Because light travels at the speed of light ($c \approx 300,000,000 \text{ m/s}$), the distance $d$ is:
$$d = \frac{c \times \Delta t}{2}$$

### Mechanical vs. Solid-State
- **Spinning Mechanical LiDAR** (e.g. Ouster OS-1, Velodyne): A cylinder containing 16, 32, 64, or 128 laser diodes spins 360 degrees horizontally, measuring a cylindrical shell of points.
- **Solid-State / Non-repetitive LiDAR** (e.g. Livox Mid-360, Robosense Bpearl): Uses optical mirrors or prisms to project a scanning rosette pattern across a hemispherical field-of-view without spinning the entire sensor body.

### What LiDAR Produces
A set of points in 3D space called a **Point Cloud**. Each point has coordinates $(x, y, z)$ measured in meters relative to the sensor, plus an **intensity** value (reflectivity of the surface).

---

## 3. Sensor 2: RGB and Depth Cameras

### RGB Camera (Standard Color)
Captures a 2D grid of pixels (width $\times$ height), where each pixel has Red, Green, and Blue values (0 to 255). It sees colors and visual textures, but **does not know how far away objects are** from a single image.

### Depth Camera (RGB-D)
Measures both color and distance for every pixel in the image grid. Common types:
- **Active Stereo** (e.g. Intel RealSense D435i): Two infrared cameras look at a scene illuminated by an invisible infrared dot projector. By measuring the parallax shift of pattern dots between the left and right cameras, it computes distance.
- **Time-of-Flight (ToF)**: An illuminated sensor array measures the phase shift of reflected infrared light across the entire image plane.

### Numerical Example of Depth Data Volume
Suppose an RGB-D camera runs at **30 frames per second (30 Hz)** with resolution **640 $\times$ 480 pixels**:
- Pixels per frame: $640 \times 480 = 307,200 \text{ pixels}$.
- RGB image: 3 bytes per pixel (Red, Green, Blue) $\rightarrow 307,200 \times 3 = 921,600 \text{ bytes}$.
- Depth image: 2 bytes per pixel (16-bit integer depth in millimeters) $\rightarrow 307,200 \times 2 = 614,400 \text{ bytes}$.
- Total per frame: $921,600 + 614,400 = 1,536,000 \text{ bytes} \approx 1.54 \text{ MB}$.
- **Data per second at 30 Hz**: $1.536 \text{ MB} \times 30 = 46.08 \text{ MB/s}$ uncompressed!

---

## 4. Sensor 3: IMU (Inertial Measurement Unit)

An **IMU** is a micro-electro-mechanical system (MEMS) chip that measures two physical quantities:

1. **Linear Acceleration ($a_x, a_y, a_z$)**: Measured in $\text{m/s}^2$ by microscopic proof masses. At rest on Earth, the accelerometer measures the upward reaction force opposing gravity ($9.81\text{ m/s}^2$ on the $Z$ axis).
2. **Angular Velocity ($\omega_x, \omega_y, \omega_z$)**: Measured in radians per second ($\text{rad/s}$) by microscopic vibrating tuning forks detecting Coriolis forces during rotation.

### Why the IMU is Indispensable for Drones
LiDAR and cameras produce data at 10 to 30 Hz. But quadcopters are dynamically unstable and can flip within 50 milliseconds if motors are not trimmed. The IMU operates at **200 to 1000 Hz**, giving the flight controller instant feedback on roll, pitch, and yaw rates to keep the drone balanced.

---

## 5. Summary Comparison

| Sensor | Sampling Rate | Data Format | Range | Primary Strength | Primary Weakness |
|---|---|---|---|---|---|
| **LiDAR** | 10 – 20 Hz | 3D $(x,y,z)$ Point Cloud | 0.5 – 100 m | Direct metric 3D accuracy | High weight, power, and cost |
| **RGB-D Camera** | 15 – 60 Hz | 2D Image Matrix $(u,v)$ | 0.2 – 10 m | Dense color & geometry | Short range, sunlight wash-out |
| **IMU** | 100 – 1000 Hz | 6-Axis Vector $[a, \omega]$ | N/A | Microsecond state updates | Integrates noise & drifts over time |
