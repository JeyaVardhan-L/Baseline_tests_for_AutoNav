"""Tiny helper for publishing benchmark telemetry to live_viewer.py."""
from __future__ import annotations
import json, time
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

def save_live_map(slam, output_dir: Path, map_pixels: int) -> bool:
    """Export BreezySLAM's current map to live_map.png; requires existing numpy/matplotlib."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        output_dir.mkdir(parents=True, exist_ok=True)
        raw = bytearray(map_pixels * map_pixels)
        slam.getmap(raw)
        image = np.frombuffer(raw, dtype=np.uint8).reshape((map_pixels, map_pixels))
        temp = output_dir / "live_map.tmp.png"
        final = output_dir / "live_map.png"
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.imshow(image, cmap="gray", origin="upper")
        ax.set_axis_off()
        fig.tight_layout(pad=0)
        fig.savefig(temp, dpi=100)
        plt.close(fig)
        temp.replace(final)
        return True
    except Exception:
        return False
