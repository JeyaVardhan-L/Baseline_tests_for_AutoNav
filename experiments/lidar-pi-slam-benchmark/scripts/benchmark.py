#!/usr/bin/env python3
"""Reproducible CARMEN FLASER + BreezySLAM benchmark; Python 3.10+."""
from __future__ import annotations
import argparse, contextlib, csv, json, math, os, platform, shutil, signal, statistics, subprocess, sys, threading, time, traceback
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO_ROOT = HERE.parents[1]
OUT = REPO_ROOT / "results" / "lidar-pi-slam-benchmark"
PERIOD_NS = 1_000_000_000

# Map defaults. Intel odometry dead-reckoning reaches 62.2 m radially from the
# start (see `verify`), and BreezySLAM starts at the map centre, so a map that
# can contain that path needs >= 124.5 m. 130 m leaves ~4% margin; 2600 px
# gives 0.05 m/px (2600^2 = 6.76 M cells). The old 35 m / 800 px (0.044 m/px)
# could not contain even the odometry-only path. A map that can contain the
# odometry path does NOT guarantee the SLAM pose stays on it; see pose_validity.
DEFAULT_MAP_METERS = 130.0
DEFAULT_MAP_PIXELS = 2600
PERCENTILE_METHOD = (
    "linear interpolation between closest ranks: index=(n-1)*p/100 on the sorted "
    "samples (identical to numpy.percentile default 'linear')"
)
STAT_NAMES = ("mean", "median", "p95", "p99", "max")

class EnvironmentProblem(RuntimeError):
    """A missing or unusable runtime dependency (e.g. BreezySLAM): an actionable, user-facing error."""


# Errors reported as one concise line (exit 2): bad arguments, bad/missing files, missing dependencies.
USER_ERRORS = (ValueError, OSError, EnvironmentProblem)
EXIT_USER_ERROR, EXIT_INTERNAL_ERROR, EXIT_INTERRUPTED = 2, 70, 130


@contextlib.contextmanager
def sigterm_as_keyboard_interrupt():
    """Treat SIGTERM like Ctrl-C so a `kill`/service stop also saves partial results.

    Only installed in the main thread; harmless where SIGTERM is not delivered (Windows)."""
    previous, installed = None, False
    if hasattr(signal, "SIGTERM") and threading.current_thread() is threading.main_thread():
        def _raise(signum, frame):
            raise KeyboardInterrupt(f"signal {signum}")
        try:
            previous = signal.signal(signal.SIGTERM, _raise)
            installed = True
        except (ValueError, OSError):
            installed = False
    try:
        yield
    finally:
        if installed:
            signal.signal(signal.SIGTERM, previous if previous is not None else signal.SIG_DFL)


def period_seconds(hz: float) -> float:
    if not math.isfinite(hz) or hz <= 0:
        raise ValueError("hz must be finite and > 0")
    return 1.0 / hz

def classify_timing(scheduled_ns: int, start_ns: int, finish_ns: int, period_ns: int) -> dict:
    duration = finish_ns - start_ns
    return {
        "processing_duration_ns": duration,
        "start_lateness_ns": max(0, start_ns - scheduled_ns),
        "finish_lateness_ns": max(0, finish_ns - (scheduled_ns + period_ns)),
        "processing_budget_exceeded": duration > period_ns,
        "deadline_missed": finish_ns > scheduled_ns + period_ns,
    }


def pose_in_map(x_mm, y_mm, map_meters: float) -> bool:
    """True if a BreezySLAM pose (mm, map frame, origin at a map corner) lies on the map."""
    size_mm = map_meters * 1000.0
    return (
        math.isfinite(x_mm) and math.isfinite(y_mm)
        and 0.0 <= x_mm < size_mm and 0.0 <= y_mm < size_mm
    )


def validity_summary(flags, indices, map_meters: float) -> dict:
    """Account for pose-in-map flags. `indices` labels each flag (e.g. scan index).

    Nothing is reset or filtered: a run with any invalid pose is reported as not
    valid for mapping-quality or performance claims.
    """
    flags, indices = list(flags), list(indices)
    if len(flags) != len(indices):
        raise ValueError("flags and indices must have equal length")
    invalid = [i for f, i in zip(flags, indices) if not f]
    total = len(flags)
    return {
        "map_meters": map_meters,
        "scans_evaluated": total,
        "invalid_scans": len(invalid),
        "invalid_fraction": (len(invalid) / total) if total else None,
        "first_invalid_scan_index": invalid[0] if invalid else None,
        "valid_for_performance_claims": bool(total) and not invalid,
        "note": (
            "Pose must stay inside [0, map_meters) on both axes for every evaluated scan. "
            "Poses are never reset or hidden; any invalid scan invalidates the run."
        ),
    }


def odometry_extent(scans, map_meters: float | None = None) -> dict:
    """Spatial extent of the recorded odometry relative to the first scan.

    Odometry is not ground truth and the SLAM pose may differ from it; this only
    bounds what map size an odometry-following pose would need. The radial bound
    is rotation-invariant, so it holds whatever the initial SLAM heading.
    """
    x0, y0 = scans[0]["x_m"], scans[0]["y_m"]
    dx = [s["x_m"] - x0 for s in scans]
    dy = [s["y_m"] - y0 for s in scans]
    radial = [math.hypot(a, b) for a, b in zip(dx, dy)]
    max_axis = max(max(abs(v) for v in dx), max(abs(v) for v in dy))
    max_radial = max(radial)
    out = {
        "x_offset_m": {"min": min(dx), "max": max(dx)},
        "y_offset_m": {"min": min(dy), "max": max(dy)},
        "max_axis_offset_m": max_axis,
        "max_radial_offset_m": max_radial,
        "min_map_meters_axis_aligned": 2.0 * max_axis,
        "min_map_meters_rotation_safe": 2.0 * max_radial,
    }
    if map_meters is not None:
        half = map_meters / 2.0
        out["configured_map_meters"] = map_meters
        out["odometry_path_fits_configured_map"] = max_radial < half
        out["first_scan_radial_offset_reaches_half_map"] = next(
            (i for i, r in enumerate(radial) if r >= half), None
        )
    return out


def output_paths(out_dir, mode: str) -> dict:
    """Mode-specific output files; offline and paced can never collide."""
    if mode not in ("offline", "paced"):
        raise ValueError(f"unknown mode {mode!r}")
    out_dir = Path(out_dir)
    return {
        "csv": out_dir / ("offline_runs.csv" if mode == "offline" else "paced_scan_timings.csv"),
        "json": out_dir / f"{mode}_summary.json",
        "map": out_dir / f"{mode}_slam_map.png",
        "trajectory": out_dir / f"{mode}_trajectory.png",
        "latency_distribution": out_dir / f"{mode}_latency_distribution.png",
        "latency_over_time": out_dir / f"{mode}_latency_over_time.png",
    }


