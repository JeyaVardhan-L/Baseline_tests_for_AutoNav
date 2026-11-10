"""autonav command line: run, list, publish, unpublish (lab is added with the Lab server)."""

import argparse
import json
import sys
from pathlib import Path

from autonav_baseline.harness.config import DATASETS, PROFILES, REPO_ROOT, VARIANTS

PUBLISHED = REPO_ROOT / "artifacts" / "published.json"


def _published():
    return json.loads(PUBLISHED.read_text()) if PUBLISHED.is_file() else {"runs": []}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(prog="autonav", description="LiDAR odometry deadline study harness")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run one measured experiment")
    r.add_argument("--dataset", required=True, choices=sorted(DATASETS))
    r.add_argument("--window", default=None, help="'a:b' frame indices, 'first:N' or 'all' (default: dataset default)")
    r.add_argument("--variant", default="baseline", choices=VARIANTS)
    r.add_argument("--profile", default="laptop-full", choices=sorted(PROFILES))
    r.add_argument("--repeats", type=int, default=3)
    r.add_argument("--warmup", type=int, default=3)
    r.add_argument("--mode", default="pipeline", choices=["pipeline", "single-frame"])
    r.add_argument("--voxel", type=float, default=0.15)
    r.add_argument("--label", default="")

    lb = sub.add_parser("lab", help="start the local Lab server")
    lb.add_argument("--port", type=int, default=8765)
    lb.add_argument("--no-browser", action="store_true")
    sub.add_parser("list", help="list runs")
    pp = sub.add_parser("postprocess", help="regenerate verdicts and visual artifacts for an existing run")
    pp.add_argument("run_id")
    p = sub.add_parser("publish", help="mark a run as published")
    p.add_argument("run_id")
    u = sub.add_parser("unpublish")
    u.add_argument("run_id")

    a = ap.parse_args(argv)
    if a.cmd == "run":
        from autonav_baseline.harness.runner import execute
        run_dir = execute(a.dataset, a.window, a.variant, a.profile, a.repeats, a.warmup, a.mode, a.voxel, a.label, argv)
        s = json.loads((run_dir / "summary.json").read_text())
        print(f"run: {run_dir.name}  status: {s.get('status')}")
        if s.get("status") == "completed":
            t = s["latency_ms"]["total_ms"]
            dl = s["deadline"]["pipeline_total_ms"]
            print(f"total_ms p50={t['p50']:.1f} p95={t['p95']:.1f} p99={t['p99']:.1f} max={t['max']:.1f}  "
                  f"violations {dl['violations']}/{dl['of']} ({dl['violation_percent']:.1f}%) of {s['deadline']['deadline_ms']:.0f} ms")
        return 0 if s.get("status") == "completed" else 1
    runs_dir = REPO_ROOT / "artifacts" / "runs"
    if a.cmd == "lab":
        from autonav_baseline.lab.server import serve
        serve(a.port, not a.no_browser)
        return 0
    if a.cmd == "postprocess":
        from autonav_baseline.harness.verdict import generate_verdicts
        from autonav_baseline.harness.viz import export_viz
        from autonav_baseline.reporting.exporter import sanitize_paths
        rd = runs_dir / a.run_id
        run = json.loads((rd / "run.json").read_text(encoding="utf-8"))
        summary = json.loads((rd / "summary.json").read_text(encoding="utf-8"))
        (rd / "verdicts.json").write_text(json.dumps(sanitize_paths(generate_verdicts(summary, run)), indent=2), encoding="utf-8")
        print("viz:", export_viz(rd, run, summary), "verdicts written")
        return 0
    if a.cmd == "list":
        pub = set(_published()["runs"])
        for d in sorted(runs_dir.glob("*")) if runs_dir.is_dir() else []:
            st = json.loads((d / "run.json").read_text())["status"] if (d / "run.json").is_file() else "incomplete"
            print(f"{'*' if d.name in pub else ' '} {d.name}  [{st}]")
        return 0
    pub = _published()
    if a.cmd == "publish":
        if not (runs_dir / a.run_id / "summary.json").is_file():
            print("unknown or incomplete run", file=sys.stderr); return 2
        if a.run_id not in pub["runs"]:
            pub["runs"].append(a.run_id)
    else:
        pub["runs"] = [x for x in pub["runs"] if x != a.run_id]
    PUBLISHED.parent.mkdir(parents=True, exist_ok=True)
    PUBLISHED.write_text(json.dumps(pub, indent=2))
    print(f"published runs: {len(pub['runs'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())