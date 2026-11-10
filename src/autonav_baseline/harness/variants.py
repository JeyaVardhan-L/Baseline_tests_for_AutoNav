"""Algorithm variants. All variants are always published side by side; baseline is never replaced."""

from typing import Any, Dict

from autonav_baseline.lidar.odometry import ICPOdometry


def make_odometry(variant: str, params: Dict[str, Any]) -> ICPOdometry:
    if variant == "baseline":
        return ICPOdometry(**params)
    if variant == "optimized":
        from autonav_baseline.harness.variants_impl import OptimizedOdometry
        return OptimizedOdometry(**params)
    if variant == "p2plane":
        from autonav_baseline.harness.variants_impl import P2PlaneOdometry
        return P2PlaneOdometry(**params)
    raise ValueError(f"unknown variant '{variant}'")