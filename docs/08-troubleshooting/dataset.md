# Troubleshooting Guide: Datasets

## 1. Helpful Missing Dataset Errors

If you run an experiment pointing to a real dataset that you have not yet downloaded:
```bash
python experiments/02-lidar-characterization/run.py --dataset newer_college
```

The system will **never crash silently or fabricate results**. Instead, it prints clear, actionable instructions:
```
[ERROR]: Oxford Newer College dataset path not found at datasets/newer-college.
Please download a sequence (e.g. 01_short_experiment) from:
  https://ori-drs.github.io/newer-college-dataset/
and place it in datasets/newer-college/
```

To test code immediately without downloading gigabytes of data, simply pass:
```bash
--dataset synthetic
```

---

## 2. Incomplete or Corrupted Archives

Verify extracted files using `tools/inspect_dataset.py`:
```bash
python tools/inspect_dataset.py --path datasets/tum-rgbd/rgbd_dataset_freiburg1_xyz
```
This tool checks for malformed image headers, zero-byte files, and timestamp gaps.
