import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch

from log_analyzer.presentation.cli import run
from log_analyzer.presentation.file_selector import FileSelectionError, select_log_file


class FakeTclError(Exception):
    pass


class FileSelectorTests(unittest.TestCase):
    def modules(self):
        tk = Mock()
        tk.TclError = FakeTclError
        return tk, {'tkinter': tk, 'tkinter.filedialog': tk.filedialog}

    def test_selection_cancellation_and_cleanup(self):
        for selection in ('/tmp/José 😊 registros', ''):
            with self.subTest(selection=selection):
                tk, modules = self.modules()
                tk.filedialog.askopenfilename.return_value = selection
                with patch.dict(sys.modules, modules):
                    self.assertEqual(select_log_file(), selection or None)
                tk.Tk.return_value.withdraw.assert_called_once_with()
                tk.Tk.return_value.destroy.assert_called_once_with()
                tk.filedialog.askopenfilename.assert_called_once_with(
                    parent=tk.Tk.return_value,
                    title='Seleccionar archivo de logs',
                    filetypes=[('Todos los archivos', '*')], multiple=False,
                )

    def test_missing_tkinter(self):
        with patch.dict(sys.modules, {'tkinter': None}):
            with self.assertRaisesRegex(FileSelectionError, 'no está disponible'):
                select_log_file()

    def test_graphical_errors(self):
        for stage in ('create', 'withdraw', 'dialog'):
            with self.subTest(stage=stage):
                tk, modules = self.modules()
                if stage == 'create':
                    tk.Tk.side_effect = FakeTclError()
                elif stage == 'withdraw':
                    tk.Tk.return_value.withdraw.side_effect = FakeTclError()
                else:
                    tk.filedialog.askopenfilename.side_effect = FakeTclError()
                with patch.dict(sys.modules, modules):
                    with self.assertRaisesRegex(FileSelectionError, 'selector gráfico'):
                        select_log_file()
                if stage != 'create':
                    tk.Tk.return_value.destroy.assert_called_once_with()

    def test_cli_cancellation_and_selector_failure(self):
        for selector, message in (
            (Mock(return_value=None), 'Selección cancelada'),
            (Mock(return_value=''), 'Selección cancelada'),
            (Mock(side_effect=FileSelectionError('Tkinter no está disponible.')),
             'python -m log_analyzer ruta_del_archivo'),
        ):
            reader = Mock()
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(run(reader, [], select_file=selector), 1)
            reader.assert_not_called()
            self.assertEqual(out.getvalue(), '')
            self.assertIn(message, err.getvalue())
            self.assertNotIn('Traceback', err.getvalue())

    def test_explicit_path_needs_neither_selector_nor_tkinter(self):
        from contextlib import nullcontext
        selector = Mock(side_effect=AssertionError('No abrir selector'))
        reader = Mock(return_value=nullcontext(iter(['[INFO] 2025-01-10 Test'])))
        with patch.dict(sys.modules, {'tkinter': None}), redirect_stdout(io.StringIO()):
            self.assertEqual(run(reader, ['archivo'], select_file=selector), 0)
        selector.assert_not_called()
        reader.assert_called_once_with('archivo')
