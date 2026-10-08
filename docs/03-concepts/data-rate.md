# Concept: Data Rate

**Data Rate** is the amount of digital information generated or processed per unit time.

---

## 1. Governing Equation

$$\text{Data Rate} = \text{Average Frame Size (bytes)} \times \text{Frame Rate (Hz)}$$

---

## 2. Numerical Example

- Average LiDAR frame size: **$1.6 \text{ MB}$** ($1,600,000 \text{ bytes}$).
- Measured sensor frame rate: **$10.0 \text{ Hz}$** ($10 \text{ frames/second}$).

### Calculation:
$$\text{Data Rate} = 1.6 \text{ MB} \times 10.0 \text{ s}^{-1} = 16.0 \text{ MB/s} \text{ [DERIVED]}$$

### Storage Accumulation:
- In 1 minute ($60 \text{ s}$): $16.0 \text{ MB/s} \times 60 = 960 \text{ MB} \approx 0.96 \text{ GB}$.
- In 1 hour ($3600 \text{ s}$): $16.0 \text{ MB/s} \times 3600 = 57,600 \text{ MB} = 57.6 \text{ GB}$.

### Crucial Engineering Insight
A standard Class 10 SD card writes at $10\text{ MB/s}$ to $15\text{ MB/s}$. An uncompressed 10 Hz LiDAR stream exceeds the card's maximum write speed, causing buffer overflow and crashed processes unless filtered or downsampled.
