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

def load_puzzle(self, filename):

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
