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

Dependencies are intentionally small. `verify`, `offline`, `paced` and `summary` use only the standard library plus BreezySLAM (for `offline`/`paced`); NumPy and Matplotlib are needed only for figures (`plot` and the map/trajectory PNGs). Optional: `psutil` adds RAM/RSS fields to the recorded `system` metadata (a note is recorded if absent) and `scipy` is needed only by `scripts/diagnose_inputs.py`. On systems without `vcgencmd` (for example Windows) `throttled_state` is recorded as `null` (not measured). Do not reinstall BreezySLAM if it already works in your venv.

## Run

```bash
B=experiments/lidar-pi-slam-benchmark/scripts/benchmark.py
D=data/lidar-pi-slam-benchmark/intel.clf
R=results/lidar-pi-slam-benchmark/runs/my_run_01   # a NEW directory per run

bash experiments/lidar-pi-slam-benchmark/scripts/download_dataset.sh
python $B verify  --input $D --out-dir $R
python $B offline --input $D --out-dir $R --runs 5
python $B paced   --input $D --out-dir $R --hz 6 --minutes 10
python $B summary --mode offline --out-dir $R
python $B summary --mode paced   --out-dir $R
python $B plot    --mode offline --out-dir $R
python $B plot    --mode paced   --out-dir $R
python -m unittest discover -s experiments/lidar-pi-slam-benchmark/tests -v
```

### Map size, pose validity and what a valid run means

- `--map-meters` / `--map-pixels` set the BreezySLAM map (defaults 130 m, 2600 px = 0.05 m/px, 6.76 M cells). BreezySLAM places the start at the map centre. `verify` reports the odometry extent of the recording: for `intel.clf` the odometry reaches 62.2 m radially from the start, so an odometry-following pose needs a map of at least 124.5 m. The previous 35 m / 800 px default could not contain even that path.
- A large enough map does **not** make the SLAM estimate correct; validity only says the pose stayed on the map.

### What the historical pose "divergence" actually was (diagnosis, `scripts/diagnose_inputs.py`)

BreezySLAM was not run for this diagnosis; it used the dataset, the committed CSVs, the upstream BreezySLAM source (read, not the installed copy) and an independent scan-only ICP chain (not ground truth).

- **The recorded odometry heading drifts; a SLAM heading that differs from it is not by itself a failure.** The ICP chain differs from odometry heading by 8° at scan 200, 41° at 440 and 75° at 800, and the paced SLAM heading follows the ICP chain (within ~14° up to scan 800), not the odometry.
- **Paced run (constant dt):** SLAM stayed within 0.3-3.5 m of the ICP chain up to scan 800 while odometry alone was 13-14 m off. It left the 35 m map at scan 829 because the robot really is ~17 m from its start there (map centred on start => +/-17.5 m), i.e. mainly a map-extent problem. After the pose is off the map (BreezySLAM drops rays that start outside the map) the track degrades; this part is inferred, not demonstrated.
- **Offline run (per-scan recorded dt):** the heading was already 179° from the ICP chain at scan 236 and the position 12-16 m off by scan 440. The recorded timestamps are arrival times: 4552 intervals are < 20 ms (631 go backwards). Passed as BreezySLAM `dt` they make its velocity-based scan compensation absurd (scan stretch factors up to 3.9, negative factors flip a scan; 1921 scans with factor error > 0.2). Scan 235 (dt 1.2 ms, factor -0.39) immediately precedes the first heading jump. This is a strong correlation; it is **not proven** until the offline run is repeated with `--dt-source nominal` on real BreezySLAM.
- **Unsigned dxy** turned 67 reversing steps into forward motion (dead-reckoning error 4.2 m vs 0.8 m signed). Minor, fixed.
- **Ruled out:** scan-index/angle ordering (BreezySLAM convention fits odometry-aligned scans, median residual 0.043 m vs 0.102 m reversed).
- **Not supported by evidence, left unchanged:** the 12 m range clamp. Upstream treats a nonzero reading as an obstacle at its own distance, so clamped no-returns (2.8% of beams are the 81.83 m sentinel) become phantom obstacles at 12 m, but the paced run tracks well with the clamp in place, so it is not shown to cause divergence. Verify against the installed BreezySLAM before changing it.

### Errors, exit codes and interrupted runs

| Exit | Meaning |
|---|---|
| 0 | success |
| 2 | usage or environment error (bad argument, bad/missing file, existing results, BreezySLAM missing): one `ERROR:` line, no traceback |
| 70 | **internal error** (a bug): `INTERNAL ERROR (<type>)` with the failing `file:line`; never reported as success or as a usage error |
| 130 | interrupted (Ctrl-C or SIGTERM); partial results may have been saved, see below |

Add `--debug` (or set `AUTONAV_DEBUG=1`) to any command for the full traceback; the exit code does not change.

`offline` and `paced` catch Ctrl-C/SIGTERM and save what was actually completed, marked `"run_status": "interrupted"` in `<mode>_summary.json` (and `RUN STATUS: INTERRUPTED` in `summary` output). An interrupted run is **never** valid for performance claims (`valid_for_performance_claims` / `all_runs_valid_for_performance_claims` are false). `paced` keeps every processed scan and computes statistics only over those scans (nothing is estimated for the rest; an `incomplete` block records requested vs elapsed time). `offline` keeps only fully completed runs and discards the run in progress. If nothing was processed, nothing is written. CSV/JSON are written atomically (temp file then replace) and before the figures, so a failed or interrupted plot never costs measurements; figure success or failure is recorded under `figures` in the JSON. Existing results are still never overwritten (the guard runs before the benchmark starts).

### Recorded rates and metadata (what the numbers mean)

