# Configuration Files

## Purpose

Shared configuration files used across multiple experiments or system components.

## Convention

- Use YAML format for configuration
- Use relative paths (configurable via environment variables or command-line arguments)
- Never hardcode machine-specific paths

## Status

Experiment-specific configs are in `experiments/*/config/`. Shared configs will be added here as needed.
