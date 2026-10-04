from dataclasses import dataclass

class FutoshikiPuzzle:

    def __init__(self):
        self.size = 0
        self.givens = {}
        self.inequalities = []

    def reset(self):
        """Clear the current puzzle."""
        self.size = 0
        self.givens = {}
        self.inequalities = []


# ==========================================================
# PARSE PUZZLE FILE
# ==========================================================

def load_puzzle(filename):

    puzzle = FutoshikiPuzzle()

    try:
        with open(filename, "r") as file:
            lines = file.readlines()

    except OSError as error:
        raise ValueError(
            f"Could not open file:\n{error}"
        )

    # Remove blank lines and comments
    cleaned_lines = []

    for line_number, line in enumerate(lines, start=1):

        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        cleaned_lines.append(
            (line_number, line)
        )

    if not cleaned_lines:
        raise ValueError(
            "The file is empty."
        )

    # ------------------------------------------------------
    # Find sections
    # ------------------------------------------------------

    sections = {
        "SIZE": [],
        "GIVENS": [],
        "INEQUALITIES": []
    }

    current_section = None

    for line_number, line in cleaned_lines:

        upper_line = line.upper()

        if upper_line in sections:

            current_section = upper_line
            continue

        # Unknown section
        if line.isupper() and "," not in line:
            raise ValueError(
                f"Unknown section '{line}' "
                f"at line {line_number}."
            )

        if current_section is None:
            raise ValueError(
                f"Data appears before a section heading "
                f"at line {line_number}."
            )

        sections[current_section].append(
            (line_number, line)
        )

    # ------------------------------------------------------
    # Validate SIZE
    # ------------------------------------------------------

    if len(sections["SIZE"]) != 1:
        raise ValueError(
            "SIZE section must contain exactly one integer."
        )

    size_line_number, size_text = sections["SIZE"][0]

    try:
        size = int(size_text)

    except ValueError:
        raise ValueError(
            f"Invalid SIZE value at line "
            f"{size_line_number}."
        )

    if size <= 0:
        raise ValueError(
            "SIZE must be a positive integer."
        )

    puzzle.size = size

    # ------------------------------------------------------
    # Validate GIVENS
    # ------------------------------------------------------

    row_values = {}
    col_values = {}

    for line_number, text in sections["GIVENS"]:

        parts = [part.strip() for part in text.split(",")]

        if len(parts) != 3:
            raise ValueError(
                f"Invalid GIVENS entry at line "
                f"{line_number}.\n"
                f"Expected: row,column,value"
            )

        try:
            row = int(parts[0])
            col = int(parts[1])
            value = int(parts[2])

        except ValueError:
            raise ValueError(
                f"GIVENS values must be integers "
                f"at line {line_number}."
            )

        # Check ranges
        if not (1 <= row <= size):
            raise ValueError(
                f"Row {row} is outside the range "
                f"1..{size} at line {line_number}."
            )

        if not (1 <= col <= size):
            raise ValueError(
                f"Column {col} is outside the range "
                f"1..{size} at line {line_number}."
            )

        if not (1 <= value <= size):
            raise ValueError(
                f"Value {value} is outside the range "
                f"1..{size} at line {line_number}."
            )

        cell = (row, col)

        # Repeated cell
        if cell in puzzle.givens:
            raise ValueError(
                f"Cell ({row},{col}) is given more than once."
            )

        # Duplicate value in same row
        if row not in row_values:
            row_values[row] = {}

        if value in row_values[row]:
            previous_col = row_values[row][value]

            raise ValueError(
                f"Duplicate fixed value {value} "
                f"in row {row}: columns "
                f"{previous_col} and {col}."
            )

        row_values[row][value] = col

        # Duplicate value in same column
        if col not in col_values:
            col_values[col] = {}

        if value in col_values[col]:
            previous_row = col_values[col][value]

            raise ValueError(
                f"Duplicate fixed value {value} "
                f"in column {col}: rows "
                f"{previous_row} and {row}."
            )

        col_values[col][value] = row

        puzzle.givens[cell] = value

    # ------------------------------------------------------
    # Validate INEQUALITIES
    # ------------------------------------------------------

    inequality_cells = set()

    for line_number, text in sections["INEQUALITIES"]:

        parts = [part.strip() for part in text.split(",")]

        if len(parts) != 5:
            raise ValueError(
                f"Invalid INEQUALITIES entry at line "
                f"{line_number}.\n"
                f"Expected: row1,column1,operator,row2,column2"
            )

        try:
            row1 = int(parts[0])
            col1 = int(parts[1])
            operator = parts[2]
            row2 = int(parts[3])
            col2 = int(parts[4])

        except ValueError:
            raise ValueError(
                f"Invalid integer in inequality "
                f"at line {line_number}."
            )

        # Validate operator
        if operator not in ("<", ">"):
            raise ValueError(
                f"Invalid operator '{operator}' "
                f"at line {line_number}."
            )

        # Validate coordinates
        if not (1 <= row1 <= size):
            raise ValueError(
                f"First row {row1} is outside the range "
                f"1..{size} at line {line_number}."
            )

        if not (1 <= col1 <= size):
            raise ValueError(
                f"First column {col1} is outside the range "
                f"1..{size} at line {line_number}."
            )

        if not (1 <= row2 <= size):
            raise ValueError(
                f"Second row {row2} is outside the range "
                f"1..{size} at line {line_number}."
            )

        if not (1 <= col2 <= size):
            raise ValueError(
                f"Second column {col2} is outside the range "
                f"1..{size} at line {line_number}."
            )

        # Repeated inequality endpoints
        endpoint_pair = (
            (row1, col1),
            (row2, col2)
        )

        if endpoint_pair in inequality_cells:
            raise ValueError(
                f"Repeated inequality between "
                f"({row1},{col1}) and ({row2},{col2})."
            )

        inequality_cells.add(endpoint_pair)

        # Check horizontal/vertical adjacency
        row_difference = abs(row1 - row2)
        col_difference = abs(col1 - col2)

        if row_difference + col_difference != 1:
            raise ValueError(
                f"Inequality cells "
                f"({row1},{col1}) and "
                f"({row2},{col2}) are not adjacent."
            )

        puzzle.inequalities.append(
            (
                row1,
                col1,
                operator,
                row2,
                col2
            )
        )

    return puzzle

