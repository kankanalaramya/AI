"""Solver, deadline, metric, and independent-validator regression tests.

AI disclosure: OpenAI Codex authored these tests for Assignment 1, Tasks 2–4.
Prompt link: https://chatgpt.com/s/cx_6ace5baac22c8191964a80d948bbdda9
"""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from io import StringIO
from itertools import permutations, product
from pathlib import Path
import random
import unittest
from unittest.mock import patch

import ac3_solver
import backtracking
from puzzle import FutoshikiPuzzle, is_consistent_so_far, load_puzzle, validate_solution

SAMPLES = Path(__file__).parent / 'puzzles'
SOLVERS = (backtracking.solve_with_backtracking, ac3_solver.solve_with_ac3)


def small_puzzle(size=2):
    puzzle = FutoshikiPuzzle()
    puzzle.size = size
    return puzzle


class SolverTests(unittest.TestCase):
    def test_all_valid_and_unsolvable_samples(self):
        paths = sorted(SAMPLES.rglob('[1468]*.txt')) + [SAMPLES.parent / 'puzzle4.txt']
        for path in paths:
            puzzle = load_puzzle(path)
            before = deepcopy(puzzle.__dict__)
            for solver in SOLVERS:
                with self.subTest(puzzle=path.name, solver=solver.__name__):
                    result = solver(puzzle, timeout=60)
                    expected = 'No solution' if 'unsolvable' in path.name else 'Solved'
                    self.assertEqual(result.status, expected)
                    if expected == 'Solved':
                        self.assertTrue(validate_solution(puzzle, result.solution))
                    else:
                        self.assertIsNone(result.solution)
                    self.assertGreaterEqual(result.runtime, 0)
                    self.assertGreaterEqual(result.nodes, 0)
                    self.assertEqual(puzzle.__dict__, before)

    def test_report_heuristic_detour_requires_more_ac3_attempts(self):
        puzzle = load_puzzle(SAMPLES / 'valid/8x8_heuristic_detour.txt')
        baseline, enhanced = (solver(puzzle) for solver in SOLVERS)
        for result in (baseline, enhanced):
            self.assertEqual(result.status, 'Solved')
            self.assertTrue(validate_solution(puzzle, result.solution))
        self.assertGreater(enhanced.nodes, baseline.nodes)
        # Runtime ordering is deliberately not asserted: it varies by machine.

    def test_inequalities_only_case_solves_without_ac3_branching(self):
        puzzle = load_puzzle(SAMPLES / 'valid/6x6_inequalities_only.txt')
        self.assertFalse(puzzle.givens)
        result = SOLVERS[1](puzzle)
        self.assertEqual(result.status, 'Solved')
        self.assertEqual(result.nodes, 0)
        self.assertTrue(validate_solution(puzzle, result.solution))

    def test_solvers_are_silent(self):
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            for solver in SOLVERS:
                solver(small_puzzle())
        self.assertEqual(output.getvalue(), '')

    def test_zero_timeout(self):
        for solver in SOLVERS:
            with self.subTest(solver=solver.__name__):
                result = solver(small_puzzle(), timeout=0)
                self.assertEqual(result.status, 'Time out')
                self.assertIsNone(result.solution)
                self.assertEqual(result.nodes, 0)

    def test_timeout_during_initialization(self):
        for module, solver in ((backtracking, SOLVERS[0]), (ac3_solver, SOLVERS[1])):
            with self.subTest(solver=solver.__name__):
                readings = iter([0.0, 0.0, 2.0])
                with patch.object(module.time, 'perf_counter', side_effect=lambda: next(readings, 2.0)):
                    result = solver(small_puzzle(), timeout=1)
                self.assertEqual(result.status, 'Time out')
                self.assertEqual(result.nodes, 0)
                self.assertEqual(result.runtime, 2)
                self.assertIsNone(result.solution)

    def test_timeout_during_final_validation_even_when_validation_fails(self):
        # Controlled clock: no sleeps or dependence on the computer's speed.
        for module, solver in ((backtracking, SOLVERS[0]), (ac3_solver, SOLVERS[1])):
            for valid in (True, False):
                with self.subTest(solver=solver.__name__, valid=valid):
                    clock = [0.0]
                    def slow_validation(*args):
                        clock[0] = 2.0
                        return valid
                    with patch.object(module.time, 'perf_counter', side_effect=lambda: clock[0]), \
                         patch.object(module, 'validate_solution', side_effect=slow_validation):
                        result = solver(small_puzzle(1), timeout=1)
                    self.assertEqual(result.status, 'Time out')
                    self.assertIsNone(result.solution)
                    self.assertEqual(result.runtime, 2)

    def test_timeout_after_last_failed_consistency_check(self):
        clock = [0.0]
        def slow_rejection(*args):
            clock[0] = 1.0
            return False
        with patch.object(backtracking.time, 'perf_counter', side_effect=lambda: clock[0]), \
             patch.object(backtracking, 'is_consistent_so_far', side_effect=slow_rejection):
            result = SOLVERS[0](small_puzzle(1), timeout=1)
        self.assertEqual(result.status, 'Time out')
        self.assertIsNone(result.solution)
        self.assertEqual(result.nodes, 1)

    def test_baseline_order_and_node_count(self):
        with patch.object(backtracking, 'is_consistent_so_far', wraps=is_consistent_so_far) as check:
            result = SOLVERS[0](small_puzzle())
        self.assertEqual(result.nodes, 6)
        self.assertEqual([(call.args[2], call.args[3]) for call in check.call_args_list],
                         [((1, 1), 1), ((1, 2), 1), ((1, 2), 2),
                          ((2, 1), 1), ((2, 1), 2), ((2, 2), 1)])

    def test_complete_puzzle_and_propagation_do_not_count_as_attempts(self):
        puzzle = load_puzzle(SAMPLES / 'valid/4x4_complete.txt')
        for solver in SOLVERS:
            result = solver(puzzle)
            self.assertEqual(result.nodes, 0)
            self.assertEqual(result.solution, puzzle.givens)
            self.assertIsNot(result.solution, puzzle.givens)
        forced = small_puzzle()
        forced.givens = {(1, 1): 1}
        self.assertEqual(SOLVERS[1](forced).nodes, 0)

    def test_search_and_repeated_runs_do_not_leak_domains(self):
        puzzle = load_puzzle(SAMPLES / 'valid/6x6_challenging.txt')
        first = SOLVERS[1](puzzle)
        second = SOLVERS[1](puzzle)
        self.assertGreater(first.nodes, 0)
        self.assertEqual(first.solution, second.solution)
        self.assertEqual(first.nodes, second.nodes)

    def test_small_cases_against_exhaustive_latin_square_oracle(self):
        # Independent oracle uses permutations and direct comparisons, not the
        # production consistency checker or either solver's search machinery.
        latin_squares = [rows for rows in product(permutations((1, 2, 3)), repeat=3)
                         if all(len({rows[r][c] for r in range(3)}) == 3 for c in range(3))]
        rng = random.Random(4117)
        cells = list(product(range(1, 4), repeat=2))
        edges = [(a, b) for a in cells for b in cells
                 if a < b and abs(a[0]-b[0])+abs(a[1]-b[1]) == 1]
        for case in range(60):
            puzzle = small_puzzle(3)
            witness = rng.choice(latin_squares)
            puzzle.givens = {cell: witness[cell[0]-1][cell[1]-1]
                             for cell in rng.sample(cells, rng.randrange(4))}
            puzzle.inequalities = [(a[0], a[1], rng.choice(('<', '>')), b[0], b[1])
                                   for a, b in rng.sample(edges, rng.randrange(7))]
            def matches(rows):
                if any(rows[r-1][c-1] != v for (r, c), v in puzzle.givens.items()):
                    return False
                return all((rows[r-1][c-1] < rows[s-1][t-1]) if op == '<'
                           else (rows[r-1][c-1] > rows[s-1][t-1])
                           for r, c, op, s, t in puzzle.inequalities)
            possible = any(matches(rows) for rows in latin_squares)
            for solver in SOLVERS:
                with self.subTest(case=case, solver=solver.__name__):
                    result = solver(puzzle)
                    self.assertEqual(result.status, 'Solved' if possible else 'No solution')
                    if possible:
                        self.assertTrue(validate_solution(puzzle, result.solution))
                    else:
                        self.assertIsNone(result.solution)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.puzzle = small_puzzle()
        self.puzzle.givens = {(1, 1): 1}
        self.puzzle.inequalities = [(1, 1, '<', 1, 2)]
        self.solution = {(1, 1): 1, (1, 2): 2, (2, 1): 2, (2, 2): 1}

    def test_valid_solution_and_nonmutation(self):
        before = deepcopy(self.solution)
        self.assertTrue(validate_solution(self.puzzle, self.solution))
        self.assertEqual(self.solution, before)

    def test_incomplete_extra_out_of_range_and_wrong_types(self):
        for solution in (None, {}, {**self.solution, (3, 1): 1},
                         {**self.solution, (1, 1): 0}, {**self.solution, (1, 1): 3},
                         {**self.solution, (1, 1): True}, {**self.solution, (1, 1): 1.0},
                         {**self.solution, (1, 1): '1'}):
            with self.subTest(solution=solution):
                self.assertFalse(validate_solution(self.puzzle, solution))

    def test_row_column_fixed_and_inequality_violations(self):
        row_duplicate = {(1, 1): 1, (1, 2): 1, (2, 1): 2, (2, 2): 2}
        col_duplicate = {(1, 1): 1, (1, 2): 2, (2, 1): 1, (2, 2): 2}
        for solution in (row_duplicate, col_duplicate, {k: 3-v for k, v in self.solution.items()}):
            self.assertFalse(validate_solution(self.puzzle, solution))
        self.puzzle.givens = {}
        self.puzzle.inequalities = [(1, 1, '>', 1, 2)]
        self.assertFalse(validate_solution(self.puzzle, self.solution))

    def test_partial_consistency_known_and_unknown_endpoints(self):
        self.assertTrue(is_consistent_so_far(self.puzzle, {}, (1, 2), 1))
        self.assertFalse(is_consistent_so_far(self.puzzle, {(1, 1): 1}, (1, 2), 1))
        self.assertTrue(is_consistent_so_far(self.puzzle, {(1, 1): 1}, (1, 2), 2))
        self.assertFalse(is_consistent_so_far(self.puzzle, {}, (1, 1), 2))
        self.assertFalse(is_consistent_so_far(self.puzzle, {}, (1, 2), True))


if __name__ == '__main__':
    unittest.main()
