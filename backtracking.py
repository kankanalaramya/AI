import time

from puzzle import SolverResult, is_consistent_so_far, validate_solution


# Solve using recursive, row-major DFS with ascending candidate values.
# Reference: COSC-4117EL-01 Assignment 1, Task 2 and measurement definitions.
# AI disclosure: OpenAI Codex added helper imports and corrected node scope
# and final-validation placement in the student's existing implementation.
# Prompt link: https://chatgpt.com/s/cx_6ac9a7918b8881918cd92ac9eaac7337
def solve_with_backtracking(puzzle, timeout=60):
    """Run silent row-major DFS; count every attempted candidate assignment."""
    start_time = time.perf_counter()
    deadline = start_time + timeout

    assignments = {}
    nodes = 0
    empty_cells = []

    def check_timeout():
        if time.perf_counter() >= deadline:
            raise TimeoutError

    # Try the next unassigned cell; validate only after every row is complete.
    # Reference: COSC-4117EL-01 Assignment 1, Tasks 2 and 4.
    # AI disclosure: OpenAI Codex corrected node scope and validation placement.
    # Prompt link: https://chatgpt.com/s/cx_6ac9a7918b8881918cd92ac9eaac7337
    def search(index):
        nonlocal nodes
        check_timeout()

        if index == len(empty_cells):
            valid = validate_solution(puzzle, assignments)
            check_timeout()
            return valid

        cell = empty_cells[index]

        for val in range(1, puzzle.size + 1):
            check_timeout()
            nodes += 1

            if not is_consistent_so_far(puzzle, assignments, cell, val):
                continue

            assignments[cell] = val

            if search(index + 1):
                return True

            del assignments[cell]

        return False

    # AI disclosure: OpenAI Codex removed search logging and added deadline
    # checks for initialization, validation, and result assembly.
    # Prompt link: https://chatgpt.com/s/cx_6ace5baac22c8191964a80d948bbdda9
    try:
        check_timeout()
        assignments = puzzle.givens.copy()
        for row in range(1, puzzle.size + 1):
            for col in range(1, puzzle.size + 1):
                check_timeout()
                if (row, col) not in puzzle.givens:
                    empty_cells.append((row, col))

        solved = search(0)
        check_timeout()
        if solved:
            status = "Solved"
            solution = assignments.copy()
        else:
            status = "No solution"
            solution = None
        check_timeout()

    except TimeoutError:
        status = "Time out"
        solution = None

    elapsed = time.perf_counter() - start_time

    return SolverResult(status, solution, elapsed, nodes)