# Check a candidate against constraints whose other values are already assigned.
# References: COSC-4117EL-01 Assignment 1, Required CSP model and Task 2;
# student's "Check Cell Consistency" algorithm in this conversation.
# AI disclosure: Generated by OpenAI Codex from the student's algorithm.
# Prompt link: TODO(student): add this conversation's share link to code/report.
def is_consistent_so_far(puzzle, assignments, cell, value):
    """Return whether a candidate fits a partial assignment, without changing it.

    Cells are one-based (row, column) tuples. Assignments is a dictionary
    containing known values, including the puzzle's fixed clues.
    """
    n = puzzle.size
    if type(n) is not int or n <= 0 or not isinstance(assignments, dict):
        return False
    if not isinstance(cell, tuple) or len(cell) != 2:
        return False

    row, col = cell
    if type(row) is not int or type(col) is not int:
        return False
    if not (1 <= row <= n and 1 <= col <= n):
        return False

    # bool is an int subclass in Python, but is not a puzzle number.
    if type(value) is not int or not 1 <= value <= n:
        return False
    if cell in puzzle.givens and puzzle.givens[cell] != value:
        return False
    if cell in assignments and assignments[cell] != value:
        return False

    for other_cell, other_value in assignments.items():
        if other_cell == cell:
            continue
        other_row, other_col = other_cell
        if (other_row == row or other_col == col) and other_value == value:
            return False

    for row1, col1, operator, row2, col2 in puzzle.inequalities:
        left, right = (row1, col1), (row2, col2)
        if cell == left and right in assignments:
            left_value, right_value = value, assignments[right]
        elif cell == right and left in assignments:
            left_value, right_value = assignments[left], value
        else:
            # Unrelated rules or rules with an unknown endpoint cannot fail yet.
            continue

        if operator == "<":
            if not left_value < right_value:
                return False
        elif operator == ">":
            if not left_value > right_value:
                return False
        else:
            return False

    return True


# Independently verify completeness and every Futoshiki constraint.
# References: COSC-4117EL-01 Assignment 1, puzzle rules and Task 4;
# student's "Validate Complete Solution" algorithm in this conversation.
# AI disclosure: Generated by OpenAI Codex from the student's algorithm.
# Prompt link: TODO(student): add this conversation's share link to code/report.
def validate_solution(puzzle, assignments):
    """Return whether a dictionary is a complete solution, without changing it."""
    n = puzzle.size
    if type(n) is not int or n <= 0 or not isinstance(assignments, dict):
        return False

    expected_cells = {
        (row, col)
        for row in range(1, n + 1)
        for col in range(1, n + 1)
    }
    # Exact coverage rejects both missing cells and extraneous coordinates.
    if set(assignments) != expected_cells:
        return False
    for cell, value in assignments.items():
        if any(type(coordinate) is not int for coordinate in cell):
            return False
        if type(value) is not int or not 1 <= value <= n:
            return False

    expected_values = set(range(1, n + 1))
    for row in range(1, n + 1):
        if {assignments[(row, col)] for col in range(1, n + 1)} != expected_values:
            return False
    for col in range(1, n + 1):
        if {assignments[(row, col)] for row in range(1, n + 1)} != expected_values:
            return False

    for cell, value in puzzle.givens.items():
        if cell not in assignments or assignments[cell] != value:
            return False

    for row1, col1, operator, row2, col2 in puzzle.inequalities:
        left, right = (row1, col1), (row2, col2)
        if left not in assignments or right not in assignments:
            return False
        left_value, right_value = assignments[left], assignments[right]
        if operator == "<":
            if not left_value < right_value:
                return False
        elif operator == ">":
            if not left_value > right_value:
                return False
        else:
            return False

    return True


@dataclass
class SolverResult:
    status: str
    solution: dict | None
    runtime: float
    nodes: int
