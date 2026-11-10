"""
Local Lab server. Python standard library only.

It serves the built site (site/dist, lab mode) and a small JSON API:
  GET  /api/config                    datasets, profiles, variants and defaults
  GET  /api/runs                      run list with headline numbers and published flag
  GET  /api/runs/<id>/<file...>       run.json, summary.json, verdicts.json, frames.csv, viz/...
  POST /api/run                       start `python -m autonav_baseline run ...` as a subprocess
  GET  /api/jobs/<job-id>             job status and progress (poll)
  POST /api/publish                   {"run_id": "...", "publish": true|false}

It binds to 127.0.0.1 only, validates every input against allow-lists, passes arguments as a list (no
shell), and runs one job at a time because concurrent runs would corrupt timing measurements.
"""

import json
import re
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from autonav_baseline.harness.config import DATASETS, PROFILES, REPO_ROOT, VARIANTS

RUNS_DIR = REPO_ROOT / "artifacts" / "runs"
PUBLISHED = REPO_ROOT / "artifacts" / "published.json"
SITE_DIST = REPO_ROOT / "site" / "dist"
JOBS = {}
LOCK = threading.Lock()
_RUN_ID = re.compile(r"^[A-Za-z0-9._-]+$")
_MIME = {".json": "application/json", ".csv": "text/csv", ".bin": "application/octet-stream", ".html": "text/html",
         ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".png": "image/png",
         ".woff2": "font/woff2", ".txt": "text/plain", ".log": "text/plain"}


def _published():
    return json.loads(PUBLISHED.read_text()) if PUBLISHED.is_file() else {"runs": []}


def _write_published(obj):
    PUBLISHED.parent.mkdir(parents=True, exist_ok=True)
    PUBLISHED.write_text(json.dumps(obj, indent=2))


def list_runs():
    pub = set(_published()["runs"])
    out = []
    for d in sorted(RUNS_DIR.glob("*"), reverse=True) if RUNS_DIR.is_dir() else []:
        item = {"run_id": d.name, "published": d.name in pub, "status": "incomplete"}
        try:
            run = json.loads((d / "run.json").read_text(encoding="utf-8"))
            item.update(status=run["status"], dataset=run["dataset"]["id"], variant=run["variant"],
                        profile=run["profile"]["id"], mode=run["mode"], label=run.get("label", ""),
                        evidence=run["dataset"]["evidence"])
            s = json.loads((d / "summary.json").read_text(encoding="utf-8"))
            if s.get("status") == "completed":
                t = s["latency_ms"]["total_ms"]
                item.update(p50_ms=t["p50"], p95_ms=t["p95"], p99_ms=t["p99"],
                            violation_percent=s["deadline"]["pipeline_total_ms"]["violation_percent"])
                acc = s.get("accuracy", {})
                if acc.get("status") == "MEASURED":
                    item["ate_rmse_m"] = acc["ate_m"]["rmse"]
        except Exception:
            pass
        out.append(item)
    return out


