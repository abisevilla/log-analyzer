import gc
import io
import tempfile
import unittest
import weakref
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import Mock, patch

from log_analyzer.application.analyze_logs import analyze_logs
from log_analyzer.domain.parser import parse_line
from log_analyzer.infrastructure.file_reader import open_log_file
from log_analyzer.presentation.cli import run


class ParserTests(unittest.TestCase):
    def test_validation_matrix(self):
        cases = [
            ('[INFO] 2025-01-10 User logged in', 'INFO', False, False),
            ('[ERROR] 2025-01-10 Failed to connect', 'ERROR', False, False),
            ('[WARNING] Invalid password attempt', 'WARNING', True, True),
            ('[DEBUGX] 2025-01-10 Test', None, False, True),
            ('[INFO] 2025-15-45 Login', 'INFO', True, False),
            ('[ERROR] 2025-01-10', 'ERROR', False, True),
            ('[INFO] 2025-02-29 Test', 'INFO', True, False),
            ('[INFO] 2024-02-29 Test', 'INFO', False, False),
            ('[INFO] 2025-1-01 Test', 'INFO', True, False),
            ('[INFO] 2025–01–10 Test', 'INFO', True, False),
            ('[INFO] 2025-01-10T10:00 Test', 'INFO', True, False),
            ('2025-01-10 [INFO] Test', None, True, True),
            ('[INFO] Login 2025-01-10', 'INFO', True, True),
            ('INFO 2025-01-10 Test', None, False, True),
            ('[info] 2025-01-10 Test', None, False, True),
            ('[INFO]', 'INFO', True, True),
            ('garbage', None, True, True),
            ('[INFO] 9999-12-31 Futuro', 'INFO', False, False),
            ('[INFO] 0000-01-01 Test', 'INFO', True, False),
        ]
        for text, level, date_error, structure_error in cases:
            with self.subTest(text=text):
                result = parse_line(text)
                self.assertEqual((result.level, result.date_error, result.structure_error),
                                 (level, date_error, structure_error))

    def test_whitespace_and_message(self):
        for blank in ('', '\n', ' \t\r\n'):
            self.assertIsNone(parse_line(blank))
        result = parse_line(' \t[INFO]\t 2025-01-10\tUsuario  José 😊  \r\n')
        self.assertTrue(result.is_valid)
        self.assertEqual(result.message, 'Usuario  José 😊')


class SummaryTests(unittest.TestCase):
    def test_counts_and_invariants(self):
        summary = analyze_logs(iter([
            '', '[INFO] 2025-01-10 Login', '[ERROR] 2025-01-10 Fallo',
            '[WARNING] Invalid password attempt', '[DEBUGX] 2025-01-10 Test',
            '[INFO] 2025-15-45 Login', '[ERROR] 2025-01-10',
        ]))
        self.assertEqual((summary.total_events, summary.info, summary.warning,
                          summary.error, summary.unknown_level), (6, 2, 1, 2, 1))
        self.assertEqual((summary.valid_events, summary.malformed_lines,
                          summary.date_errors, summary.structure_errors), (2, 4, 2, 3))
        self.assertEqual(summary.total_events, summary.info + summary.warning +
                         summary.error + summary.unknown_level)
        self.assertEqual(summary.total_events, summary.valid_events + summary.malformed_lines)

    def test_streaming_without_retaining_results(self):
        references = []

        class TrackedResult:
            level = 'INFO'
            date_error = structure_error = False
            is_valid = True

        def parser(line):
            gc.collect()
            self.assertLessEqual(sum(ref() is not None for ref in references), 1)
            result = TrackedResult()
            references.append(weakref.ref(result))
            return result

        class OnePass:
            def __init__(self):
                self.started = False

            def __iter__(self):
                if self.started:
                    raise AssertionError('El iterable se recorrió más de una vez')
                self.started = True
                yield from ('line' for _ in range(30))

            def read(self, *args):
                raise AssertionError('No debe leer el archivo completo')

            readlines = read

        with patch('log_analyzer.application.analyze_logs.parse_line', parser):
            self.assertEqual(analyze_logs(OnePass()).total_events, 30)
        self.assertTrue(all(ref() is None for ref in references))


class CliTests(unittest.TestCase):
    def invoke(self, reader=open_log_file, argv=None, select_file=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = run(reader, argv, select_file=select_file or Mock(return_value=None))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_files_and_visual_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'registros José 😊 sin extensión'
            path.write_bytes(('\ufeff[INFO] 2025-01-10 José 😊\r\n'
                              '\n[ERROR] 2025-01-10 Fallo').encode('utf-8'))
            code, output, error = self.invoke(argv=[str(path)])
            self.assertEqual(code, 0)
            self.assertIn('Total de eventos: 2', output)
            self.assertEqual(error, '')
            selector = Mock(return_value=str(path))
            self.assertEqual(self.invoke(argv=[], select_file=selector)[0], 0)
            selector.assert_called_once_with()
            for content in ('', '\n \t\n'):
                path.write_text(content, encoding='utf-8')
                code, output, _ = self.invoke(argv=[str(path)])
                self.assertEqual(code, 0)
                self.assertIn('No hay eventos', output)
                self.assertIn('Total de eventos: 0', output)
            path.write_bytes(b'\xff')
            self.assert_failed(self.invoke(argv=[str(path)]), 'UTF-8')
            self.assert_failed(self.invoke(argv=[directory]), 'directorio')
            self.assert_failed(self.invoke(argv=[str(path) + '.missing']), 'no existe')

    def assert_failed(self, result, message):
        code, output, error = result
        self.assertEqual(code, 1)
        self.assertNotIn('Resumen', output)
        self.assertIn(message, error)
        self.assertNotIn('Traceback', error)

    def test_access_errors(self):
        for exception, message in [(PermissionError(), 'permisos'),
                                   (OSError(), 'No se pudo leer'),
                                   (ValueError(), 'No se pudo leer')]:
            with self.subTest(exception=exception):
                def reader(path):
                    raise exception
                self.assert_failed(self.invoke(reader, ['test']), message)

    def test_failure_after_valid_event(self):
        for failure in (OSError('fallo'), UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'inválido')):
            @contextmanager
            def reader(path):
                def lines():
                    yield '[INFO] 2025-01-10 Test'
                    raise failure
                yield lines()
            self.assert_failed(self.invoke(reader, ['test']), 'no se completó')

    def test_empty_path_and_cancellation(self):
        self.assert_failed(self.invoke(argv=['  ']), 'ruta')
        for exception in (KeyboardInterrupt, EOFError):
            self.assert_failed(self.invoke(argv=[], select_file=Mock(side_effect=exception)), 'cancelada')

    def test_argument_codes(self):
        for argv, code in [(['--help'], 0), (['one', 'two'], 2)]:
            selector = Mock()
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    run(open_log_file, argv, select_file=selector)
            self.assertEqual(raised.exception.code, code)
            selector.assert_not_called()

    def test_reader_closes_stream(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'log'
            path.write_text('[INFO] 2025-01-10 Test', encoding='utf-8')
            with self.assertRaises(RuntimeError):
                with open_log_file(str(path)) as stream:
                    self.assertFalse(stream.closed)
                    raise RuntimeError('fallo del consumidor')
            self.assertTrue(stream.closed)


if __name__ == '__main__':
    unittest.main()
