# Troubleshooting Guide: ROS 2 and Bag Files

## 1. ROS 1 vs. ROS 2 Bag Compatibility

### Symptom:
`ros2 bag info` fails with `Unknown file format` when opening a `.bag` file from Newer College or OpenLORIS.

### Cause:
Earlier datasets were recorded in **ROS 1 format (`.bag`)**. ROS 2 uses **SQLite3 or MCAP directories (`metadata.yaml`)**.

### Solution:
Install the pure-Python `rosbags` library to read or convert bags on Windows without needing ROS installed:
```bash
pip install rosbags

# Convert ROS 1 bag to ROS 2 bag format:
rosbags-convert input.bag --dst output_ros2_bag/
```

---

## 2. Reading Bags Without Installing ROS

In this repository, the dataset adapters are designed to read standard binary dumps, CSVs, and PNG directories directly so you **do not need a full ROS 2 desktop installation** to run the first learning path.
