"""
LiDAR-only Iterative Closest Point (ICP) scan-to-scan odometry baseline.

What is ICP?
  Iterative Closest Point (ICP) is the fundamental algorithm in robotics for aligning two 3D point
  clouds. Given a source scan P and a target scan Q, ICP iteratively:
    1. Finds the closest point in Q for each point in P using a spatial k-d tree.
    2. Filters outlier correspondences based on a maximum distance threshold.
    3. Calculates the optimal 3D rigid transformation (Rotation R, Translation t) that minimizes
       the sum of squared distances between matched point pairs using Singular Value Decomposition (SVD).
    4. Applies the transformation to P and repeats until convergence.

Why scan-to-scan odometry?
  By estimating relative motion (R_k, t_k) between consecutive sensor scans k-1 and k,
  the vehicle's global 6-DoF pose can be estimated by accumulating transformations:
    T_0^k = T_0^{k-1} * T_{k-1}^k

Failure Modes & Limitations (Important for Beginners):
  1. Geometric Degeneracy: In long featureless corridors or flat fields, points can slide along
     the wall without constraint, leading to unobservable longitudinal motion.
  2. Velocity Bounds: If vehicle displacement between scans exceeds `max_correspondence_distance`,
     the algorithm associates points with wrong surfaces and diverges.
  3. Cumulative Drift: Scan-to-scan odometry does not perform loop closure or global bundle adjustment;
     small errors in each frame accumulate quadratically over distance.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any, List
import time
import numpy as np
from scipy.spatial import cKDTree

from autonav_baseline.lidar.filtering import remove_invalid_points, filter_by_range, voxel_downsample


@dataclass
class ICPResult:
    """Result of registering a single pair of point clouds."""
    success: bool
    transformation: np.ndarray  # 4x4 rigid transformation matrix [R, t; 0, 1]
    rotation: np.ndarray        # 3x3 rotation matrix R
    translation: np.ndarray     # 3-vector translation t in meters
    fitness_score: float        # Mean Euclidean residual of inlier correspondences (meters)
    inlier_ratio: float         # inliers / total source points
    num_inliers: int
    iterations: int
    status: str                 # "CONVERGED", "MAX_ITERATIONS", "INSUFFICIENT_POINTS", "DEGENERATE"


@dataclass
class OdometryStepResult:
    """Result of processing one frame in the odometry sequence."""
    frame_index: int
    timestamp: Optional[float]
    success: bool
    pose_4x4: np.ndarray        # 4x4 global pose in world frame
    position_xyz: np.ndarray    # [x, y, z] position in world frame
    step_translation_m: float   # Distance moved since previous frame (meters)
    registration_latency_ms: float
    raw_points_count: int
    downsampled_points_count: int
    fitness_score: float
    inlier_ratio: float
    status: str


def compute_best_rigid_transform(source: np.ndarray, target: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes optimal 3D rigid transformation [R, t] aligning source points to target points
    using the Kabsch-Umeyama SVD algorithm. Minimizes: sum(||target_i - (R * source_i + t)||^2).
    """
    assert len(source) == len(target) and len(source) >= 3

    centroid_source = np.mean(source, axis=0)
    centroid_target = np.mean(target, axis=0)

    # Center coordinates
    p = source - centroid_source
    q = target - centroid_target

    # Cross-covariance matrix H = P^T * Q
    h = p.T @ q

    # SVD
    u, _, vt = np.linalg.svd(h)
    r = vt.T @ u.T

    # Reflection check (ensure det(R) == +1, not -1)
    if np.linalg.det(r) < 0:
        vt[-1, :] *= -1
        r = vt.T @ u.T

    t = centroid_target - r @ centroid_source
    return r, t


