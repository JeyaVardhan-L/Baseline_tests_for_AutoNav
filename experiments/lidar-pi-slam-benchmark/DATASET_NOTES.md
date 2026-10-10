# Dataset notes: Intel Research Lab planar laser log

## Candidate

The Intel Research Lab laser dataset is a well-known indoor ground-robot SLAM sequence. Radish is the original-style repository for robotics logs and describes its collection as containing real-robot odometry and laser data under a Creative Commons Attribution licence: https://radish.sourceforge.net/

A commonly used Freiburg SLAM evaluation mirror is referenced by this package as a download candidate. Hosting availability is not guaranteed; the downloader supports `DATASET_URL` so a user can supply a verified working URL. Do not cite a mirror as the original data owner.

## Format assumptions

The parser accepts CARMEN-style text records beginning with `FLASER`, with a scan count, range values in metres, then x, y, heading, timestamp and odometry timestamp. It preserves input order and timestamps. Any line that starts with FLASER but has a malformed count or too few fields raises an error. Non-FLASER records are ignored because CARMEN logs can include other sensor record types.

The script reports inferred angular coverage only as a parameterized estimate when the range count is known; it does not claim an exact field of view or range resolution unless configured from verified dataset metadata. The dataset is from a ground robot, not an aerial vehicle, and its motion/geometry are not representative of a drone-mounted YDLIDAR X2.

## Licensing and attribution

Radish advertises a Creative Commons Attribution licence for its datasets. Confirm the specific recording's accompanying metadata and licence before redistribution or commercial use. Keep the original dataset citation and source URL with derived results. This repository does not redistribute the dataset.

Suggested paper citation for the dataset source: Robotics Data Set Repository (Radish), https://radish.sourceforge.net/ (accessed on the date of download). Also cite the dataset's original accompanying paper/metadata where supplied.

## Known limitations

- Download URL/mirror must be checked at run time; this repository does not claim a dataset download has already succeeded.
- The CARMEN pose fields are odometry/reference fields, not automatically ground truth.
- This benchmark is for 2D planar scan computational feasibility. It does not validate altitude estimation, 3D obstacle clearance, sensor vibration, rotor interference, or safe autonomous landing.
