#!/usr/bin/env python3
"""
Collect system information for experiment reproducibility.

Outputs system details (OS, CPU, GPU, RAM, Python, libraries) in both
human-readable and JSON formats.

Usage:
    python tools/collect_sysinfo.py
    python tools/collect_sysinfo.py --json
    python tools/collect_sysinfo.py --output sysinfo.json
"""

import argparse
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_cpu_info() -> dict:
    """Collect CPU information."""
    info = {
        "processor": platform.processor() or "UNKNOWN",
        "architecture": platform.machine(),
        "physical_cores": "UNKNOWN",
        "logical_cores": "UNKNOWN",
    }
    try:
        import psutil
        info["physical_cores"] = psutil.cpu_count(logical=False)
        info["logical_cores"] = psutil.cpu_count(logical=True)
    except ImportError:
        pass
    return info


def get_ram_info() -> dict:
    """Collect RAM information."""
    info = {"total_bytes": "UNKNOWN", "total_gb": "UNKNOWN"}
    try:
        import psutil
        mem = psutil.virtual_memory()
        info["total_bytes"] = mem.total
        info["total_gb"] = round(mem.total / (1024 ** 3), 2)
    except ImportError:
        pass
    return info


def get_gpu_info() -> str:
    """Attempt to detect GPU."""
    # Try nvidia-smi
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    return "NONE DETECTED or NOT APPLICABLE"


def get_python_packages() -> dict:
    """Get versions of key packages."""
    packages = {}
    package_map = {
        "numpy": "numpy",
        "matplotlib": "matplotlib",
        "pyyaml": "yaml",
        "psutil": "psutil",
        "open3d": "open3d",
        "pandas": "pandas",
        "scipy": "scipy",
        "jupyter": "jupyter",
    }
    for display_name, mod_name in package_map.items():
        try:
            mod = __import__(mod_name)
            packages[display_name] = getattr(mod, "__version__", "INSTALLED (version unknown)")
        except ImportError:
            packages[display_name] = "NOT INSTALLED"
    return packages


def get_git_info(repo_root: Path | None = None) -> dict:
    """Get current Git commit info."""
    info = {"commit": "UNKNOWN", "branch": "UNKNOWN", "dirty": "UNKNOWN"}
    git_exe = shutil.which("git")
    if not git_exe:
        return info

    cwd = str(repo_root) if repo_root else None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=cwd
        )
        if result.returncode == 0:
            info["commit"] = result.stdout.strip()

        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=cwd
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip()

        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=5, cwd=cwd
        )
        if result.returncode == 0:
            info["dirty"] = len(result.stdout.strip()) > 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return info


def collect_sysinfo(repo_root: Path | None = None) -> dict:
    """Collect all system information into a dictionary."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "gpu": get_gpu_info(),
        "packages": get_python_packages(),
        "git": get_git_info(repo_root),
    }


def print_sysinfo(info: dict) -> None:
    """Print system info in human-readable format."""
    print("=" * 60)
    print("SYSTEM INFORMATION")
    print("=" * 60)
    print(f"Timestamp:    {info['timestamp']}")
    print()
    print("--- Platform ---")
    for key, val in info["platform"].items():
        print(f"  {key:12s}: {val}")
    print()
    print("--- Python ---")
    for key, val in info["python"].items():
        print(f"  {key:14s}: {val}")
    print()
    print("--- CPU ---")
    for key, val in info["cpu"].items():
        print(f"  {key:16s}: {val}")
    print()
    print("--- RAM ---")
    for key, val in info["ram"].items():
        print(f"  {key:12s}: {val}")
    print()
    print(f"--- GPU ---")
    print(f"  {info['gpu']}")
    print()
    print("--- Packages ---")
    for pkg, ver in info["packages"].items():
        print(f"  {pkg:16s}: {ver}")
    print()
    print("--- Git ---")
    for key, val in info["git"].items():
        print(f"  {key:8s}: {val}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Collect system information")
    parser.add_argument("--json", action="store_true", help="Output as JSON only")
    parser.add_argument("--output", type=str, help="Save JSON output to file")
    parser.add_argument("--repo-root", type=str, help="Repository root path for Git info")
    args = parser.parse_args()

    repo_root = Path(args.repo_root) if args.repo_root else None
    info = collect_sysinfo(repo_root)

    if args.json:
        print(json.dumps(info, indent=2, default=str))
    else:
        print_sysinfo(info)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dumps(info, f, indent=2, default=str)
            json.dump(info, f, indent=2, default=str)
        print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
