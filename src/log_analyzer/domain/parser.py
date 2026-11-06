"""Análisis puro de una línea, sin recuperación de campos desordenados."""

import re
from datetime import date

from .models import LineResult, Severity

LEVELS: dict[str, Severity] = {
    "[INFO]": "INFO", "[WARNING]": "WARNING", "[ERROR]": "ERROR"
}
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def parse_line(line: str) -> LineResult | None:
    text = line.strip()
    if not text:
        return None
    fields = re.split(r"[ \t]+", text, maxsplit=2)
    level = LEVELS.get(fields[0])
    date_field = fields[1] if len(fields) > 1 else ""
    message = fields[2] if len(fields) > 2 else ""
    date_attempt = bool(date_field) and date_field[0] in "0123456789"
    date_error = True
    if date_attempt and DATE_PATTERN.fullmatch(date_field):
        try:
            date.fromisoformat(date_field)
            date_error = False
        except ValueError:
            pass
    structure_error = level is None or not date_attempt or not message.strip()
    return LineResult(level, date_error, structure_error, message)
