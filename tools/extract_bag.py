#!/usr/bin/env python3
"""
Extract Ouster point clouds from a ROS1 bag into PCD files (no ROS installation needed).

Requires the optional [data] extra (`pip install rosbags`). The core pipeline never imports it.

Output files are named cloud_<sec>_<nsec>.pcd from each message's header stamp (the same naming the
Newer College raw PCD release uses), written as packed little-endian binary PCD with the fields
that exist in the message (x y z intensity t reflectivity ring noise range).

Usage:
    python tools/extract_bag.py --bag <file.bag> --out <dir> [--topic /os1_cloud_node/points] [--max-frames N]
"""

import argparse
import sys
from pathlib import Path

import numpy as np

# ROS PointField datatype -> (numpy dtype, PCD TYPE letter)
_ROS_TYPES = {
    1: ("i1", "I"), 2: ("u1", "U"), 3: ("<i2", "I"), 4: ("<u2", "U"),
    5: ("<i4", "I"), 6: ("<u4", "U"), 7: ("<f4", "F"), 8: ("<f8", "F"),
}
_WANTED = ["x", "y", "z", "intensity", "t", "reflectivity", "ring", "noise", "range"]


def _build_dtypes(fields, point_step):
    names, formats, offsets = [], [], []
    for f in fields:
        if f.name in _WANTED and f.datatype in _ROS_TYPES:
            names.append(f.name)
            formats.append(_ROS_TYPES[f.datatype][0])
            offsets.append(int(f.offset))
    if not {"x", "y", "z"} <= set(names):
        raise ValueError(f"PointCloud2 lacks x/y/z fields: {[f.name for f in fields]}")
    src = np.dtype({"names": names, "formats": formats, "offsets": offsets, "itemsize": int(point_step)})
    order = [n for n in _WANTED if n in names]
    packed = np.dtype([(n, src.fields[n][0]) for n in order])
    return src, packed, order


def _pcd_header(order, packed, width, height):
    sizes = [packed.fields[n][0].itemsize for n in order]
    types = []
    for n in order:
        code = packed.fields[n][0].kind
        types.append({"f": "F", "u": "U", "i": "I"}[code])
    n_points = width * height
    lines = [
        "# .PCD v0.7 - Point Cloud Data file format", "VERSION 0.7",
        "FIELDS " + " ".join(order), "SIZE " + " ".join(map(str, sizes)),
        "TYPE " + " ".join(types), "COUNT " + " ".join("1" for _ in order),
        f"WIDTH {width}", f"HEIGHT {height}", "VIEWPOINT 0 0 0 1 0 0 0",
        f"POINTS {n_points}", "DATA binary",
    ]
    return ("\n".join(lines) + "\n").encode("ascii")


def extract(bag: Path, out_dir: Path, topic: str, max_frames: int | None) -> int:
    from rosbags.rosbag1 import Reader          # optional [data] extra
    from rosbags.typesys import Stores, get_typestore

    typestore = get_typestore(Stores.ROS1_NOETIC)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    with Reader(bag) as reader:
        conns = [c for c in reader.connections if c.topic == topic]
        if not conns:
            raise SystemExit(f"Topic {topic} not found. Available: {sorted({c.topic for c in reader.connections})}")
        for conn, _t, raw in reader.messages(connections=conns):
            msg = typestore.deserialize_ros1(raw, conn.msgtype)
            src, packed, order = _build_dtypes(msg.fields, msg.point_step)
            n = int(msg.width) * int(msg.height)
            buf = np.asarray(msg.data, dtype=np.uint8)[: n * int(msg.point_step)]
            arr = np.frombuffer(buf, dtype=src, count=n)
            rec = np.empty(n, dtype=packed)
            for name in order:
                rec[name] = arr[name]
            stamp = msg.header.stamp
            name = f"cloud_{int(stamp.sec)}_{int(stamp.nanosec)}.pcd"
            (out_dir / name).write_bytes(_pcd_header(order, packed, int(msg.width), int(msg.height)) + rec.tobytes())
            written += 1
            if max_frames and written >= max_frames:
                break
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract Ouster PointCloud2 messages from a ROS1 bag to PCD files.")
    ap.add_argument("--bag", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--topic", default="/os1_cloud_node/points")
    ap.add_argument("--max-frames", type=int, default=None)
    args = ap.parse_args()
    n = extract(args.bag, args.out, args.topic, args.max_frames)
    print(f"wrote {n} PCD files")
    return 0


if __name__ == "__main__":
    sys.exit(main())