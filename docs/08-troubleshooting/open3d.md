# Troubleshooting Guide: Open3D and Visualization

## 1. No Display / Headless Environment

### Symptom:
`GLFW Error: Failed to open window` or crash on remote SSH connections.

### Fix:
Use the `--cli` flag in playback experiments:
```bash
python experiments/03-pointcloud-playback/run.py --dataset synthetic --cli
```
This prints live frame telemetry and progress bars directly in your terminal without requiring an OpenGL window.

---

## 2. Wayland / Remote Desktop Rendering Glitches

On remote Linux desktops or WSL2, OpenGL hardware acceleration can be disabled. Set software rendering:
```bash
export LIBGL_ALWAYS_SOFTWARE=1
```
