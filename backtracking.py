import time

from puzzle import SolverResult, is_consistent_so_far, validate_solution


# Solve using recursive, row-major DFS with ascending candidate values.
# Reference: COSC-4117EL-01 Assignment 1, Task 2 and measurement definitions.
# AI disclosure: OpenAI Codex added helper imports and corrected node scope
# and final-validation placement in the student's existing implementation.
# Prompt link: https://chatgpt.com/s/cx_6ac9a7918b8881918cd92ac9eaac7337
def solve_with_backtracking(puzzle, timeout=60):
    start_time = time.perf_counter()
    deadline = start_time + timeout

    assignments = puzzle.givens.copy()
    nodes = 0

    empty_cells = [
        (row, col)
        for row in range(1, puzzle.size + 1)
        for col in range(1, puzzle.size + 1)
        if (row, col) not in puzzle.givens
    ]

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
            print("\nValidating solution:")

            for row in range(1, puzzle.size + 1):
                for col in range(1, puzzle.size + 1):
                    print(f"{assignments[(row, col)]:3}", end="")
                print()

            valid = validate_solution(puzzle, assignments)
            print(f"Solution valid: {valid}")
            return valid

        cell = empty_cells[index]
        row, col = cell

        print(f"\nTrying cell: ({row}, {col})")

        for val in range(1, puzzle.size + 1):
            check_timeout()
            nodes += 1

            print(f"Cell ({row}, {col}), trying value: {val}")

            if not is_consistent_so_far(puzzle, assignments, cell, val):
                print("Not consistent")
                continue

            print(f"Assigning {val} to ({row}, {col})")
            assignments[cell] = val

            if search(index + 1):
                print(f"Solution found; keeping ({row}, {col}) = {val}")
                return True

            print(f"No solution with ({row}, {col}) = {val}. Backtracking")
            print(f"Del ({row}, {col}): {val}")
            del assignments[cell]

        print(f"All values failed for ({row}, {col}). Returning False")
        return False

    try:
        check_timeout()

        if search(0):
            status = "Solved"
            solution = assignments.copy()
        else:
            status = "No solution"
            solution = None

    except TimeoutError:
        status = "Time out"
        solution = None

    elapsed = time.perf_counter() - start_time

    return SolverResult(status, solution, elapsed, nodes)
