# 2D LiDAR + SLAM benchmark for Raspberry Pi 5

This experiment package extends the AutoNav evidence-gathering repository without replacing existing experiments or environments. It evaluates whether BreezySLAM can process a real, sequential planar laser log within a nominal 6 Hz scan period (166.7 ms). It is an offline dataset benchmark, not a live sensor test or flight-safety claim.

## Dataset choice and scope

Primary candidate: the Intel Research Lab 2D laser dataset distributed through the Robotics Data Set Repository (Radish). The Intel Research Lab log is commonly distributed by the Freiburg SLAM evaluation dataset page. A clear per-recording licence was not verified, so verify terms with the host before redistribution or commercial use. The downloader accepts an explicit URL because mirrors and hosting availability can change; verify the source and checksum before using it in a paper.

Dataset documentation: https://radish.sourceforge.net/  
Common mirror: https://raw.githubusercontent.com/PRBonn/ir-mcl/main/data/intel.clf (verify availability before relying on it).  
BreezySLAM: https://github.com/simondlevy/BreezySLAM

The parser targets CARMEN-style `FLASER` records (ranges followed by odometry pose and timestamps). It does not silently fabricate motion: x/y/theta fields are parsed and logged, but are not automatically treated as accurate ground truth. The file must contain valid records or parsing fails.

## Environment

Use the existing AutoNav environment if BreezySLAM imports there. From the repository root:

```bash
source .venv/bin/activate
python -c "from breezyslam.algorithms import RMHC_SLAM; print('BreezySLAM import OK')"
python -m pip install -r experiments/lidar-pi-slam-benchmark/requirements.txt
```

Dependencies are intentionally small. Matplotlib is only needed for figures; NumPy is used for summaries. Do not reinstall BreezySLAM if it already works in your venv.

## Run

```bash
bash experiments/lidar-pi-slam-benchmark/scripts/download_dataset.sh
python experiments/lidar-pi-slam-benchmark/scripts/benchmark.py verify --input data/lidar-pi-slam-benchmark/intel.clf
python experiments/lidar-pi-slam-benchmark/scripts/benchmark.py offline --input data/lidar-pi-slam-benchmark/intel.clf --runs 5
python experiments/lidar-pi-slam-benchmark/scripts/benchmark.py paced --input data/lidar-pi-slam-benchmark/intel.clf --hz 6 --minutes 10
python experiments/lidar-pi-slam-benchmark/scripts/benchmark.py plot
python -m unittest discover -s experiments/lidar-pi-slam-benchmark/tests -v
```

The paced run repeats the recording in sequence until the requested duration is reached, annotating loop boundaries. This measures replay scheduling and processing latency; it cannot reproduce sensor transport, actual live queue behavior, or drone dynamics.

## Evidence rules

- CSV and JSON outputs are written beneath `results/lidar-pi-slam-benchmark/`.
- Offline throughput is measured separately from dataset parsing and initialization.
- Per-scan processing time uses `time.perf_counter_ns()`.
- A processing-budget exceedance means processing duration > 1/hz. A scheduled-deadline miss means finish time > scheduled release + period.
- Mapping and pose estimates are reported only if BreezySLAM is installed and the data parser succeeds. BreezySLAM's RMHC algorithm is a lightweight 2D laser SLAM baseline, not a full inertial or drone navigation stack.
- The 6 Hz result is encouraging only if tail latency, deadline behavior, thermal stability, memory, and system headroom are acceptable. Camera, IMU, control, I/O, and safety workloads remain untested here.
