# Matplotlib in Autonomous Robotics

## Why Does Matplotlib Exist in This Project?

Robotics engineering is empirical science. You cannot evaluate a state estimation pipeline or sensor stream by staring at thousands of numbers scrolling down a terminal screen.

**Matplotlib** is the standard scientific plotting library used to generate publication-quality figures, timelines, and distributions.

---

## 1. The Core Philosophy: Question-Driven Graphs

In this repository, **we never generate a graph just because a graph is possible**. Every single graph is titled with the specific engineering question it answers:

1. **`point_count_vs_frame.png`**  
   *Question*: "Does the sensor produce a stable amount of data per frame?"
2. **`range_histogram.png`**  
   *Question*: "What distances are being observed in the environment?"
3. **`pipeline_latency_vs_frame.png`**  
   *Question*: "Does processing remain stable and meet the sensor deadline?"
4. **`imu_interval_histogram.png`**  
   *Question*: "Is the IMU arriving at a stable rate without timing jitter?"
5. **`available_margin_vs_frame.png`**  
   *Question*: "Does the host computer finish processing before the next scan arrives?"

---

## 2. Headless Execution

All plots in this repository use the headless `Agg` backend (`matplotlib.use("Agg")`), allowing automated batch generation and test execution on remote headless servers, CI/CD pipelines, and workstations without display servers.
