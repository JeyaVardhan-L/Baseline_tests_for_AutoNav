# Final report

Branch `refine/autonav-lab`, local commits only. Nothing was pushed, deployed or published. Dates 2026-11-10.

## 1. The central question, per hardware tier

> Can scan-to-scan LiDAR odometry process each frame within the 100 ms arrival period of a 10 Hz sensor, and what does it take to close the gap?

**Answer so far: not with this implementation on this machine. No published run met the deadline.** The lowest published violation rate is 97.2 % of frames; the best median latency is 248 ms (2.5x the deadline). These are measurements of ordinary Python on one shared laptop, not hard real-time guarantees.

Pipeline latency (preprocess + register, frame already in memory). Spread is the range of the per-repeat medians. Violations = frames above 100 ms.

| Tier / run | Dataset | Variant | Median [spread] | P95 | P99 | Max | Violations | Run id |
|---|---|---|---|---|---|---|---|---|
| A laptop-full | Newer College (OS1-64) | baseline | 750 ms [674-839] | 1548 | 2112 | 2684 | 798/798 | `20261110T080635Z_newer_college_bag9_baseline_laptop-full_0862f4f` |
| A laptop-4c | Newer College | baseline | 676 ms [649-739] | 1310 | 1816 | 2328 | 798/798 | `20261110T081752Z_..._laptop-4c_0862f4f` |
| A laptop-1c | Newer College | baseline | 672 ms [650-676] | 1367 | 1864 | 2319 | 798/798 | `20261110T082758Z_..._laptop-1c_0862f4f` |
| A laptop-full | Newer College | optimized v2 | 324 ms [218-523] | 1018 | 1521 | 3190 | 776/798 (97.2 %) | `20261110T100756Z_..._optimized_laptop-full_2917b44` |
| A laptop-4c / 1c | Newer College | optimized v2 | 611 ms [538-691] / 870 ms [793-954] | 1746 / 2090 | 2694 / 2808 | 6836 / 4922 | 99.9 % / 99.9 % | `..._laptop-4c_2917b44`, `..._laptop-1c_2917b44` |
| A laptop-full | Newer College | p2plane | 734 ms [721-750] | 997 | 1232 | 1770 | 798/798 | `20261110T091234Z_..._p2plane_laptop-full_5539c47` |
| A laptop-full, controlled pair (5 repeats) | Newer College | baseline vs optimized | 887 ms [785-963] vs 506 ms [331-1386] | 2069 vs 2301 | 4124 vs 3642 | 8971 vs 10755 | 100 % vs 98.8 % | `20261110T104330Z_..._e9036cd`, `20261110T110724Z_..._e9036cd` |
| A laptop-full | Oxford Spires (**Hesai QT64, not OS1-64**) | baseline | 522 ms [499-565] | 921 | 1295 | 2433 | 888/888 | `20261110T092233Z_oxford_spires_baseline_laptop-full_5539c47` |
| A laptop-4c / 1c | Oxford Spires | baseline | 438 ms [407-474] / 779 ms [736-825] | 757 / 2103 | 1068 / 2936 | 1720 / 4978 | 100 % | `..._laptop-4c_5539c47`, `..._laptop-1c_5539c47` |
| A laptop-full | Oxford Spires | optimized v2 | 248 ms [245-251] | 457 | 1056 | 3695 | 877/888 (98.8 %) | `20261110T103808Z_oxford_spires_optimized_laptop-full_2917b44` |
| A laptop-full | Oxford Spires | p2plane | 518 ms [496-541] | 658 | 794 | 2877 | 888/888 | `20261110T095748Z_oxford_spires_p2plane_laptop-full_5539c47` |
| A laptop-full | Newer College, NON-CONSECUTIVE sample | preprocessing only, no odometry | 143 ms [139-165] | 186 | 199 | 250 | 539/591 (91.2 %) | `20261110T083801Z_newer_college_sparse_baseline-sf_laptop-full_0862f4f` |
| B ARM cloud VM | | | **pending first CI run** (workflow written, needs a push) | | | | | |
| C Raspberry Pi 5 | | | **UNAVAILABLE** (not measured) | | | | | |

