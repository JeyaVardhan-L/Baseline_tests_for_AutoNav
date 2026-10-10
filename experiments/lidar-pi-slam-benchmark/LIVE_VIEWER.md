# Live browser viewer

The viewer uses only Python's standard library. Keep it on a trusted LAN.

## 1. Start the viewer on the Pi

From the repository root:

```bash
python experiments/lidar-pi-slam-benchmark/scripts/live_viewer.py --port 8765     --output-dir results/lidar-pi-slam-benchmark/runs/my_run_01
```

Use the same directory you pass to `benchmark.py paced --out-dir`. The viewer shows only the `live_map.png` snapshot written by `save_live_map` into that directory. It does **not** fall back to any other map: the old unlabelled `slam_map.png` is the known-invalid 35 m paced map and is ignored, and final per-mode maps (`paced_slam_map.png`) are not served because their validity is not known to the viewer. If no `live_map.png` exists the page says so and tells you what to do.

**Failed map refreshes are visible.** `save_live_map` no longer swallows errors: a missing matplotlib/numpy, a rendering error or an I/O error prints a warning to stderr (once per distinct reason), sets `live_publish.LAST_MAP_ERROR`, leaves the previous `live_map.png` untouched and writes `live_map.error.txt` next to it. While that marker is newer than the map, the viewer hides the older map and shows the reason, because that map would no longer be current; the next successful refresh removes the marker. A marker from an earlier run is ignored.

**Stale maps are never shown.** The viewer remembers when the current run's first telemetry arrived (a new run is detected after a >3 s telemetry gap or when `scans_processed` decreases) and serves `live_map.png` only if it was written at or after that moment. A `live_map.png` left over from an earlier run, or present before any telemetry arrived, is reported as stale and not displayed. Call `publish_state` for a scan before the first `save_live_map`, as in the snippet below; a map written earlier than the first telemetry is treated as stale until the next snapshot. The viewer and the benchmark must run on the same host (file modification times are compared with the viewer's clock).

Find the Pi's LAN address with `hostname -I`. On the laptop, open `http://PI_LAN_IP:8765`.

If the laptop cannot connect, check that both devices are on the same LAN and allow TCP port 8765 through the Pi firewall. Do not port-forward this dashboard to the public internet.

## 2. Connect the benchmark publisher

In `scripts/benchmark.py`, add these imports near the top:

```python
from live_publish import publish_state, save_live_map
```

Because this script is run directly, its own directory is on Python's import path.

In `command_paced`, immediately after `pose=slam_one(...)` and after `finish=time.monotonic_ns()`, publish a snapshot. Adapt variable names to your local version:

```python
elapsed_ms = (finish - actual_start) / 1e6
publish_state({
    "mode": "paced replay",
    "scans_processed": index + 1,
    "sample_id": index,
    "scan_rate_hz": hz,
    "processing_ms": elapsed_ms,
    "pose_x_m": pose[0] / 1000.0,
    "pose_y_m": pose[1] / 1000.0,
    "pose_theta_deg": pose[2],
    "deadline_misses": missed,
    "cpu_temperature_c": system_metadata().get("cpu_temperature_c"),
    "process_rss_mb": (
        system_metadata().get("process_rss_bytes", 0) / (1024 * 1024)
    ),
})
if index % 10 == 0:
    save_live_map(slam, out_dir, args.map_pixels)   # `out_dir` is the --out-dir Path defined at the top of command_paced
```

This example calls `system_metadata()` for simplicity, but it may read several system files and take a CPU snapshot. For a cleaner timing benchmark, collect resource metrics on a separate slower cadence (e.g. once per second), and publish cached values here. The viewer POST is short-timeout and failures are ignored.

## 3. Important details

- The helper writes a temporary PNG and atomically renames it, so the browser does not normally read a partially written image.
- Map export every 10 scans adds rendering overhead to the benchmark. For valid latency numbers, compare a run with viewer/map publishing disabled against a separate visualization run.
- The browser refreshes the map and state continuously. It shows estimated SLAM pose, not ground truth.
- The viewer binds to `0.0.0.0` by default for LAN access. Use `--host 127.0.0.1` for local-only access.
