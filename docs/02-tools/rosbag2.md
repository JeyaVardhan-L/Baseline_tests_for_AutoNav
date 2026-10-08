# rosbag2: Recording and Replaying Robot Data

## Why Does rosbag2 Exist?

When developing an autonomous UAV, you cannot test new localization algorithms by flying an untested drone outdoors every time you change a line of code. If your algorithm has a bug, the drone crashes into the ground.

**rosbag2** is the recording and playback mechanism in ROS 2. It records every message published on specified topics into a high-performance SQLite or MCAP database on disk, complete with exact microsecond timestamps.

Later, sitting at your desk, you can "replay" the bag file: the recorded sensor messages are re-published in software with identical timing, tricking your navigation code into believing it is flying on a real drone in real time.

---

## 1. Useful rosbag2 Commands

### Inspecting a Bag File
```bash
ros2 bag info <path_to_bag_folder>
```
Displays:
- Recording duration
- Total message count
- List of topics and their message types
- Average publishing frequency

### Replaying a Bag File
```bash
ros2 bag play <path_to_bag_folder> --rate 1.0
```
- `--rate 1.0`: Real-time 1x playback speed.
- `--rate 0.5`: Half-speed (useful for running compute-heavy debugging pipelines).
- `--rate 2.0`: Double-speed replay.