What the evidence supports:
- **Where the time goes (baseline, laptop-full, `20261110T080635Z...`):** preprocessing 145 ms (median), registration 588 ms over a median of 10 ICP iterations on about 32,000 voxel points. Registration dominates.
- **Implementation tuning helps the part it targets.** A packed-key voxel filter cuts the voxel stage from 128 ms to 13 ms on one real frame (profiled, DEC-019). The optimized variant gives the same trajectory as baseline (unit test, <1e-3; identical ATE and RPE in the published runs). Its overall speed-up is about 2.1x at the median where spreads are tight (Spires: 248 ms [245-251] vs 522 ms [499-565]; the baseline Spires run has no recorded background load) and is inconsistent where the machine drifted (Newer College: 324 ms [218-523] vs baseline 750 ms [674-839]; controlled pair 506 ms [331-1386] vs 887 ms [785-963]). Even the best case is 2.5-3x over the deadline.
- **Point-to-plane with a constant-velocity guess does not make a frame faster but makes it more accurate and less erratic.** Median latency is about equal to baseline (734 vs 750 ms) while the tail is shorter (P99 1232 vs 2112 ms) and iterations halve (5 vs 10). Position error against ground truth: ATE RMSE 0.15 m vs 0.51 m (Newer College) and 0.15 m vs 1.32 m (Spires); 10 m position RPE 2.5 % vs 7.8 % and 1.4 % vs 11.4 %.
- **Accuracy of the baseline** (deterministic across repeats): 269/269 registrations passed the validity gate; ATE RMSE 0.51 m over 22.5 m of ground-truth path (estimated path 26.3 m); 10 m position RPE 7.8 %. Caveat: ATE and position RPE include any unmodelled sensor-to-body lever arm (DEC-022), so they mix drift with extrinsic bias.
- **Core count:** no consistent effect was measurable. Profile medians are non-monotonic (for example Spires baseline 4c 438 ms is faster than full 522 ms) because profiles were measured at different times on a drifting machine. The one-way inference **[ASSUMED, not measured]**: a miss on 4 laptop cores makes a Raspberry Pi 5 miss very likely; no pass here says anything about a Pi.
- **What it would take (untested suggestions, not results):** frame cost is about 2.5-3x too high in the best case. Candidates: coarser voxels or point subsampling (changes accuracy), compiled code for the nearest-neighbour search and solver, reusing normals and trees across frames, and a motion prior to cut iterations.

## 2. Machine conditions (required disclosure)

- **Hardware:** Intel Core i5-13420H, 4 performance + 4 efficiency cores (8 cores / 12 threads), 15.63 GB RAM, Windows 11 (10.0.26200), Python 3.14.6, NumPy 2.5.1, SciPy 1.18.0, psutil 7.2.2.
- **Profiles:** `laptop-4c` / `laptop-1c` use thread environment variables plus CPU affinity (logical CPUs 0,2,4,6 / 0). Docker is not installed. No memory cap and no clock cap, so this is core-count scaling only.
- **Not an isolated benchmark host.** At sampling the laptop was on AC power, Balanced power plan, running at about 66 % processor performance (1500 of 2100 MHz), with 1.9-2.7 GB of RAM available; Chrome and other user applications were present. Pre-run CPU load recorded for the later runs ranged 17.6-99.9 %.
- **Effect:** the same variant's repeat medians differ by up to 2.4x (optimized v2: 218, 346, 523 ms) and baseline medians ranged 650-890 ms across sessions. Throughput and peak memory (median peak resident memory 74-97 MB) are less affected.
- **Record keeping:** background load, free RAM and power plan are recorded only for runs from `20261110T103808Z` onward. Several earlier runs have `git.dirty = true` because harness files were uncommitted when they ran; the registration/odometry code they exercised is unchanged except an added default-valued `workers` parameter. Runs from different commits (`0862f4f`, `5539c47`, `2917b44`, `e9036cd`) are all labelled on the site.
- **Rule used:** a difference is only reported when per-repeat ranges do not overlap; the verdict generator enforces this for profile comparisons.

