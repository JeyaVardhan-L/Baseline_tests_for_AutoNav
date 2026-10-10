"""Tiny helper for publishing benchmark telemetry to live_viewer.py."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
from urllib.request import Request, urlopen

def publish_state(state: dict, url: str = "http://127.0.0.1:8765/api/update", timeout: float = 0.15) -> bool:
    """POST one JSON snapshot; never let viewer/network failure stop SLAM."""
    payload = dict(state)
    payload.setdefault("updated_at", time.strftime("%H:%M:%S"))
    try:
        req = Request(url, data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=timeout) as response:
            return 200 <= response.status < 300
    except Exception:
        return False

MAP_ERROR_FILE = "live_map.error.txt"
LAST_MAP_ERROR = None  # reason of the most recent failed save_live_map(), None after a success


def _report_map_failure(output_dir: Path, reason: str) -> None:
    """Make a failed map refresh diagnosable and impossible to mistake for a current map.

    A warning goes to stderr when the reason changes (not on every retry), and a marker file is
    written next to live_map.png; live_viewer.py then refuses to show any earlier map because it
    would no longer be current.
    """
    global LAST_MAP_ERROR
    if reason != LAST_MAP_ERROR:
        print(f"WARNING: live map not updated: {reason}", file=sys.stderr)
    LAST_MAP_ERROR = reason
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        tmp = output_dir / (MAP_ERROR_FILE + ".tmp")
        tmp.write_text(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n{reason}\n", encoding="utf-8")
        tmp.replace(output_dir / MAP_ERROR_FILE)
    except OSError:
        pass  # cannot even write the marker (e.g. disk full): the stderr warning above remains


def _clear_map_failure(output_dir: Path) -> None:
    global LAST_MAP_ERROR
    LAST_MAP_ERROR = None
    try:
        (output_dir / MAP_ERROR_FILE).unlink()  # only the marker this module wrote
    except OSError:
        pass


def save_live_map(slam, output_dir: Path, map_pixels: int) -> bool:
    """Export BreezySLAM's current map to live_map.png; requires numpy and matplotlib.

    Returns True on success. Expected failures (optional dependency missing, rendering or I/O
    errors) never stop the benchmark, but they are no longer silent: the reason is printed to
    stderr, kept in LAST_MAP_ERROR and written to live_map.error.txt, and a failed refresh
    leaves live_map.png untouched (the viewer hides it while the marker is newer).
    """
    output_dir = Path(output_dir)
    temp = output_dir / "live_map.tmp.png"
    fig = plt = None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        output_dir.mkdir(parents=True, exist_ok=True)
        raw = bytearray(map_pixels * map_pixels)
        slam.getmap(raw)
        image = np.frombuffer(raw, dtype=np.uint8).reshape((map_pixels, map_pixels))
        final = output_dir / "live_map.png"
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.imshow(image, cmap="gray", origin="upper")
        ax.set_axis_off()
        fig.tight_layout(pad=0)
        fig.savefig(temp, dpi=100)
        temp.replace(final)
    except ImportError as exc:
        _report_map_failure(output_dir, f"matplotlib/numpy not available ({exc})")
        return False
    except Exception as exc:  # rendering / I/O / SLAM getmap failure
        _report_map_failure(output_dir, f"{type(exc).__name__}: {exc}")
        return False
    finally:
        if fig is not None and plt is not None:
            plt.close(fig)
        try:
            temp.unlink()  # our own temporary file, if a failure left it behind
        except OSError:
            pass
    _clear_map_failure(output_dir)
    return True
