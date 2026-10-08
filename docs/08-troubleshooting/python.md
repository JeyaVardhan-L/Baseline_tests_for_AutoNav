# Troubleshooting Guide: Python Environment

## 1. Missing Packages

Run the environment checker to inspect dependencies:
```bash
python tools/check_environment.py
```

If packages are missing, install via pip:
```bash
pip install -r requirements/requirements.txt
```

---

## 2. Python 3.14+ C-Extension Incompatibilities

Prebuilt compiled binary wheels for some external libraries (like Open3D or PyTorch) may not yet exist for new preview Python versions (Python 3.14).

### Project Safeguard:
All computational operations in this repository (voxel downsampling, NaN removal, distance bounding, data rate calculation) are implemented in pure NumPy and standard libraries.
