# Reproduce a result

Everything below runs from a clean clone. Times are for the development laptop (Intel Core i5-13420H).

```powershell
git clone <repo> ; cd <repo>
python -m venv .venv ; .venv\Scripts\Activate.ps1
pip install -e .
python -B -m unittest discover -s tests -v          # 74+ tests, no datasets needed
```

## 1. Get the data (see docs/datasets.md)
- Oxford Spires window (public): `pip install -e ".[data]"` then `python tools/fetch_spires.py` (about 240 MB).
- Newer College: request access from the Oxford Robotics Institute, place the recording as described in `docs/datasets.md`, then `python tools/extract_bag.py --bag <file.bag> --out datasets/newer-college/01_short_experiment/contiguous_bag9/point_clouds` and place `registered_poses.csv` in `datasets/newer-college/01_short_experiment/contiguous/`.
- Validate a window before using it: `python tools/validate_window.py --frames <dir> --gt <poses.csv> --out artifacts/validation/<name>`.

## 2. Run
```powershell
autonav run --dataset newer_college_bag9 --variant baseline --profile laptop-full --repeats 3
autonav run --dataset oxford_spires --variant optimized --profile laptop-4c --repeats 3
autonav run --dataset newer_college_sparse --mode single-frame --repeats 3    # non-consecutive: preprocessing only
autonav list
```
Each run writes `artifacts/runs/<run-id>/` (`run.json`, `frames.csv`, `summary.json`, `verdicts.json`, `viz/`). Do not run anything else heavy at the same time: concurrent load corrupts timings.

## 3. Compare with published records
Poses, accepted-registration counts and accuracy are deterministic and should match exactly. Latency depends on CPU model, clocks, background load, Python/NumPy/SciPy versions and BLAS threading. Expect the same ordering between variants and profiles and a similar tail shape, not identical milliseconds; compare per-repeat spread (`summary.json: repeat_spread`) before calling a difference real.

## 4. Publish and view
```powershell
autonav publish <run-id>              # marks the run as publishable
python tools/export_site_data.py      # copies published runs to site/public/data (refuses SYNTHETIC; scans for private data)
cd site ; npm install ; npm run build ; npm run check:numbers
autonav lab                           # local Lab mode: launch runs, compare, publish (needs `npm run build:lab` once)
```
Raspberry Pi 5: run the same CLI on the Pi with `--profile pi5`. The CPU model recorded in `run.json` identifies the machine. Until that is done the Pi tier is UNAVAILABLE.