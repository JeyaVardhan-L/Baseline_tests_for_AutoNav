#!/usr/bin/env python3
"""Synthetic 2-D LiDAR + lightweight scan-matching SLAM demonstration.

This is a simulation/algorithm smoke test, NOT a production SLAM engine and
NOT a measurement of physical sensor ingestion. It ray-casts a small indoor
scene, creates X2-like scans, estimates relative motion using 2-D ICP, and
builds an accumulated map.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree


# Axis-aligned rectangles: (xmin, ymin, xmax, ymax)
ROOM = (0.0, 0.0, 10.0, 8.0)
OBSTACLES = [
    (2.0, 1.4, 2.8, 3.0),
    (4.1, 4.5, 6.4, 5.1),
    (7.0, 1.8, 7.7, 3.7),
    (4.1, 2.0, 5.0, 2.5),
]


def ray_segment_distance(px, py, dx, dy, ax, ay, bx, by):
    """Distance along a ray to a finite segment, or infinity if no hit."""
    sx, sy = bx - ax, by - ay
    denom = dx * sy - dy * sx
    if abs(denom) < 1e-10:
        return np.inf
    qx, qy = ax - px, ay - py
    t = (qx * sy - qy * sx) / denom
    u = (qx * dy - qy * dx) / denom
    if t >= 0.0 and 0.0 <= u <= 1.0:
        return t
    return np.inf


def scene_segments():
    xmin, ymin, xmax, ymax = ROOM
    rects = [ROOM] + OBSTACLES
    segments = []
    for x0, y0, x1, y1 in rects:
        segments.extend([
            (x0, y0, x1, y0), (x1, y0, x1, y1),
            (x1, y1, x0, y1), (x0, y1, x0, y0),
        ])
    return segments


SEGMENTS = scene_segments()


def raycast_scan(pose, angles, max_range=8.0, noise_std=0.008, rng=None):
    """Return local XY endpoints for a 360-degree 2-D scan."""
    x, y, yaw = pose
    world_angles = angles + yaw
    ranges = np.full(len(angles), max_range, dtype=np.float64)
    for i, a in enumerate(world_angles):
        dx, dy = math.cos(float(a)), math.sin(float(a))
        best = max_range
        for ax, ay, bx, by in SEGMENTS:
            hit = ray_segment_distance(x, y, dx, dy, ax, ay, bx, by)
            if hit < best:
                best = hit
        ranges[i] = best
    if rng is not None and noise_std > 0:
        ranges += rng.normal(0.0, noise_std, size=ranges.shape)
    ranges = np.clip(ranges, 0.05, max_range)
    return np.column_stack((ranges * np.cos(angles), ranges * np.sin(angles))), ranges


def transform(points, pose):
    """Transform local XY points into world coordinates."""
    x, y, yaw = pose
    c, s = math.cos(yaw), math.sin(yaw)
    rot = np.array([[c, -s], [s, c]])
    return points @ rot.T + np.array([x, y])


def fit_rigid_2d(source, target):
    """Least-squares rigid transform mapping source onto target."""
    src_mean, dst_mean = source.mean(axis=0), target.mean(axis=0)
    a, b = source - src_mean, target - dst_mean
    u, _, vt = np.linalg.svd(a.T @ b)
    rot = vt.T @ u.T
    if np.linalg.det(rot) < 0:
        vt[-1, :] *= -1
        rot = vt.T @ u.T
    trans = dst_mean - rot @ src_mean
    yaw = math.atan2(rot[1, 0], rot[0, 0])
    return np.array([trans[0], trans[1], yaw])


def apply_pose(points, pose):
    return transform(points, pose)


def compose_pose(a, b):
    """Compose planar poses: world_T_a times a_T_b."""
    c, s = math.cos(a[2]), math.sin(a[2])
    return np.array([
        a[0] + c * b[0] - s * b[1],
        a[1] + s * b[0] + c * b[1],
        math.atan2(math.sin(a[2] + b[2]), math.cos(a[2] + b[2])),
    ])


def icp_current_to_previous(current, previous, max_iterations=20, max_correspondence=0.45):
    """Point-to-point ICP. Returns transform from current scan frame to previous."""
    estimate = np.array([0.0, 0.0, 0.0])
    tree = cKDTree(previous)
    for _ in range(max_iterations):
        moved = apply_pose(current, estimate)
        distances, indices = tree.query(moved, k=1, workers=1)
        keep = distances < max_correspondence
        if int(keep.sum()) < 20:
            break
        delta = fit_rigid_2d(moved[keep], previous[indices[keep]])
        estimate = compose_pose(delta, estimate)
        if np.linalg.norm(delta[:2]) < 1e-4 and abs(delta[2]) < 1e-4:
            break
    moved = apply_pose(current, estimate)
    distances, indices = tree.query(moved, k=1, workers=1)
    keep = distances < max_correspondence
    rmse = float(np.sqrt(np.mean(distances[keep] ** 2))) if int(keep.sum()) else float("nan")
    return estimate, rmse, int(keep.sum())


def ground_truth_pose(i, frames):
    """Smooth loop-like trajectory, kept away from the room walls."""
    t = 2.0 * math.pi * i / max(frames - 1, 1)
    x = 5.0 + 1.15 * math.cos(t)
    y = 4.0 + 0.95 * math.sin(2.0 * t)
    # Face approximately along the direction of travel.
    dx = -1.15 * math.sin(t)
    dy = 1.90 * math.cos(2.0 * t)
    yaw = math.atan2(dy, dx)
    return np.array([x, y, yaw])


def main():
    parser = argparse.ArgumentParser(description="Simulated 2-D LiDAR + scan-matching SLAM demo")
    parser.add_argument("--frames", type=int, default=60, help="Number of simulated scans")
    parser.add_argument("--scan-hz", type=float, default=6.0, help="Nominal scan frequency (X2 is typically 5-8 Hz)")
    parser.add_argument("--sample-rate", type=float, default=3000.0, help="Nominal range samples/second")
    parser.add_argument("--max-range", type=float, default=8.0, help="Maximum simulated range in metres")
    parser.add_argument("--noise-mm", type=float, default=8.0, help="Gaussian range noise standard deviation in mm")
    parser.add_argument("--out", default="results/synthetic/11_2d_lidar_slam_simulation", help="Output directory")
    parser.add_argument("--no-animation", action="store_true", help="Skip GIF output")
    args = parser.parse_args()

    if args.frames < 2 or args.scan_hz <= 0 or args.sample_rate <= 0:
        parser.error("--frames must be >= 2 and rates must be positive")

    out = Path(args.out)
    figures = out / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    # The X2 is rated around 3000 range samples/s and 5-8 scans/s.
    # Thus ~500 samples/scan at 6 Hz is a nominal simulation, not a guarantee.
    points_per_scan = max(90, int(round(args.sample_rate / args.scan_hz)))
    angles = np.linspace(-math.pi, math.pi, points_per_scan, endpoint=False)
    rng = np.random.default_rng(7)
    gt = [ground_truth_pose(i, args.frames) for i in range(args.frames)]

    metrics = []
    all_raw = []
    all_map = []
    estimated_poses = [gt[0].copy()]
    previous_scan = None
    start = time.perf_counter()

    for i, true_pose in enumerate(gt):
        t0 = time.perf_counter()
        local_points, ranges = raycast_scan(
            true_pose, angles, max_range=args.max_range,
            noise_std=args.noise_mm / 1000.0, rng=rng
        )
        scan_generation_ms = (time.perf_counter() - t0) * 1000.0
        valid = np.isfinite(ranges) & (ranges > 0.05) & (ranges <= args.max_range)
        filtered = local_points[valid]
        filter_ms = (time.perf_counter() - t0) * 1000.0 - scan_generation_ms

        icp_ms = 0.0
        rmse = float("nan")
        correspondences = 0
        if i > 0 and previous_scan is not None:
            t_icp = time.perf_counter()
            relative, rmse, correspondences = icp_current_to_previous(filtered, previous_scan)
            icp_ms = (time.perf_counter() - t_icp) * 1000.0
            pose = compose_pose(estimated_poses[-1], relative)
            estimated_poses.append(pose)
        else:
            estimated_poses[0] = true_pose.copy()

        map_points = transform(filtered, estimated_poses[-1])
        all_map.append(map_points)
        all_raw.append(np.column_stack((np.full(len(filtered), i), angles[valid], ranges[valid])))
        previous_scan = filtered

        gt_pose = true_pose
        est_pose = estimated_poses[-1]
        pose_error = float(np.linalg.norm(est_pose[:2] - gt_pose[:2]))
        total_ms = (time.perf_counter() - t0) * 1000.0
        metrics.append({
            "frame": i,
            "timestamp_sim_s": i / args.scan_hz,
            "points_generated": int(len(local_points)),
            "points_valid": int(valid.sum()),
            "points_filtered_out": int((~valid).sum()),
            "raw_scan_bytes_float32_xy": int(local_points.astype(np.float32).nbytes),
            "scan_generation_ms": round(scan_generation_ms, 3),
            "filter_ms": round(filter_ms, 3),
            "icp_ms": round(icp_ms, 3),
            "pipeline_ms": round(total_ms, 3),
            "deadline_ms": round(1000.0 / args.scan_hz, 3),
            "deadline_met": bool(total_ms < 1000.0 / args.scan_hz),
            "icp_rmse_m": round(rmse, 5) if math.isfinite(rmse) else "",
            "icp_correspondences": correspondences,
            "gt_x_m": round(float(gt_pose[0]), 4),
            "gt_y_m": round(float(gt_pose[1]), 4),
            "estimated_x_m": round(float(est_pose[0]), 4),
            "estimated_y_m": round(float(est_pose[1]), 4),
            "position_error_m": round(pose_error, 4),
        })

    elapsed = time.perf_counter() - start
    all_raw_array = np.concatenate(all_raw, axis=0) if all_raw else np.empty((0, 3))
    np.savez_compressed(out / "simulated_scans.npz", frame_angle_range=all_raw_array,
                        angles_rad=angles, ground_truth_poses=np.asarray(gt),
                        estimated_poses=np.asarray(estimated_poses))
    with (out / "metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(metrics[0].keys()))
        writer.writeheader()
        writer.writerows(metrics)

    total_generated = sum(m["points_generated"] for m in metrics)
    total_valid = sum(m["points_valid"] for m in metrics)
    total_bytes = sum(m["raw_scan_bytes_float32_xy"] for m in metrics)
    latency = np.array([m["pipeline_ms"] for m in metrics])
    errors = np.array([m["position_error_m"] for m in metrics])
    summary = {
        "classification": "SIMULATION — not physical sensor or production SLAM evidence",
        "sensor_model_reference": "YDLIDAR X2-like nominal parameters",
        "assumptions": {
            "range_samples_per_second": args.sample_rate,
            "scan_frequency_hz": args.scan_hz,
            "points_per_scan_derived": points_per_scan,
            "max_range_m": args.max_range,
            "range_noise_std_mm": args.noise_mm,
            "room_m": {"width": ROOM[2], "height": ROOM[3]},
            "slam_method": "Adjacent-scan 2-D point-to-point ICP; no loop closure or IMU",
        },
        "frames": args.frames,
        "simulated_duration_s": (args.frames - 1) / args.scan_hz,
        "points_generated_total": total_generated,
        "points_valid_total": total_valid,
        "mean_points_per_scan": round(total_generated / args.frames, 2),
        "mean_valid_points_per_scan": round(total_valid / args.frames, 2),
        "derived_nominal_point_rate_per_s": round(points_per_scan * args.scan_hz, 2),
        "raw_xy_float32_bytes_total": total_bytes,
        "raw_xy_float32_data_rate_bytes_per_s": round(points_per_scan * 2 * 4 * args.scan_hz, 2),
        "pipeline_latency_ms_mean": round(float(np.mean(latency)), 3),
        "pipeline_latency_ms_p95": round(float(np.percentile(latency, 95)), 3),
        "sensor_period_ms": round(1000.0 / args.scan_hz, 3),
        "frames_under_nominal_deadline": int(sum(m["deadline_met"] for m in metrics)),
        "position_error_m_mean": round(float(np.mean(errors)), 4),
        "position_error_m_max": round(float(np.max(errors)), 4),
        "wall_clock_runtime_s": round(elapsed, 3),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "outputs": ["metrics.csv", "summary.json", "simulated_scans.npz",
                    "figures/slam_map.png", "figures/metrics_dashboard.png"],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Attractive map visualization: room, obstacles, accumulated estimated map, trajectory.
    fig, ax = plt.subplots(figsize=(9, 7))
    for x0, y0, x1, y1 in [ROOM] + OBSTACLES:
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0,
                                   fill=False, linewidth=2 if (x0, y0, x1, y1) == ROOM else 1.8))
    map_sample = np.concatenate(all_map, axis=0)
    if len(map_sample) > 12000:
        map_sample = map_sample[::int(math.ceil(len(map_sample) / 12000))]
    ax.scatter(map_sample[:, 0], map_sample[:, 1], s=2, alpha=0.38, label="Accumulated scan map")
    gt_arr, est_arr = np.asarray(gt), np.asarray(estimated_poses)
    ax.plot(gt_arr[:, 0], gt_arr[:, 1], "--", linewidth=2, label="Ground-truth path (simulation)")
    ax.plot(est_arr[:, 0], est_arr[:, 1], linewidth=2, label="ICP estimated path")
    ax.scatter([gt_arr[0, 0]], [gt_arr[0, 1]], marker="*", s=150, label="Start")
    ax.set(xlim=(-0.3, 10.3), ylim=(-0.3, 8.3), aspect="equal",
           title="2-D LiDAR scan-matching simulation — accumulated map")
    ax.set_xlabel("X (m)"); ax.set_ylabel("Y (m)")
    ax.grid(alpha=0.2); ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(figures / "slam_map.png", dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    frames_idx = np.arange(args.frames)
    axes[0, 0].plot(frames_idx, [m["points_generated"] for m in metrics], label="Generated")
    axes[0, 0].plot(frames_idx, [m["points_valid"] for m in metrics], label="Valid")
    axes[0, 0].set_title("Points per scan"); axes[0, 0].set_xlabel("Scan"); axes[0, 0].set_ylabel("Points")
    axes[0, 0].legend()
    axes[0, 1].plot(frames_idx, [m["pipeline_ms"] for m in metrics], label="Pipeline latency")
    axes[0, 1].axhline(1000.0 / args.scan_hz, linestyle="--", label="Scan period")
    axes[0, 1].set_title("Processing time vs scan deadline"); axes[0, 1].set_xlabel("Scan"); axes[0, 1].set_ylabel("ms")
    axes[0, 1].legend()
    axes[1, 0].plot(frames_idx, [m["position_error_m"] for m in metrics])
    axes[1, 0].set_title("Position error (simulation ground truth available)"); axes[1, 0].set_xlabel("Scan"); axes[1, 0].set_ylabel("m")
    axes[1, 1].plot(frames_idx, [m["icp_rmse_m"] or np.nan for m in metrics])
    axes[1, 1].set_title("ICP correspondence RMSE"); axes[1, 1].set_xlabel("Scan"); axes[1, 1].set_ylabel("m")
    for ax in axes.flat:
        ax.grid(alpha=0.25)
    fig.suptitle("AutoNav — 2-D LiDAR + lightweight SLAM simulation", fontsize=14)
    fig.tight_layout()
    fig.savefig(figures / "metrics_dashboard.png", dpi=160)
    plt.close(fig)

    if not args.no_animation:
        try:
            from matplotlib.animation import FuncAnimation, PillowWriter
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.set(xlim=(-0.3, 10.3), ylim=(-0.3, 8.3), aspect="equal",
                   title="2-D LiDAR SLAM playback (simulated)")
            for x0, y0, x1, y1 in [ROOM] + OBSTACLES:
                ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, linewidth=1.5))
            scat = ax.scatter([], [], s=3, alpha=0.5)
            path_line, = ax.plot([], [], linewidth=2)
            robot_dot, = ax.plot([], [], "o", markersize=7)
            label = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top")
            def update(k):
                pts = np.concatenate(all_map[:k + 1], axis=0)
                if len(pts) > 5000:
                    pts = pts[::int(math.ceil(len(pts) / 5000))]
                scat.set_offsets(pts)
                path_line.set_data(est_arr[:k + 1, 0], est_arr[:k + 1, 1])
                robot_dot.set_data([est_arr[k, 0]], [est_arr[k, 1]])
                label.set_text(f"Scan {k + 1}/{args.frames} | {metrics[k]['points_valid']} valid points")
                return scat, path_line, robot_dot, label
            ani = FuncAnimation(fig, update, frames=args.frames, interval=150, blit=False)
            ani.save(out / "slam_playback.gif", writer=PillowWriter(fps=7))
            plt.close(fig)
            summary["outputs"].append("slam_playback.gif")
            (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[WARN] GIF could not be created ({exc}); PNG figures are still available.")

    print("\n=== 2-D LIDAR + SLAM SIMULATION ===")
    print("Evidence class: SIMULATION (not physical hardware evidence)")
    print(f"Scans: {args.frames} | points/scan: {points_per_scan} nominal | scan rate: {args.scan_hz:g} Hz")
    print(f"Generated points: {total_generated:,} | valid: {total_valid:,}")
    print(f"Derived XY float32 data rate: {summary['raw_xy_float32_data_rate_bytes_per_s']:.0f} B/s (excludes transport overhead)")
    print(f"Pipeline latency mean/P95: {summary['pipeline_latency_ms_mean']:.2f}/{summary['pipeline_latency_ms_p95']:.2f} ms")
    print(f"Mean/max simulated position error: {summary['position_error_m_mean']:.3f}/{summary['position_error_m_max']:.3f} m")
    print(f"Outputs: {out.resolve()}")
    print("NOTE: ICP here is a teaching/demo scan matcher; no loop closure, IMU, real serial input, or production SLAM.")


if __name__ == "__main__":
    main()
