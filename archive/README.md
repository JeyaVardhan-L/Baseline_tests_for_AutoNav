# Archive

Files moved here during the AutoNav refinement (branch `refine/autonav-lab`). Nothing was deleted;
`git log --follow` keeps the history. None of this is imported by the package.

| Path | Why it was archived |
|---|---|
| `adapters/hilti.py` | Inspect-only. It counted every file as a frame and had no frame loader. |
| `adapters/openloris.py` | Inspect-only. No frame loader; OpenLORIS is RGB-D/IMU oriented, not a 3D LiDAR dataset for this question. |
| `adapters/tum_rgbd.py` | RGB-D only (no LiDAR). Not relevant to a LiDAR deadline study. |
| `datasets/hilti-2023`, `datasets/openloris`, `datasets/tum-rgbd` | README stubs for the adapters above. |
| `configs/datasets/{hilti_2023,openloris,tum_rgbd}.yaml` | Config for the archived adapters. |
| `configs/experiments/exp01..exp10_*.yaml` | Never loaded by any code. Superseded by run profiles (`autonav run`). |
| `docs/01-datasets/{hilti-2023,openloris-scene,tum-rgbd}.md` | Docs for the archived adapters. |

To revive an adapter, move it back under `src/autonav_baseline/datasets/`, implement `get_lidar_frames`,
add it to `registry.py`, and add tests that use real-format fixtures.