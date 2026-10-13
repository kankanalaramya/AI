"""Loader regression tests. Run with python -m unittest discover -v.

AI disclosure: OpenAI Codex authored these tests for Assignment 1, Tasks 1/4.
Prompt link: https://chatgpt.com/s/cx_6ace5baac22c8191964a80d948bbdda9
"""
from pathlib import Path
import tempfile
import unittest

from puzzle import load_puzzle

SAMPLES = Path(__file__).parent / 'puzzles'


class LoadingTests(unittest.TestCase):
    def load_text(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'puzzle.txt'
            path.write_text(text, encoding='utf-8')
            return load_puzzle(path)

    def test_sample_folder_classification(self):
        self.assertEqual(list(SAMPLES.glob('*.txt')), [])
        for category in ('valid', 'invalid', 'unsolvable'):
            paths = list((SAMPLES / category).glob('*.txt'))
            self.assertTrue(paths, category)
            for path in paths:
                with self.subTest(path=path):
                    self.assertEqual(path.name.startswith('malformed_'), category == 'invalid')
                    self.assertEqual('unsolvable' in path.stem, category == 'unsolvable')

    def test_valid_samples(self):
        for path in SAMPLES.rglob('[1468]*.txt'):
            with self.subTest(path=path.name):
                self.assertEqual(load_puzzle(path).size, int(path.name[0]))

    def test_malformed_samples(self):
        paths = list((SAMPLES / 'invalid').glob('malformed_*.txt'))
        self.assertGreaterEqual(len(paths), 16)
        for path in paths:
            with self.subTest(path=path.name), self.assertRaises(ValueError):
                load_puzzle(path)

    def test_empty_sections_comments_case_whitespace_and_bom(self):
        puzzle = self.load_text('\ufeff # comment\n size \n 4 \n\n givens\n# none\n inequalities \n')
        self.assertEqual(puzzle.size, 4)
        self.assertEqual(puzzle.givens, {})
        self.assertEqual(puzzle.inequalities, [])

    def test_all_headings_required(self):
        sections = ['SIZE\n4\n', 'GIVENS\n', 'INEQUALITIES\n']
        for omit in range(3):
            with self.subTest(omit=omit), self.assertRaises(ValueError):
                self.load_text(''.join(s for i, s in enumerate(sections) if i != omit))

    def test_structural_errors(self):
        for text in ('', '# comment\n', 'SIZE\nGIVENS\nINEQUALITIES\n',
                     'SIZE\n4\n5\nGIVENS\nINEQUALITIES\n',
                     'SIZE:\n4\nGIVENS\nINEQUALITIES\n',
                     'SIZE\n4\nGIVENS\nINEQUALITIES\nGIVENS\n',
                     'SIZE\n4\nINEQUALITIES\nGIVENS\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.load_text(text)

    def test_invalid_size(self):
        for size in ('0', '-1', 'four', '4.0', '4,4'):
            with self.subTest(size=size), self.assertRaises(ValueError):
                self.load_text(f'SIZE\n{size}\nGIVENS\nINEQUALITIES\n')

    def test_invalid_given_records(self):
        for record in ('0,1,1', '5,1,1', '1,0,1', '1,5,1', '1,1,0',
                       '1,1,5', '1,1,1,1', 'a,1,1', '1,b,1', '1,1,c'):
            with self.subTest(record=record), self.assertRaises(ValueError):
                self.load_text(f'SIZE\n4\nGIVENS\n{record}\nINEQUALITIES\n')

    def test_invalid_inequality_records(self):
        for record in ('0,1,<,1,1', '1,0,<,1,1', '1,1,<,5,1', '1,1,<,1,5',
                       '1,1,<,1,1', '1,1,<,2,2', '1,1,<,1,3', '1,1,<=,1,2',
                       '1,1,<,1', 'a,1,<,1,2', '1,1,<,1,b',
                       '1,1,<,1,2\n1,1,>,1,2', '1,1,<,1,2\n1,2,<,1,1'):
            with self.subTest(record=record), self.assertRaises(ValueError):
                self.load_text(f'SIZE\n4\nGIVENS\nINEQUALITIES\n{record}\n')

    def test_error_retains_physical_line_number(self):
        with self.assertRaisesRegex(ValueError, 'line 6'):
            self.load_text('# comment\n\nSIZE\n4\nGIVENS\n1,1,no\nINEQUALITIES\n')

    def test_missing_file_and_invalid_encoding(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'missing.txt'
            with self.assertRaisesRegex(ValueError, 'Could not open file'):
                load_puzzle(path)
            path.write_bytes(b'\xff\xfe\x80')
            with self.assertRaisesRegex(ValueError, 'Could not open file'):
                load_puzzle(path)


if __name__ == '__main__':
    unittest.main()
