# AutoNav: LiDAR odometry deadline study

A reproducible study measuring whether scan-to-scan LiDAR odometry can meet a 10 Hz sensor's 100 ms deadline, what it costs in accuracy, and what it takes to close the gap, built before committing to robot hardware.

It is a measurement study, not a navigation system. Every result is labelled with the hardware it ran on.

**Results site (static, read-only):** https://jeyavardhan-l.github.io/Baseline_tests_for_AutoNav/ . The final audit is in [docs/final-report.md](docs/final-report.md).

Origin: an autonomous-navigation feasibility investigation for the ISRO IRoC-U challenge. License: MIT (code). Datasets keep their own licences (see below).

## The question

> Can baseline 3D LiDAR odometry process each incoming point-cloud frame within the sensor's arrival period (100 ms at 10 Hz) on a constrained companion computer?

Three things are kept apart: algorithmic feasibility, measured software performance on the machine used, and deployment on target hardware. Only the middle one is measured here, and only on the machines listed in each run record. A Python benchmark gives no hard real-time guarantee.

## Status (what is verified, what is not)

| Item | Status |
|---|---|
| Point-to-point ICP odometry, voxel/range filtering, registration validity gate | Implemented, unit-tested |
| Pose convention (`W_k = W_{k-1} @ T`), checked against hand-derived expectations | Verified by tests |
| ATE (timestamp association + Umeyama) and RPE (time and distance windows) | Implemented, unit-tested on known-answer cases |
| PCD loader (header `POINTS` is authoritative), ROS-style filename timestamps | Implemented, unit-tested |
| Newer College: odometry window from the rosbag, with ground truth | Data downloaded; extraction and validation in progress, see `docs/progress.md` |
| Latency / deadline results on real data | **Not yet produced.** Any number you may have seen in older versions of this README was unsupported and has been removed. |
| Raspberry Pi 5 / any embedded hardware | **UNAVAILABLE.** Not measured. |

Everything in `docs/progress.md` carries the command that was run. `docs/decision-log.md` records every non-trivial decision and the alternatives.

## Install and test

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
python -m unittest discover -s tests -v
```

Core dependencies: NumPy, SciPy, psutil (plus matplotlib, pandas, PyYAML already used by the package). Optional extras for data acquisition (`rosbags`, `gdown`, `huggingface_hub`) are never imported by the core pipeline.

## Datasets

| Dataset | Role | Sensor | Licence |
|---|---|---|---|
| Newer College (2020), `01_short_experiment` | Primary | Ouster OS1-64, 10 Hz | CC BY-NC-SA 4.0 |
| Oxford Spires | Secondary (one window) | Hesai QT64 (different from OS1-64) | Verify before publishing excerpts |

Raw data is never committed and never redistributed. Obtain it from the Oxford Robotics Institute (https://ori.ox.ac.uk/datasets/newer-college-dataset/) and place it as described in `datasets/newer-college/README.md`. Dataset locations are read from a git-ignored `config.local.yaml`, never from machine-specific paths in tracked files.

Synthetic data (`SyntheticAdapter`) exists only for tests and is never presented as evidence. Interleaved or thinned frames are labelled NON-CONSECUTIVE and are used only for single-frame statistics.

## Layout

```
src/autonav_baseline/   datasets/ lidar/ metrics/ timing/ reporting/ system/ visualization/
tests/                  unit tests (real-format fixtures + known-answer maths)
experiments/            numbered scripts; lidar-pi-slam-benchmark/ is a separate 2D study (see its README)
docs/                   decision-log.md, progress.md, concepts, methodology
archive/                moved, not deleted: see archive/README.md
```

## Evidence classes

Every published value is tagged `MEASURED` (timer or file), `DERIVED` (calculated from measured data), `DECLARED` (dataset documentation), `ASSUMED`, `UNAVAILABLE` or `UNVERIFIED`. Frame 0 is excluded from registration statistics. A P95 under 100 ms is never reported as "meets the deadline" without the violation rate.

## Credits

The 2D LiDAR SLAM benchmark in `experiments/lidar-pi-slam-benchmark/` was written by Priyangshu Ghosh (`@PriyangshuGhosh`) and is a separate study. Newer College Dataset: Ramezani, Wang, Camurri, Wisth, Mattamala, Fallon, "The Newer College Dataset: Handheld LiDAR, Inertial and Vision with Ground Truth", IROS 2020.