def ensure_writable(paths, overwrite: bool = False) -> None:
    """Refuse to overwrite existing measurements unless explicitly allowed."""
    existing = [str(p) for p in paths if Path(p).exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "Refusing to overwrite existing file(s): " + ", ".join(existing)
            + ". Choose a new --out-dir (recommended) or pass --overwrite."
        )


def parse_flaser_line(line: str, line_number: int = 0):
    fields = line.strip().split()
    if not fields or fields[0] != "FLASER":
        return None

    try:
        n = int(fields[1])
        if n < 2:
            raise ValueError("scan must contain at least two ranges")

        # FLASER n ranges laser_x laser_y laser_theta
        #       odom_x odom_y odom_theta ipc_timestamp hostname logger_timestamp
        pose_start = 2 + n
        expected_min = pose_start + 9

        if len(fields) < expected_min:
            raise ValueError(
                f"declares {n} ranges but record has only "
                f"{len(fields)} fields"
            )

        ranges = [float(v) for v in fields[2:pose_start]]

        # Laser pose
        laser_x, laser_y, laser_theta = map(
            float, fields[pose_start:pose_start + 3]
        )

        # Odometry pose
        odom_x, odom_y, odom_theta = map(
            float, fields[pose_start + 3:pose_start + 6]
        )

        # Logger metadata follows the odometry pose.
        ipc_timestamp = float(fields[pose_start + 6])
        hostname = fields[pose_start + 7]
        logger_timestamp = float(fields[pose_start + 8])

        numeric_values = (
            ranges
            + [
                laser_x, laser_y, laser_theta,
                odom_x, odom_y, odom_theta,
                ipc_timestamp, logger_timestamp,
            ]
        )

        if not all(math.isfinite(v) for v in numeric_values):
            raise ValueError("non-finite numeric field")
        if any(r < 0 for r in ranges):
            raise ValueError("negative range")

        # Use the IPC timestamp for scan ordering and replay timing.
        return {
            "ranges_m": ranges,
            "x_m": odom_x,
            "y_m": odom_y,
            "theta_rad": odom_theta,
            "timestamp": ipc_timestamp,
            "odom_timestamp": logger_timestamp,
            "hostname": hostname,
            "line_number": line_number,
        }

    except (ValueError, IndexError) as exc:
        raise ValueError(
            f"Malformed FLASER record on line {line_number}: {exc}"
        ) from exc


def load_scans(path: Path):
    scans = []
    with path.open("r", encoding="utf-8", errors="strict") as f:
        for i, line in enumerate(f, 1):
            scan = parse_flaser_line(line, i)
            if scan is not None:
                scans.append(scan)
    if len(scans) < 2:
        raise ValueError(f"Expected >=2 FLASER scans in {path}; found {len(scans)}")
    lengths = {len(s["ranges_m"]) for s in scans}
    if len(lengths) != 1:
        raise ValueError(f"Inconsistent scan lengths found: {sorted(lengths)}")
    times = [s["timestamp"] for s in scans]
    non_increasing = sum(
        b <= a for a, b in zip(times, times[1:])
    )
    if non_increasing:
        print(
            f"WARNING: {non_increasing} non-increasing source timestamp "
            "transitions found. Preserving original scan order. "
            "Paced replay uses the configured replay rate.",
            file=sys.stderr,
        )
    return scans

def percentile(values, p):
    if not values:
        return None
    s = sorted(values)
    i = (len(s)-1) * p / 100.0
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return s[lo] if lo == hi else s[lo] * (hi-i) + s[hi] * (i-lo)

def stats(values):
    if not values:
        return {}
    return {"mean": statistics.fmean(values), "median": statistics.median(values),
            "p95": percentile(values, 95), "p99": percentile(values, 99), "max": max(values)}

def _stats_n(values):
    return {"n": len(values), **stats(values)}


def summarize_runs(latency_ms_by_run: dict) -> dict:
    """Aggregate per-run latency samples (ms). Every block is labelled.

    per_run:            statistics of each run's own samples.
    median_across_runs: median over runs of each per-run statistic (a median of
                        run P99s is NOT the P99 of all samples).
    worst_run:          maximum over runs of each per-run statistic.
    pooled:             statistics of all samples from all runs concatenated.
    """
    if not latency_ms_by_run:
        raise ValueError("no runs to summarize")
    for run, v in latency_ms_by_run.items():
        validate_latencies(v, f"run {run}")
    per_run = {run: _stats_n(v) for run, v in sorted(latency_ms_by_run.items())}
    pooled_values = [x for v in latency_ms_by_run.values() for x in v]
    return {
        "percentile_method": PERCENTILE_METHOD,
        "run_count": len(per_run),
        "per_run": per_run,
        "median_across_runs": {
            k: statistics.median(r[k] for r in per_run.values()) for k in STAT_NAMES
        },
        "worst_run": {k: max(r[k] for r in per_run.values()) for k in STAT_NAMES},
        "pooled": _stats_n(pooled_values),
    }


def load_csv_rows(path: Path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; run the matching benchmark mode first")
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path} contains no data rows")
    return rows


def _to_bool(text: str) -> bool:
    return str(text).strip().lower() == "true"


def summarize_offline_csv(rows, map_meters: float | None = None) -> dict:
    required = {"run", "scan_index", "processing_ms"}
    if not required <= set(rows[0]):
        raise ValueError(f"not an offline CSV: need columns {sorted(required)}, got {sorted(rows[0])}")
    by_run: dict = {}
    for r in rows:
        by_run.setdefault(int(r["run"]), []).append(float(r["processing_ms"]))
    summary = {"mode": "offline", "unit": "ms per scan (timed scans only; warm-up excluded)"}
    summary.update(summarize_runs(by_run))
    summary["pose_validity"] = _csv_validity(rows, map_meters, ("run", "scan_index"))
    return summary


def summarize_paced_csv(rows, map_meters: float | None = None) -> dict:
    required = {"index", "processing_duration_ns", "start_lateness_ns"}
    if not required <= set(rows[0]):
        raise ValueError(f"not a paced CSV: need columns {sorted(required)}, got {sorted(rows[0])}")
    dur = [int(r["processing_duration_ns"]) / 1e6 for r in rows]
    start_late = [int(r["start_lateness_ns"]) / 1e6 for r in rows]
    validate_latencies(dur, "paced processing_duration_ns")
    validate_latencies(start_late, "paced start_lateness_ns")
    return {
        "mode": "paced",
        "percentile_method": PERCENTILE_METHOD,
        "scans": len(rows),
        "processing_ms": _stats_n(dur),
        "start_lateness_ms": _stats_n(start_late),
        "processing_budget_exceedances": sum(_to_bool(r["processing_budget_exceeded"]) for r in rows),
        "deadline_misses": sum(_to_bool(r["deadline_missed"]) for r in rows),
        "pose_validity": _csv_validity(rows, map_meters, ("index",)),
    }


