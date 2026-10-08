# Concept: Timestamp Jitter

**Timestamp Jitter** is the statistical variation in inter-arrival times between consecutive sensor packets.

---

## 1. Mathematical Formulation

Let $t_1, t_2, \dots, t_N$ be sensor packet arrival timestamps. The inter-sample intervals are:
$$\Delta t_i = t_i - t_{i-1}$$

The **Mean Interval** is:
$$\overline{\Delta t} = \frac{1}{N-1}\sum_{i=2}^N \Delta t_i$$

The **Jitter ($\sigma_{\Delta t}$)** is the sample standard deviation:
$$\text{Jitter} = \sqrt{\frac{1}{N-2}\sum_{i=2}^N (\Delta t_i - \overline{\Delta t})^2}$$

---

## 2. Impact on Inertial Integration

In an IMU, velocity is integrated from acceleration:
$$\mathbf{v}(t) = \mathbf{v}(0) + \sum_{i=1}^N \mathbf{a}_i \Delta t_i$$

If the software assumes a fixed $\Delta t = 5.0\text{ ms}$, but the real interval fluctuates randomly between $2\text{ ms}$ and $8\text{ ms}$, numerical integration errors compound quadratically into position drift.
