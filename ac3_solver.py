import time
from collections import deque

from puzzle import SolverResult, validate_solution


# Solve with AC-3, recursive backtracking, MRV, degree tie-breaking, and LCV.
# References: COSC-4117EL-01 Assignment 1, Tasks 3 and 4 and measurement definitions.
# AI disclosure: OpenAI Codex formatted the existing solver, added perf_counter
# timing before initialization, deadline checks, assignment-attempt counting,
# and SolverResult returns for success, failure, and timeout. Existing search
# and propagation algorithms were retained. Development-only printing and the
# hard-coded demo puzzle were removed at the student's request.
# Prompt link: TODO(student): add this conversation's share link to code/report.
def solve_with_ac3(puzzle, timeout=60):
    """Return a validated solution and metrics for a parser-validated puzzle.

    Runtime includes initialization, propagation, heuristics, search, and final
    validation. Nodes count tentative choices, including ones propagation rejects;
    givens and values forced by propagation do not count as search attempts.
    """
    start_time = time.perf_counter()
    deadline = start_time + timeout

    domains = {}
    rules = {}
    size = puzzle.size
    nodes = 0

    # Enforce the same configurable deadline throughout the solver.
    # Reference: Assignment 1, Task 2 timeout and required measurement definitions.
    # AI disclosure: OpenAI Codex added this helper using the baseline's
    # perf_counter/deadline/TimeoutError pattern, with a default of 60 seconds.
    # Prompt link: https://chatgpt.com/s/cx_6ac9a7918b8881918cd92ac9eaac7337
    def check_timeout():
        if time.perf_counter() >= deadline:
            raise TimeoutError

    # Require one value pair to satisfy every binary rule between these cells.
    # Reference: Assignment 1, Task 3, REVISE supporting-value requirement.
    # AI disclosure: OpenAI Codex retained the existing comparisons, removed
    # redundant parentheses, and added a deadline check for support/LCV scans.
    # Prompt link: https://chatgpt.com/s/cx_6ac9a7918b8881918cd92ac9eaac7337
    def values_consistent(cell1, value1, cell2, value2):
        check_timeout()
        for operator in rules[(cell1, cell2)]:
            if operator == "!=" and value1 == value2:
                return False
            if operator == ">" and value1 <= value2:
                return False
            if operator == "<" and value1 >= value2:
                return False
        return True

    # Remove values from the first domain that have no support in the second.
    # Reference: Assignment 1, Task 3, REVISE.
    # AI disclosure: OpenAI Codex formatted the existing revision loop, renamed
    # value variables, simplified the Boolean check, and added deadline checks.
    # Prompt link: https://chatgpt.com/s/cx_6ac9a7918b8881918cd92ac9eaac7337
    def revise(cell1, cell2):
        changed = False
        for value1 in domains[cell1].copy():
            check_timeout()
            supported = False
            for value2 in domains[cell2]:
                if values_consistent(cell1, value1, cell2, value2):
                    supported = True
                    break

            if not supported:
                domains[cell1].discard(value1)
                changed = True
        return changed

    def ac3(arcs=None):
        for cell in domains:
            check_timeout()
            if not domains[cell]:
                return False

        if arcs is None:
            queue = deque(rules)
        else:
            queue = deque(arcs)

        while queue:
            check_timeout()
            cell1, cell2 = queue.popleft()
            if revise(cell1, cell2):
                if not domains[cell1]:
                    return False

                # Recheck cells that may have lost support in cell1.
                for neighbor in domains:
                    check_timeout()
                    if neighbor != cell2 and (neighbor, cell1) in rules:
                        queue.append((neighbor, cell1))
        return True

    # Choose MRV first, then the largest number of unresolved neighbors.
    # Reference: Assignment 1, Task 3, MRV and Most Constraining Variable.
    # AI disclosure: OpenAI Codex reformatted the existing tie-break condition
    # and added deadline checks to both scans; selection priorities are unchanged.
    # Prompt link: https://chatgpt.com/s/cx_6ac9a7918b8881918cd92ac9eaac7337
    def select_cell():
        selected = None
        smallest_domain = size + 1
        highest_degree = -1
        for cell in domains:
            check_timeout()
            # Singleton domains already determine the value of a cell.
            if len(domains[cell]) <= 1:
                continue

            degree = 0
            for neighbor in domains:
                check_timeout()
                if (cell, neighbor) in rules and len(domains[neighbor]) > 1:
                    degree += 1

            # Remaining ties keep the original row-major order.
            if (
                len(domains[cell]) < smallest_domain
                or (
                    len(domains[cell]) == smallest_domain
                    and degree > highest_degree
                )
            ):
                selected = cell
                smallest_domain = len(domains[cell])
                highest_degree = degree
        return selected

    # Try values excluding the fewest values from unresolved neighbors first.
    # Reference: Assignment 1, Task 3, Least Constraining Value.
    # AI disclosure: OpenAI Codex retained existing LCV scores and ascending
    # tie-breaking, simplified Boolean syntax, and added deadline checks.
    # Prompt link: https://chatgpt.com/s/cx_6ac9a7918b8881918cd92ac9eaac7337
    def order_values(cell):
        scores = []
        for value in domains[cell]:
            check_timeout()
            removed = 0
            for neighbor in domains:
                check_timeout()
                if (cell, neighbor) not in rules or len(domains[neighbor]) <= 1:
                    continue
                for other_value in domains[neighbor]:
                    if not values_consistent(cell, value, neighbor, other_value):
                        removed += 1
            scores.append((removed, value))

        scores.sort()
        return [value for removed, value in scores]

    # Search with propagation after every tentative choice and restore on failure.
    # References: Assignment 1, Tasks 3 and 4 and node measurement definition.
    # AI disclosure: OpenAI Codex added nonlocal node accounting and deadline
    # checks, including after final validation. Existing per-set domain copying,
    # affected-arc propagation, and recursive backtracking were retained.
    # Prompt link: https://chatgpt.com/s/cx_6ac9a7918b8881918cd92ac9eaac7337
    def search():
        nonlocal domains, nodes
        check_timeout()
        cell = select_cell()
        if cell is None:
            assignments = {}
            for assigned_cell in domains:
                check_timeout()
                if len(domains[assigned_cell]) != 1:
                    return False
                assignments[assigned_cell] = next(iter(domains[assigned_cell]))
            valid = validate_solution(puzzle, assignments)
            check_timeout()
            return valid

        # Copy every set: a dictionary-only copy would share mutable domains.
        saved_domains = {cell: values.copy() for cell, values in domains.items()}
        for value in order_values(cell):
            # Each attempt starts with independent copies of the parent domains.
            domains = {
                cell: values.copy() for cell, values in saved_domains.items()
            }
            check_timeout()
            nodes += 1
            domains[cell] = {value}

            arcs = []
            for neighbor in domains:
                check_timeout()
                if (neighbor, cell) in rules:
                    arcs.append((neighbor, cell))

            if ac3(arcs) and search():
                return True

        # Every candidate failed; restore this call's original domains.
        domains = saved_domains
        return False

    try:
        check_timeout()

        # Initialization is inside both the timed interval and timeout handler.
        for row in range(1, size + 1):
            for col in range(1, size + 1):
                check_timeout()
                cell = (row, col)
                if cell in puzzle.givens:
                    domains[cell] = {puzzle.givens[cell]}
                else:
                    domains[cell] = set(range(1, size + 1))

        # Remove given values from other domains in the same row and column.
        for (row, col), value in puzzle.givens.items():
            for index in range(1, size + 1):
                check_timeout()
                if index != col:
                    domains[(row, index)].discard(value)
                if index != row:
                    domains[(index, col)].discard(value)

        for cell1 in domains:
            for cell2 in domains:
                check_timeout()
                if cell1 == cell2:
                    continue
                if cell1[0] == cell2[0] or cell1[1] == cell2[1]:
                    rules[(cell1, cell2)] = ["!="]

        # Preserve not-equal rules and represent inequalities in both directions.
        for row1, col1, operator, row2, col2 in puzzle.inequalities:
            check_timeout()
            cell1 = (row1, col1)
            cell2 = (row2, col2)
            rules[(cell1, cell2)].append(operator)
            reverse_operator = "<" if operator == ">" else ">"
            rules[(cell2, cell1)].append(reverse_operator)

        solved = ac3() and search()
        check_timeout()
        if solved:
            status = "Solved"
            solution = {
                cell: next(iter(values)) for cell, values in domains.items()
            }
        else:
            status = "No solution"
            solution = None
        check_timeout()

    except TimeoutError:
        status = "Time out"
        solution = None

    elapsed = time.perf_counter() - start_time

    return SolverResult(status, solution, elapsed, nodes)
