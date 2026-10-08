#!/usr/bin/env python3
"""
Experiment 10 — Preparing for Navigation (Architecture & Data Flow)
Educational and conceptual verification of the autonomous navigation pipeline:
  Sensor Data -> State Estimation -> Mapping -> Localization -> Planning -> Flight Control

Strictly enforces the architectural separation between:
  1. HIGH LEVEL: Mission Control ("Search this area", "Survey waypoint zone")
  2. AUTONOMOUS NAVIGATION: State estimation, local representation, free space, path selection
  3. LOW LEVEL FLIGHT CONTROL: Attitude, angular rates, motor outputs (PX4/ArduPilot autopilot)

Generates conceptual architecture diagrams and interface data contract specifications.
"""

import argparse
import sys
import time
from pathlib import Path
import numpy as np

# Add src to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from autonav_baseline.visualization.terminal import print_banner, print_section, print_field
from autonav_baseline.visualization.plots import save_plot
from autonav_baseline.reporting.exporter import ExperimentExporter


def main():
    parser = argparse.ArgumentParser(description="EXP-10: Preparing for Navigation Architecture")
    parser.add_argument("--verify-contracts", action="store_true", default=True, help="Verify data interface contracts")
    args = parser.parse_args()

    print_banner("EXPERIMENT 10 - PREPARING FOR NAVIGATION", "Conceptual Architecture & Interface Contracts")

    print_section("THREE-TIER SYSTEM ARCHITECTURE BOUNDARIES")
    print("""
    +------------------------------------------------------------------------+
    | 1. HIGH-LEVEL MISSION CONTROL (Ground Station / Mission Supervisor)     |
    |    "Search this designated 50m x 50m sector at 10m altitude"            |
    |    Outputs: Target Region, Search Pattern, High-level Objectives       |
    +------------------------------------------------------------------------+
                                      |
                                      v
    +------------------------------------------------------------------------+
    | 2. AUTONOMOUS NAVIGATION (Onboard Companion Computer / GPU)             |
    |    - Sensor Ingestion & Timestamp Synchronization                      |
    |    - State Estimation: Fused Pose (x, y, z, roll, pitch, yaw) & Vels  |
    |    - Local Mapping: 3D Voxel Grid / 2.5D Elevation Costmap             |
    |    - Free-Space Identification: Obstacle detection & safety margins    |
    |    - Path Planning: 3D collision-free trajectory generation            |
    |    - Path Tracking: Closed-loop guidance setpoints                     |
    |    Outputs: Target Position / Velocity / Yaw Rate Setpoints (e.g. 20Hz)|
    +------------------------------------------------------------------------+
                                      | (MAVLink / microXRCE-DDS)
                                      v
    +------------------------------------------------------------------------+
    | 3. LOW-LEVEL FLIGHT CONTROL (Autopilot: PX4 / ArduPilot / Micro)       |
    |    - Fast Inner Feedback Loops (250 - 1000 Hz)                         |
    |    - Attitude Control (Roll, Pitch, Yaw stabilization)                 |
    |    - Angular Rate Control (p, q, r PID loops)                          |
    |    - Motor Mixer & PWM / DShot ESC Signals                             |
    |    Maintains aerodynamic stability regardless of high-level state      |
    +------------------------------------------------------------------------+
    """)

    print_section("DATA FLOW TRANSFORMATIONS")
    transformations = [
        ("Raw Sensor Telemetry", "Points, Pixels, Accel, Gyro (Unprocessed)"),
        ("State Estimation (SLAM / EKF)", "6-DoF Pose [x, y, z, q] + Velocity [vx, vy, vz]"),
        ("Local Representation (Mapping)", "3D Volumetric Voxel Map / Point Octree"),
        ("Free Space Analysis", "Distance field & traversability costmap"),
        ("Motion Planning", "Kinodynamically feasible collision-free spline path"),
        ("Guidance Controller", "Setpoint commands: Position (x,y,z), Velocity, Yaw"),
        ("Autopilot Flight Controller", "Inner-loop motor thrust and torque commands"),
    ]

    for idx, (stage, desc) in enumerate(transformations, start=1):
        print(f"  Step {idx}: {stage:<32} -> {desc}")
    print("=" * 60)

    # Exporter
    exporter = ExperimentExporter("conceptual", "10_sensor_fusion_preparation")

    # Generate Architecture Block Diagram
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Tier 1 Box
    t1 = patches.FancyBboxPatch((0.5, 7.8), 9.0, 1.6, boxstyle="round,pad=0.2",
                                facecolor="#E3F2FD", edgecolor="#1565C0", linewidth=1.5)
    ax.add_patch(t1)
    ax.text(5.0, 8.8, "TIER 1: HIGH-LEVEL MISSION CONTROL", ha="center", va="center", fontsize=11, fontweight="bold", color="#0D47A1")
    ax.text(5.0, 8.2, "Responsible for: Strategic Objectives, Waypoint Sectors, Geofencing, User Command\n\"Search area A at 5m/s while maintaining safety perimeter\"",
            ha="center", va="center", fontsize=9, color="#1A237E")

    # Arrow 1->2
    ax.annotate("", xy=(5.0, 7.3), xytext=(5.0, 7.7),
                arrowprops=dict(arrowstyle="->", lw=2, color="#1565C0"))

    # Tier 2 Box
    t2 = patches.FancyBboxPatch((0.5, 3.4), 9.0, 3.7, boxstyle="round,pad=0.2",
                                facecolor="#E8F5E9", edgecolor="#2E7D32", linewidth=1.5)
    ax.add_patch(t2)
    ax.text(5.0, 6.7, "TIER 2: AUTONOMOUS NAVIGATION (Companion Computer / GPU)", ha="center", va="center", fontsize=11, fontweight="bold", color="#1B5E20")
    ax.text(5.0, 5.2, "Sensor Ingestion (LiDAR 10Hz, Camera 30Hz, IMU 200Hz)\n"
                      "   ↓\n"
                      "State Estimation (Odometry, EKF Pose Estimation)\n"
                      "   ↓\n"
                      "Local Mapping (Voxel Grid, Occupancy Field, Free-Space)\n"
                      "   ↓\n"
                      "Trajectory Planning (3D Spline Path, Obstacle Clearance)\n"
                      "   ↓\n"
                      "Trajectory Tracking (Position / Velocity / Yaw Setpoints)",
            ha="center", va="center", fontsize=8.5, color="#2E7D32")

    # Arrow 2->3
    ax.annotate("", xy=(5.0, 2.9), xytext=(5.0, 3.3),
                arrowprops=dict(arrowstyle="->", lw=2, color="#2E7D32"))
    ax.text(5.5, 3.1, "MAVLink Setpoints (10 - 50 Hz)", fontsize=8, color="#37474F", style="italic")

    # Tier 3 Box
    t3 = patches.FancyBboxPatch((0.5, 0.5), 9.0, 2.2, boxstyle="round,pad=0.2",
                                facecolor="#FFF3E0", edgecolor="#E65100", linewidth=1.5)
    ax.add_patch(t3)
    ax.text(5.0, 2.2, "TIER 3: LOW-LEVEL FLIGHT CONTROL (Autopilot: PX4 / ArduPilot)", ha="center", va="center", fontsize=11, fontweight="bold", color="#BF360C")
    ax.text(5.0, 1.2, "Responsible for: Inner-Loop Stabilization (250 - 1000 Hz)\n"
                      "Attitude Control (Roll, Pitch, Yaw) | Rate Dampers (p, q, r PID)\n"
                      "Motor ESC PWM / DShot Mixing | Emergency Failsafe Recovery",
            ha="center", va="center", fontsize=8.5, color="#E65100")

    save_plot(fig, exporter.figures_dir / "navigation_architecture_hierarchy.png")

    exporter.export_json({
        "architecture_layers": [
            {"tier": 1, "name": "Mission Control", "function": "Strategic objectives and search zone delegation"},
            {"tier": 2, "name": "Autonomous Navigation", "function": "State estimation, mapping, obstacle avoidance, trajectory planning"},
            {"tier": 3, "name": "Flight Controller", "function": "Fast inner-loop aerodynamic attitude and motor thrust control"},
        ],
        "interface_contract": {
            "tier2_to_tier3_protocol": "MAVLink / microXRCE-DDS",
            "message_types": ["SET_POSITION_TARGET_LOCAL_NED", "ATTITUDE_TARGET"],
            "expected_frequency_hz": "10 - 50 Hz",
        }
    })

    exporter.write_summary_md(
        title="EXP-10: Navigation Architecture & Data Flow Preparation",
        metrics_dict={
            "Tier 1 Function": "High-Level Strategic Mission Control [SPECIFIED]",
            "Tier 2 Function": "Autonomous Navigation & Trajectory Generation [SPECIFIED]",
            "Tier 3 Function": "Low-Level Flight Stabilization & Motor Mixing [SPECIFIED]",
            "Companion-to-Autopilot Interface": "MAVLink NED Setpoints (10-50 Hz) [SPECIFIED]",
            "Flight Controller Loop Rate": "250 - 1000 Hz [SPECIFIED]",
        },
        conclusions=[
            "Strict architectural boundary separates autonomous navigation (Tier 2) from attitude control (Tier 3).",
            "The flight controller remains unconditionally responsible for aerodynamic stabilization, failsafes, and motor mixing.",
            "The autonomous navigation computer provides target position, velocity, and yaw rate setpoints without bypassing inner-loop rate dampers.",
        ]
    )
    print(f"\n[DONE] Results and architecture diagram saved to {exporter.experiment_dir}")


if __name__ == "__main__":
    main()
