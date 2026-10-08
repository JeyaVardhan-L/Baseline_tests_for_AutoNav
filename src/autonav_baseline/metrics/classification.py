"""
Metric classification system.

Every value presented in autonav_baseline must be clearly identified with
one of the following scientific categories:
  - MEASURED: An empirical value directly measured by an instrument or timer.
  - DERIVED: A mathematical calculation computed from measured values.
  - ASSUMED: A nominal specification or working hypothesis taken from datasheets.
  - ESTIMATED: An approximation with modeled uncertainty.
"""

from enum import Enum
from typing import Any, Dict


class Classification(str, Enum):
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    ASSUMED = "ASSUMED"
    ESTIMATED = "ESTIMATED"

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
