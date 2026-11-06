"""Acumulación incremental de resultados."""

from collections.abc import Iterable

from log_analyzer.domain.models import AnalysisSummary
from log_analyzer.domain.parser import parse_line


def analyze_logs(lines: Iterable[str]) -> AnalysisSummary:
    summary = AnalysisSummary()
    for line in lines:
        result = parse_line(line)
        if result is None:
            continue
        summary.total_events += 1
        if result.level == "INFO":
            summary.info += 1
        elif result.level == "WARNING":
            summary.warning += 1
        elif result.level == "ERROR":
            summary.error += 1
        else:
            summary.unknown_level += 1
        summary.date_errors += result.date_error
        summary.structure_errors += result.structure_error
        if result.is_valid:
            summary.valid_events += 1
        else:
            summary.malformed_lines += 1
    return summary
