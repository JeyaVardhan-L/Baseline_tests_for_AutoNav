# Concept: CPU Load and Thermal Throttling

**CPU Load** represents the percentage of central processing unit core time consumed by active instructions.

---

## 1. Single-Core vs. Multi-Core Utilization

Modern processors have multiple physical cores (e.g. 4, 8, or 12 cores):
- **Single-Core Bound**: If a filter algorithm is written sequentially in Python or C++ on 1 core, it can only reach a maximum of $100\%$ of that single core (which displays as $12.5\%$ total utilization on an 8-core CPU). If that single core is pegged at $100\%$, the pipeline drops frames even though 7 other cores are completely idle!
- **Multi-Threaded**: Distributing voxel grid calculation across multiple worker threads (e.g. via OpenMP or ThreadPool).

---

## 2. The Danger of Thermal Throttling on a UAV

On an enclosed UAV chassis without active cooling fans, running all CPU cores at $100\%$ causes die temperature to rapidly exceed $85^\circ\text{C}$.

When this happens, the operating system's CPU governor activates **thermal throttling**, dropping clock frequencies from $2.4\text{ GHz}$ down to $1.1\text{ GHz}$ to prevent physical silicon damage. Suddenly, an algorithm that took $70\text{ ms}$ now takes $150\text{ ms}$, crashing the real-time deadline.
