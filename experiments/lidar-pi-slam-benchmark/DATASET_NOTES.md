# Dataset notes: Intel Research Lab planar laser log

## Candidate

The Intel Research Lab laser dataset is a well-known indoor ground-robot SLAM sequence, commonly distributed through the Freiburg SLAM evaluation dataset page: http://ais.informatik.uni-freiburg.de/slamevaluation/datasets.php. Hosting availability is not guaranteed; the downloader supports `DATASET_URL` so a user can supply a verified working URL. Do not cite a mirror as the original data owner.

**Licence caveat:** a clear per-recording licence for this Intel log was not verified during repository preparation. Treat it as research/evaluation material, retain attribution, and verify permission from the host before redistribution or commercial use. Do not assume a general Radish licence applies to this separate recording.

## Format assumptions

The parser accepts CARMEN-style text records beginning with `FLASER`, with a scan count, range values in metres, odometry x/y/heading, laser x/y/heading, then scan and odometry timestamps. It preserves input order and timestamps. Any line that starts with FLASER but has a malformed count or too few fields raises an error. Non-FLASER records are ignored because CARMEN logs can include other sensor record types.

The script reports inferred angular coverage only as a parameterized estimate when the range count is known; it does not claim an exact field of view or range resolution unless configured from verified dataset metadata. The dataset is from a ground robot, not an aerial vehicle, and its motion/geometry are not representative of a drone-mounted YDLIDAR X2.

## Licensing and attribution

A clear licence for this specific Intel recording was not verified. Confirm the host's terms before redistribution or commercial use. Keep source attribution and URL with derived results. This repository does not redistribute the dataset.

Suggested source reference: Freiburg SLAM evaluation dataset page, http://ais.informatik.uni-freiburg.de/slamevaluation/datasets.php (accessed on the date of download). Also cite original dataset paper/metadata supplied by the host.

## Known limitations

- Download URL/mirror must be checked at run time; this repository does not claim a dataset download has already succeeded.
- The CARMEN pose fields are odometry/reference fields, not automatically ground truth.
- This benchmark is for 2D planar scan computational feasibility. It does not validate altitude estimation, 3D obstacle clearance, sensor vibration, rotor interference, or safe autonomous landing.
