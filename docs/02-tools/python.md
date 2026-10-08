# Python in Autonomous Robotics

## Why Does Python Exist in This Project?

**Python** is the primary high-level language used in this repository for the experimental research framework, data ingestion adapters, timing instrumentation, and rapid prototyping.

---

## 1. Role in the Engineering Workflow

1. **Experiment Framework**: Orchestrating reproducible runs, passing configuration files (YAML), parsing arguments, and managing directories.
2. **Data Pipeline Prototyping**: Reading raw binary files, inspecting headers, validating timestamps, and computing metrics before committing algorithms to real-time C++.
3. **Hardware-Agnostic Execution**: Works uniformly on Windows development laptops, Linux workstations, and embedded ARM companion computers.

---

## 2. Python vs. C++ in UAV Flight

- **Python**: Excellent for offline analysis, data characterization, visualization, and rapid experimentation.
- **C++**: Used in subsequent phases for real-time onboard flight autonomy (SLAM, trajectory generation, and microsecond sensor drivers) due to deterministic memory management and zero garbage-collection latency.

By building our baseline experiments in clean, pure Python with NumPy acceleration, anyone can run the experiments with zero compilation steps.
