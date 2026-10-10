from collections import deque

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

    # AI assistance: ChatGPT helped add REVISE and the AC-3 queue below.
    # Each directed pair maps to all rules between its two cells.
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

    def revise(cell1, cell2):
        changed = False
        for v1 in domains[cell1].copy():
            keep_v1 = False
            for v2 in domains[cell2]:
                # The SAME v2 must satisfy every rule for this pair.
                supported = True
                for op in rules[(cell1, cell2)]:
                    if (op == "!=" and v1 == v2):
                        supported = False
                    if (op == ">" and v1 <= v2):
                        supported = False
                    if (op == "<" and v1 >= v2):
                        supported = False

                if supported:
                    keep_v1 = True
                    break

            if keep_v1 == False:
                domains[cell1].discard(v1)
                changed = True
        return changed

    def ac3():
        # The earlier given-value filtering may already have emptied a domain.
        for cell in domains:
            if len(domains[cell]) == 0:
                return False

        queue = deque(rules)
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

    consistent = ac3()
    print_status(domains, size)
    if consistent == False:
        print("No solution: a domain became empty.")
    # True means propagation succeeded; search may still be needed.
    return consistent

from puzzle import FutoshikiPuzzle

puzzle = FutoshikiPuzzle()
puzzle.size = 4
puzzle.givens = {(1,1): 3}
puzzle.inequalities = [(1, 2, ">", 1, 3),
                       (2, 2, ">", 1, 2),
                       (4, 2, ">", 4, 3),
                       (4, 3, "<", 4, 4)]

solve_with_ac3(puzzle)         
