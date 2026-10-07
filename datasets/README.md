# Datasets

## Purpose

This directory contains documentation and instructions for datasets used in experiments. **Raw dataset files are NOT stored in Git** due to their size.

## How to Use Datasets

1. Check [`dataset-registry.md`](dataset-registry.md) for available datasets
2. Download the dataset from the official source
3. Place it in the expected directory structure (see instructions per dataset)
4. Run the experiment — scripts will verify dataset availability before proceeding

## Directory Structure

```
datasets/
├── README.md                  # This file
├── dataset-registry.md        # Registry of all evaluated datasets
└── (dataset files are NOT committed to Git)
```

## Important Rules

1. **Never commit raw dataset files to Git** — they are too large
2. **Never modify original downloaded files** — use `raw/` and `processed/` separation
3. **Always document** the exact version, URL, and expected structure
4. **Record checksums** where practical for reproducibility
5. **Use `.gitignore`** to prevent accidental commits

## Downloading Datasets

Each experiment's README contains specific download instructions for the datasets it uses.