def _csv_validity(rows, map_meters, label_cols):
    """Pose validity from a raw CSV.

    The CSV does not store the map size. Rows written by this version carry a
    `pose_in_map` column recorded during the run against the run's real map; that
    is preferred. Otherwise --map-meters must be the size the run actually used
    (a wrong value gives a wrong answer, e.g. legacy runs used 35 m).
    """
    labels = [tuple(int(r[c]) for c in label_cols) for r in rows]
    labels = [l[-1] if len(l) == 1 else l for l in labels]
    if map_meters is not None:
        flags = [pose_in_map(float(r["pose_x_mm"]), float(r["pose_y_mm"]), map_meters) for r in rows]
        source = f"recomputed from CSV poses for a {map_meters:g} m map (caller-supplied; must equal the run's map)"
    elif "pose_in_map" in rows[0]:
        flags = [_to_bool(r["pose_in_map"]) for r in rows]
        source = "pose_in_map column recorded during the run"
    else:
        return {"evaluated": False,
                "reason": "legacy CSV without pose_in_map; pass --map-meters with the map size the run used"}
    out = validity_summary(flags, labels, map_meters)
    out["evaluated"] = True
    out["source"] = source
    out["scope"] = "rows present in the CSV only (offline warm-up scans are not recorded there)"
    return out


def load_provenance(csv_path, mode: str, rows) -> dict:
    """Where a summary's numbers came from. Never infers a platform that was not recorded.

    The recorded platform is read from the `system` block of the run's own
    `<mode>_summary.json` next to the CSV. Results are called "current schema" if the CSV
    carries the `pose_in_map` column written by this version, otherwise "legacy schema"
    (a historical measurement from before pose-validity and dt-policy recording).
    """
    csv_path = Path(csv_path)
    meta_path = csv_path.parent / f"{mode}_summary.json"
    prov = {
        "source_csv": str(csv_path.resolve()),
        "result_generation": (
            "current schema (pose_in_map recorded during the run)"
            if "pose_in_map" in rows[0] else
            "legacy schema (historical measurement; no pose_in_map, map size not recorded)"
        ),
        "current_machine": platform.platform(),
        "metadata_file": None,
        "recorded_platform": None,
        "recorded_machine": None,
        "recorded_python": None,
        "recorded_timestamp_utc": None,
        "measured_on_this_machine": None,
        "run_status": None,
    }
    if not meta_path.exists():
        prov["note"] = f"metadata file {meta_path.name} not found next to the CSV: recorded platform UNKNOWN (not inferred)"
        return prov
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        prov["metadata_file"] = str(meta_path.resolve())
        prov["note"] = f"metadata file unreadable ({exc}): recorded platform UNKNOWN (not inferred)"
        return prov
    prov["metadata_file"] = str(meta_path.resolve())
    system = meta.get("system") if isinstance(meta, dict) else None
    if meta.get("mode") not in (None, mode) or not isinstance(system, dict) or not system.get("platform"):
        prov["note"] = "metadata present but has no matching mode/system.platform: recorded platform UNKNOWN (not inferred)"
        return prov
    prov["run_status"] = meta.get("run_status")
    prov["recorded_platform"] = system.get("platform")
    prov["recorded_machine"] = system.get("machine")
    prov["recorded_python"] = str(system.get("python", "")).split()[0] or None
    prov["recorded_timestamp_utc"] = system.get("timestamp_utc")
    prov["measured_on_this_machine"] = system["platform"] == prov["current_machine"]
    return prov


def format_summary(s: dict) -> str:
    lines = [f"mode: {s['mode']}", f"percentile method: {s['percentile_method']}"]
    pv = s.get("provenance")
    if pv:
        lines.append(f"source CSV: {pv['source_csv']}")
        lines.append(f"result generation: {pv['result_generation']}")
        if pv.get("run_status") == "interrupted":
            lines.append("RUN STATUS: INTERRUPTED - incomplete run (partial results only); NOT valid for performance claims")
        elif pv.get("run_status"):
            lines.append(f"run status: {pv['run_status']}")
        if pv["recorded_platform"]:
            where = {True: "this machine", False: "a DIFFERENT machine than this one", None: "unknown"}[pv["measured_on_this_machine"]]
            lines.append(f"recorded platform: {pv['recorded_platform']} (python {pv['recorded_python']}, {pv['recorded_timestamp_utc']}); measured on {where}")
        else:
            lines.append(f"recorded platform: UNKNOWN - {pv.get('note', 'no metadata')}")
        lines.append(f"this machine: {pv['current_machine']}")
    fmt = lambda d: "  ".join(f"{k}={d[k]:.4f}" for k in STAT_NAMES if k in d)
    if s["mode"] == "offline":
        lines.append(f"{s['unit']}")
        for run, d in s["per_run"].items():
            lines.append(f"[per run {run}] n={d['n']}  {fmt(d)}")
        lines.append(f"[median across {s['run_count']} runs of each per-run statistic]  {fmt(s['median_across_runs'])}")
        lines.append(f"[worst run: max across runs of each per-run statistic]  {fmt(s['worst_run'])}")
        lines.append(f"[pooled over all {s['pooled']['n']} samples]  {fmt(s['pooled'])}")
    else:
        lines.append(f"[paced processing ms, n={s['scans']}]  {fmt(s['processing_ms'])}")
        lines.append(f"[paced start lateness ms]  {fmt(s['start_lateness_ms'])}")
        lines.append(f"budget exceedances={s['processing_budget_exceedances']}  deadline misses={s['deadline_misses']}")
    v = s["pose_validity"]
    if not v.get("evaluated"):
        lines.append(f"pose validity: NOT EVALUATED ({v['reason']})")
    elif v["valid_for_performance_claims"]:
        lines.append(f"pose validity: all {v['scans_evaluated']} evaluated poses inside the map ({v['source']})")
    else:
        lines.append(
            f"pose validity: INVALID - {v['invalid_scans']}/{v['scans_evaluated']} "
            f"({100 * v['invalid_fraction']:.1f}%) poses outside the map ({v['source']}), "
            f"first at {v['first_invalid_scan_index']}. Latency figures are NOT valid for performance claims."
        )
    return "\n".join(lines)


