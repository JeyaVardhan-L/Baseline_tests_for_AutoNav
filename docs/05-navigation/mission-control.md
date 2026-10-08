# Mission Control vs. Autonomous Navigation

## The Fundamental Boundary: Separation of Concerns

A common architectural failure in amateur robotics projects is mixing strategic mission logic with local collision avoidance.

---

## 1. High-Level Mission Control (Strategic Level)

- **Answers**: *"WHAT should the robot accomplish?"*
- **Examples**:
  - "Take off and climb to 5 meters."
  - "Search the 50m x 50m sector using a boustrophedon (lawnmower) pattern."
  - "If battery falls below 20%, abort mission and return to home."
- **Executes**: On the Ground Control Station (GCS) or as a high-level Python/Behavior Tree state machine on the companion computer.

---

## 2. Autonomous Navigation (Tactical Autonomy Level)

- **Answers**: *"HOW does the robot get there without hitting anything?"*
- **Examples**:
  - "There is a concrete column 3 meters ahead; steer 40 degrees left."
  - "The hallway ceiling is low; maintain 1.2 meters clearance from the roof."
- **Executes**: On the onboard companion computer in a tight real-time loop.

---

## 3. Low-Level Flight Control (Aerodynamic Stabilization Level)

- **Answers**: *"HOW do the motors spin to keep the vehicle balanced?"*
- **Examples**:
  - "Wind gust induced a 10 deg/s roll rate; increase motor 1 and 2 RPM."
- **Executes**: On the dedicated real-time microcontroller (e.g. PX4 autopilot at 500 Hz).
- **Rule**: The autonomous navigation stack **never bypasses the flight controller's attitude loops**.