def start_job(body):
    dataset, variant, profile = body.get("dataset"), body.get("variant", "baseline"), body.get("profile", "laptop-full")
    mode = body.get("mode", "pipeline")
    if dataset not in DATASETS or variant not in VARIANTS or profile not in PROFILES or mode not in ("pipeline", "single-frame"):
        return None, "invalid dataset, variant, profile or mode"
    try:
        repeats = int(body.get("repeats", 3))
        warmup = int(body.get("warmup", 3))
    except (TypeError, ValueError):
        return None, "repeats/warmup must be integers"
    if not (1 <= repeats <= 10 and 0 <= warmup <= 20):
        return None, "repeats must be 1-10 and warmup 0-20"
    window = str(body.get("window", "") or "")
    if window and not re.fullmatch(r"(all|first:\d{1,6}|\d{1,6}:\d{1,6})", window):
        return None, "invalid window"
    with LOCK:
        if any(j["state"] == "running" for j in JOBS.values()):
            return None, "a job is already running (one at a time to protect timing)"
        job_id = uuid.uuid4().hex[:10]
        cmd = [sys.executable, "-B", "-m", "autonav_baseline", "run", "--dataset", dataset, "--variant", variant,
               "--profile", profile, "--repeats", str(repeats), "--warmup", str(warmup), "--mode", mode, "--label", "lab"]
        if window:
            cmd += ["--window", window]
        job = {"id": job_id, "state": "running", "run_id": None, "log": [], "returncode": None}
        JOBS[job_id] = job

    def work():
        env = {**__import__("os").environ, "PYTHONPATH": str(REPO_ROOT / "src")}
        proc = subprocess.Popen(cmd, cwd=REPO_ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            line = line.rstrip()
            job["log"].append(line)
            m = re.match(r"run-id:\s*(\S+)", line)
            if m:
                job["run_id"] = m.group(1)
        proc.wait()
        job["returncode"] = proc.returncode
        job["state"] = "done" if proc.returncode == 0 else "failed"

    threading.Thread(target=work, daemon=True).start()
    return job_id, None


def job_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return None
    out = {k: job[k] for k in ("id", "state", "run_id", "returncode")}
    out["log_tail"] = job["log"][-8:]
    if job["run_id"]:
        rd = RUNS_DIR / job["run_id"]
        try:
            out["run_progress"] = json.loads((rd / "progress.json").read_text())
            reps = sorted((rd / "repeats").glob("rep*/progress.json"))
            if reps:
                out["frame_progress"] = json.loads(reps[-1].read_text())
        except Exception:
            pass
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "AutonavLab/1"

    def log_message(self, fmt, *args):  # quiet
        pass

    def _send(self, code, body: bytes, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj).encode("utf-8"))

    def _file(self, path: Path, root: Path):
        try:
            resolved = path.resolve()
            resolved.relative_to(root.resolve())
        except (ValueError, OSError):
            return self._json(404, {"error": "not found"})
        if not resolved.is_file():
            return self._json(404, {"error": "not found"})
        self._send(200, resolved.read_bytes(), _MIME.get(resolved.suffix.lower(), "application/octet-stream"))

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/config":
            return self._json(200, {"mode": "lab", "datasets": {k: {kk: v[kk] for kk in ("sensor", "sequence", "evidence", "consecutive", "default_window", "licence")} for k, v in DATASETS.items()},
                                    "profiles": {k: v["claim"] for k, v in PROFILES.items()}, "variants": list(VARIANTS)})
        if path == "/api/runs":
            return self._json(200, list_runs())
        m = re.fullmatch(r"/api/runs/([^/]+)/(.+)", path)
        if m and _RUN_ID.match(m.group(1)):
            return self._file(RUNS_DIR / m.group(1) / m.group(2), RUNS_DIR)
        m = re.fullmatch(r"/api/jobs/([0-9a-f]+)", path)
        if m:
            st = job_status(m.group(1))
            return self._json(200, st) if st else self._json(404, {"error": "unknown job"})
        rel = path.lstrip("/") or "index.html"
        target = SITE_DIST / rel
        if target.is_dir():
            target = target / "index.html"
        if SITE_DIST.is_dir():
            return self._file(target, SITE_DIST)
        return self._send(200, b"<h1>AutoNav Lab</h1><p>Site not built. Run <code>npm run build:lab</code> in site/.</p>", "text/html")

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 10_000)
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self._json(400, {"error": "invalid JSON"})
        if path == "/api/run":
            job_id, err = start_job(body)
            return self._json(409 if err and "already running" in err else 400, {"error": err}) if err else self._json(202, {"job_id": job_id})
        if path == "/api/publish":
            run_id = str(body.get("run_id", ""))
            if not _RUN_ID.match(run_id) or not (RUNS_DIR / run_id / "summary.json").is_file():
                return self._json(404, {"error": "unknown run"})
            pub = _published()
            runs = [r for r in pub["runs"] if r != run_id]
            if body.get("publish", True):
                runs.append(run_id)
            _write_published({"runs": runs})
            return self._json(200, {"published": run_id in runs})
        return self._json(404, {"error": "not found"})


def serve(port: int = 8765, open_browser: bool = True) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"AutoNav Lab at {url}  (localhost only; Ctrl-C to stop)")
    if open_browser:
        import webbrowser
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass