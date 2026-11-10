# Decision Log

All significant design and engineering decisions are recorded here with context, rationale, and revisit conditions.

---

## DEC-001 — Navigation Computation Architecture

| Field | Value |
|-------|-------|
| **Date** | 2026-10-07 |
| **Status** | ACCEPTED |
| **Decision** | Navigation computation shall be designed as onboard computation rather than depending on ground-station computation. |
| **Context** | The UAV must navigate autonomously in a GPS-denied environment. The competition may restrict or prohibit telemetry during the mission. Even if communication is available, relying on it for navigation creates a single point of failure. |
| **Options considered** | 1. All computation onboard the UAV. 2. Offload heavy computation to the ground station via RF link. 3. Hybrid — critical path onboard, optional augmentation from ground. |
| **Evidence** | IRoC-U 2026 rules state "No telemetry or remote piloting during the mission." Latency over RF links would introduce unacceptable delays for real-time control. |
| **Reason** | Autonomous navigation must remain operational without ground computation. Competition rules prohibit remote piloting. Communication link failure must not cause navigation failure. |
| **Consequences** | The onboard computer must be powerful enough to run the full navigation stack. This increases weight and power requirements. |
| **Revisit condition** | If competition rules explicitly permit ground-station computation for navigation, this decision should be re-evaluated. |

---

## DEC-002 — Phase 1 Uses Public Datasets

| Field | Value |
|-------|-------|
| **Date** | 2026-10-07 |
| **Status** | ACCEPTED |
| **Decision** | Phase 1 experiments shall use publicly available sensor datasets rather than collecting our own data. |
| **Context** | We do not yet have a LiDAR sensor or finalized hardware. We need to understand sensor data characteristics before purchasing anything. |
| **Options considered** | 1. Purchase a LiDAR first and collect our own data. 2. Use public datasets to characterize data before purchasing. 3. Use only simulation data. |
| **Evidence** | Multiple high-quality public LiDAR datasets exist (KITTI, Newer College, MulRan, etc.) with known sensor specifications and ground truth. |
| **Reason** | Public datasets allow us to study real sensor data at zero cost and produce evidence to justify future hardware purchases. |
| **Consequences** | Our experiments will reflect the characteristics of the specific sensors used in those datasets, not necessarily the exact sensor we will purchase. Results must be interpreted accordingly. |
| **Revisit condition** | When we have our own hardware and can collect data. |

---

## DEC-003 — Python as Primary Phase 1 Language

| Field | Value |
|-------|-------|
| **Date** | 2026-10-07 |
| **Status** | ACCEPTED |
| **Decision** | Phase 1 experiments shall be implemented in Python. |
| **Context** | Phase 1 is about data analysis, characterization, and feasibility — not real-time performance. |
| **Options considered** | 1. Python (rapid development, rich ecosystem). 2. C++ (performance, ROS integration). 3. MATLAB (familiar to some team members, but proprietary). |
| **Evidence** | Python with NumPy/Matplotlib provides fast development for data analysis tasks. Open3D provides Python bindings for point-cloud processing. |
| **Reason** | Development speed is more important than execution speed in Phase 1. The team is familiar with Python. All tools are free and open-source. |
| **Consequences** | Performance measurements from Phase 1 Python code do not directly represent the performance of an optimized C++ navigation stack. Phase 2+ may require C++ for real-time components. |
| **Revisit condition** | If Python performance is insufficient even for offline analysis, or when transitioning to real-time implementation. |

---

*New decisions should be appended below with the next sequential ID (DEC-004, etc.)*

## DEC-004 — Work on a local branch; archive instead of delete

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED |
| **Decision** | All refinement work is on local branch `refine/autonav-lab` (from `master`). Obsolete files are moved to `archive/` with `archive/README.md`, never deleted. Nothing under `datasets/` is modified or deleted, only added to. |
| **Alternatives** | Delete obsolete files (smaller tree, loses context); work on `master` (rejected: brief forbids it). |
| **Reason** | Keeps history and lets the owner review every removal. `git mv` preserves `git log --follow`. |

## DEC-005 — Pose composition was backwards; fixed

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED (verified by tests/unit/test_pose_math.py) |
| **Decision** | ICP registers scan k (source) onto scan k-1 (target), so its transform is T = T_{k-1}^{k}. The world pose accumulates as `W_k = W_{k-1} @ T`. The old code used `W_{k-1} @ inv(T)`. |
| **Evidence** | Static scene, sensor advances +1 m in x: old code reported x = -1.0. New tests compare against hand-derived expected poses and replay the old bug to show it lands >3 m away over a 10-frame chain. |
| **Consequence** | Any trajectory produced before this commit was mirrored. None had been published (the real-data runner crashed before exporting). |

