# Standard Experiment Documentation Template

Every experiment in this repository must strictly adhere to the following 18-section structure:

---

```markdown
# Experiment XX: Title

## 1. Objective
Clear statement of what is being measured or evaluated.

## 2. Why This Matters
Explanation of why an autonomous UAV cannot operate without understanding this phenomenon.

## 3. Required Knowledge
Mathematical and robotic concepts required to understand the results.

## 4. Dataset
Which datasets are supported (Newer College, Hilti, OpenLORIS, TUM RGB-D, Synthetic).

## 5. Input
Specific input data formats and structures.

## 6. Output
Generated files, plots, CSV metrics, and JSON summaries.

## 7. Parameters
All configurable arguments with units and default values.

## 8. Method
Step-by-step scientific procedure.

## 9. Equations
Explicit mathematical formulas used to derive every calculated number.

## 10. Command
Exact reproducible terminal command to run.

## 11. Expected Terminal Output
Literal text output demonstrating what the user should expect.

## 12. Live Visualization
Description of interactive GUI or terminal progress displays.

## 13. Graphs
List of generated plots and the specific engineering question each answers.

## 14. Metrics
Table classifying all output values: `[MEASURED]`, `[DERIVED]`, `[ASSUMED]`, or `[ESTIMATED]`.

## 15. Interpretation
How to read the results and diagnose bottlenecks.

## 16. Limitations
What the experiment does NOT tell us.

## 17. Reproducibility Information
Random seeds, operating system, hardware specs captured in metadata.

## 18. What Decision This Experiment Can Inform
The exact engineering trade-off or payload parameter this evidence informs.
```
