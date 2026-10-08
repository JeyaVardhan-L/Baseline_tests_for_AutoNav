# Concept: Real-Time Systems in Autonomous Flight

## Hard vs. Soft Real-Time

In computer science, real-time systems are categorized by the consequence of missing a deadline:

1. **Hard Real-Time**: Missing a single deadline causes total system failure or catastrophic physical damage.
   - *Example*: The quadcopter flight controller attitude stabilization loop ($500\text{ Hz}$). If motor PWM updates are delayed by 20 ms, the drone flips upside down and crashes.
2. **Soft Real-Time**: Missing an occasional deadline degrades performance or increases latency, but does not immediately cause catastrophic failure.
   - *Example*: High-level global path planner ($1\text{ Hz}$). If an obstacle replanning query takes 1.2 seconds instead of 1.0 second, the drone can temporarily slow down or hold position while waiting for the new path.

The boundary between Hard Real-Time (Autopilot) and Soft Real-Time (Companion Computer Autonomy Stack) is the fundamental architectural dividing line in UAV avionics.