def system_metadata():
    d = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(),
         "machine": platform.machine(), "python": sys.version, "cpu_count": os.cpu_count(),
         "pid": os.getpid()}
    try:
        import psutil
        d["ram_total_bytes"] = psutil.virtual_memory().total
        d["system_cpu_percent_over_100ms_at_metadata_time"] = psutil.cpu_percent(interval=0.1)
        d["process_rss_bytes"] = psutil.Process().memory_info().rss
    except ImportError:
        d["psutil"] = "unavailable; install optional psutil for process/system metrics"
    try:
        d["cpu_temperature_c"] = float(Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()) / 1000
    except (OSError, ValueError):
        d["cpu_temperature_c"] = None
    # No shell and no stderr redirect: the old shell redirect made cmd.exe print "The system cannot find the
    # path specified." on Windows. None means "not measured" (vcgencmd absent or failed).
    d["throttled_state"] = None
    if shutil.which("vcgencmd"):
        try:
            res = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                d["throttled_state"] = res.stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        d["cpu_governor"] = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor").read_text().strip()
    except OSError:
        d["cpu_governor"] = None
    d["metadata_sampling_note"] = (
        "cpu/RSS/temperature/throttled/governor are single readings taken when this metadata was "
        "generated (after the timed work for offline/paced), not sampled during the benchmark. The CPU "
        "figure is system-wide utilisation over a 100 ms window at that moment. None of them is CPU load, "
        "peak memory, a temperature trend or throttling history of the run."
    )
    return d

def make_slam(scan_size, hz, args):
    try:
        from breezyslam.algorithms import RMHC_SLAM
        from breezyslam.sensors import Laser
    except ImportError as exc:
        raise EnvironmentProblem("BreezySLAM is not importable in this Python environment. Reuse the AutoNav .venv.") from exc
    laser = Laser(scan_size, hz, args.fov, int(args.max_range_m * 1000), 0)
    slam = RMHC_SLAM(laser, args.map_pixels, args.map_meters, random_seed=args.seed)
    return slam

def odom_delta(prev, cur, dt_override=None, fallback_dt=None):
    dx = cur["x_m"] - prev["x_m"]
    dy = cur["y_m"] - prev["y_m"]
    # BreezySLAM advances its pose by dxy along its own heading (x += dxy*cos(theta)),
    # so dxy must be signed: negative when the robot moves against its heading.
    # An unsigned hypot turned the 67 reversing steps of intel.clf into forward motion.
    heading = prev["theta_rad"]
    along = dx * math.cos(heading) + dy * math.sin(heading)
    dxy_mm = math.copysign(math.hypot(dx, dy) * 1000.0, along if along != 0 else 1.0)
    dtheta_deg = math.degrees(cur["theta_rad"] - prev["theta_rad"])
    dtheta_deg = (dtheta_deg + 180.0) % 360.0 - 180.0

    source_dt = cur["timestamp"] - prev["timestamp"]
    if dt_override is not None:
        dt = dt_override
    elif source_dt > 0:
        dt = source_dt
    else:
        dt = fallback_dt if fallback_dt is not None else 0.0

    return dxy_mm, dtheta_deg, dt


def slam_one(slam, scan, previous, args, dt_override=None, fallback_dt=None):
    ranges_mm = [
        min(int(round(r * 1000)), int(args.max_range_m * 1000)) if r > 0 else 0
        for r in scan["ranges_m"]
    ]
    pose_change = (
        (0, 0, 0)
        if previous is None
        else odom_delta(previous, scan, dt_override, fallback_dt)
    )
    slam.update(ranges_mm, pose_change=pose_change)
    return slam.getpos()

def write_csv(path, rows):
    """Write atomically (temp file + replace): an interruption never leaves a half-written CSV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    tmp = path.with_name(path.name + ".tmp")
    try:
        with tmp.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def write_json(path, obj):
    """Atomic JSON write (see write_csv)."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def timing_rates(timestamps) -> dict:
    """Frequencies implied by recorded timestamps, with what each one does and does not mean.

    median_positive_interval_rate_hz: 1 / median of the strictly positive intervals only. It is a
        typical-gap frequency, not a sustained sensor rate; zero and backward intervals are excluded.
    mean_rate_hz_over_recording: (N-1) / (max - min timestamp). Every interval counts as one scan, and
        backward steps shorten nothing (the span is max-min), so it is the average throughput over the
        whole recording including gaps and stalls.
    """
    ts = list(timestamps)
    n = len(ts)
    intervals = [b - a for a, b in zip(ts, ts[1:])]
    positive = [d for d in intervals if d > 0]
    span = (max(ts) - min(ts)) if ts else 0.0
    median_pos = statistics.median(positive) if positive else None
    return {
        "scan_count": n,
        "intervals": len(intervals),
        "positive_intervals": len(positive),
        "zero_or_backward_intervals": len(intervals) - len(positive),
        "median_positive_interval_s": median_pos,
        "median_positive_interval_rate_hz": (1.0 / median_pos) if median_pos else None,
        "recording_span_s": span,
        "mean_rate_hz_over_recording": ((n - 1) / span) if span > 0 and n > 1 else None,
        "notes": [
            "median_positive_interval_rate_hz = 1/median(positive intervals): a typical-gap frequency, NOT a "
            "sustained sensor rate. Zero and backward intervals are excluded from the median, which pushes the "
            "median interval up and the frequency down relative to using every interval.",
            "mean_rate_hz_over_recording = (scans-1)/(max-min timestamp): average throughput over the whole "
            "recording including gaps and stalls. Zero and backward intervals still count as scans here, but "
            "cannot lengthen the span (max-min).",
            "Recorded timestamps are message arrival times, not acquisition times; neither number is the "
            "sensor's configured scan rate.",
        ],
    }

def timestamp_diagnostics(scans, short_s: float = 0.02) -> dict:
    """Characterise the recorded inter-scan intervals (see DATASET_NOTES.md)."""
    dts = [b["timestamp"] - a["timestamp"] for a, b in zip(scans, scans[1:])]
    positive = [d for d in dts if d > 0]
    return {
        "intervals": len(dts),
        "backward_or_zero_transitions": sum(d <= 0 for d in dts),
        "positive_intervals_shorter_than_s": short_s,
        "positive_short_intervals": sum(0 < d < short_s for d in dts),
        "positive_short_fraction": (sum(0 < d < short_s for d in dts) / len(dts)) if dts else None,
        "median_positive_interval_s": statistics.median(positive) if positive else None,
        "note": (
            "Recorded timestamps are message-arrival times, not scan-to-scan intervals: many "
            "consecutive scans are only ~1 ms apart. As BreezySLAM dt they imply absurd speeds "
            "(see offline --dt-source)."
        ),
    }


