"""Selector visual opcional; Tkinter solo se carga cuando se necesita."""


class FileSelectionError(Exception):
    """No es posible abrir o utilizar el selector gráfico."""


def select_log_file() -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:
        raise FileSelectionError("Tkinter no está disponible.") from exc

    try:
        root = tk.Tk()
        try:
            root.withdraw()
            return filedialog.askopenfilename(
                parent=root,
                title="Seleccionar archivo de logs",
                filetypes=[("Todos los archivos", "*")],
                multiple=False,
            ) or None
        finally:
            root.destroy()
    except tk.TclError as exc:
        raise FileSelectionError("No se pudo abrir el selector gráfico.") from exc
