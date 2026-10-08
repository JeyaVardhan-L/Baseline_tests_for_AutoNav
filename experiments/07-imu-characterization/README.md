# Experiment 07: IMU Characterization

## 1. Objective
Analyze high-rate Inertial Measurement Unit (IMU) telemetry streams to measure sampling rate, packet timing stability, delta-time jitter, dropped samples, and stationary accelerometer/gyroscope noise and bias characteristics.

## 2. Why This Matters
An autonomous UAV cannot navigate without an IMU. While LiDAR and cameras produce spatial environment measurements at 10 to 30 Hz, the IMU operates at 100 to 500 Hz to propagate state estimates (attitude, velocity, position) between slower camera/LiDAR frames. Irregular IMU sample intervals, lost packets, or unmodeled bias lead to exponential integration drift in dead-reckoning.

## 3. Required Knowledge
- **Accelerometer**: Measures specific force $\mathbf{f} = \mathbf{a} - \mathbf{g}$ in $\text{m/s}^2$. At rest on Earth, it measures upward reaction force equal to gravity ($9.81 \text{ m/s}^2$).
- **Gyroscope**: Measures angular velocity $\boldsymbol{\omega}$ in $\text{rad/s}$ about the sensor body axes.
- **Sensor Bias ($\mathbf{b}$)**: A slowly drifting non-zero offset present even when the sensor is stationary.
- **Sampling Jitter**: The standard deviation of the time differences $\Delta t = t_i - t_{i-1}$ between consecutive readings.
- **Dropped Packets**: Abnormally large $\Delta t > 1.8 \times \overline{\Delta t}$ indicating dropped serial/USB messages or buffer overflows.

## 4. Dataset
- Oxford Newer College (`newer_college`) — Ouster OS-1 internal IMU (100 Hz)
- Hilti SLAM 2023 (`hilti_2023`) — XSens MTi-600 industrial IMU (200 Hz)
- OpenLORIS-Scene (`openloris`) — RealSense D435i IMU (200 Hz / 400 Hz)
- Synthetic benchmark stream (`synthetic`)

## 5. Input
Stream of timestamped 6-axis IMU packets containing linear acceleration $[a_x, a_y, a_z]$ and angular velocity $[\omega_x, \omega_y, \omega_z]$.

## 6. Output
- `metrics.csv`: Tabular time-series of per-sample timestamps, $\Delta t$, accelerations, and angular rates.
- `summary.json`: Statistical distribution of timing and sensor noise.
- `figures/accel_vs_time.png`: Linear acceleration vs. time.
- `figures/gyro_vs_time.png`: Angular velocity vs. time.
- `figures/sample_interval_vs_time.png`: Time spacing between consecutive packets.
- `figures/sample_interval_histogram.png`: Histogram answering *"Is the stream arriving at a stable rate?"*
- `summary.md`: Standardized engineering summary.

## 7. Parameters
- `--dataset`: Dataset identifier (`synthetic`, `newer_college`, `hilti_2023`, `openloris`).
- `--max-samples`: Number of IMU packets to process (default: 1000).
- `--expected-hz`: Manufacturer nominal frequency in Hz (default: 200.0).

## 8. Method
1. Read sequential IMU frames and extract floating-point timestamps and 6-axis vectors.
2. Compute delta time series $\Delta t_i = t_i - t_{i-1}$ in milliseconds.
3. Compute mean sampling rate $f_{\text{obs}} = 1000 / \overline{\Delta t}$.
4. Calculate standard deviation of $\Delta t$ to quantify hardware/driver jitter.
5. Identify any $\Delta t > 1.8 \times \overline{\Delta t}$ as potential dropped messages.
6. Compute mean and standard deviation of acceleration and gyro readings.

## 9. Equations
$$\Delta t_i = (t_i - t_{i-1}) \times 1000 \text{ ms}$$
$$\overline{\Delta t} = \frac{1}{N-1}\sum_{i=2}^N \Delta t_i$$
$$f_{\text{obs}} = \frac{1000}{\overline{\Delta t}} \text{ Hz}$$
$$\text{Jitter} = \sqrt{\frac{1}{N-1}\sum_{i=2}^N (\Delta t_i - \overline{\Delta t})^2}$$
$$\|\mathbf{a}\| = \sqrt{a_x^2 + a_y^2 + a_z^2}$$