def odometry_reverse_steps(scans, min_step_m: float = 0.02) -> dict:
    """Count steps where odometry moves against the (start-of-step) heading."""
    moving = reverse = 0
    for a, b in zip(scans, scans[1:]):
        dx, dy = b["x_m"] - a["x_m"], b["y_m"] - a["y_m"]
        if math.hypot(dx, dy) <= min_step_m:
            continue
        moving += 1
        reverse += (dx * math.cos(a["theta_rad"]) + dy * math.sin(a["theta_rad"])) < 0
    return {"moving_steps": moving, "reversing_steps": reverse, "min_step_m": min_step_m}


def positive_finite(name: str, value) -> float:
    """Shared CLI validation: a real number that is finite and > 0 (rejects 0, <0, NaN, inf, bool, None)."""
    ok = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0
    if not ok:
        raise ValueError(f"--{name.replace('_', '-')} must be finite and > 0 (got {value!r})")
    return value


def check_map_args(args):
    """Validate whichever map arguments the command defines (verify has only --map-meters)."""
    for name in ("map_meters", "map_pixels"):
        if hasattr(args, name):
            positive_finite(name, getattr(args, name))


def check_sensor_args(args):
    """--hz, --fov and --max-range-m are handed to BreezySLAM's Laser; BreezySLAM divides by
    int(hz * 360), so zero/negative/NaN values must never reach it."""
    for name in ("hz", "fov", "max_range_m"):
        positive_finite(name, getattr(args, name))


def check_run_args(args):
    """An empty benchmark is not a result: require at least one run and a non-negative warm-up."""
    if not isinstance(args.runs, int) or isinstance(args.runs, bool) or args.runs < 1:
        raise ValueError(f"--runs must be an integer >= 1 (got {args.runs!r}); zero runs produce no measurement")
    if not isinstance(args.warmup, int) or isinstance(args.warmup, bool) or args.warmup < 0:
        raise ValueError(f"--warmup must be an integer >= 0 (got {args.warmup!r})")


def validate_latencies(values, label: str) -> None:
    """Refuse to compute statistics from negative or non-finite latency samples."""
    bad = [(i, v) for i, v in enumerate(values) if not math.isfinite(v) or v < 0]
    if bad:
        raise ValueError(
            f"{label}: {len(bad)} invalid latency value(s) (negative or non-finite); first at "
            f"sample {bad[0][0]} = {bad[0][1]!r}. Refusing to compute statistics from invalid data."
        )


def map_config(args) -> dict:
    return {
        "map_meters": args.map_meters,
        "map_pixels": args.map_pixels,
        "resolution_m_per_pixel": args.map_meters / args.map_pixels,
        "map_cells": int(args.map_pixels) ** 2,
    }


def command_verify(args):
    check_map_args(args)
    out_dir = Path(args.out_dir)
    ensure_writable([out_dir / "dataset_summary.json"], args.overwrite)
    scans = load_scans(Path(args.input))
    intervals = [
        b["timestamp"] - a["timestamp"]
        for a, b in zip(scans, scans[1:])
    ]
    positive_intervals = [dt for dt in intervals if dt > 0]
    non_increasing = sum(dt <= 0 for dt in intervals)

    if not positive_intervals:
        raise ValueError("Dataset has no positive timestamp intervals")

    ranges = [r for scan in scans for r in scan["ranges_m"] if r > 0]
    timestamps = [scan["timestamp"] for scan in scans]

    summary = {
        "input": str(Path(args.input).resolve()),
        "scan_count": len(scans),
        "range_count_per_scan": len(scans[0]["ranges_m"]),
        "first_timestamp": scans[0]["timestamp"],
        "last_timestamp": scans[-1]["timestamp"],
        "duration_seconds": max(timestamps) - min(timestamps),
        "timing_rates": timing_rates(timestamps),
        "timestamp_interval_seconds_positive_only": stats(positive_intervals),
        "non_increasing_timestamp_transitions": non_increasing,
        "valid_range_count": len(ranges),
        "range_m": {
            "min": min(ranges),
            "median": statistics.median(ranges),
            "max": max(ranges),
        } if ranges else None,
        "odometry_fields_present": True,
        "odometry_is_ground_truth": False,
        "odometry_extent": odometry_extent(scans, args.map_meters),
        "timestamp_diagnostics": timestamp_diagnostics(scans),
        "odometry_reverse_steps": odometry_reverse_steps(scans),
        "system": system_metadata(),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "dataset_summary.json").write_text(json.dumps(summary, indent=2))
    if non_increasing:
        print(
            f"WARNING: {non_increasing} non-increasing timestamp transitions. "
            "Statistics use positive intervals only; original scan order is preserved.",
            file=sys.stderr,
        )
    print(json.dumps(summary, indent=2))

def validity_banner(validity: dict) -> str:
    if validity["valid_for_performance_claims"]:
        return "pose stayed inside the map"
    return (
        f"INVALID: pose left the {validity['map_meters']:g} m map at scan "
        f"{validity['first_invalid_scan_index']} "
        f"({validity['invalid_scans']}/{validity['scans_evaluated']} scans, "
        f"{100 * validity['invalid_fraction']:.1f}%) - not valid for mapping or performance claims"
    )


def warn_if_invalid(label: str, validity: dict):
    if not validity["valid_for_performance_claims"]:
        print(f"WARNING [{label}]: {validity_banner(validity)}", file=sys.stderr)