## DEC-006 — Registration validity gate

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED (thresholds revisit-able, see below) |
| **Decision** | ICP `success` only means the solver ran. A registration is accepted only if inlier ratio >= 0.30, mean inlier residual <= 0.25 m, step translation <= 1.0 m and step rotation <= 20 deg. Rejections are counted by reason. A rejected frame leaves the pose AND the reference scan unchanged. |
| **Alternatives** | Update the reference anyway (pose loses motion silently); constant-velocity fallback (hides failures). |
| **Reason** | Thresholds come from sensor physics (walking ~0.1 m per 10 Hz scan, ground truth max 0.35 m per step), fixed BEFORE comparing against ground-truth error, and are stored in `run.json`. Tuning them on ATE would leak ground truth into the method. |
| **Evidence** | Previously two unrelated scans, 24.8 s apart, were reported CONVERGED with a 0.40 inlier ratio and 0.54 m residual. |

## DEC-007 — PCD header is authoritative; timestamps never invented

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED |
| **Decision** | The PCD loader reads exactly `POINTS` records (error if the payload is shorter, trailing bytes ignored and reported). Filename timestamps `cloud_<sec>_<nsec>.pcd` are parsed (nsec is an integer nanosecond count). The KITTI adapter returns `timestamp=None` unless a `times.txt` exists. |
| **Evidence** | Real Newer College files returned 65,668 points for a header declaring 65,536. Real filenames were not recognised, so no timestamps were found. |

## DEC-008 — The 1,734 + 50 interleaved Newer College frames are not odometry data

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED |
| **Decision** | Frames in `contiguous/point_clouds/ouster_scan` and `point_clouds/` are an 11.3% thinned sample (longest consecutive run: 4 frames, median gap 0.6 s). They are used only for single-frame preprocessing timing and point-count statistics, labelled NON-CONSECUTIVE. Odometry uses a window extracted from the full rosbag. |

## DEC-009 — Ground-truth frame and RPE definition

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED, assumption UNVERIFIED |
| **Decision** | ATE: position error after rigid SE(3) Umeyama alignment (no scale) with timestamp association (max 20 ms, one-to-one). RPE: Sturm et al. relative pose error over fixed time windows (1 s, 10 s) and fixed ground-truth path-length windows (10 m, 50 m). The old "RPE" compared step lengths and was removed. |
| **Assumption** | The ground-truth poses describe the same body frame as the estimate (the LiDAR frame). This is recorded in every summary as UNVERIFIED until checked against the dataset documentation or the bag's TF tree. |

## DEC-010 — Archived adapters

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED |
| **Decision** | Hilti, OpenLORIS and TUM RGB-D adapters moved to `archive/adapters/` (inspect-only or no LiDAR). `configs/experiments/exp01..10` moved too (never loaded). A test-only `SyntheticAdapter` was added; it is flagged `synthetic` and never published. |

## DEC-011 — No Docker; thread env + CPU affinity fallback

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED |
| **Decision** | Docker is not installed, so the 4-core and 1-core laptop profiles use thread environment variables plus CPU affinity (psutil), and record peak RSS instead of a memory cap. This limits CPU count only; it does not emulate a Pi's memory bandwidth, cache or clock. |

## DEC-012 — Ground-truth body frame differs from the sensor frame: extrinsic-free RPE by default

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED (supersedes the assumption in DEC-009) |
| **Evidence** | On the first 40 frames of the bag window, the mean step direction differs by ~141 deg yaw between the estimate (sensor frame) and the ground truth (body frame); z axes agree. Full SE(3) RPE over 1 s gave 2.35 m (183 %) while Umeyama ATE was 0.10 m, which is only consistent with a frame offset. GT per-step rotations are also jittery (alternating +-2-3 deg) whereas total yaw over the window agrees (GT 23.1 deg, estimate 19.3 deg). |
| **Decision** | `evaluate_trajectory` defaults to world-frame position RPE after global Umeyama alignment (independent of any sensor-to-body extrinsic). Rotation RPE is reported UNAVAILABLE. Full SE(3) RPE remains available with `body_frames_match=True`. |
| **Alternatives** | Hand-eye calibrate the extrinsic from the same sequence (uses ground truth to tune the evaluation; ill-conditioned for near-straight windows). Left as future work. |
| **Limits** | Alignment is fitted over the whole window, so position RPE is mildly optimistic. A short straight window can be aligned even when reversed, so ATE alone is never used as the only check. |

## DEC-013 — Frames are sorted by parsed timestamp, not by filename

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED |
| **Evidence** | `cloud_<sec>_<nsec>` has an unpadded nsec field; lexicographic sort scrambled the 271 extracted frames (dt min -0.50 s). The earlier sparse sets hid this because few frames shared a second. |
| **Decision** | `scan_sort_key` sorts by (sec, nsec); the adapter and `tools/validate_window.py` use it. Extracted names keep the dataset's unpadded convention. Regression tests added. |

## DEC-014 — Oxford Spires as the secondary dataset; licence and sensor caveats

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED |
| **Decision** | Use one sequence (`2024-03-13-observatory-quarter-01`, outdoor, 2,894 clouds at 10 Hz with no gap above 0.15 s) and a 300-frame window chosen by a fixed rule: the consecutive window with the largest ground-truth path length. `tools/fetch_spires.py` reads the remote zip with HTTP range requests, so only the window (~240 MB) is downloaded, not the 2.1 GB archive. |
| **Licence (verified)** | CC BY-NC-SA 4.0 on both the Hugging Face dataset card and the project page. Non-commercial research use with attribution is allowed, so results and heavily decimated excerpts may be published with attribution. No raw redistribution. |
| **Sensor** | Hesai QT64: 64 channels, 10 Hz, ~104 deg vertical field of view, 60 m range (project page). The OS1-64 has a 360 deg horizontal field of view. Every Spires result is labelled as a different sensor and never read as an OS1-64 result. |
| **Ground truth** | Centimetre-level poses from registering the LiDAR to a Leica RTC360 map; each pose is the BASE frame in the world frame (not the LiDAR frame), so position-only RPE (DEC-012) is used. |
| **Format notes** | PCD headers use `COUNT 4` / `COUNT 14` padding fields named `_`; the loader now honours COUNT and skips padding (test added). |

## DEC-015 — Variant definitions

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED |
| **baseline** | Current algorithm after the Phase 0 bug fixes. Never replaced. |
| **optimized** | Same algorithm and same gate; implementation speedups only (packed-key voxel filter, one-pass validity/range mask, cached KD-tree, multi-worker queries over the CPUs the process may use). Must match baseline accuracy within tolerance. |
| **p2plane** | Point-to-plane ICP (PCA normals, k=10) with a constant-velocity initial guess. Preprocessing is deliberately identical to baseline, so differences in `register_ms` come from the registration algorithm rather than implementation tuning. Normal estimation is inside the measured registration cost. |
| **Alternative** | p2plane on top of the optimized preprocessing. Rejected for the primary comparison because it mixes two effects; stage timings let readers combine them. |

## DEC-016 — ARM cloud job uses Spires, not Newer College

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED |
| **Decision** | The `arm-benchmark` workflow fetches a Spires window from Hugging Face inside the runner. Newer College data is not redistributable and its download link is private, so it cannot be used in CI without a repository secret (an account action). The workflow only runs after the owner pushes; no ARM results exist yet. |

## DEC-017 — `intel.clf` licence: unresolved

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | OPEN (owner/teammate to confirm) |
| **Finding** | The Radish repository states a Creative Commons licence without naming the version (and asks users to cite the repository and the data provider). An MIT DSpace mirror lists an `intel_lab` dataset under CC0 1.0, but that entry describes the Intel Lab in Hillsboro, Oregon, not the Seattle log in `intel.clf`. The teammate's README already says a per-recording licence was not verified. |
| **Action taken** | None to the file (it is the teammate's, untouched, not featured on the site). Recommendation: confirm the licence before the repository is made more prominent, or fetch the file at setup time instead of tracking 16 MB of it. |

## DEC-018 — Lab server design

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED |
| **Decision** | `autonav lab` runs a stdlib `http.server` on 127.0.0.1. It validates inputs against allow-lists, passes arguments as a list (no shell), runs one job at a time (concurrent runs would corrupt timings) and contains no algorithm logic: it spawns the same `autonav run` CLI and serves artifacts. |

## DEC-019 — `optimized` v1 was slower per query; v2 uses the default k-d tree

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED |
| **Finding** | The first `optimized` measurements (commit 5539c47) showed no gain on one core (723 ms vs 671 ms baseline median). Profiling one real frame pair (single thread, 32k points): voxel filter 128 ms -> 13 ms, but a `balanced_tree=False, compact_nodes=False` tree queried 63 ms vs 47 ms for the default tree. Over ~10 ICP iterations that cancels the voxel gain. |
| **Decision** | v2 uses the default tree. The v1 runs stay on disk, are labelled `phase5`, and are not published; published `optimized` runs are the v2 re-measurements. |
| **Lesson** | Implementation tuning must be measured per stage; a cheaper build is not a cheaper pipeline. |

## DEC-020 — Published run data is committed under site/public/data

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED |
| **Decision** | `artifacts/runs/` stays git-ignored, but `tools/export_site_data.py` output (`site/public/data`, 5.3 MB: summaries, per-frame CSV, verdicts, decimated clouds of at most ~6,000 points per layer) is committed so a Pages build can run from the repository alone. The excerpts carry attribution and are few and heavily decimated, within the CC BY-NC-SA 4.0 terms of both datasets. Raw clouds are never committed. |

## DEC-021 — Which runs are published; the machine was not isolated

| Field | Value |
|-------|-------|
| **Date** | 2026-11-10 |
| **Status** | ACCEPTED (owner instruction: no further benchmarks; publish what is on disk) |
| **Published** | 15 runs: baseline x 3 profiles (phase3), optimized v2 x 3 profiles, p2plane, a controlled baseline + optimized pair with 5 repeats (`final`), single-frame study, Spires baseline x 3 profiles, Spires optimized v2 and p2plane. |
| **Not published** | optimized v1 (superseded, DEC-019), synthetic smoke runs (refused by the exporter), the interrupted p2plane `final` run (incomplete; stopped on request). |
| **Machine conditions** | Shared development laptop, not an isolated benchmark host. At sampling: AC power, Balanced power plan, ~66 % processor performance (1500 of 2100 MHz), 1.9-2.7 GB RAM available. Run-to-run drift is large: the same variant's repeat medians differ by up to 2.4x (for example optimized v2 repeats of 218, 346 and 523 ms) and baseline medians ranged 650-890 ms across sessions. Runs from the first sessions have no recorded background load (`conditions_before_run` was added later). Several early runs carry `git.dirty = true` (harness files were uncommitted); the algorithm code they exercised is unchanged except for an added default-valued `workers` parameter. |
| **Consequence** | Conclusions use the violation rate and ordering with the per-repeat spread; differences smaller than the spread are not claimed. |

## DEC-022 — Review amendments (independent review, 2026-11-10)

| Field | Value |
|-------|-------|
| **Lever arm (amends DEC-012)** | Position RPE removes the step-direction (yaw) offset between the ground-truth body frame and the sensor frame, but it is **not** independent of a sensor-to-body lever arm, and ATE compares sensor positions with body-frame ground-truth positions. A reviewer test (stationary body, 0.5 m lever arm rotating 1 rad) gave ATE RMSE 0.14 m purely from the offset. Published ATE/RPE therefore mix drift with extrinsic bias; this is stated in the accuracy verdict, the metric definitions and the algorithm page. The extrinsic was not calibrated. |
| **RPE window bug (fixed)** | Time-window RPE took only the right-hand timestamp neighbour, so windows whose target sat just above a frame were dropped (124 of 260 one-second windows on the headline run). Now the nearer neighbour is used (regression test added). Accuracy of all 15 published runs was recomputed from their stored poses; no benchmark was re-run. Distance-window RPE was unaffected. |
| **Scaling statements** | `compare_profiles` now claims a difference only when per-repeat median ranges do not overlap, notes that profiles were measured at different times on a shared machine, and tags the Raspberry Pi inference `[ASSUMED]`. |
| **Private-data scan** | The exporter and `check-numbers.mjs` now match JSON-escaped and forward-slash user paths, `/home/` paths, e-mail addresses, Drive links, Drive-id-like tokens and the OS user name. |
| **Not changed** | Git history of the original repository (before this branch) contains a local Windows user-profile path in an old README (commit 337d95a, removed on this branch) and upstream contributor e-mail addresses. Rewriting history needs your decision before any push. Several published runs come from dirty trees or different commits (disclosed on the site and in the report). `check-numbers` reads git-ignored `artifacts/`, so it runs locally, not in CI; prose numbers outside `<Num>` are not machine-checked. Throughput is exact only for windows starting at frame 0 (all published runs). |
