"""
Dataset adapter registry and factory.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from autonav_baseline.datasets.base import DatasetAdapter
from autonav_baseline.datasets.newer_college import NewerCollegeAdapter
from autonav_baseline.datasets.hilti import HiltiAdapter
from autonav_baseline.datasets.openloris import OpenLORISAdapter
from autonav_baseline.datasets.tum_rgbd import TUMRGBDAdapter
from autonav_baseline.datasets.oxford_spires import OxfordSpiresAdapter
from autonav_baseline.datasets.kitti import KITTIAdapter
from autonav_baseline.datasets.synthetic import SyntheticAdapter

ADAPTERS = {
    "newer_college": NewerCollegeAdapter,
    "newer-college": NewerCollegeAdapter,
    "hilti": HiltiAdapter,
    "hilti_2023": HiltiAdapter,
    "hilti-2023": HiltiAdapter,
    "openloris": OpenLORISAdapter,
    "openloris_scene": OpenLORISAdapter,
    "openloris-scene": OpenLORISAdapter,
    "tum_rgbd": TUMRGBDAdapter,
    "tum-rgbd": TUMRGBDAdapter,
    "oxford_spires": OxfordSpiresAdapter,
    "oxford-spires": OxfordSpiresAdapter,
    "kitti": KITTIAdapter,
    "synthetic": SyntheticAdapter,
}


def get_adapter(
    dataset_name: str,
    root_path: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None,
) -> DatasetAdapter:
    """Instantiates a dataset adapter by canonical name or alias."""
    key = dataset_name.lower().strip()
    if key not in ADAPTERS:
        available = ", ".join(sorted(list(set(ADAPTERS.keys()))))
        raise ValueError(f"Unknown dataset '{dataset_name}'. Available datasets: {available}")
    cls = ADAPTERS[key]
    return cls(root_path=root_path, config=config)