def command_offline(args):
    check_map_args(args)
    check_sensor_args(args)
    check_run_args(args)
    out_dir = Path(args.out_dir)
    paths = output_paths(out_dir, "offline")
    ensure_writable([paths["csv"], paths["json"], paths["map"], paths["trajectory"]], args.overwrite)
    scans = load_scans(Path(args.input))
    if args.warmup >= len(scans):
        raise ValueError(f"--warmup ({args.warmup}) must be smaller than the scan count ({len(scans)}): no scan would be timed")

    intervals = [
        b["timestamp"] - a["timestamp"]
        for a, b in zip(scans, scans[1:])
    ]
    positive_intervals = [dt for dt in intervals if dt > 0]
    if not positive_intervals:
        raise ValueError("Dataset has no positive timestamp intervals")
    fallback_dt = statistics.median(positive_intervals)
    # Recorded intervals are arrival times (see timestamp_diagnostics): used as dt they make
    # BreezySLAM's velocity-based scan compensation absurd. Default: one constant nominal dt.
    dt_source = getattr(args, "dt_source", "nominal")
    dt_override = fallback_dt if dt_source == "nominal" else None

    allrows, run_summaries = [], []
    last_complete = None
    interrupted = False
    current_run = 0
    try:
        with sigterm_as_keyboard_interrupt():
            for run in range(1, args.runs + 1):
                current_run = run
                slam = make_slam(len(scans[0]["ranges_m"]), args.hz, args)
                lat_ms, poses, run_rows = [], [], []
                run_started_ns = time.perf_counter_ns()

                # Warm-up scans affect algorithm state but are excluded from latency stats.
                for i, scan in enumerate(scans):
                    prev = scans[i - 1] if i else None
                    t0 = time.perf_counter_ns()
                    pose = slam_one(
                        slam, scan, prev, args, dt_override=dt_override, fallback_dt=fallback_dt
                    )
                    elapsed = (time.perf_counter_ns() - t0) / 1e6

                    if i >= args.warmup:
                        lat_ms.append(elapsed)
                        run_rows.append({
                            "run": run,
                            "scan_index": i,
                            "processing_ms": elapsed,
                            "pose_x_mm": pose[0],
                            "pose_y_mm": pose[1],
                            "pose_theta_deg": pose[2],
                        })
                    poses.append(pose)

                wall_seconds = (time.perf_counter_ns() - run_started_ns) / 1e9

                # Validity is evaluated after the timed loop and covers ALL scans, warm-up included.
                flags = [pose_in_map(p[0], p[1], args.map_meters) for p in poses]
                validity = validity_summary(flags, range(len(poses)), args.map_meters)
                for r in run_rows:
                    r["pose_in_map"] = flags[r["scan_index"]]
                warn_if_invalid(f"offline run {run}", validity)
                run_summary = {
                    "run": run,
                    "scans_total": len(scans),
                    "timed_scans": len(lat_ms),
                    "total_wall_seconds": wall_seconds,
                    "sum_timed_processing_seconds": sum(lat_ms) / 1000.0,
                    "latency_ms": stats(lat_ms),
                    "pose_validity": validity,
                }
                # Only fully completed runs are recorded (rows first, then the summary).
                allrows.extend(run_rows)
                run_summaries.append(run_summary)
                last_complete = (slam, poses, validity, run)
    except KeyboardInterrupt:
        interrupted = True

    # An interrupted run contributes nothing; make rows and summaries agree exactly.
    done = {s["run"] for s in run_summaries}
    allrows = [r for r in allrows if r["run"] in done]
    interrupted_during_run = current_run if interrupted and current_run not in done else None
    if interrupted and not run_summaries:
        print(f"INTERRUPTED during run {current_run}: no run completed, so nothing was written.", file=sys.stderr)
        return 130

    out_dir.mkdir(parents=True, exist_ok=True)  # created only once there is something to write
    write_csv(paths["csv"], allrows)
    summary = {
        "mode": "offline",
        "run_status": "interrupted" if interrupted else "complete",
        "runs_requested": args.runs,
        "runs_completed": len(run_summaries),
        "interrupted_during_run": interrupted_during_run,
        "input": str(Path(args.input).resolve()),
        "map": map_config(args),
        "dt_policy": {
            "dt_source": dt_source,
            "dt_seconds": dt_override if dt_override is not None else "per-scan recorded (legacy)",
        },
        "all_runs_valid_for_performance_claims": (not interrupted) and bool(run_summaries) and all(
            r["pose_validity"]["valid_for_performance_claims"] for r in run_summaries
        ),
        "figures": {"written": None, "reason": "pending"},
        "runs": run_summaries,
        "system": system_metadata(),
        "note": (
            "Wall time covers the scan loop including warm-up; per-scan latency "
            "excludes warm-up. Dataset parsing and SLAM construction are excluded. "
            "dt passed to BreezySLAM follows dt_policy: 'nominal' (default) is the median positive "
            "recorded interval for every scan; 'recorded' is the legacy per-scan arrival-time delta "
            "(nonpositive deltas use the median) and distorts scans. "
            "Cross-run aggregates: use the `summary` command. "
            "A run whose pose leaves the map is not valid for mapping or performance claims."
        ),
    }
    if interrupted:
        summary["note"] += (
            f" INCOMPLETE: interrupted after {len(run_summaries)} of {args.runs} run(s)"
            + (f" while run {interrupted_during_run} was in progress; that run's scans were discarded, "
               "not estimated" if interrupted_during_run else "")
            + ". Only completed runs are recorded. Not valid for performance claims."
        )
        print(f"WARNING: INTERRUPTED - {len(run_summaries)}/{args.runs} run(s) completed and saved; "
              "this result is incomplete and not valid for performance claims.", file=sys.stderr)
    write_json(paths["json"], summary)  # data first; figures are rendered last and can never cost results
    if interrupted or last_complete is None:
        summary["figures"] = {"written": False, "reason": "not produced: run interrupted"}
    else:
        slam, poses, validity, run = last_complete
        summary["figures"] = save_map_and_trajectory(
            slam, poses, args, out_dir, "offline",
            f"run {run}/{args.runs}, scans 0-{len(poses) - 1} processed "
            f"(timed from scan {args.warmup})", validity,
        )
    write_json(paths["json"], summary)
    print(json.dumps(summary, indent=2))
    return 130 if interrupted else 0

def save_map_and_trajectory(slam, poses, args, out_dir, mode, scan_desc, validity, incomplete=None):
    """Render the map and trajectory. Never raises: returns {"written": bool, "reason": str|None}
    so a plotting failure cannot cost the measurements (the failure is reported, not hidden)."""
    paths = output_paths(out_dir, mode)
    banner = validity_banner(validity)
    if incomplete:
        banner = f"INCOMPLETE RUN ({incomplete}); {banner}"
    color = "black" if validity["valid_for_performance_claims"] and not incomplete else "red"
    written = []
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        raw = bytearray(args.map_pixels * args.map_pixels)
        slam.getmap(raw)
        arr = np.frombuffer(raw,dtype=np.uint8).reshape((args.map_pixels,args.map_pixels))
        Path(out_dir).mkdir(parents=True,exist_ok=True)
        plt.figure(figsize=(8,8)); plt.imshow(arr,cmap="gray",origin="upper")
        plt.title(f"BreezySLAM map - {mode}, {scan_desc}\n{banner}", fontsize=9, color=color)
        plt.tight_layout(); plt.savefig(paths["map"],dpi=150); plt.close(); written.append(paths["map"].name)
        plt.figure(figsize=(8,6))
        plt.plot([p[0]/1000 for p in poses],[p[1]/1000 for p in poses],label="BreezySLAM pose")
        m = args.map_meters
        plt.plot([0, m, m, 0, 0], [0, 0, m, m, 0], "r--", linewidth=1, label=f"map bounds ({m:g} m)")
        plt.title(f"BreezySLAM trajectory - {mode}, {scan_desc}\n{banner}", fontsize=9, color=color)
        plt.xlabel("x (m)"); plt.ylabel("y (m)"); plt.axis("equal"); plt.legend(); plt.tight_layout()
        plt.savefig(paths["trajectory"],dpi=150); plt.close(); written.append(paths["trajectory"].name)
        return {"written": True, "reason": None, "files": written}
    except ImportError as exc:
        reason = f"matplotlib/numpy not available ({exc})"
    except Exception as exc:  # rendering/IO failure: report, keep the measurements
        reason = f"{type(exc).__name__}: {exc}"
    print(f"WARNING: figures not written: {reason}. Measurements (CSV/JSON) are unaffected.", file=sys.stderr)
    return {"written": False, "reason": reason, "files": written}

