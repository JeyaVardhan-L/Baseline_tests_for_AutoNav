# Repository Audit and Real-Data Research Scope

**Repository:** `https://github.com/JeyaVardhan-L/Baseline_tests_for_AutoNav.git`  
**Target:** ISRO Robotics Challenge Autonomous Navigation Feasibility Study  
**Date:** October 2026  
**Auditor:** Lead Research-Software Engineer  

---

## 1. Executive Summary

This repository supports an autonomous-navigation feasibility investigation for an ISRO robotics challenge. The core objective is to evaluate **real, publicly available sensor datasets** to measure and compare the algorithmic performance and computational requirements of LiDAR-based odometry and SLAM.

The previous state of the repository contained a proliferation of synthetic generators, simulation raycasters, unverified skeleton adapters, speculative directories, and artificial benchmark reports in `results/synthetic/`. These artifacts gave a misleading impression of feasibility without testing physical sensor ingestion or authentic point clouds.

This audit establishes the baseline engineering state, catalogs team contributions, determines which components to retain, archive, or remove, and defines a small, linear, beginner-friendly research workflow strictly rooted in real sensor data.

---

## 2. Git Status and Team Contributions

### 2.1 Branch and History
- **Active Branch:** `master`
- **Remote Origin:** `https://github.com/JeyaVardhan-L/Baseline_tests_for_AutoNav.git`
- **Recent Merges:**
  - `28ac0a2`: PR #4 (`improve/pi5-slam-benchmark` from `PriyangshuGhosh`)
  - `541dce7`: PR #3 (`PriyangshuGhosh/master`)
  - `88e1ff7`: PR #2 (`PriyangshuGhosh/feat/lidar-pi-slam-benchmark`)
- **Recent Baseline Commits:**
  - `dfcace8`: `docs: simplify research workflow and define validation status`
  - `1023869`: `fix: make dataset inspection and timestamps evidence-based`
  - `59a06ce`: `feat: add minimal ICP odometry baseline`
  - `40060ec`: `feat: add reproducible odometry metrics and visualizations`
  - `4ec7346`: `test: validate the first end-to-end research workflow`

### 2.2 Team Contributions
- **Priyangshu Ghosh (`@PriyangshuGhosh`):** Authored the 2D LiDAR SLAM Raspberry Pi 5 benchmark using a 2D Carmen log (`intel.clf`), including diagnostic scripts, live WebSocket streaming, and timing benchmarks.
  - *Decision:* Preserve as an optional legacy benchmark under `benchmarks/lidar-pi-slam-benchmark/`, isolated from the primary 3D LiDAR research pipeline.
- **JeyaVardhan-L (`@JeyaVardhan-L`):** Repository architecture, pull request management, baseline ICP scan-to-scan odometry, real file parsers (`.pcd`, `.bin`, `.ply`), evidence classification framework, and research documentation.

---

## 3. Inventory and Classification of Repository Files

