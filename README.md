# Futoshiki Puzzle Solver

COSC-4117EL-01 — Artificial Intelligence, Assignment 1 (Fall 2026).

This Python application models Futoshiki as a constraint satisfaction problem.
Each cell contains an integer from 1 to N; rows and columns contain no repeated
values, fixed clues remain unchanged, and all inequality clues must hold.

## Requirements

- Python 3.10 or newer.
- Tkinter and a graphical desktop to run the GUI.
- No third-party Python packages or ready-made CSP solvers are used.

Tkinter may require a separate system package on some Python installations.
Check its availability with `python3 -m tkinter`.

## Run the GUI

From the project directory:

```bash
python3 futoshiki_gui.py
```

Click **Load Puzzle**, choose `puzzle4.txt`, select **Basic Backtracking** or
**AC-3 Enhanced Backtracking**, and
click **Solve**. The GUI displays the result, runtime, and nodes visited. Fixed
clues appear in black and solver-generated values appear in blue.

Both solver options are connected to the GUI and use a 60-second timeout.

## Run AC-3 from the terminal

Run this command from the project directory. It loads the supplied puzzle,
prints the solver metrics, and independently checks a returned solution.

```bash
python3 - <<'PY'
from ac3_solver import solve_with_ac3
from puzzle import load_puzzle, validate_solution

puzzle = load_puzzle("puzzle4.txt")
result = solve_with_ac3(puzzle, timeout=60)
print(f"Status: {result.status}")
print(f"Runtime: {result.runtime:.6f} seconds")
print(f"Nodes visited: {result.nodes}")

if result.solution is not None:
    print(f"Solution valid: {validate_solution(puzzle, result.solution)}")
    for row in range(1, puzzle.size + 1):
        print(" ".join(str(result.solution[(row, col)])
                       for col in range(1, puzzle.size + 1)))
PY
```

To use the baseline programmatically, import `solve_with_backtracking` from
`backtracking` and call it with the same arguments. Running `ac3_solver.py`
directly does not run a puzzle; its development demo has been removed.

## Solver behavior and measurements

- **Basic backtracking:** recursive DFS, row-major variable order, ascending
  candidate values, and consistency checks before committing an assignment.
- **AC-3 enhanced backtracking:** initial AC-3 propagation, MRV variable
  selection, degree tie-breaking using unresolved neighbors, and LCV ordering.
  Each tentative choice triggers AC-3 on incoming affected arcs. Each branch
  copies the domain dictionary and every domain set; failed branches restore
  the parent domains. Complete assignments pass `validate_solution`.
- **Timeout:** both solver functions accept `timeout` in seconds, defaulting to
  60. AC-3 checks the deadline during initialization, propagation, heuristic
  scans, and recursive search, and after final validation.
- **Runtime:** measured with `time.perf_counter()` from before solver
  initialization through completion or timeout. Puzzle-file loading and GUI
  rendering are outside this interval. Baseline debug printing currently occurs
  inside its timed interval and can affect performance comparisons.
- **Nodes:** one per attempted value assignment to an unassigned variable,
  including choices rejected by consistency checks or propagation. Given clues
  and values forced by AC-3 propagation do not count as search attempts.

Both solvers return the shared `SolverResult` defined in `puzzle.py`:

| Field | Meaning |
| --- | --- |
| `status` | `Solved`, `No solution`, or `Time out` |
| `solution` | Dictionary mapping one-based `(row, column)` tuples to integers, or `None` on failure/timeout |
| `runtime` | Elapsed wall-clock seconds |
| `nodes` | Number of attempted assignments |

Invalid puzzle files are reported separately by the loader as `ValueError`.
Solver functions expect a puzzle that has passed input validation.

## Puzzle file format

All three section headings are required by the assignment, even when a section
has no records. Coordinates are one-based. Blank lines and lines beginning with
`#` are ignored.

```text
SIZE
4
GIVENS
1,1,2
2,3,1
INEQUALITIES
1,2,>,1,3
2,4,>,3,4
3,4,>,4,4
```

A given is `row,column,value`. An inequality is
`row1,column1,operator,row2,column2`, where the operator is `<` or `>` and the
cells are horizontally or vertically adjacent.

## Project files

| File | Purpose |
| --- | --- |
| `futoshiki_gui.py` | Tkinter interface, loading, puzzle display, and integration of both solvers |
| `puzzle.py` | Puzzle model, parser, consistency checking, independent solution validation, and `SolverResult` |
| `backtracking.py` | Baseline recursive solver |
| `ac3_solver.py` | AC-3 enhanced recursive solver |
| `puzzle4.txt` | Supplied 4×4 example |
| `test_solvers.py` | Currently empty; automated test suite remains to be added |

## Verification and remaining assignment work

During development, Codex ran 200 generated 3×3 cases against an exhaustive
Latin-square oracle and validated returned solutions. Additional checks covered
the supplied 4×4 puzzle, node counting, silent imports, and forced timeout
expiration during initialization and algorithm helper calls. These checks were
run as temporary scripts; they are not a committed test suite or the required
full performance experiment.

Remaining work includes:

- Reject missing and repeated section headings in the parser.
- Add reproducible tests and puzzle files for valid 4×4, 6×6, and 8×8 cases,
  at least two difficulty levels, an unsolvable case, and malformed input.
- Compare both solvers on the same machine and puzzle set, with baseline debug
  output disabled for meaningful timing comparisons.
- Complete the required report with experimental results, limitations,
  references, and AI disclosure.

## References and generative AI disclosure

Primary reference: **COSC-4117EL-01(2026Fall)_ Assignment1.docx**, particularly the
required CSP model, Tasks 2–4, and required measurement definitions. The separate
D2L programming-standards document was not supplied, so compliance with that
additional document has not been verified.

AI assistance recorded in this project and conversation:

- **ChatGPT:** the existing GUI file acknowledges development assistance; an
  earlier AC-3 revision also acknowledged assistance with REVISE and its queue.
- **OpenAI Codex:** implemented `is_consistent_so_far` and `validate_solution`
  from the student's supplied algorithms; corrected baseline helper imports,
  node-variable scope, and final-validation placement.
- **OpenAI Codex:** reviewed the student's updated AC-3 search, formatted the
  file, added runtime/deadline handling and assignment-attempt counting, returned
  `SolverResult`, and removed development printing and the hard-coded demo.
  The existing AC-3, MRV, degree, LCV, and domain-restoration algorithms were
  retained in that update.
- **OpenAI Codex:** connected the GUI’s AC-3 menu option to `solve_with_ac3`,
  retaining the existing status, metrics, and solution display.
- **OpenAI Codex:** ran the temporary checks described above and wrote this README
  from the current code and supplied assignment requirements.

**Prompt links:** TODO(student): replace the placeholders in source comments and
add the relevant conversation share links here and in the report. The prompts
covered consistency/validation implementation, AC-3 review, timing and formatting,
removal of the development demo, and README documentation. Include separate
links for earlier ChatGPT-assisted work where applicable.

The student must review the generated material and describe their own
verification or changes in the final report; the disclosure above records tool
contributions, not a claim that student review has already occurred.