def command_paced(args):
    check_map_args(args)
    check_sensor_args(args)
    positive_finite("minutes", args.minutes)
    out_dir = Path(args.out_dir)
    paths = output_paths(out_dir, "paced")
    ensure_writable([paths["csv"], paths["json"], paths["map"], paths["trajectory"]], args.overwrite)
    scans = load_scans(Path(args.input))
    hz = args.hz
    period_ns = int(period_seconds(hz) * 1e9)
    target_ns = int(args.minutes * 60 * 1e9)
    slam = make_slam(len(scans[0]["ranges_m"]), hz, args)

    rows = []
    index = 0
    started = time.monotonic_ns()
    deadline = started
    previous = None
    over = missed = 0
    interrupted = False

    try:
        with sigterm_as_keyboard_interrupt():
            while time.monotonic_ns() - started < target_ns:
                source_index = index % len(scans)
                scan = scans[source_index]
                loop = index // len(scans)

                scheduled = deadline
                now = time.monotonic_ns()
                if now < scheduled:
                    time.sleep((scheduled - now) / 1e9)

                actual_start = time.monotonic_ns()
                # Do not carry an odometry delta across the end/start of a recording loop.
                previous_for_update = (
                    None if index > 0 and source_index == 0 else previous
                )
                pose = slam_one(
                    slam, scan, previous_for_update, args,
                    dt_override=period_ns / 1e9,
                )
                finish = time.monotonic_ns()

                timing = classify_timing(scheduled, actual_start, finish, period_ns)
                over += int(timing["processing_budget_exceeded"])
                missed += int(timing["deadline_missed"])
                rows.append({
                    "index": index,
                    "source_scan_index": source_index,
                    "recording_loop": loop,
                    "scheduled_ns": scheduled,
                    "start_ns": actual_start,
                    "finish_ns": finish,
                    **timing,
                    "pose_x_mm": pose[0],
                    "pose_y_mm": pose[1],
                    "pose_theta_deg": pose[2],
                })

                previous = scan
                index += 1
                deadline = scheduled + period_ns
    except KeyboardInterrupt:
        interrupted = True

    if not rows:
        if interrupted:
            print("INTERRUPTED before any scan was processed: nothing was written.", file=sys.stderr)
            return 130
        raise ValueError("paced run processed no scans (--minutes too small?)")

    elapsed_s = (rows[-1]["finish_ns"] - started) / 1e9

    # Validity is evaluated after the timed loop.
    flags = [pose_in_map(r["pose_x_mm"], r["pose_y_mm"], args.map_meters) for r in rows]
    validity = validity_summary(flags, [r["index"] for r in rows], args.map_meters)
    for r, f in zip(rows, flags):
        r["pose_in_map"] = f
    warn_if_invalid("paced", validity)

    out_dir.mkdir(parents=True, exist_ok=True)  # created only once there is something to write
    write_csv(paths["csv"], rows)
    durations = [r["processing_duration_ns"] / 1e6 for r in rows]
    lateness = [r["finish_lateness_ns"] / 1e6 for r in rows]
    source_span = (
        f"source scans {min(r['source_scan_index'] for r in rows)}-"
        f"{max(r['source_scan_index'] for r in rows)}, "
        f"{rows[-1]['recording_loop'] + 1} recording loop(s)"
    )
    incomplete = None
    if interrupted:
        incomplete = {
            "reason": "interrupted (Ctrl-C or termination signal)",
            "requested_minutes": args.minutes,
            "elapsed_minutes_at_last_scan": elapsed_s / 60.0,
            "scans_processed": len(rows),
            "note": ("Statistics below cover only the scans actually processed; nothing is estimated for the "
                     "rest. The saved map may include at most one scan that is not in the CSV (an update that "
                     "finished just as the interrupt arrived)."),
        }
        print(f"WARNING: INTERRUPTED after {len(rows)} scans ({elapsed_s / 60.0:.2f} of {args.minutes:g} min); "
              "partial results saved and marked incomplete, not valid for performance claims.", file=sys.stderr)
    summary = {
        "mode": "paced",
        "run_status": "interrupted" if interrupted else "complete",
        "map": map_config(args),
        "valid_for_performance_claims": (not interrupted) and validity["valid_for_performance_claims"],
        "incomplete": incomplete,
        "pose_validity": validity,
        "target_hz": hz,
        "period_ms": period_ns / 1e6,
        "requested_minutes": args.minutes,
        "elapsed_seconds_processed": elapsed_s,
        "scans_processed": len(rows),
        "source_scan_span": source_span,
        "processing_budget_exceedances": over,
        "scheduled_deadline_misses": missed,
        "processing_latency_ms": stats(durations),
        "finish_lateness_ms": stats(lateness),
        "figures": {"written": None, "reason": "pending"},
        "system": system_metadata(),
        "note": (
            "Single-threaded replay has no sensor queue; backlog/queue growth "
            "is not measured. Odometry dt uses the configured replay period, "
            "and odometry deltas reset at recording-loop boundaries. "
            "If pose_validity shows the pose left the map, the run is not valid "
            "for mapping or performance claims."
        ),
    }
    write_json(paths["json"], summary)  # data first; figures are rendered last and can never cost results
    summary["figures"] = save_map_and_trajectory(
        slam,
        [(r["pose_x_mm"], r["pose_y_mm"], r["pose_theta_deg"]) for r in rows],
        args, out_dir, "paced",
        f"processed scans 0-{len(rows) - 1} ({source_span})", validity,
        incomplete=(f"interrupted after {len(rows)} scans" if interrupted else None),
    )
    write_json(paths["json"], summary)
    print(json.dumps(summary, indent=2))
    return 130 if interrupted else 0