def icp_point_to_point(
    source_points: np.ndarray,
    target_points: np.ndarray,
    max_correspondence_distance: float = 1.5,
    max_iterations: int = 30,
    tolerance: float = 1e-4,
    initial_transform: Optional[np.ndarray] = None,
    min_inliers: int = 20,
) -> ICPResult:
    """
    Point-to-point ICP registration using pure NumPy and SciPy cKDTree.

    Args:
        source_points: (M, 3) point cloud to align (moving scan).
        target_points: (N, 3) reference point cloud (fixed scan).
        max_correspondence_distance: Maximum distance in meters to accept a point correspondence.
        max_iterations: Maximum number of alignment iterations.
        tolerance: Minimum translation change norm in meters to declare convergence.
        initial_transform: Optional 4x4 initial guess matrix.
        min_inliers: Minimum matched points required to proceed with registration.

    Returns:
        ICPResult with estimated 4x4 transformation and quality diagnostics.
    """
    identity_4x4 = np.eye(4, dtype=np.float64)

    if len(source_points) < min_inliers or len(target_points) < min_inliers:
        return ICPResult(
            success=False,
            transformation=identity_4x4,
            rotation=np.eye(3, dtype=np.float64),
            translation=np.zeros(3, dtype=np.float64),
            fitness_score=float("inf"),
            inlier_ratio=0.0,
            num_inliers=0,
            iterations=0,
            status="INSUFFICIENT_POINTS",
        )

    # Initialize current transformation
    current_t = identity_4x4.copy() if initial_transform is None else initial_transform.copy().astype(np.float64)
    r_accum = current_t[:3, :3]
    t_accum = current_t[:3, 3]

    # Build k-d tree on static target points once
    target_tree = cKDTree(target_points)

    num_source = len(source_points)
    src_pts = source_points.copy().astype(np.float64)

    prev_error = float("inf")
    converged = False
    iterations_run = 0
    final_inliers = 0
    final_error = float("inf")

    for it in range(max_iterations):
        iterations_run = it + 1

        # Transform source points with current accumulated pose
        transformed_src = (r_accum @ src_pts.T).T + t_accum

        # Query nearest neighbors in target
        distances, indices = target_tree.query(transformed_src, k=1, workers=1)

        # Inlier filtering
        inlier_mask = distances <= max_correspondence_distance
        num_inliers = int(np.sum(inlier_mask))
        final_inliers = num_inliers

        if num_inliers < min_inliers:
            return ICPResult(
                success=False,
                transformation=current_t,
                rotation=r_accum,
                translation=t_accum,
                fitness_score=float("inf"),
                inlier_ratio=num_inliers / num_source,
                num_inliers=num_inliers,
                iterations=iterations_run,
                status="DEGENERATE_MATCHES_UNDER_THRESHOLD",
            )

        matched_src = transformed_src[inlier_mask]
        matched_tgt = target_points[indices[inlier_mask]]

        # Compute incremental step
        delta_r, delta_t = compute_best_rigid_transform(matched_src, matched_tgt)

        # Update accumulated transformation: T_new = delta_T * T_curr
        r_accum = delta_r @ r_accum
        t_accum = delta_r @ t_accum + delta_t
        current_t[:3, :3] = r_accum
        current_t[:3, 3] = t_accum

        mean_error = float(np.mean(distances[inlier_mask]))
        final_error = mean_error

        # Check convergence
        trans_delta_norm = float(np.linalg.norm(delta_t))
        if trans_delta_norm < tolerance or abs(prev_error - mean_error) < tolerance:
            converged = True
            break

        prev_error = mean_error

    status_str = "CONVERGED" if converged else "MAX_ITERATIONS"
    inlier_ratio = final_inliers / max(num_source, 1)

    return ICPResult(
        success=True,
        transformation=current_t,
        rotation=r_accum,
        translation=t_accum,
        fitness_score=final_error,
        inlier_ratio=inlier_ratio,
        num_inliers=final_inliers,
        iterations=iterations_run,
        status=status_str,
    )