| Category | Components / Files | Action & Justification |
| :--- | :--- | :--- |
| **1. Required for Real-Data Experiment** | - `src/autonav_baseline/datasets/newer_college.py`<br>- `src/autonav_baseline/datasets/io.py`<br>- `src/autonav_baseline/datasets/base.py`<br>- `src/autonav_baseline/lidar/odometry.py`<br>- `src/autonav_baseline/lidar/filtering.py`<br>- `src/autonav_baseline/lidar/statistics.py`<br>- `src/autonav_baseline/metrics/`<br>- `src/autonav_baseline/system/monitor.py`<br>- `src/autonav_baseline/reporting/exporter.py`<br>- `src/autonav_baseline/visualization/plots.py`<br>- `experiments/01_inspect_dataset.py`<br>- `experiments/02_analyze_lidar_odometry.py`<br>- `configs/dataset.yaml`<br>- `datasets/newer-college/manifest.json` | **Retain & Consolidate:** Form the core linear research pipeline for real LiDAR inspection and ICP odometry. |
| **2. Useful Teammate Work (Outside Scope)** | - `experiments/lidar-pi-slam-benchmark/`<br>- `data/lidar-pi-slam-benchmark/intel.clf`<br>- Pi benchmark unit tests | **Relocate to `benchmarks/lidar-pi-slam-benchmark/`:** Preserve teammate's working 2D hardware benchmark without cluttering primary 3D odometry experiment directory. |
| **3. Redundant or Misleading** | - `src/autonav_baseline/datasets/synthetic.py` (`SyntheticAdapter`)<br>- `experiments/11-2d-lidar-slam-simulation/`<br>- Speculative skeleton adapters (`hilti.py`, `openloris.py`, `oxford_spires.py`, `tum_rgbd.py`, `kitti.py`)<br>- Stale experiment subfolders (`experiments/01-data-inspection/` to `10-sensor-fusion-preparation/`) | **Remove:** Fabricated/synthetic data is explicitly banned as research evidence. Speculative empty adapters provide no real parser implementations and create false impressions of multi-dataset support. |
| **4. Speculative / Empty Directories** | - `simulation/README.md`<br>- `hardware/README.md`<br>- `logs/README.md`<br>- `reports/README.md`<br>- 10 unused configs in `configs/experiments/` | **Prune / Simplify:** Consolidate into concise root directories or single READMEs. Remove empty scaffoldings. |
| **5. Generated Artifacts** | - `results/synthetic/*` (62 files of fake experiment graphs, CSVs, JSONs)<br>- `results/conceptual/*`<br>- `.coverage`<br>- `nothing`<br>- `benchmark.py.bak` | **Remove from Git:** Never commit machine-specific or synthetic test outputs. Maintain clean `.gitignore`. |
| **6. User Data & Test Fixtures** | - Minimal real-format parser fixtures (`tests/fixtures/`) | **Preserve & Expand:** Use solely for validating software parsers and math functions without representing them as research results. |

---

## 4. Non-Negotiable Project Principles

1. **Real Data First:** Synthetic data generators, raycasting simulators, and synthetic result reports are removed from the primary workflow.
2. **Evidence Classification:** All metrics are categorized strictly as:
   - `MEASURED`: directly obtained from physical sensors or host runtime.
   - `DERIVED`: mathematically computed from measured values with documented formulas.
   - `DECLARED`: extracted from authoritative sensor specifications or dataset papers.
   - `ASSUMED`: explicitly documented nominal parameters.
   - `UNAVAILABLE`: data absent or unrecorded.
   - `UNVERIFIED`: algorithm or metric not yet validated against physical ground truth.
3. **Keep the Repository Small:** A beginner must be able to understand the entire pipeline in minutes:
   - Two numbered scripts in `experiments/`: `01_inspect_dataset.py` and `02_analyze_lidar_odometry.py`.
   - Single configuration file `configs/dataset.yaml`.
   - Clear dataset manifest and manual download documentation.
4. **Hardware & Cost Constraints ($0 Budget):** No paid cloud services, no mandatory GPU, fully functional on Windows 11 with standard Python (NumPy, SciPy, Matplotlib).

---

## 5. Implementation Roadmap

1. **Audit & Scope:** Record baseline state and cleanup decisions (*this document*).
2. **Artifact Cleanup & Ignore Rules:** Remove synthetic results, temporary files, and update `.gitignore`.
3. **Dataset Manifest & Download Guide:** Document official Newer College dataset source, license, sequence details, and manual acquisition steps.
4. **Consolidated Numbered Workflow:** Unify inspection and odometry into `01_inspect_dataset.py` and `02_analyze_lidar_odometry.py`.
5. **Real-Data Parsers & Test Suite:** Validate `.pcd`, `.bin`, `.ply` parsers and timestamp validators against isolated unit test fixtures.
6. **Odometry & Resource Measurement:** Execute scan-to-scan ICP on real point-cloud sequences, measuring per-frame latency, CPU usage, and memory.
7. **Evidence Packaging:** Produce standardized summary reports and research plots.
8. **Authoritative Documentation:** Rewrite root `README.md` and `experiments/README.md` with complete PowerShell instructions and evidence tables.