## 10. Command
```bash
# Run with synthetic 200 Hz test stream
python experiments/07-imu-characterization/run.py --dataset synthetic --max-samples 1000

# Run with Hilti 2023 XSens IMU
python experiments/07-imu-characterization/run.py --dataset hilti_2023 --expected-hz 200.0
```

## 11. Expected Terminal Output
```
============================================================
  EXPERIMENT 07 - IMU CHARACTERIZATION
  Dataset: synthetic
============================================================

IMU TIMING & SAMPLING RATE
------------------------------------------------------------
Samples Analyzed          : 1000 samples [MEASURED]
Stream Duration           : 4.995 seconds [MEASURED]
Nominal Sensor Rate       : 200.0 Hz [ASSUMED] (Manufacturer specification)
Observed Sampling Rate    : 200.0 Hz [DERIVED] (1000 / mean interval)
Mean Sample Interval      : 5.0 ms [MEASURED]
Timing Jitter (Std Dev)   : 0.05 ms [MEASURED] (Inter-sample variance)
Min / Max Interval        : 4.85 / 5.15 ms [MEASURED]
Suspected Dropped Samples : 0 samples [DERIVED] (dt > 1.8x mean interval)

ACCELEROMETER MEASUREMENTS (m/s^2)
------------------------------------------------------------
Mean Accel [X, Y, Z]      : [0.002, -0.004, 9.808] m/s^2 [MEASURED]
Noise / Std [X, Y, Z]     : [0.048, 0.051, 0.049] m/s^2 [MEASURED]
Mean Norm Magnitude       : 9.808 m/s^2 [MEASURED] (Earth gravity + motion)

GYROSCOPE MEASUREMENTS (rad/s)
------------------------------------------------------------
Mean Gyro [X, Y, Z]       : [0.0001, -0.0002, 0.0001] rad/s [MEASURED] (Sensor bias estimate)
Noise / Std [X, Y, Z]     : [0.0052, 0.0049, 0.0051] rad/s [MEASURED]
Mean Norm Magnitude       : 0.0088 rad/s [MEASURED]
============================================================
```

## 12. Live Visualization
Outputs 4 figures to `results/<dataset>/07_imu_characterization/figures/`.

## 13. Graphs
- **`accel_vs_time.png`**: Answers *"What acceleration and vibration forces are sensed?"*
- **`gyro_vs_time.png`**: Answers *"What rotation rates are experienced?"*
- **`sample_interval_vs_time.png`**: Answers *"Does the sensor maintain regular sample spacing over time?"*
- **`sample_interval_histogram.png`**: Answers *"What is the statistical spread and jitter of sensor packet arrivals?"*

## 14. Metrics
| Metric | Type | Unit | Description |
|---|---|---|---|
| Observed Frequency | `[DERIVED]` | Hz | Empirical sample rate |
| Mean Interval | `[MEASURED]` | ms | Average time between consecutive packets |
| Jitter | `[MEASURED]` | ms | Standard deviation of sample intervals |
| Dropped Samples | `[DERIVED]` | count | Packets missing based on delta gaps |
| Accel / Gyro Bias | `[MEASURED]` | $\text{m/s}^2$ / $\text{rad/s}$ | Stationary offset from true zero |

## 15. Interpretation
- If jitter exceeds 15% of the sample period, the host OS or serial driver is introducing latency spikes that degrade Kalman filter integration.
- If dropped samples occur frequently, hardware flow control, USB polling rates, or interrupt priority must be adjusted.

## 16. Limitations
- Evaluates raw sensor stream without thermal chamber calibration (IMU bias drifts with temperature).
- Static tests do not capture rotor vibration harmonics encountered on a flying UAV.

## 17. Reproducibility Information
- All data stored in standard floating-point array format.
- Timing measured using hardware-stamped or monotonic host clocks.

## 18. What Decision This Experiment Can Inform
- Confirms whether an IMU driver provides the deterministic timing required for tight-coupled EKF state estimation.
