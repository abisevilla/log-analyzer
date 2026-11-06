"""Conexión de adaptadores y punto de entrada del paquete."""

from log_analyzer.infrastructure.file_reader import open_log_file
from log_analyzer.presentation.cli import run
from log_analyzer.presentation.file_selector import select_log_file

if __name__ == "__main__":
    raise SystemExit(run(open_log_file, select_file=select_log_file))
