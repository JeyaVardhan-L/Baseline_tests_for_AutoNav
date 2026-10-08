# How to Run an Experiment

This guide explains how to execute any experiment in this repository on Windows, Linux, or macOS.

---

## 1. Quick Verification (Offline Synthetic Stream)

Before downloading large datasets, run the environment check and synthetic smoke test:

```bash
# Verify Python and dependencies
python tools/check_environment.py

# Run Experiment 01 on synthetic data
python experiments/01-data-inspection/run.py --dataset synthetic
```

---

## 2. Running Against a Real Downloaded Dataset

### Step 1: Download the sequence
Download a sequence manually from the official mirror (see [`docs/01-datasets/`](../01-datasets/)).

### Step 2: Extract to the dataset directory
Extract the files into `datasets/<dataset_name>/`:
```
datasets/
    newer-college/
        01_short_experiment/
    tum-rgbd/
        rgbd_dataset_freiburg1_xyz/
```

### Step 3: Run the experiment pointing to the dataset
```bash
# LiDAR Characterization on Newer College
python experiments/02-lidar-characterization/run.py --dataset newer_college --max-frames 100

# Depth Characterization on TUM RGB-D
python experiments/06-depth-characterization/run.py --dataset tum_rgbd --path datasets/tum-rgbd/rgbd_dataset_freiburg1_xyz
```

---

## 3. Where to Find Results

All outputs are automatically saved to:
```
results/<dataset_name>/<experiment_name>/
    metrics.csv       # Frame-by-frame data
    summary.json      # Structured dictionary
    metadata.json     # Hardware and git snapshot
    summary.md        # Summary report
    figures/          # Generated PNG graphs
```
