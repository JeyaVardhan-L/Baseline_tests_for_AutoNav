# Datasets: setup, provenance, licences

Raw data is never committed (see `.gitignore`) and never redistributed. Locations default to repo-relative folders and can be overridden in a git-ignored `config.local.yaml`:

```yaml
dataset_roots:
  newer_college_bag9: D:/data/ncd/bag9/point_clouds
  newer_college_bag9_gt: D:/data/ncd/registered_poses.csv
```

## Newer College Dataset (primary)

| | |
|---|---|
| Source | Oxford Robotics Institute, https://ori.ox.ac.uk/datasets/newer-college-dataset/ (access is granted by the ORI team) |
| Reference | Ramezani, Wang, Camurri, Wisth, Mattamala, Fallon. *The Newer College Dataset: Handheld LiDAR, Inertial and Vision with Ground Truth.* IROS 2020 |
| Licence | CC BY-NC-SA 4.0 (non-commercial; attribution; share-alike) |
| Sensor | Ouster OS1-64 Gen1: 64 beams, 1024 columns, 10 Hz, 65,536 points per frame |
| Sequence | `01_short_experiment` |

Two kinds of data from this sequence are used, for different purposes:

1. **Odometry window** (`newer_college_bag9`): the single recording `rooster_2020-03-10-11-01-34_9.bag` (27 s, 271 consecutive scans) read with `tools/extract_bag.py` (needs `pip install -e ".[data]"`), written to `datasets/newer-college/01_short_experiment/contiguous_bag9/point_clouds/`. Ground truth: `contiguous/registered_poses.csv` (10 Hz). Validate before use:
   `python tools/validate_window.py --frames <dir> --gt <registered_poses.csv> --out artifacts/validation/newer_college_bag9`
   (result: PASS, see `artifacts/validation/newer_college_bag9.md`).
2. **Thinned sample** (`newer_college_sparse`): 1,734 scans from the raw PCD release. These are 11.3 % of the scans (median gap 0.6 s, longest consecutive run 4 frames), so they are **never** used for odometry, only for single-frame preprocessing timing and point-count statistics, labelled NON-CONSECUTIVE.

Filenames are `cloud_<sec>_<nsec>.pcd` with an unpadded nanosecond field: frames are sorted by parsed timestamp, never by name.

## Oxford Spires (secondary)

| | |
|---|---|
| Source | https://huggingface.co/datasets/ori-drs/oxford_spires_dataset, project page https://dynamic.robots.ox.ac.uk/datasets/oxford-spires/ |
| Licence | CC BY-NC-SA 4.0 (verified on the dataset card and project page) |
| Sensor | Hesai QT64: 64 channels, 10 Hz, ~104 degree vertical field of view, 60 m range. **Not an OS1-64**: beam layout, field of view and range differ, so Spires results are never presented as OS1-64 results |
| Ground truth | LiDAR registered to a Leica RTC360 survey map; the pose of the **base** frame in the world frame |
| Window | `python tools/fetch_spires.py` fetches 300 consecutive clouds of `2024-03-13-observatory-quarter-01` (largest ground-truth path length) with HTTP range requests, about 240 MB instead of the 2.1 GB archive |

## Evaluated, not used

KITTI (adapter kept; Velodyne HDL-64E, automotive; no run published), MulRan (not evaluated), Hilti / OpenLORIS / TUM RGB-D (archived, see `archive/README.md`). Synthetic data (`SyntheticAdapter`) is for unit tests only and is refused by the site export.