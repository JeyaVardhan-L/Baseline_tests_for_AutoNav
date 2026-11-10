# Architecture

```
datasets/ (git-ignored raw data)        tools/ extract_bag, fetch_spires, validate_window, export_site_data
        |
src/autonav_baseline/
  datasets/   adapters (newer_college, oxford_spires, kitti, synthetic[tests only]), io, groundtruth
  lidar/      filtering, odometry (ICP + gate), fast_voxel, registration_p2plane
  metrics/    trajectory_evaluation (association, Umeyama ATE, RPE), classification (evidence tags)
  harness/    config (datasets, profiles), worker (one measured repeat), runner (repeats, aggregation),
              variants(+_impl), verdict (rules), viz (decimated artifacts), env (hardware capture)
  lab/        stdlib http.server: spawns the CLI, serves artifacts; no algorithm logic
  cli.py      autonav run | list | publish | unpublish | postprocess | lab
        |
artifacts/runs/<run-id>/  run.json  frames.csv  summary.json  verdicts.json  viz/  (git-ignored)
artifacts/published.json  (which runs the public site may show)
        |
tools/export_site_data.py -> site/public/data/  ->  site/ (Astro static; renders only what was exported)
```

The Python pipeline is the source of truth and is independent of the site at runtime. The site never recomputes a metric; `npm run check:numbers` compares every rendered number with `artifacts/`.