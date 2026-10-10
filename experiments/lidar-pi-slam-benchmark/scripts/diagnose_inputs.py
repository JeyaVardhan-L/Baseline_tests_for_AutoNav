#!/usr/bin/env python3
"""Read-only diagnostics of the BreezySLAM benchmark inputs and of a finished run.

Does NOT use BreezySLAM and writes no files. Requires numpy and scipy.

  inputs   scan-angle ordering test, odometry sign/dead-reckoning check, timestamp
           statistics and the within-scan velocity compensation implied by them.
  compare  compare a run's recorded poses with an independent scan-only ICP chain.

The ICP chain is an odometry-seeded point-to-point ICP over consecutive scans. It is NOT
ground truth and it drifts; it only shows whether a SLAM pose track is consistent with the
scans themselves, independent of the (drifting) wheel odometry and of BreezySLAM.
"""
from __future__ import annotations
import argparse, csv, importlib.util, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("benchmark", HERE / "benchmark.py")
benchmark = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(benchmark)


def _np():
    try:
        import numpy as np
        from scipy.spatial import cKDTree
    except ImportError as exc:
        raise RuntimeError("diagnose_inputs.py needs numpy and scipy") from exc
    return np, cKDTree


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def scan_points(ranges, reverse=False, max_range=12.0, min_range=0.3):
    """Local XY points using BreezySLAM's convention: index k at -FOV/2 + k*FOV/(n-1), CCW."""
    np, _ = _np()
    r = np.asarray(ranges, float)
    ang = np.radians(-90.0 + np.arange(len(r)) * 180.0 / (len(r) - 1))
    if reverse:
        ang = -ang
    m = (r > min_range) & (r < max_range)
    return np.c_[r[m] * np.cos(ang[m]), r[m] * np.sin(ang[m])]


def icp(cur, prev, init, iters=30, max_dist=0.5):
    """Pose (x, y, theta) of `cur` in the frame of `prev` (point-to-point ICP)."""
    np, cKDTree = _np()
    x, y, th = init
    tree = cKDTree(prev)
    for _ in range(iters):
        c, s = math.cos(th), math.sin(th)
        moved = cur @ np.array([[c, s], [-s, c]]) + [x, y]
        d, j = tree.query(moved)
        k = d < max_dist
        if k.sum() < 20:
            break
        a, b = moved[k], prev[j[k]]
        am, bm = a.mean(0), b.mean(0)
        u, _, vt = np.linalg.svd((a - am).T @ (b - bm))
        rot = vt.T @ u.T
        if np.linalg.det(rot) < 0:
            vt[-1] *= -1
            rot = vt.T @ u.T
        t = bm - rot @ am
        dth = math.atan2(rot[1, 0], rot[0, 0])
        c2, s2 = math.cos(dth), math.sin(dth)
        x, y, th = c2 * x - s2 * y + t[0], s2 * x + c2 * y + t[1], th + dth
        if abs(dth) < 1e-5 and math.hypot(*t) < 1e-5:
            break
    return x, y, th


def icp_chain(scans, limit):
    """Scan-only pose chain for scans 0..limit (metres, radians; start at the origin)."""
    np, _ = _np()
    limit = min(limit, len(scans) - 1)
    pts = [scan_points(s["ranges_m"]) for s in scans[: limit + 1]]
    world = [(0.0, 0.0, 0.0)]
    for i in range(1, limit + 1):
        a, b = scans[i - 1], scans[i]
        d = math.hypot(b["x_m"] - a["x_m"], b["y_m"] - a["y_m"])
        dth = wrap(b["theta_rad"] - a["theta_rad"])
        x, y, th = icp(pts[i], pts[i - 1], (d * math.cos(dth / 2), d * math.sin(dth / 2), dth))
        X, Y, T = world[-1]
        c, s = math.cos(T), math.sin(T)
        world.append((X + c * x - s * y, Y + s * x + c * y, T + th))
    return world


