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

Click **Load Puzzle**, choose `puzzle_sample.txt`, select **Basic Backtracking** or
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
directly does not run a puzzle; its development stage demo has been removed.

## Solver behavior and measurements

- **Basic backtracking:** recursive DFS, row-major variable order, ascending
  candidate values, and consistency checks before committing an assignment.
- **AC-3 enhanced backtracking:** initial AC-3 propagation, MRV variable
  selection, degree tie-breaking using unresolved neighbors, and LCV ordering.
  Each tentative choice triggers AC-3 on incoming affected arcs. Each branch
  copies the domain dictionary and every domain set; failed branches restore
  the parent domains. Complete assignments pass `validate_solution`.
- **Timeout:** both solver functions accept `timeout` in seconds, defaulting to
  60. Both solvers check during initialization and search, after final
  validation, and before returning a result. AC-3 also checks during propagation
  and heuristic scans. Deadlines are cooperative: a helper may finish just after
  the deadline, but the result must then be reported as `Time out`.
- **Runtime:** measured with `time.perf_counter()` from before solver
  initialization through completion or timeout. Puzzle-file loading and GUI
  rendering are outside this interval. Both solvers are silent. The GUI prints
  one result summary after the solver returns, outside the measured interval.
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

Each heading must appear exactly once, in this order: `SIZE`, `GIVENS`,
`INEQUALITIES`. `SIZE` requires exactly one positive integer; the other sections
may be empty. Headings are case-insensitive and surrounding whitespace is
ignored. Coordinates are one-based. Blank lines and lines beginning with `#`
are ignored. Files use UTF-8, with or without a byte-order mark. Repeated
inequality edges are rejected even when their endpoints are reversed. A failed
GUI load clears the previous puzzle and metrics; cancelling the picker preserves
them.

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
| `puzzle_sample.txt` | Supplied 4×4 example |
| `puzzles/` | 34 additional sample files: required sizes/difficulties, contradictions, boundary cases, and malformed files |
| `test_loading.py` | Section structure, records, ranges, encoding, and file errors |
| `test_solvers.py` | Both solvers, deadlines, node counts, independent validation, and an exhaustive small-case oracle |
| `test_gui.py` | Headless GUI behavior tests and optional real-Tk smoke test |
| `test_results.csv` | Editable manual test worksheet with 56 planned runs and outcome fields |

## Sample puzzles and difficulty

Puzzles are grouped by expected behavior: `puzzles/valid/` contains solvable
inputs, `puzzles/unsolvable/` contains correctly formatted contradictions, and
`puzzles/invalid/` contains malformed inputs rejected by the loader. `puzzle_sample.txt`
remains the original assignment example at the project root.

| Files | Scenario / expected result |
| --- | --- |
| `valid/4x4_easy.txt`, `valid/6x6_easy.txt`, `valid/8x8_easy.txt` | Valid, densely clued; Solved |
| `valid/4x4_challenging.txt`, `valid/6x6_challenging.txt`, `valid/8x8_challenging.txt` | Valid, sparsely clued; Solved |
| `unsolvable/4x4_unsolvable.txt`, `unsolvable/6x6_unsolvable.txt`, `unsolvable/8x8_unsolvable.txt` | Valid format, strict inequality cycle; No solution |
| `unsolvable/4x4_unsolvable_givens.txt` | Locally valid givens leave a cell without a possible value; No solution |
| `valid/4x4_empty.txt` | Both record sections empty, multiple solutions; Solved |
| `valid/4x4_complete.txt` | Already solved, zero assignment attempts; Solved |
| `valid/1x1_valid.txt` | Smallest positive size; Solved |
| `invalid/malformed_*.txt` (16 files) | Missing/repeated/out-of-order/unknown headings, records before headings, invalid integers/ranges/field counts, repeated cells, duplicate row/column givens, invalid operators, nonadjacent cells, or reversed duplicate edges; Invalid puzzle |

The easy/challenging pairs use the same underlying Latin square for each size,
constructed by shuffling rows, columns, and symbols of a cyclic Latin square
with Python `random.Random(4117 + N)`. Easy puzzles retain 75% of fixed values
and 35% of adjacent inequality edges; challenging puzzles retain 15% and 25%,
respectively (counts rounded down). Clues are nested between each pair. These
are construction labels, not calibrated human difficulty ratings. All six
puzzles were solved and independently validated with both methods during the
regression checks; challenging cases required more baseline nodes at each size.
Uniqueness is not guaranteed or required: any independently valid completion
is accepted.

The cycle cases require `a < b < c < d < a`, which is impossible. The givens-only
case forces row 1's last value to be 4, but column 4 already contains 4. These
arguments establish unsatisfiability independently of the solvers. Calling
`validate_solution` on a missing solution cannot establish unsatisfiability.

## Run the tests

```bash
python3 -m unittest discover -v
```

The suite covers all sample files with both solvers and validates each returned
solution. It also compares 60 deterministic 3×3 cases against an exhaustive
Latin-square oracle, checks baseline ordering and node counts, verifies silent
solver execution, and uses a controlled clock for timeout regression tests
(including expiration inside final validation).

GUI tests exercise actual controller methods with mocked Tk widgets and dialogs,
including loading errors, cancellation, both methods, status/metric updates,
fixed/generated colours, all eight clue orientations, and shrinking the grid.
A real-widget smoke test runs when a graphical display is available and reports
an explicit skip otherwise. Tkinter itself is still required for GUI tests.
On a desktop, also run the GUI to inspect visual spacing and window behavior;
headless tests cannot establish visual quality or responsiveness. The current GUI
runs solvers synchronously, so it can be unresponsive during a long solve.

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
- **OpenAI Codex:** previously ran temporary solver checks and wrote the initial
  README from the code and supplied assignment requirements.
- **OpenAI Codex:** tightened section/edge/encoding validation, fixed baseline
  timeout reporting, removed timed debug output, cleared stale GUI state after
  invalid loads, and added regression tests, generated sample puzzles, and the
  editable results worksheet in response to the current testing request.
- **OpenAI Codex:** organized puzzles into valid/invalid/unsolvable folders,
  updated test and worksheet paths, and generated and verified five additional
  valid puzzles for performance and representation comparisons.

**Prompt links:**
- https://chatgpt.com/s/cx_6ac9a7918b8881918cd92ac9eaac7337
- https://chatgpt.com/s/cx_6ace5baac22c8191964a80d948bbdda9