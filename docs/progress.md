# Progress

Branch: `refine/autonav-lab`. Machine: Intel Core i5-13420H (8 cores / 12 threads), 15.6 GB RAM, Windows 11, Python 3.14.6, NumPy 2.5.1, SciPy 1.18.0.

## Phase 0: correctness fixes

| Item | Status | Evidence |
|---|---|---|
| Pose composition direction | Done | `python -B -m unittest tests.unit.test_pose_math` (18 tests OK) |
| Step 2 `initialization_frames` crash | Done | key now returned by `get_summary_statistics` |
| PCD loader ignored header `POINTS` | Done | `tests/unit/test_phase0_io.py::TestPcdHeaderIsAuthoritative` |
| Filename timestamp regex | Done | `TestRosStyleFilenames` |
| Stale/unsupported README numbers, private path | Done | README rewritten; exporter sanitises paths (`TestSanitisingAndSyntheticFlag`) |
| Fabricated KITTI timestamps | Done | `TestKittiDoesNotInventTimestamps` |
| Registration validity gate | Done | `TestRegistrationGate` |
| ATE with association + Umeyama, real RPE | Done | `TestTrajectoryEvaluation` |
| Voxel known-answer check | Done | `TestVoxelKnownAnswer` |

Findings during Phase 1 (see DEC-012, DEC-013): unpadded-nsec filenames broke chronological order; GT body frame differs from the sensor frame, so RPE is now extrinsic-free by default. Suite after these fixes: `python -B -m unittest discover -s tests` -> Ran 67 tests, OK.

Full suite after Phase 0: `python -B -m unittest discover -s tests` -> Ran 63 tests, OK (35 pre-existing + 28 new).

## Phase 1: data

| Item | Status |
|---|---|
| Newer College rosbag downloaded (1.74 GB) | Done |
| `tools/extract_bag.py` + validation report | Open |
| Oxford Spires window | Open |

## Phase 2: harness and profiles

`autonav run` writes complete run folders. Verified: synthetic smoke runs on laptop-full, laptop-1c (affinity {0}), laptop-4c (affinity {0,2,4,6}, OMP/OPENBLAS threads 4); `run.json` records the worker's effective environment. Suite: 74 tests OK (`python -B -m unittest discover -s tests`).

## Phase 3: first real results (baseline, Newer College bag window, frames 0-269, 3 repeats each)

| Profile | Run id | P50 | P95 | P99 | Max | Violations |
|---|---|---|---|---|---|---|
| laptop-full | 20261110T080635Z_..._laptop-full_0862f4f | 749.9 ms | 1547.6 ms | 2111.6 ms | 2684.2 ms | 798/798 |
| laptop-4c | 20261110T081752Z_..._laptop-4c_0862f4f | 676.2 ms | 1309.6 ms | 1816.2 ms | 2328.2 ms | 798/798 |
| laptop-1c | 20261110T082758Z_..._laptop-1c_0862f4f | 671.5 ms | 1367.2 ms | 1864.3 ms | 2318.7 ms | 798/798 |

Accuracy (laptop-full, deterministic across repeats): 269/269 registrations accepted; ATE RMSE 0.507 m over 22.5 m ground-truth path (estimated path 26.3 m); position RPE 10 m windows 0.79 m (7.8 %). Single-frame preprocessing study on the NON-CONSECUTIVE sample: median 142.7 ms, P95 186.5 ms, 539/591 frames over 100 ms.
Commands: `autonav run --dataset newer_college_bag9 --variant baseline --profile <p> --repeats 3`; `autonav run --dataset newer_college_sparse --mode single-frame --profile laptop-full --repeats 3`.

## Phase 5: variants and Spires
Window fetched with `python tools/fetch_spires.py` (300 frames, 45.6 m path; GT irregular, 281 of 300 frames have a pose within 20 ms). Variant tests: optimized == baseline trajectory (<1e-3), p2plane recovers a known rigid motion. Timing queue (optimized x 3 profiles, p2plane, Spires baseline x 3 profiles, Spires optimized/p2plane): in progress.

## Open
Phase 6 workflows are written and YAML-validated but have not run (they need a push). Phase 7 site build and Phase 8 review are pending.