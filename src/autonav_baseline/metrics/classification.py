"""
Metric classification system.

Every value presented in autonav_baseline must be clearly identified with
one of the six non-negotiable scientific evidence categories:
  - MEASURED: Obtained directly from the actual dataset or host runtime.
  - DERIVED: Calculated from measured data using a documented formula.
  - DECLARED: Stated in authoritative dataset documentation or sensor datasheets.
  - ASSUMED: An explicit parameter or nominal assumption used for comparison.
  - UNAVAILABLE: The information cannot currently be obtained.
  - UNVERIFIED: The measurement or implementation has not been validated sufficiently.
"""

from enum import Enum
from typing import Any, Dict


class Classification(str, Enum):
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    DECLARED = "DECLARED"
    ASSUMED = "ASSUMED"
    UNAVAILABLE = "UNAVAILABLE"
    UNVERIFIED = "UNVERIFIED"
    ESTIMATED = "ESTIMATED"  # Legacy compatibility alias

    def __str__(self) -> str:
        return self.value


def tag(value: Any, classification: Classification, unit: str = "", note: str = "") -> Dict[str, Any]:
    """Wraps a numerical value with an explicit classification tag, unit, and note."""
    return {
        "value": value,
        "classification": classification.value,
        "unit": unit,
        "note": note,
    }
