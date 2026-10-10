import importlib.util
from pathlib import Path

import numpy as np

SCRIPT = Path(__file__).resolve().parents[2] / "experiments" / "11-2d-lidar-slam-simulation" / "run.py"
SPEC = importlib.util.spec_from_file_location("lidar_slam_sim", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_scan_has_expected_shape_and_finite_points():
    angles = np.linspace(-np.pi, np.pi, 180, endpoint=False)
    points, ranges = MODULE.raycast_scan((5.0, 4.0, 0.0), angles, rng=np.random.default_rng(1))
    assert points.shape == (180, 2)
    assert ranges.shape == (180,)
    assert np.isfinite(points).all()
    assert ((ranges > 0) & (ranges <= 8.0)).all()


def test_rigid_fit_recovers_simple_translation():
    source = np.array([[0., 0.], [1., 0.], [0., 1.], [1., 1.]])
    target = source + np.array([0.2, -0.1])
    pose = MODULE.fit_rigid_2d(source, target)
    assert np.allclose(pose[:2], [0.2, -0.1], atol=1e-6)
    assert abs(pose[2]) < 1e-6
