"""Lectura UTF-8 estricta con cierre garantizado."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import TextIO


@contextmanager
def open_log_file(path: str) -> Iterator[TextIO]:
    with open(path, encoding="utf-8-sig", errors="strict") as stream:
        yield stream