def ordering_test(scans, pairs=300, gap=8):
    """Median nearest-neighbour residual after odometry alignment, for both index orderings."""
    np, cKDTree = _np()

    def to_frame(P, a, b):
        sa, sb = scans[a], scans[b]
        cb, sbn = math.cos(sb["theta_rad"]), math.sin(sb["theta_rad"])
        W = np.c_[cb * P[:, 0] - sbn * P[:, 1] + sb["x_m"], sbn * P[:, 0] + cb * P[:, 1] + sb["y_m"]]
        ca, san = math.cos(sa["theta_rad"]), math.sin(sa["theta_rad"])
        d = W - [sa["x_m"], sa["y_m"]]
        return np.c_[ca * d[:, 0] + san * d[:, 1], -san * d[:, 0] + ca * d[:, 1]]

    res = {False: [], True: []}
    used = 0
    for a in range(0, len(scans) - gap, 7):
        b = a + gap
        sa, sb = scans[a], scans[b]
        rot = abs(wrap(sb["theta_rad"] - sa["theta_rad"]))
        if math.hypot(sb["x_m"] - sa["x_m"], sb["y_m"] - sa["y_m"]) <= 0.25 and rot <= math.radians(8):
            continue  # need motion for the test to discriminate
        out = {}
        for rev in (False, True):
            pa, pb = scan_points(sa["ranges_m"], rev), scan_points(sb["ranges_m"], rev)
            if len(pa) < 30 or len(pb) < 30:
                break
            out[rev] = float(np.median(cKDTree(pa).query(to_frame(pb, a, b))[0]))
        else:
            for rev in (False, True):
                res[rev].append(out[rev])
            used += 1
            if used >= pairs:
                break
    if not used:
        return None
    f, r = np.array(res[False]), np.array(res[True])
    return {"pairs": used, "median_residual_m_breezyslam_order": float(np.median(f)),
            "median_residual_m_reversed": float(np.median(r)),
            "fraction_pairs_breezyslam_order_better": float((f < r).mean())}


def dead_reckoning_error(scans, signed):
    """Integrate dxy/dtheta exactly as BreezySLAM updates its pose; compare with recorded odometry."""
    x = y = 0.0
    th = scans[0]["theta_rad"]
    worst = 0.0
    for prev, cur in zip(scans, scans[1:]):
        dxy_mm, dth_deg, _ = benchmark.odom_delta(prev, cur, dt_override=1.0)
        if not signed:
            dxy_mm = abs(dxy_mm)
        d = dxy_mm / 1000.0
        x += d * math.cos(th)
        y += d * math.sin(th)
        th += math.radians(dth_deg)
        worst = max(worst, math.hypot(x - (cur["x_m"] - scans[0]["x_m"]), y - (cur["y_m"] - scans[0]["y_m"])))
    return worst


def velocity_compensation(scans, dts, rate_hz):
    """Within-scan distortion BreezySLAM applies per scan for the given dt list (see coreslam.c)."""
    np, _ = _np()
    dps = int(rate_hz * 360)
    shift, stretch = [], []
    for (a, b), dt in zip(zip(scans, scans[1:]), dts):
        dxy_mm, dth_deg, _ = benchmark.odom_delta(a, b, dt_override=dt)
        shift.append(abs(dxy_mm / dt / dps * (len(b["ranges_m"]) - 1)))
        stretch.append(abs(dth_deg / dt / dps))
    return np.array(shift), np.array(stretch)


def cmd_inputs(args):
    np, _ = _np()
    scans = benchmark.load_scans(Path(args.input))
    print("== scan-angle ordering (odometry-predicted scan-to-scan consistency) ==")
    o = ordering_test(scans)
    print(o if o else "not enough moving scan pairs")
    print("== odometry dead reckoning exactly as BreezySLAM integrates it ==")
    print(benchmark.odometry_reverse_steps(scans))
    print("  worst position error vs recorded odometry, signed dxy   : %.2f m" % dead_reckoning_error(scans, True))
    print("  worst position error vs recorded odometry, unsigned dxy : %.2f m" % dead_reckoning_error(scans, False))
    print("== timestamps ==")
    print(benchmark.timestamp_diagnostics(scans))
    src = [b["timestamp"] - a["timestamp"] for a, b in zip(scans, scans[1:])]
    med = float(np.median([d for d in src if d > 0]))
    rec = [d if d > 0 else med for d in src]
    for label, dts in (("recorded dt (legacy offline)", rec), ("constant median dt (default offline)", [med] * len(src))):
        sh, st = velocity_compensation(scans, dts, args.rate_hz)
        print(f"  {label}: max within-scan skew {sh.max():.0f} mm; |scan stretch-1| max {st.max():.2f}; "
              f"scans with |stretch-1|>0.2: {(st > 0.2).sum()}")


