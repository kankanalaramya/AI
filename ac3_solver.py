from collections import deque
from puzzle import validate_solution

def print_status (doms, size):
    for x in range(1, size+1):
        for y in range(1, size+1):
            print(f"{x},{y}: {doms[(x, y)]}")
        print()

def solve_with_ac3 (puzzle, timeout=60):
    domains = {}
    size = puzzle.size
    givens = puzzle.givens.copy()
    ineqs = puzzle.inequalities

    # generate the domains
    for x in range(1, size+1):
        for y in range(1, size+1):
            if ((x, y) in givens):
                domains[(x, y)] = {givens[(x, y)]}
            else:
                domains[(x, y)] = set(range(1, size + 1))

    # filter out the givens from the domains
    for (row, col), val in givens.items():
        for y in range(1, size+1):
            celly = (row, y)
            if celly != (row, col):
                domains[celly].discard(val)
        for x in range(1, size+1):
            cellx = (x, col)
            if cellx != (row, col):
                domains[cellx].discard(val)

    rules = {}
    for cell1 in domains:
        for cell2 in domains:
            if cell1 == cell2:
                continue
            if cell1[0] == cell2[0] or cell1[1] == cell2[1]:
                rules[(cell1, cell2)] = ["!="]

    # Add each inequality in both directions, preserving the not-equal rule.
    for ineq in ineqs:
        x1, y1, op, x2, y2 = ineq
        cell1 = (x1, y1)
        cell2 = (x2, y2)
        rules[(cell1, cell2)].append(op)
        reverse_op = "<" if op == ">" else ">"
        rules[(cell2, cell1)].append(reverse_op)

    def values_consistent(cell1, v1, cell2, v2):
        # The same pair of values must satisfy every rule between the cells.
        for op in rules[(cell1, cell2)]:
            if (op == "!=" and v1 == v2):
                return False
            if (op == ">" and v1 <= v2):
                return False
            if (op == "<" and v1 >= v2):
                return False
        return True

    def revise(cell1, cell2):
        changed = False
        for v1 in domains[cell1].copy():
            keep_v1 = False
            for v2 in domains[cell2]:
                if values_consistent(cell1, v1, cell2, v2):
                    keep_v1 = True
                    break

            if keep_v1 == False:
                domains[cell1].discard(v1)
                changed = True
        return changed

    def ac3(arcs=None):
        # The earlier given-value filtering may already have emptied a domain.
        for cell in domains:
            if len(domains[cell]) == 0:
                return False

        # Initially use all arcs; after a choice, start with affected arcs.
        if arcs is None:
            queue = deque(rules)
        else:
            queue = deque(arcs)
        while queue:
            cell1, cell2 = queue.popleft()
            if revise(cell1, cell2):
                if len(domains[cell1]) == 0:
                    return False

                # Recheck cells that may have lost support in cell1.
                for neighbor in domains:
                    if neighbor != cell2 and (neighbor, cell1) in rules:
                        queue.append((neighbor, cell1))
        return True

    def select_cell():
        selected = None
        smallest_domain = size + 1
        highest_degree = -1
        for cell in domains:
            # Singleton domains already determine the value of a cell.
            if len(domains[cell]) <= 1:
                continue

            degree = 0
            for neighbor in domains:
                if (cell, neighbor) in rules and len(domains[neighbor]) > 1:
                    degree += 1

            # MRV first, then most unassigned neighbors (degree).
            # Remaining ties keep the original row-major order.
            if (len(domains[cell]) < smallest_domain or
                (len(domains[cell]) == smallest_domain and degree > highest_degree)):
                selected = cell
                smallest_domain = len(domains[cell])
                highest_degree = degree
        return selected

    def order_values(cell):
        scores = []
        for val in domains[cell]:
            removed = 0
            for neighbor in domains:
                if (cell, neighbor) not in rules or len(domains[neighbor]) <= 1:
                    continue
                for other_val in domains[neighbor]:
                    if values_consistent(cell, val, neighbor, other_val) == False:
                        removed += 1
            scores.append((removed, val))

        # LCV: fewest excluded neighbor values first, then ascending value.
        scores.sort()
        return [val for removed, val in scores]

    def search():
        nonlocal domains
        cell = select_cell()
        if cell is None:
            assignments = {}
            for assigned_cell in domains:
                if len(domains[assigned_cell]) != 1:
                    return False
                assignments[assigned_cell] = next(iter(domains[assigned_cell]))
            return validate_solution(puzzle, assignments)

        # Copy every set: a dictionary-only copy would share the domain sets.
        saved_domains = {c: values.copy() for c, values in domains.items()}
        for val in order_values(cell):
            # Each attempt starts with the domains from before this decision.
            domains = {c: values.copy() for c, values in saved_domains.items()}
            domains[cell] = {val}

            arcs = []
            for neighbor in domains:
                if (neighbor, cell) in rules:
                    arcs.append((neighbor, cell))

            if ac3(arcs) and search():
                return True

        # Every candidate failed; restore this call's original domains.
        domains = saved_domains
        return False

    solved = False
    if ac3():
        solved = search()
    print_status(domains, size)
    if solved == False:
        print("No solution.")
    # True now means a complete solution passed independent validation.
    return solved

from puzzle import FutoshikiPuzzle

puzzle = FutoshikiPuzzle()
puzzle.size = 4
puzzle.givens = {(1,1): 3}
puzzle.inequalities = [(1, 2, ">", 1, 3),
                       (2, 2, ">", 1, 2),
                       (4, 2, ">", 4, 3),
                       (4, 3, "<", 4, 4)]

solve_with_ac3(puzzle)         