class ICPOdometry:
    """
    Sequential LiDAR scan-to-scan odometry pipeline.
    Accumulates relative 3D pose transformations over time.
    """

    def __init__(
        self,
        voxel_size: float = 0.15,
        min_range: float = 0.5,
        max_range: float = 50.0,
        max_correspondence_distance: float = 1.5,
        max_iterations: int = 30,
        tolerance: float = 1e-4,
    ):
        self.voxel_size = voxel_size
        self.min_range = min_range
        self.max_range = max_range
        self.max_correspondence_distance = max_correspondence_distance
        self.max_iterations = max_iterations
        self.tolerance = tolerance

        # State
        self.current_pose = np.eye(4, dtype=np.float64)
        self.previous_points: Optional[np.ndarray] = None
        self.step_history: List[OdometryStepResult] = []
        self.successful_steps = 0
        self.failed_steps = 0

    def preprocess_points(self, raw_points: np.ndarray) -> np.ndarray:
        """Filters non-finite points, bounds ranges, and applies voxel downsampling."""
        clean_pts, _ = remove_invalid_points(raw_points)
        if len(clean_pts) == 0:
            return clean_pts
        range_pts, _ = filter_by_range(clean_pts, min_range=self.min_range, max_range=self.max_range)
        if len(range_pts) == 0 or self.voxel_size <= 0:
            return range_pts
        downsampled, _ = voxel_downsample(range_pts, voxel_size=self.voxel_size)
        return downsampled

    def process_frame(
        self,
        raw_points: np.ndarray,
        frame_index: int,
        timestamp: Optional[float] = None,
    ) -> OdometryStepResult:
        """
        Processes one incoming point cloud frame and updates vehicle state.
        """
        raw_count = len(raw_points)
        t_start = time.perf_counter()

        # Preprocessing
        pts = self.preprocess_points(raw_points)
        downsampled_count = len(pts)

        # Initial frame
        if self.previous_points is None or len(self.step_history) == 0:
            self.previous_points = pts
            latency_ms = (time.perf_counter() - t_start) * 1000.0
            res = OdometryStepResult(
                frame_index=frame_index,
                timestamp=timestamp,
                success=True,
                pose_4x4=self.current_pose.copy(),
                position_xyz=self.current_pose[:3, 3].copy(),
                step_translation_m=0.0,
                registration_latency_ms=latency_ms,
                raw_points_count=raw_count,
                downsampled_points_count=downsampled_count,
                fitness_score=0.0,
                inlier_ratio=1.0,
                status="INITIAL_FRAME",
            )
            self.step_history.append(res)
            self.successful_steps += 1
            return res

        # Register current frame (source) against previous frame (target)
        icp_res = icp_point_to_point(
            source_points=pts,
            target_points=self.previous_points,
            max_correspondence_distance=self.max_correspondence_distance,
            max_iterations=self.max_iterations,
            tolerance=self.tolerance,
        )

        step_dist = 0.0
        if icp_res.success:
            # Relative motion: T_{prev}^{curr}.
            # Update global pose: T_{world}^{curr} = T_{world}^{prev} * inv(T_{prev}^{curr})
            rel_transform = icp_res.transformation
            try:
                rel_inv = np.linalg.inv(rel_transform)
            except np.linalg.LinAlgError:
                rel_inv = np.eye(4)

            step_dist = float(np.linalg.norm(rel_inv[:3, 3]))
            self.current_pose = self.current_pose @ rel_inv
            self.previous_points = pts
            self.successful_steps += 1
        else:
            self.failed_steps += 1

        latency_ms = (time.perf_counter() - t_start) * 1000.0

        step_res = OdometryStepResult(
            frame_index=frame_index,
            timestamp=timestamp,
            success=icp_res.success,
            pose_4x4=self.current_pose.copy(),
            position_xyz=self.current_pose[:3, 3].copy(),
            step_translation_m=step_dist,
            registration_latency_ms=latency_ms,
            raw_points_count=raw_count,
            downsampled_points_count=downsampled_count,
            fitness_score=icp_res.fitness_score,
            inlier_ratio=icp_res.inlier_ratio,
            status=icp_res.status,
        )
        self.step_history.append(step_res)
        return step_res

    def get_trajectory_positions(self) -> np.ndarray:
        """Returns (K, 3) array of estimated positions in meters."""
        if not self.step_history:
            return np.zeros((0, 3), dtype=np.float64)
        return np.array([s.position_xyz for s in self.step_history], dtype=np.float64)

    def get_total_path_length_m(self) -> float:
        """Returns total integrated distance traveled in meters."""
        return float(sum(s.step_translation_m for s in self.step_history))

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Calculates aggregate odometry metrics."""
        latencies = [s.registration_latency_ms for s in self.step_history]
        total_frames = len(self.step_history)
        path_length = self.get_total_path_length_m()

        lat_mean = float(np.mean(latencies)) if latencies else 0.0
        lat_median = float(np.median(latencies)) if latencies else 0.0
        lat_p95 = float(np.percentile(latencies, 95)) if latencies else 0.0

        return {
            "total_frames_processed": total_frames,
            "successful_registrations": self.successful_steps,
            "failed_registrations": self.failed_steps,
            "success_rate_percent": round((self.successful_steps / max(total_frames, 1)) * 100.0, 1),
            "total_path_length_m": round(path_length, 3),
            "final_position_xyz": [round(c, 3) for c in (self.current_pose[:3, 3].tolist())],
            "latency_mean_ms": round(lat_mean, 2),
            "latency_median_ms": round(lat_median, 2),
            "latency_p95_ms": round(lat_p95, 2),
        }
