"""Selección de archivo y resultados en español."""

import argparse
import sys
from collections.abc import Callable, Iterable, Sequence
from contextlib import AbstractContextManager

from log_analyzer.application.analyze_logs import analyze_logs
from log_analyzer.domain.models import AnalysisSummary
from log_analyzer.presentation.file_selector import FileSelectionError

Reader = Callable[[str], AbstractContextManager[Iterable[str]]]


def format_summary(summary: AnalysisSummary) -> str:
    rows = []
    if summary.total_events == 0:
        rows.append("No hay eventos para analizar: el archivo está vacío o solo contiene líneas vacías.")
    rows.extend([
        "Resumen del análisis",
        f"Total de eventos: {summary.total_events}",
        f"INFO: {summary.info}",
        f"WARNING: {summary.warning}",
        f"ERROR: {summary.error}",
        f"Nivel desconocido o ausente: {summary.unknown_level}",
        f"Eventos válidos: {summary.valid_events}",
        f"Líneas mal formateadas o incompletas: {summary.malformed_lines}",
        f"Errores de fecha: {summary.date_errors}",
        f"Errores de estructura: {summary.structure_errors}",
        "Los errores de fecha y estructura pueden solaparse en una misma línea.",
    ])
    return "\n".join(rows)


def run(
    reader: Reader,
    argv: Sequence[str] | None = None,
    *,
    select_file: Callable[[], str | None],
) -> int:
    parser = argparse.ArgumentParser(
        description="Analiza un archivo de logs UTF-8. Sin ruta, abre un selector de archivos."
    )
    parser.add_argument("path", nargs="?", help="ruta del archivo (opcional; sin ella se abre el selector)")
    args = parser.parse_args(argv)
    try:
        path = args.path if args.path is not None else select_file()
        if path is None or (args.path is None and path == ""):
            print("Selección cancelada", file=sys.stderr)
            return 1
        if not path.strip():
            print("Error: debe indicar una ruta de archivo.", file=sys.stderr)
            return 1
        with reader(path) as lines:
            summary = analyze_logs(lines)
    except FileSelectionError as exc:
        message = f"{exc} Ejecute: python -m log_analyzer ruta_del_archivo."
    except FileNotFoundError:
        message = "El archivo indicado no existe."
    except PermissionError:
        message = "No tiene permisos para leer el archivo."
    except IsADirectoryError:
        message = "La ruta corresponde a un directorio; indique un archivo."
    except UnicodeError:
        message = "El archivo no contiene texto UTF-8 válido."
    except (OSError, ValueError):
        message = "No se pudo leer el archivo; compruebe la ruta y su disponibilidad."
    except (KeyboardInterrupt, EOFError):
        message = "Operación cancelada."
    else:
        print(format_summary(summary))
        return 0
    print(f"Error: {message} El análisis no se completó.", file=sys.stderr)
    return 1