`verify` writes a `timing_rates` block (it replaces the old `nominal_hz_from_median_interval`, which implied a sustained sensor rate it never established; historical files keep the old name):

- `median_positive_interval_rate_hz` = 1 / median of the strictly positive timestamp intervals: a typical-gap frequency. Zero and backward intervals are excluded from the median, which raises the median interval and so lowers this frequency compared with using every interval.
- `mean_rate_hz_over_recording` = (scans - 1) / (max - min timestamp): average throughput over the whole recording including gaps and stalls. Zero/backward intervals still count as scans but cannot lengthen the span.
- For `intel.clf`: about 9.48 Hz (median positive interval) versus about 5.06 Hz (whole recording). Timestamps are message-arrival times, so neither is the sensor's configured scan rate.

The `system` block is a set of **single readings taken when the metadata was generated** (after the timed work for `offline`/`paced`): `system_cpu_percent_over_100ms_at_metadata_time` (renamed from `cpu_percent_snapshot`; historical files keep the old name), RSS, temperature, `throttled_state`, governor. They are not CPU load, peak memory, a temperature trend or throttling history of the run; sampling those during the run is not implemented. `metadata_sampling_note` in the JSON says so.

### dt policy and signed dxy

`offline` now passes one constant `dt` (the median positive recorded interval, written to `offline_summary.json` as `dt_policy`) instead of the per-scan arrival-time delta. `--dt-source recorded` reproduces the legacy behaviour. `paced` already used the constant replay period. `dxy` is signed by the motion's projection on the previous heading. Compare a run with the ICP reference:

```bash
python experiments/lidar-pi-slam-benchmark/scripts/diagnose_inputs.py inputs --input $D
python experiments/lidar-pi-slam-benchmark/scripts/diagnose_inputs.py compare --input $D --csv $R/offline_runs.csv --mode offline --run 1 --map-meters 130
```
- Every run records, for **every** scan (offline: warm-up included), whether the pose lies inside `[0, map_meters)` on both axes: `pose_in_map` per CSV row, and `pose_validity` (invalid-scan count, fraction, first invalid scan) in the JSON summary. Poses are never reset, clamped or dropped.
- If any pose is outside the map, the run is **not valid for mapping-quality or performance claims**; this is printed as a warning, written to the JSON (`valid_for_performance_claims`), and shown in red in the figure titles. No recovery strategy is implemented.
- Validity is computed after the timed loop and does not add to the measured per-scan latency.

### Output files (never shared between modes)

| Mode | Raw data | Summary | Figures |
|---|---|---|---|
| offline | `offline_runs.csv` | `offline_summary.json` | `offline_slam_map.png`, `offline_trajectory.png`, `offline_latency_distribution.png`, `offline_latency_over_time.png` |
| paced | `paced_scan_timings.csv` | `paced_summary.json` | `paced_slam_map.png`, `paced_trajectory.png`, `paced_latency_distribution.png`, `paced_latency_over_time.png` |

Map and trajectory titles state the mode, the processed scan range and the validity. `plot --mode` is required and reads only that mode's CSV; it errors rather than falling back to the other mode. Commands refuse to overwrite existing result files unless `--overwrite` is passed, so use a new `--out-dir` for each run. Old unlabelled files in `results/lidar-pi-slam-benchmark/` (`slam_map.png`, `trajectory.png`, `latency_*.png`) are historical: the map/trajectory there came from the **paced** run, were produced with the 35 m map, and are not valid evidence (the pose left the map).

### Summary command and percentile method

`summary` is read-only (unless `--output` is given) and reports, separately and labelled: per-run statistics; the **median across runs** of each per-run statistic (a median of run P99s is not the P99 of all samples); the **worst run** (max across runs of each per-run statistic); and the **pooled** statistics over all samples. Percentiles use linear interpolation between closest ranks, `index=(n-1)*p/100` on the sorted samples (same as `numpy.percentile` default). The CSVs do not store the map size: new CSVs carry the recorded `pose_in_map` column; for older CSVs pass `--map-meters` with the size the run actually used (the legacy runs used 35):

```bash
python $B summary --mode offline --map-meters 35   # historical committed offline_runs.csv
```

`summary` also prints the **provenance** of what it read: the source CSV path, whether the file is a legacy-schema historical measurement or a current-schema result, and the platform/Python/time recorded in the sibling `<mode>_summary.json`, with a flag when that platform differs from the machine running `summary`. If the metadata file is missing or unreadable it says the platform is UNKNOWN; it never infers one. It refuses to compute statistics from negative or non-finite latencies, and `--map-meters` must be finite and > 0 (as for `verify`/`offline`). `offline` requires `--runs >= 1` and `0 <= --warmup < scan count`; `paced` requires `--minutes > 0`.

The paced run repeats the recording in sequence until the requested duration is reached, annotating loop boundaries. This measures replay scheduling and processing latency; it cannot reproduce sensor transport, actual live queue behavior, or drone dynamics.

## Evidence rules

- CSV and JSON outputs are written beneath `results/lidar-pi-slam-benchmark/`.
- Offline throughput is measured separately from dataset parsing and initialization.
- Offline per-scan processing time and run wall time use `time.perf_counter_ns()`. Paced replay uses `time.monotonic_ns()` for its schedule, start/finish timestamps and per-scan duration.
- A processing-budget exceedance means processing duration > 1/hz. A scheduled-deadline miss means finish time > scheduled release + period.
- Mapping and pose estimates are reported only if BreezySLAM is installed and the data parser succeeds. BreezySLAM's RMHC algorithm is a lightweight 2D laser SLAM baseline, not a full inertial or drone navigation stack.
- The 6 Hz result is encouraging only if tail latency, deadline behavior, thermal stability, memory, and system headroom are acceptable. Camera, IMU, control, I/O, and safety workloads remain untested here.
