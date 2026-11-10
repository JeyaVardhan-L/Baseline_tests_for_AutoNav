#!/usr/bin/env python3
"""
Fetch ONE window of Oxford Spires raw LiDAR clouds plus ground truth, without downloading the full
sequence archive (the zip is read remotely with HTTP range requests).

Requires the optional [data] extra (`pip install huggingface_hub`). Data is CC BY-NC-SA 4.0
(https://huggingface.co/datasets/ori-drs/oxford_spires_dataset): keep it out of git, attribute it,
no commercial use.

The window is chosen by a documented rule: the `--frames` consecutive clouds (no gap > 0.15 s) with the
largest ground-truth path length. Ground truth is the pose of the BASE frame in the world frame
(not the LiDAR frame).

Usage:
    python tools/fetch_spires.py [--sequence 2024-03-13-observatory-quarter-01] [--frames 300] [--out datasets/oxford-spires/window]
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np

REPO = "datasets/ori-drs/oxford_spires_dataset"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sequence", default="2024-03-13-observatory-quarter-01")
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--out", type=Path, default=Path("datasets/oxford-spires/window"))
    a = ap.parse_args()

    from huggingface_hub import HfFileSystem
    fs = HfFileSystem()
    base = f"{REPO}/sequences/{a.sequence}"
    gt_lines = fs.open(f"{base}/processed/trajectory/gt-tum.txt", "rb").read().decode().splitlines()
    gt = np.array([[float(x) for x in l.split()] for l in gt_lines if l.strip() and not l.startswith("#")])
    if np.any(np.diff(gt[:, 0]) <= 0):
        keep = np.concatenate([[True], np.diff(gt[:, 0]) > 0])
        gt = gt[keep]

    with fs.open(f"{base}/raw/lidar-clouds.zip", "rb") as f:
        z = zipfile.ZipFile(f)
        members = [i for i in z.infolist() if not i.is_dir() and i.filename.endswith(".pcd")]
        members.sort(key=lambda i: float(Path(i.filename).name[:-4]))
        ts = np.array([float(Path(i.filename).name[:-4]) for i in members])
        dt = np.diff(ts)
        # candidate windows: consecutive clouds only; score = GT path length inside the window
        best, best_len = None, -1.0
        n = a.frames
        for s in range(0, len(ts) - n + 1, 5):
            if dt[s:s + n - 1].max() > 0.15:
                continue
            sel = (gt[:, 0] >= ts[s]) & (gt[:, 0] <= ts[s + n - 1])
            if sel.sum() < 3:
                continue
            length = float(np.linalg.norm(np.diff(gt[sel, 1:4], axis=0), axis=1).sum())
            if length > best_len:
                best, best_len = s, length
        if best is None:
            raise SystemExit("no consecutive window found")
        s = best
        out_l = a.out / "lidar"
        out_l.mkdir(parents=True, exist_ok=True)
        for info in members[s:s + n]:
            (out_l / Path(info.filename).name).write_bytes(z.read(info))

    t0, t1 = ts[s], ts[s + n - 1]
    sel = (gt[:, 0] >= t0 - 1.0) & (gt[:, 0] <= t1 + 1.0)
    with open(a.out / "gt.csv", "w", encoding="utf-8") as f:
        f.write("#t,x,y,z,qx,qy,qz,qw\n")
        for row in gt[sel]:
            f.write(",".join(repr(float(v)) for v in row) + "\n")
    manifest = {
        "dataset": "Oxford Spires", "sequence": a.sequence, "source": "huggingface.co/datasets/ori-drs/oxford_spires_dataset",
        "licence": "CC BY-NC-SA 4.0", "sensor": "Hesai QT64 (64 ch, 10 Hz, ~104 deg FOV, 60 m) - differs from OS1-64",
        "window_rule": "consecutive clouds (gap <= 0.15 s) with the largest ground-truth path length",
        "first_cloud_index": int(s), "n_frames": int(n), "t_start": float(t0), "t_end": float(t1),
        "gt_file": "processed/trajectory/gt-tum.txt (pose of the base frame in the world frame)",
        "gt_path_length_m_in_window": best_len,
    }
    (a.out / "window.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())