def command_summary(args):
    out_dir = Path(args.out_dir)
    paths = output_paths(out_dir, args.mode)
    if args.map_meters is not None:
        positive_finite("map_meters", args.map_meters)
    source = Path(args.csv) if args.csv else paths["csv"]
    rows = load_csv_rows(source)
    summarize = summarize_offline_csv if args.mode == "offline" else summarize_paced_csv
    summary = summarize(rows, args.map_meters)
    summary["provenance"] = load_provenance(source, args.mode, rows)
    if args.output:
        ensure_writable([args.output], args.overwrite)
        Path(args.output).write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2) if args.json else format_summary(summary))

def command_plot(args):
    out_dir = Path(args.out_dir)
    paths = output_paths(out_dir, args.mode)
    source = Path(args.csv) if args.csv else paths["csv"]
    rows = load_csv_rows(source)
    key = "processing_ms" if args.mode == "offline" else "processing_duration_ns"
    if key not in rows[0]:
        raise ValueError(f"{source} is not a {args.mode} CSV (missing column {key!r}); refusing to plot")
    ensure_writable([paths["latency_distribution"], paths["latency_over_time"]], args.overwrite)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise EnvironmentProblem("Install matplotlib to generate plots") from exc
    scale = 1.0 if args.mode == "offline" else 1e6
    xkey = "scan_index" if args.mode == "offline" else "index"
    series = {}
    for r in rows:
        series.setdefault(int(r["run"]) if args.mode == "offline" else 1, []).append(
            (int(r[xkey]), float(r[key]) / scale))
    vals = [v for s in series.values() for _, v in s]
    if "pose_in_map" in rows[0]:
        bad = sum(not _to_bool(r["pose_in_map"]) for r in rows)
        note = ("pose stayed inside the map" if bad == 0 else
                f"INVALID: pose outside map for {bad}/{len(rows)} plotted scans - not valid for performance claims")
    else:
        note = "pose validity not recorded in this CSV (legacy file); check with `summary --map-meters`"
    xs = [x for s in series.values() for x, _ in s]
    desc = (f"{args.mode}, {len(series)} run(s), {len(rows)} scans from {source.name} "
            f"(scan index {min(xs)}-{max(xs)})")
    color = "red" if note.startswith("INVALID") else "black"
    plt.figure(); plt.hist(vals,bins=50); plt.xlabel("Processing latency (ms)"); plt.ylabel("Count")
    plt.title(f"Latency distribution (pooled) - {desc}\n{note}", fontsize=8, color=color)
    plt.tight_layout(); plt.savefig(paths["latency_distribution"],dpi=150); plt.close()
    plt.figure()
    for run, s in sorted(series.items()):
        plt.plot([x for x, _ in s],[v for _, v in s],linewidth=.7,label=f"run {run}" if args.mode == "offline" else None)
    if args.mode == "offline": plt.legend(fontsize=7)
    plt.xlabel("Scan index"); plt.ylabel("Processing latency (ms)")
    plt.title(f"Latency over time - {desc}\n{note}", fontsize=8, color=color)
    plt.tight_layout(); plt.savefig(paths["latency_over_time"],dpi=150); plt.close()
    print(f"{args.mode} plots written under {out_dir}")

def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest="command",required=True)
    def outputs(q):
        q.add_argument("--out-dir",default=str(OUT),help="output directory (default: results/lidar-pi-slam-benchmark)")
        q.add_argument("--overwrite",action="store_true",help="allow overwriting existing result files (default: refuse)")
        q.add_argument("--debug",action="store_true",help="print full tracebacks (also enabled by AUTONAV_DEBUG=1)")
    def map_args(q):
        q.add_argument("--map-pixels",type=int,default=DEFAULT_MAP_PIXELS); q.add_argument("--map-meters",type=float,default=DEFAULT_MAP_METERS)
    def common(q):
        q.add_argument("--input",required=True); q.add_argument("--hz",type=float,default=6.0)
        q.add_argument("--fov",type=float,default=180.0); q.add_argument("--max-range-m",type=float,default=12.0)
        map_args(q); q.add_argument("--seed",type=int,default=42); outputs(q)
    v=sub.add_parser("verify"); v.add_argument("--input",required=True); v.add_argument("--map-meters",type=float,default=DEFAULT_MAP_METERS); outputs(v); v.set_defaults(func=command_verify)
    o=sub.add_parser("offline"); common(o); o.add_argument("--runs",type=int,default=5); o.add_argument("--warmup",type=int,default=20); o.add_argument("--dt-source",choices=("nominal","recorded"),default="nominal",help="dt given to BreezySLAM: constant median recorded interval (default) or legacy per-scan recorded delta"); o.set_defaults(func=command_offline)
    paced=sub.add_parser("paced"); common(paced); paced.add_argument("--minutes",type=float,default=10); paced.set_defaults(func=command_paced)
    s=sub.add_parser("summary",help="per-run, median-across-runs and pooled statistics from a raw CSV (read-only unless --output)")
    s.add_argument("--mode",required=True,choices=("offline","paced")); s.add_argument("--csv",help="CSV to read (default: the mode's CSV in --out-dir)")
    s.add_argument("--map-meters",type=float,default=None,help="evaluate pose-in-map from the CSV poses for this map size (use the size the run used; legacy runs used 35)")
    s.add_argument("--json",action="store_true"); s.add_argument("--output",help="also write the summary JSON here"); outputs(s); s.set_defaults(func=command_summary)
    pl=sub.add_parser("plot"); pl.add_argument("--mode",required=True,choices=("offline","paced")); pl.add_argument("--csv",help="CSV to read (default: the mode's CSV in --out-dir)"); outputs(pl); pl.set_defaults(func=command_plot)
    args=p.parse_args()
    debug = bool(getattr(args, "debug", False)) or os.environ.get("AUTONAV_DEBUG", "") not in ("", "0")
    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt:
        print("INTERRUPTED: stopped before any result could be written.", file=sys.stderr)
        return EXIT_INTERRUPTED
    except USER_ERRORS as exc:
        # Invalid arguments, bad/missing files, missing dependencies: one actionable line.
        print(f"ERROR: {exc}", file=sys.stderr)
        if debug:
            traceback.print_exc()
        return EXIT_USER_ERROR
    except Exception as exc:
        # Anything else is a bug in the benchmark: never disguise it as a usage error or a success.
        last = traceback.extract_tb(exc.__traceback__)[-1]
        print(f"INTERNAL ERROR ({type(exc).__name__}): {exc}\n  at {last.filename}:{last.lineno} in {last.name}\n"
              "  This is a bug, not a usage error. Re-run with --debug (or AUTONAV_DEBUG=1) for the full traceback.",
              file=sys.stderr)
        if debug:
            traceback.print_exc()
        return EXIT_INTERNAL_ERROR
if __name__=="__main__": raise SystemExit(main())
