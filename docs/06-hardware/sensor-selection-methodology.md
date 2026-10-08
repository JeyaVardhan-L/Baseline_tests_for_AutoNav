# Sensor Selection Methodology

## 1. Principles of Sensor Evaluation

The sensor suite dictates both what the UAV can see and how much physical load it must carry.

---

## 2. Trade-Off Dimensions

1. **Mass vs. Range**:
   - Long-range 100m automotive LiDARs weigh 800g to 1200g; lightweight solid-state UAV LiDARs weigh 150g to 300g with 30m range.
2. **Field-of-View (FoV)**:
   - For vertical collision avoidance (e.g. descending under pipes or climbing through stairwells), wide vertical FoV (e.g. $90^\circ$ dome or omnidirectional) is vastly superior to narrow horizontal automotive slits ($15^\circ$ to $30^\circ$).
3. **Power Draw (Watts)**:
   - Every additional Watt drawn by sensors reduces flight endurance by seconds.
4. **Lighting Resilience**:
   - Active LiDAR operates identically in pitch darkness and bright midday sunlight; optical stereo cameras degrade in darkness and featureless textureless environments.
