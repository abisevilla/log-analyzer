"""Resultados de validación y contadores del análisis."""

from dataclasses import dataclass
from typing import Literal

Severity = Literal["INFO", "WARNING", "ERROR"]


@dataclass(frozen=True, slots=True)
class LineResult:
    level: Severity | None
    date_error: bool
    structure_error: bool
    message: str = ""

    @property
    def is_valid(self) -> bool:
        return not (self.date_error or self.structure_error)


@dataclass(slots=True)
class AnalysisSummary:
    total_events: int = 0
    info: int = 0
    warning: int = 0
    error: int = 0
    unknown_level: int = 0
    valid_events: int = 0
    malformed_lines: int = 0
    date_errors: int = 0
    structure_errors: int = 0
