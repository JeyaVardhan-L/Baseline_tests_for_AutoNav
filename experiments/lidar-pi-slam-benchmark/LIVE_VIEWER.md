# Live browser viewer

The viewer uses only Python's standard library. Keep it on a trusted LAN.

## 1. Start the viewer on the Pi

From the repository root:

```bash
python experiments/lidar-pi-slam-benchmark/scripts/live_viewer.py --port 8765
```

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
    save_live_map(slam, OUT, args.map_pixels)
```

This example calls `system_metadata()` for simplicity, but it may read several system files and take a CPU snapshot. For a cleaner timing benchmark, collect resource metrics on a separate slower cadence (e.g. once per second), and publish cached values here. The viewer POST is short-timeout and failures are ignored.

## 3. Important details

- The helper writes a temporary PNG and atomically renames it, so the browser does not normally read a partially written image.
- Map export every 10 scans adds rendering overhead to the benchmark. For valid latency numbers, compare a run with viewer/map publishing disabled against a separate visualization run.
- The browser refreshes the map and state continuously. It shows estimated SLAM pose, not ground truth.
- The viewer binds to `0.0.0.0` by default for LAN access. Use `--host 127.0.0.1` for local-only access.
