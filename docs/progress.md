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

## Open

See later phases in the execution brief; nothing below Phase 1 has been started.