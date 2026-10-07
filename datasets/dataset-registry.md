# Dataset Registry

## Purpose

Evaluate and document publicly available datasets for use in our experiments. A dataset must be evaluated before use — we do not choose datasets blindly.

## Evaluated Datasets

### KITTI Odometry ⭐ SELECTED FOR EXP-01

| Field | Value |
|-------|-------|
| **Name** | KITTI Vision Benchmark Suite — Odometry |
| **Source** | Karlsruhe Institute of Technology / Toyota Technological Institute |
| **URL** | https://www.cvlibs.net/datasets/kitti/eval_odometry.php |
| **Sensor** | Velodyne HDL-64E (64-beam LiDAR) + stereo cameras + GPS/IMU |
| **LiDAR Model** | Velodyne HDL-64E |
| **Point Format** | Binary `.bin` files — float32 (x, y, z, reflectance) per point |
| **Frequency** | 10 Hz |
| **Fields** | x, y, z, reflectance |
| **Points per Scan** | ~100,000–130,000 |
| **Environment** | Urban driving — roads, buildings, vegetation, pedestrians |
| **Sequences** | 22 sequences (00–21), 11 with ground-truth poses |
| **Total LiDAR Size** | ~80 GB (all sequences) |
| **Ground Truth** | 6-DoF poses for sequences 00–10 |
| **Availability** | Free with registration |
| **License** | Creative Commons Attribution-NonCommercial-ShareAlike 3.0 |
| **Relevance** | Well-documented format, widely benchmarked, real outdoor LiDAR data, known sensor specs. Ideal for understanding LiDAR data characteristics and testing odometry algorithms. |
| **Limitations** | Ground-vehicle perspective (not aerial). HDL-64E is a large/expensive sensor — not representative of lightweight UAV LiDARs. Data characteristics (point density, range) will differ from a UAV-mounted low-cost LiDAR. |
| **Why Selected for EXP-01** | Simple binary format (easy to parse). Well-documented sensor specifications. Known point counts and frame rates allow verification of our analysis pipeline. Large research community for cross-reference. Individual sequences are manageable in size. |

### Newer College Dataset

| Field | Value |
|-------|-------|
| **Name** | Newer College Dataset |
| **Source** | Oxford Robotics Institute |
| **URL** | https://ori.ox.ac.uk/datasets/newer-college-dataset |
| **Sensor** | Ouster OS-1 64-beam (v1) / OS-0 128-beam (v2) |
| **LiDAR Model** | Ouster OS-1 Gen 1 (64-beam), OS-0 (128-beam) |
| **Point Format** | ROS bag files |
| **Frequency** | 10 Hz |
| **Environment** | University campus — built environments, open spaces, vegetation |
| **Ground Truth** | High-accuracy 6-DoF (~3 cm) from survey-grade LiDAR |
| **Availability** | Free |
| **License** | CC BY-NC-SA 4.0 |
| **Relevance** | Handheld collection (more similar to UAV motion than car). Excellent ground truth. Pedestrian-scale environment. |
| **Limitations** | ROS bag format requires ROS for native processing. Larger download sizes. |
| **Status** | CANDIDATE for future experiments (EXP-03, EXP-07) |

### MulRan

| Field | Value |
|-------|-------|
| **Name** | MulRan — Multimodal Range Dataset |
| **Source** | KAIST |
| **URL** | https://sites.google.com/view/mulran-pr |
| **Sensor** | Ouster OS1-64 + radar |
| **Environment** | Urban environments (South Korea) |
| **Relevance** | Multi-session, different times — useful for long-term localization |
| **Limitations** | Large dataset, focused on place recognition |
| **Status** | CANDIDATE for future experiments |

### Hilti SLAM Challenge

| Field | Value |
|-------|-------|
| **Name** | Hilti SLAM Challenge Dataset |
| **Source** | University of Zurich / Hilti |
| **URL** | https://hilti-challenge.com/ |
| **Sensor** | Multiple LiDARs + cameras + IMU |
| **Environment** | Construction sites, offices, labs |
| **Ground Truth** | Millimeter-accurate |
| **Relevance** | Challenging environments, robust SLAM testing |
| **Limitations** | Indoor-focused, specialized environment |
| **Status** | CANDIDATE for future experiments |

## Selection Criteria

When selecting a dataset for an experiment, evaluate:

1. **Relevance** — Does the sensor/environment match our use case?
2. **Format** — Can we easily parse and process it?
3. **Size** — Is it manageable for our current infrastructure?
4. **Ground truth** — Does it provide reference for validation?
5. **Documentation** — Are sensor specs and collection details known?
6. **License** — Is it free for academic/research use?
7. **Community** — Are there published benchmarks for comparison?

## Important Note

The KITTI dataset uses a Velodyne HDL-64E, which is a **large, expensive, high-end LiDAR** (64 beams, ~1.3M points/sec). This is NOT the kind of LiDAR we would mount on a < 2 kg UAV.

However, for **EXP-01 (data characterization)**, this is acceptable because:

1. We are studying what LiDAR data looks like and how to process it
2. We can downsample to simulate lower-resolution sensors
3. The binary format is simple and well-documented
4. Known specs allow us to verify our analysis pipeline

For later experiments, we will also evaluate datasets from **lighter/cheaper sensors** (e.g., Livox, Ouster OS0, etc.) to better match our UAV constraints.
