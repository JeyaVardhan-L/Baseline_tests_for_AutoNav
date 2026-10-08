# Experiment 03 — Real-Time Point Cloud Playback

## 1. Objective
Enable human visual inspection of streaming point clouds as they arrive frame-by-frame, overlaid with live computational telemetry (FPS, frame index, point counts, RAM, and CPU utilization).

## 2. Why This Matters
Numbers and CSV tables do not reveal sensor blind spots, ground reflections, or moving obstacles. An engineer must visually see the point cloud to understand what the robot actually perceives.

## 3. Required Knowledge
- **Frame Rate (FPS)**: Frames per second rendered to the display.
- **Bird's-Eye View (BEV)**: Top-down projection onto the $X\text{-}Y$ horizontal plane.

## 4. Dataset
Supports any registered dataset (`synthetic`, `newer_college`, `hilti_2023`, `kitti`).

## 5. Input
Normalized stream of `LiDARFrame` records.

## 6. Output
- Live interactive graphical window with telemetry overlay.
- CLI streaming output mode for headless / remote terminal environments.

## 7. Interactive Controls
| Key | Action |
| :--- | :--- |
| **SPACE** | Pause / Resume playback |
| **N / Right Arrow** | Step forward by 1 frame |
| **B / Left Arrow** | Step backward by 1 frame |
| **+ / =** | Increase playback speed multiplier |
| **- / _** | Decrease playback speed multiplier |
| **R** | Reset playback to frame 0 |
| **ESC / Q** | Close viewer |

## 8. Command
```bash
# Interactive GUI playback (Default)
python experiments/03-pointcloud-playback/run.py --dataset synthetic --frames 100

# Terminal streaming playback (Headless / SSH / fast inspection)
python experiments/03-pointcloud-playback/run.py --dataset synthetic --frames 50 --cli
```

## 9. Expected Terminal Output (CLI Mode)
```text
Frame    Timestamp    Points     Mean Range   RAM (MB)   CPU %   
-----------------------------------------------------------------
0        0.000        65,536     5.62         51.2       0.0     
1        0.100        65,536     5.65         51.2       0.0     
2        0.200        65,536     5.68         51.2       0.0     
```

## 10. Limitations
Matplotlib 2D projections display planar spatial structure effectively; full interactive 3D rotation requires optional Open3D visualization packages.