def cmd_compare(args):
    np, _ = _np()
    scans = benchmark.load_scans(Path(args.input))
    benchmark.positive_finite("map_meters", args.map_meters)
    benchmark.positive_finite("tolerance_m", args.tolerance_m)
    if args.limit < 1 or args.every < 1:
        raise ValueError("--limit and --every must be >= 1")
    all_rows = benchmark.load_csv_rows(Path(args.csv))
    index_col = "scan_index" if args.mode == "offline" else "index"
    needed = {index_col, "pose_x_mm", "pose_y_mm", "pose_theta_deg"} | ({"run"} if args.mode == "offline" else set())
    if not needed <= set(all_rows[0]):
        raise ValueError(f"{args.csv} is not a {args.mode} CSV: missing columns {sorted(needed - set(all_rows[0]))}")
    if args.mode == "offline":
        available = sorted({int(r["run"]) for r in all_rows})
        rows = [r for r in all_rows if int(r["run"]) == args.run]
        if not rows:
            raise ValueError(f"run {args.run} does not exist in {args.csv} (available runs: {available})")
    else:
        rows = all_rows
    index = {int(r[index_col]): r for r in rows}
    usable = [i for i in index if 0 <= i <= min(args.limit, len(scans) - 1)]
    if not usable:
        raise ValueError(
            f"no usable observations: recorded scans {min(index)}..{max(index)} do not overlap the ICP "
            f"reference range 0..{min(args.limit, len(scans) - 1)} (raise --limit or choose another run). "
            "An empty comparison is not evidence that the pose tracks."
        )
    centre_mm = args.map_meters * 500.0
    world = icp_chain(scans, args.limit)
    print(f"{len(index)} recorded poses; ICP reference over scans 0..{len(world) - 1} (not ground truth)")
    print("scan | SLAM offset from start (m) | ICP offset (m) | distance (m) | heading SLAM-ICP (deg)")
    first_far = None
    compared = 0
    for i in sorted(index):
        if i >= len(world):
            break
        compared += 1
        r = index[i]
        sx, sy = (float(r["pose_x_mm"]) - centre_mm) / 1000, (float(r["pose_y_mm"]) - centre_mm) / 1000
        dist = math.hypot(sx - world[i][0], sy - world[i][1])
        hd = (float(r["pose_theta_deg"]) - math.degrees(world[i][2]) + 180) % 360 - 180
        if first_far is None and dist > args.tolerance_m:
            first_far = i
        if i % args.every == 0:
            print(f"{i:5d} | ({sx:7.1f},{sy:7.1f}) | ({world[i][0]:7.1f},{world[i][1]:7.1f}) | {dist:6.1f} | {hd:7.1f}")
    if first_far is None:
        print(f"no compared pose ({compared}) was > {args.tolerance_m:g} m from the ICP reference "
              f"(limited to scans 0..{len(world) - 1}; the reference drifts and is not ground truth)")
    else:
        print(f"first scan where SLAM is > {args.tolerance_m:g} m from the ICP reference: {first_far} ({compared} poses compared)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("inputs"); a.add_argument("--input", required=True)
    a.add_argument("--rate-hz", type=float, default=6.0, help="Laser scan_rate_hz given to BreezySLAM")
    a.set_defaults(func=cmd_inputs)
    c = sub.add_parser("compare"); c.add_argument("--input", required=True)
    c.add_argument("--csv", required=True, help="offline_runs.csv or paced_scan_timings.csv")
    c.add_argument("--mode", required=True, choices=("offline", "paced"))
    c.add_argument("--run", type=int, default=1, help="offline run number to use")
    c.add_argument("--map-meters", type=float, required=True, help="map size the run used (CSV poses are map-frame)")
    c.add_argument("--limit", type=int, default=1500, help="ICP chain length in scans")
    c.add_argument("--every", type=int, default=100)
    c.add_argument("--tolerance-m", type=float, default=5.0)
    c.set_defaults(func=cmd_compare)
    args = p.parse_args()
    try:
        args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
