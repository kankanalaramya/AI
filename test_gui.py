"""Headless GUI behavior tests plus a real-Tk smoke test when a display exists.

AI disclosure: OpenAI Codex authored these tests for Assignment 1, Tasks 1/4.
Prompt link: https://chatgpt.com/s/cx_6ace5baac22c8191964a80d948bbdda9
"""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from futoshiki_gui import FutoshikiGUI
from puzzle import FutoshikiPuzzle, SolverResult, load_puzzle, validate_solution

SAMPLES = Path(__file__).parent / 'puzzles'


class GUIBehaviorTests(unittest.TestCase):
    def setUp(self):
        # Only the Tk widgets/dialogs are replaced; actual controller methods,
        # file loading, and rendering decisions run without a display server.
        self.gui = FutoshikiGUI.__new__(FutoshikiGUI)
        self.gui.root = MagicMock()
        self.gui.puzzle = FutoshikiPuzzle()
        self.gui.cells = {}
        self.gui.puzzle_frame = MagicMock()
        self.gui.puzzle_frame.grid_size.return_value = (0, 0)
        self.gui.puzzle_frame.winfo_children.return_value = []
        self.gui.bold_font = MagicMock()
        self.gui.bold_font.metrics.return_value = 20
        self.gui.solver_var = MagicMock()
        self.gui.solver_var.get.return_value = 'Basic Backtracking'
        for name in ('status_label', 'runtime_label', 'nodes_label', 'info_label'):
            setattr(self.gui, name, MagicMock())
        self.labels = []
        def new_label(*args, **kwargs):
            label = MagicMock()
            self.labels.append((label, kwargs))
            return label
        self.label_patch = patch('futoshiki_gui.tk.Label', side_effect=new_label)
        self.label_patch.start()
        self.addCleanup(self.label_patch.stop)
        self.errors = self.start_patch(patch('futoshiki_gui.messagebox.showerror'))
        self.warnings = self.start_patch(patch('futoshiki_gui.messagebox.showwarning'))
        self.picker = self.start_patch(patch('futoshiki_gui.filedialog.askopenfilename'))

    def start_patch(self, patcher):
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def test_cancel_preserves_current_puzzle_and_metrics(self):
        self.gui.puzzle = load_puzzle(SAMPLES / 'valid/4x4_easy.txt')
        previous = self.gui.puzzle
        self.picker.return_value = ''
        self.gui.load_puzzle()
        self.assertIs(self.gui.puzzle, previous)
        self.gui.status_label.config.assert_not_called()
        self.gui.runtime_label.config.assert_not_called()
        self.errors.assert_not_called()

    def test_load_success_resets_metrics_and_draws_cells(self):
        self.picker.return_value = str(SAMPLES / 'valid/6x6_easy.txt')
        self.gui.load_puzzle()
        self.assertEqual(len(self.gui.cells), 36)
        self.gui.status_label.config.assert_called_with(text='Puzzle loaded successfully')
        self.gui.runtime_label.config.assert_called_with(text='-')
        self.gui.nodes_label.config.assert_called_with(text='-')
        self.errors.assert_not_called()

    def test_all_malformed_samples_rejected_without_stale_puzzle(self):
        for path in sorted((SAMPLES / 'invalid').glob('malformed_*.txt')):
            with self.subTest(path=path.name):
                self.gui.puzzle = load_puzzle(SAMPLES / 'valid/4x4_easy.txt')
                self.gui.display_puzzle()
                self.picker.return_value = str(path)
                self.gui.load_puzzle()
                self.gui.status_label.config.assert_called_with(text='Invalid puzzle')
                self.gui.runtime_label.config.assert_called_with(text='-')
                self.gui.nodes_label.config.assert_called_with(text='-')
                self.assertEqual(self.gui.puzzle.size, 0)
                self.assertEqual(self.gui.cells, {})
                self.assertTrue(self.errors.call_args.args[1])
                self.gui.solve()
                self.warnings.assert_called()

    def test_unreadable_file_is_reported_safely(self):
        self.picker.return_value = str(SAMPLES / 'does_not_exist.txt')
        self.gui.load_puzzle()
        self.errors.assert_called_once()
        self.gui.status_label.config.assert_called_with(text='Invalid puzzle')

    def test_solve_without_puzzle(self):
        with patch('futoshiki_gui.solve_with_backtracking') as solver:
            self.gui.solve()
        solver.assert_not_called()
        self.warnings.assert_called_once()

    def test_both_solver_selections_status_metrics_and_solution_colours(self):
        for name, target in [('Basic Backtracking', 'solve_with_backtracking'),
                             ('AC-3 Enhanced Backtracking', 'solve_with_ac3')]:
            with self.subTest(method=name):
                self.gui.puzzle = load_puzzle(SAMPLES / 'valid/4x4_easy.txt')
                self.gui.solver_var.get.return_value = name
                solution = dict(self.gui.puzzle.givens)
                generated = next((r, c) for r in range(1, 5) for c in range(1, 5)
                                 if (r, c) not in solution)
                solution[generated] = 2
                def solve(puzzle, timeout):
                    self.gui.status_label.config.assert_called_with(text='Solving...')
                    self.gui.runtime_label.config.assert_called_with(text='-')
                    self.gui.root.update_idletasks.assert_called()
                    return SolverResult('Solved', solution, .125, 42)
                output = StringIO()
                with patch('futoshiki_gui.' + target, side_effect=solve) as solver, redirect_stdout(output):
                    self.gui.solve()
                solver.assert_called_once_with(self.gui.puzzle, timeout=60)
                self.gui.status_label.config.assert_called_with(text='Solved')
                self.gui.runtime_label.config.assert_called_with(text='0.125000 seconds')
                self.gui.nodes_label.config.assert_called_with(text='42')
                for cell, value in solution.items():
                    self.gui.cells[cell].config.assert_called_with(
                        text=str(value), foreground='black' if cell in self.gui.puzzle.givens else 'blue')
                self.assertEqual(len(output.getvalue().splitlines()), 1)
                self.assertIn('Nodes visited: 42', output.getvalue())

    def test_failure_and_timeout_show_metrics_without_rendering_a_solution(self):
        for status in ('No solution', 'Time out'):
            with self.subTest(status=status):
                self.gui.puzzle = load_puzzle(SAMPLES / 'valid/4x4_easy.txt')
                with patch('futoshiki_gui.solve_with_backtracking',
                           return_value=SolverResult(status, None, 60.001, 123)), redirect_stdout(StringIO()):
                    self.gui.solve()
                self.gui.status_label.config.assert_called_with(text=status)
                self.gui.runtime_label.config.assert_called_with(text='60.001000 seconds')
                self.gui.nodes_label.config.assert_called_with(text='123')
                for widget in self.gui.cells.values():
                    widget.config.assert_not_called()

    def test_horizontal_and_vertical_clue_directions(self):
        for first, second, operator, symbol, position in (
            ((1, 1), (1, 2), '<', '<', (0, 1)),
            ((1, 1), (1, 2), '>', '>', (0, 1)),
            ((1, 2), (1, 1), '<', '>', (0, 1)),
            ((1, 2), (1, 1), '>', '<', (0, 1)),
            ((1, 1), (2, 1), '<', '^', (1, 0)),
            ((1, 1), (2, 1), '>', 'v', (1, 0)),
            ((2, 1), (1, 1), '<', 'v', (1, 0)),
            ((2, 1), (1, 1), '>', '^', (1, 0)),
        ):
            with self.subTest(first=first, second=second, operator=operator):
                self.gui.puzzle.size = 2
                self.gui.puzzle.inequalities = [(*first, operator, *second)]
                self.gui.display_puzzle()
                label, options = self.labels[-1]
                self.assertEqual(options['text'], symbol)
                label.grid.assert_called_with(row=position[0], column=position[1])

    def test_resize_destroys_old_widgets_and_resets_spacing(self):
        old = [MagicMock(), MagicMock()]
        self.gui.puzzle_frame.winfo_children.return_value = old
        self.gui.puzzle_frame.grid_size.return_value = (15, 15)
        self.gui.puzzle = load_puzzle(SAMPLES / 'valid/4x4_easy.txt')
        self.gui.display_puzzle()
        for widget in old:
            widget.destroy.assert_called_once()
        self.gui.puzzle_frame.grid_columnconfigure.assert_any_call(14, minsize=0)
        self.gui.puzzle_frame.grid_rowconfigure.assert_any_call(14, minsize=0)
        self.assertEqual(len(self.gui.cells), 16)
        for label, options in self.labels[:16]:
            self.assertEqual(options['foreground'], 'black')

    def test_real_solvers_through_gui(self):
        for method in ('Basic Backtracking', 'AC-3 Enhanced Backtracking'):
            with self.subTest(method=method):
                self.picker.return_value = str(SAMPLES / 'valid/4x4_easy.txt')
                self.gui.load_puzzle()
                self.gui.solver_var.get.return_value = method
                with redirect_stdout(StringIO()):
                    self.gui.solve()
                self.gui.status_label.config.assert_called_with(text='Solved')
                solution = {cell: int(widget.config.call_args.kwargs['text'])
                            for cell, widget in self.gui.cells.items()}
                self.assertTrue(validate_solution(self.gui.puzzle, solution))


class RealTkSmokeTests(unittest.TestCase):
    def test_load_and_solve_with_real_widgets(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Graphical display unavailable: {error}')
        self.addCleanup(root.destroy)
        root.withdraw()
        gui = FutoshikiGUI(root)
        with patch('futoshiki_gui.filedialog.askopenfilename',
                   return_value=str(SAMPLES / 'valid/4x4_easy.txt')):
            gui.load_puzzle()
        gui.solver_var.set('AC-3 Enhanced Backtracking')
        with redirect_stdout(StringIO()):
            gui.solve()
        self.assertEqual(gui.status_label.cget('text'), 'Solved')
        solution = {cell: int(widget.cget('text')) for cell, widget in gui.cells.items()}
        self.assertTrue(validate_solution(gui.puzzle, solution))


if __name__ == '__main__':
    unittest.main()