## 3. What changed

- **Phase 0:** pose composition fixed (the old code mirrored trajectories); PCD loader honours `POINTS` and `COUNT`/padding; ROS-style filename timestamps and chronological sort; Step 2 crash; KITTI no longer invents timestamps; registration validity gate; ATE with timestamp association and real RPE; private paths removed; README rewritten without unsupported numbers. 40 new tests.
- **Phase 1:** bag downloaded and extracted (271 frames), validated (PASS); Spires window fetched (300 frames; 19 without a ground-truth pose); two new tools (`extract_bag.py`, `fetch_spires.py`) plus `validate_window.py`.
- **Phase 2-3:** `autonav run | list | publish | postprocess | lab`, worker-per-repeat, hardware profiles, per-stage timing, deadline-violation statistics, environment capture, rule-based verdicts, decimated 3D artifacts.
- **Phase 4-5:** Lab server (stdlib only); optimized and p2plane variants with equivalence/accuracy tests.
- **Phase 6:** `ci.yml` (Linux + Windows) and `arm-benchmark.yml` (`ubuntu-24.04-arm`, manual) written and YAML-validated; **never run**.
- **Phase 7:** Astro + TypeScript + three.js + Plotly site, sections A-G, showcase/lab modes, number check.
- **Moved to `archive/` (not deleted, see `archive/README.md`):** Hilti, OpenLORIS and TUM RGB-D adapters, their dataset READMEs and configs, three dataset docs, and the ten never-loaded `configs/experiments/exp*.yaml`.
- **Added dependencies:** `psutil` (already used), optional `[data]` extra (`rosbags`, `gdown`, `huggingface_hub`); site: Astro, three, plotly.js-dist-min, `@fontsource-variable/geist` (design font), `@astrojs/check`, `@types/*`, `cross-env`, `typescript`.

## 4. Verification actually run

| Check | Command | Result |
|---|---|---|
| Unit tests | `python -B -m unittest discover -s tests` | 75 tests OK |
| Site build | `npm run build` (site/) | 8 pages built |
| Types | `npm run check` | 0 errors, 0 warnings, 0 hints |
| Site numbers vs artifacts | `npm run check:numbers` | 139 rendered numbers, 0 mismatches; no private path, Drive link or e-mail in the build |
| Responsive | headless iframe widths 375, 768, 1280 over 8 pages | no horizontal overflow (after two fixes) |
| Visual | built-in browser | overview, 3D viewer (registered clouds), six Plotly charts render, no console errors |
| Lab mode | `autonav lab` + API | validation, path-traversal block, one-job rule, 8-frame synthetic launch (not a benchmark, not published), publish toggle |
| Workflows | PyYAML parse | both valid; **not executed** |
| Independent review | fresh-context agent, read-only | maths PASS WITH NOTES; evidence tags PASS WITH NOTES; private data FAIL for git history only; synthetic/non-consecutive PASS. Findings fixed or logged in DEC-022 |
| Clean-shell reproduction from the README only | **not done** (no further benchmarks were allowed) | see section 5 |

## 5. Unverified or blocked

- **ARM cloud tier and CI:** need a push; no ARM result exists. Raspberry Pi 5: not measured.
- **Reproduction from a clean shell:** not performed. The brief asked for it; it requires re-running a benchmark, which you stopped. The tests and the data tools run from the documented commands, and accuracy figures are deterministic, but latency reproduction within variance has not been checked.
- **Ground-truth frame:** the ground-truth body frame differs from the sensor frame (about 141 deg yaw observed). The extrinsic was not calibrated, so rotation RPE is UNAVAILABLE and ATE/RPE include lever-arm bias. The Spires ground truth is the base frame; 19 of 300 frames have no pose.
- **Dirty-tree and mixed-commit runs, early runs without recorded load** (section 2). The interrupted `final` p2plane run is on disk, incomplete and unpublished. Optimized v1 runs (superseded) are on disk and unpublished.
- **`check:numbers`** reads git-ignored `artifacts/`, so it runs locally, not in CI; numbers typed in prose are not machine-checked.
- **`intel.clf` licence** (teammate benchmark): unresolved (DEC-017).
- **Throughput** is exact only for windows starting at frame 0 (all published runs do).
- Not evaluated: KITTI, MulRan; GPU/Jetson (out of scope); IMU fusion; loop closure.

