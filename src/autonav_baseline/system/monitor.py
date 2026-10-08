"""
System resource monitoring (CPU, RAM, platform).
"""

import os
import platform
import psutil
from typing import Dict, Any
from autonav_baseline.metrics.classification import Classification, tag


def get_process_memory_mb() -> float:
    """Returns current process Resident Set Size (RSS) in megabytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024.0 * 1024.0)


def get_cpu_percent() -> float:
    """Returns current process CPU utilization percentage."""
    process = psutil.Process(os.getpid())
    return process.cpu_percent(interval=None)


def get_system_snapshot() -> Dict[str, Any]:
    """Captures a complete machine snapshot for metadata records."""
    vm = psutil.virtual_memory()
    return {
        "os": f"{platform.system()} {platform.release()}",
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "total_ram_gb": tag(round(vm.total / (1024.0 ** 3), 2), Classification.MEASURED, "GB"),
        "available_ram_gb": tag(round(vm.available / (1024.0 ** 3), 2), Classification.MEASURED, "GB"),
    }
