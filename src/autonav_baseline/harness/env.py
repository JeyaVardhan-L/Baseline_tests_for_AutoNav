"""Environment capture for run.json: machine specification (not measured usage)."""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]


def cpu_model() -> str:
    try:
        if sys.platform == "win32":
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                return str(winreg.QueryValueEx(k, "ProcessorNameString")[0]).strip()
        if sys.platform.startswith("linux"):
            for line in Path("/proc/cpuinfo").read_text().splitlines():
                if line.lower().startswith(("model name", "hardware", "processor\t: ") ) and ":" in line:
                    val = line.split(":", 1)[1].strip()
                    if val and not val.isdigit():
                        return val
        if sys.platform == "darwin":
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    except Exception:
        pass
    return platform.processor() or "UNKNOWN"


def git_info() -> Dict[str, Any]:
    def run(*args):
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    try:
        return {"commit": run("rev-parse", "HEAD"), "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
                "dirty": bool(run("status", "--porcelain"))}
    except Exception:
        return {"commit": "UNKNOWN", "branch": "UNKNOWN", "dirty": None}


def blas_config() -> Dict[str, Any]:
    try:
        cfg = np.show_config(mode="dicts")
        deps = cfg.get("Build Dependencies", {})
        return {k: {kk: vv for kk, vv in v.items() if kk in ("name", "version", "openblas configuration")}
                for k, v in deps.items() if k in ("blas", "lapack")}
    except Exception:
        return {"note": "numpy.show_config unavailable"}


def _power_plan() -> str:
    try:
        if sys.platform == "win32":
            out = subprocess.check_output(["powercfg", "/getactivescheme"], text=True, stderr=subprocess.DEVNULL)
            return out.split("(")[-1].strip(") \r\n")
    except Exception:
        pass
    return "UNKNOWN"


def collect_environment() -> Dict[str, Any]:
    import psutil
    import scipy
    vm = psutil.virtual_memory()
    freq = psutil.cpu_freq()
    proc = psutil.Process()
    try:
        affinity = proc.cpu_affinity()
    except Exception:
        affinity = None
    return {
        "cpu_model": cpu_model(),
        "cpu_architecture": platform.machine(),
        "cpu_cores_physical": psutil.cpu_count(logical=False),
        "cpu_cores_logical": psutil.cpu_count(logical=True),
        "cpu_clock_mhz": {"current": getattr(freq, "current", None), "min": getattr(freq, "min", None),
                          "max": getattr(freq, "max", None), "note": "reported by the OS; sustained clock under load is not measured"},
        "ram_total_gb": round(vm.total / 1024 ** 3, 2),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "psutil": psutil.__version__,
        "blas_lapack": blas_config(),
        "thread_env": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
        "cpu_affinity_effective": affinity,
        "gpu": "not used (CPU-only pipeline)",
        "conditions_before_run": {
            "system_cpu_percent_1s": psutil.cpu_percent(interval=1.0),
            "ram_available_gb": round(psutil.virtual_memory().available / 1024 ** 3, 2),
            "power_plan": _power_plan(),
            "note": "The machine is a shared development laptop, not an isolated benchmark host; other applications may be running.",
        },
    }


def peak_rss_mb() -> float:
    """Peak resident memory of this process in MB (Windows: peak working set)."""
    import psutil
    mi = psutil.Process().memory_info()
    peak = getattr(mi, "peak_wset", None)
    if peak is None:
        try:
            import resource
            peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
        except Exception:
            peak = mi.rss
    return peak / 1024 ** 2