## 6. Decisions to review (docs/decision-log.md)

DEC-006 (gate thresholds, fixed before looking at ground truth), DEC-009/012/022 (ground-truth frame, extrinsic-free RPE, lever arm), DEC-014 (Spires window rule and sensor caveat), DEC-015 (p2plane keeps baseline preprocessing), DEC-017 (`intel.clf` licence), DEC-019 (optimized v1 -> v2), DEC-020 (published data committed under `site/public/data`), DEC-021 (which runs are published and machine conditions).

## 7. Needs your permission next

1. **Git history:** the original repository history contains a local Windows user-profile path (an old README, commit 337d95a, removed on this branch) and upstream contributors' e-mail addresses. Decide whether to rewrite history before pushing. I did not.
2. **Push** the branch (this triggers `ci.yml` and lets you start `arm-benchmark.yml` for the first ARM-cloud result).
3. **GitHub Pages deploy** of `site/dist` (set `SITE_BASE` for a project site) and merging into `master`.
4. Whether to commit the committed run excerpts (`site/public/data`, 5.3 MB) as-is.

## 8. Suggested next experiments

1. Re-measure the published set on a quiet machine (fixed power plan, high-performance clocks, nothing else running) with 10 repeats, interleaving variants to cancel drift; record load for every run.
2. Run `--profile pi5` on a real Raspberry Pi 5, then the ARM cloud workflow.
3. Calibrate the sensor-to-body extrinsic (hand-eye) on a separate segment so rotation RPE becomes available and the lever-arm bias can be removed.
4. Sweep voxel size and point subsampling against accuracy (latency/accuracy frontier); test fewer ICP iterations with the p2plane guess.
5. Compile the nearest-neighbour and solver stages (C++ or Numba) and re-measure per stage.
6. Longer Newer College windows (the other bag parts) and a second walking Spires sequence to separate scene effects from algorithm effects.
## 9. After the report: push and Pages (2026-11-10)

- **Pushed:** `master` was fast-forwarded from `ce0e670` to `d89a231` (no force, history kept, as decided: DEC-023). A history rewrite was prepared and verified in a throwaway clone but deliberately not pushed; the old path string therefore remains in old public commits (`337d95a`) and is gone from the tip. A verified bundle backup of the pre-push history exists outside the repository.
- **CI (`tests` workflow) ran on GitHub and passed on all four jobs** (Ubuntu and Windows, Python 3.11 and 3.13) from a fresh clone, with no datasets: this is independent confirmation that the 75 tests do not depend on the author's machine.
- **Pages: not live yet.** The `pages` workflow builds up to `actions/configure-pages`, which fails because GitHub Pages is not enabled for the repository and the workflow token cannot enable it. **One setting is needed from the owner:** repository Settings -> Pages -> Build and deployment -> Source: **GitHub Actions**, then re-run the `pages` workflow (Actions tab) or push any change under `site/`. The expected address is `https://jeyavardhan-l.github.io/Baseline_tests_for_AutoNav/`. The README already links to it, so the link will 404 until then.
- **ARM-cloud benchmark:** still not run. It is a manual workflow (`arm-benchmark`, Actions tab -> Run workflow); its results will be the first real ARM measurement.
- Mistake found and fixed: the first `pages.yml` was invalid YAML (an unquoted colon in a step name) because I had validated the other two workflows but not that one; it is fixed in `d89a231` and all three workflow files now parse.