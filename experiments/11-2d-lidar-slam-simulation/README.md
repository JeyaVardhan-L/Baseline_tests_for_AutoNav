# Experiment 11 — 2-D LiDAR + scan-matching simulation

This experiment generates a small indoor scene, simulates a 360-degree 2-D LiDAR, filters valid returns, runs adjacent-scan 2-D ICP (a lightweight scan-matching SLAM demonstration), accumulates a map, and exports timing/data metrics plus plots and an optional GIF.

> **Evidence warning:** this is a synthetic simulation. It does not read the physical LiDAR, measure USB/serial ingest, or validate production SLAM. The ICP implementation has no loop closure or IMU fusion and is for feasibility learning/visualization only.

## Why the point count is configurable

For an X2-like sensor, the published nominal ranging rate is about 3,000 range samples/s and scan frequency is 5–8 Hz. The simulator derives a nominal scan size as:

`points per scan ≈ ranging samples per second ÷ scans per second`

At 3,000 samples/s and 6 Hz, that is approximately **500 points/scan**. Real scan counts can vary with device configuration and SDK behavior; measure the actual count from the connected unit before using it in a report. See the [YDLIDAR X2 specifications](https://www.ydlidar.com/products/view/6.html) and [SDK example](https://github.com/YDLIDAR/YDLidar-SDK/blob/master/doc/YDLIDAR_SDK_API_for_Developers.md).

## Run on Raspberry Pi 5

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python experiments/11-2d-lidar-slam-simulation/run.py --frames 60 --scan-hz 6 --sample-rate 3000
```

If the repo was already installed and the dependencies are present, skip the installation commands.

For a faster first run or if GIF support is missing:

```bash
python experiments/11-2d-lidar-slam-simulation/run.py --frames 30 --no-animation
```

## Output files

Outputs are written under `results/synthetic/11_2d_lidar_slam_simulation/` by default:

- `summary.json`: assumptions, point counts, derived byte rate, latency percentiles and simulated pose error.
- `metrics.csv`: one row per scan, including generated/valid points and processing time.
- `simulated_scans.npz`: compact angle/range records and ground-truth/estimated poses.
- `figures/slam_map.png`: accumulated scan map and trajectory comparison.
- `figures/metrics_dashboard.png`: point count, deadline, position-error and ICP-fit plots.
- `slam_playback.gif`: animated map accumulation (unless `--no-animation` is supplied or Pillow is unavailable).

Example variations:

```bash
# Stress the processing loop with more scans
python experiments/11-2d-lidar-slam-simulation/run.py --frames 120 --scan-hz 6

# Model a higher nominal scan rate
python experiments/11-2d-lidar-slam-simulation/run.py --frames 60 --scan-hz 8 --sample-rate 3000

# Use an alternate output directory
python experiments/11-2d-lidar-slam-simulation/run.py --out results/pi5_run_01
```

## How to interpret the measurements

- `points_generated` is the number of simulated rays in a scan; `points_valid` counts the returns retained after validation.
- `raw_xy_float32_data_rate_bytes_per_s` is a **derived in-memory XY array rate**, not the LiDAR's UART wire rate. It excludes angle/range packet framing and transport overhead.
- `pipeline_ms` is measured on the computer running the script. Compare its P95 with `1000 / scan_hz` to see whether this demo finishes within the nominal scan period.
- `position_error_m` compares ICP output against simulator ground truth. That ground truth is available only because this is a simulation.
- `scan_generation_ms` measures the simulator's ray-casting cost too, so it is not a sensor read latency. This can make the simulation slower than processing a scan already received from hardware.

## Next stage: physical sensor + real SLAM

Do not use this experiment alone to claim the Pi can run real LiDAR SLAM. The physical test should separately:
1. Capture SDK scans from the real LiDAR and record the actual points/scan, scans/s, timestamps, dropped scans and bytes received.
2. Replay those recorded scans through a real 2-D SLAM engine (for example, a ROS 2-compatible 2-D laser SLAM stack).
3. Run live sensor ingestion and that engine concurrently for 10–15 minutes; record CPU, RAM, temperature/throttling, queue growth, pose output and end-to-end latency.

A single downward-facing 2-D scan plane does not automatically provide a 3-D terrain map. This simulation models a horizontal planar scanner in a 2-D indoor scene to demonstrate point counting and scan matching, not downward-facing landing-surface reconstruction.
