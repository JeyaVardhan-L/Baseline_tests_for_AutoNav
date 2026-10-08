"""
Interactive real-time point cloud playback viewer.
Provides interactive keyboard controls:
  SPACE: Play/Pause
  N: Next frame
  B: Previous frame
  +: Increase playback speed
  -: Decrease playback speed
  R: Reset to frame 0
  ESC/Q: Exit viewer
"""

import time
from typing import List, Optional
import numpy as np
from autonav_baseline.datasets.base import LiDARFrame
from autonav_baseline.system.monitor import get_cpu_percent, get_process_memory_mb


class PointCloudPlaybackViewer:
    """
    Interactive 2D/3D projection point cloud playback viewer with telemetry overlay.
    """

    def __init__(self, frames: List[LiDARFrame], fps: float = 10.0, cli_only: bool = False):
        self.frames = frames
        self.fps = fps
        self.cli_only = cli_only
        self.current_idx = 0
        self.is_paused = False
        self.playback_speed = 1.0

    def run_cli(self) -> None:
        """Lightweight terminal-based streaming playback."""
        print("Running CLI Playback mode (Ctrl+C to stop)...")
        print(f"{'Frame':<8} {'Timestamp':<12} {'Points':<10} {'Mean Range':<12} {'RAM (MB)':<10} {'CPU %':<8}")
        print("-" * 65)

        for frame in self.frames:
            r = np.linalg.norm(frame.points[:, :3], axis=1) if len(frame.points) > 0 else np.array([0])
            mean_r = float(np.mean(r))
            ram = get_process_memory_mb()
            cpu = get_cpu_percent()

            print(
                f"{frame.index:<8d} {frame.timestamp:<12.3f} {frame.num_points:<10,d} "
                f"{mean_r:<12.2f} {ram:<10.1f} {cpu:<8.1f}"
            )
            time.sleep(max(1e-3, (1.0 / self.fps) / self.playback_speed))

    def run_interactive(self) -> None:
        """Matplotlib interactive playback with key listeners."""
        import matplotlib
        import matplotlib.pyplot as plt

        if len(self.frames) == 0:
            print("No frames available for playback.")
            return

        fig, ax = plt.subplots(figsize=(10, 8))
        fig.canvas.manager.set_window_title("IRoC-U Point Cloud Live Playback")

        # Initial frame
        frame = self.frames[0]
        pts = frame.points[:, :3]
        sub = pts[::max(1, len(pts) // 8000)] if len(pts) > 8000 else pts

        scatter = ax.scatter(sub[:, 0], sub[:, 1], c=sub[:, 2], cmap="viridis", s=1.0, alpha=0.7)
        ax.set_xlim(-20, 20)
        ax.set_ylim(-20, 20)
        ax.set_aspect("equal")
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.set_xlabel("X (meters, forward)")
        ax.set_ylabel("Y (meters, left)")

        title_text = ax.set_title("Initializing...", fontsize=9, loc="left")

        # Key listener
        def on_key(event):
            if event.key in [" ", "space"]:
                self.is_paused = not self.is_paused
            elif event.key in ["n", "right"]:
                self.current_idx = min(len(self.frames) - 1, self.current_idx + 1)
            elif event.key in ["b", "left"]:
                self.current_idx = max(0, self.current_idx - 1)
            elif event.key in ["+", "="]:
                self.playback_speed = min(5.0, self.playback_speed + 0.25)
            elif event.key in ["-", "_"]:
                self.playback_speed = max(0.25, self.playback_speed - 0.25)
            elif event.key in ["r", "R"]:
                self.current_idx = 0
            elif event.key in ["escape", "q"]:
                plt.close(fig)

        fig.canvas.mpl_connect("key_press_event", on_key)

        plt.ion()
        plt.show()

        while plt.fignum_exists(fig.number):
            t_start = time.perf_counter()
            frame = self.frames[self.current_idx]
            pts = frame.points[:, :3]
            sub = pts[::max(1, len(pts) // 8000)] if len(pts) > 8000 else pts

            scatter.set_offsets(sub[:, :2])
            scatter.set_array(sub[:, 2])

            r = np.linalg.norm(pts, axis=1) if len(pts) > 0 else np.array([0])
            mean_r = float(np.mean(r))
            t_proc_ms = (time.perf_counter() - t_start) * 1000.0

            title_str = (
                f"Frame: {self.current_idx}/{len(self.frames)-1} | Time: {frame.timestamp:.2f}s | "
                f"Pts: {frame.num_points:,} | Mean Range: {mean_r:.1f}m\n"
                f"Speed: {self.playback_speed:.2f}x | Proc: {t_proc_ms:.1f}ms | "
                f"RAM: {get_process_memory_mb():.1f}MB | CPU: {get_cpu_percent():.1f}%\n"
                f"[SPACE: Pause | N/B: Step | +/-: Speed | R: Reset | Q: Quit]"
            )
            title_text.set_text(title_str)

            fig.canvas.draw_idle()
            fig.canvas.flush_events()

            if not self.is_paused:
                if self.current_idx < len(self.frames) - 1:
                    self.current_idx += 1
                else:
                    self.is_paused = True  # Loop or pause at end

            sleep_time = max(0.001, (1.0 / self.fps) / self.playback_speed - (time.perf_counter() - t_start))
            time.sleep(sleep_time)
