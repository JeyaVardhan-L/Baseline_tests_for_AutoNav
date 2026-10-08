#!/usr/bin/env python3
"""
Environment and dependency validation tool for autonav_baseline.
Run this first to verify that your system is ready.
Usage:
    python tools/check_environment.py
"""

import sys
import platform
import shutil
import psutil

print("=" * 65)
print("AUTONAV BASELINE - SYSTEM ENVIRONMENT VERIFICATION")
print("=" * 65)

# Python check
py_major, py_minor, py_micro = sys.version_info[:3]
is_py_ok = (py_major, py_minor) >= (3, 9)
status_py = "PASS" if is_py_ok else "FAIL (requires Python >= 3.9)"
print(f"Python Version        : {py_major}.{py_minor}.{py_micro} ({platform.architecture()[0]}) [{status_py}]")

# OS check
print(f"Operating System      : {platform.system()} {platform.release()} (Build {platform.version()})")

# Hardware check
vm = psutil.virtual_memory()
ram_gb = vm.total / (1024.0 ** 3)
cpu_phys = psutil.cpu_count(logical=False)
cpu_log = psutil.cpu_count(logical=True)
status_ram = "PASS" if ram_gb >= 4.0 else "WARNING (< 4 GB RAM)"
print(f"System Memory (RAM)   : {ram_gb:.2f} GB total, {vm.available / (1024.0 ** 3):.2f} GB free [{status_ram}]")
print(f"Processor (CPU)       : {cpu_phys} physical cores, {cpu_log} logical cores")

print("\nPython Package Status:")
packages = [
    ("numpy", "Core multidimensional array computation", True),
    ("matplotlib", "Scientific graph plotting", True),
    ("pyyaml", "YAML configuration loading", True),
    ("psutil", "Process CPU and memory telemetry", True),
    ("scipy", "Scientific algorithms and spatial KDTree", True),
    ("pandas", "Tabular dataset analysis", False),
    ("open3d", "Optional 3D visualizer", False),
]

all_core_ok = True
for pkg, purpose, is_required in packages:
    mod_name = "yaml" if pkg == "pyyaml" else pkg
    req_tag = "REQUIRED" if is_required else "OPTIONAL"
    try:
        mod = __import__(mod_name)
        ver = getattr(mod, "__version__", "INSTALLED")
        print(f"  [+] {pkg:<14} : {ver:<18} ({req_tag}) - {purpose}")
    except ImportError:
        status = "FAIL" if is_required else "NOT INSTALLED"
        print(f"  [-] {pkg:<14} : {status:<18} ({req_tag}) - {purpose}")
        if is_required:
            all_core_ok = False

print("\nGit Version Control:")
git_path = shutil.which("git")
if git_path:
    print(f"  [+] git executable found at: {git_path}")
else:
    print("  [-] git executable NOT found in PATH")

print("=" * 65)
if all_core_ok and is_py_ok:
    print("SYSTEM STATUS: ALL CORE REQUIREMENTS SATISFIED.")
    print("You are ready to run the experiments.")
else:
    print("SYSTEM STATUS: MISSING PREREQUISITES.")
    print("Please install missing dependencies: pip install -r requirements/requirements.txt")
print("=" * 65)
