# -*- coding: utf-8 -*-
"""
CPSC-4117EL-01 Artificial Intelligence
Assignment 1 - Futoshiki Puzzle Solver

Task 1:
GUI and Puzzle Loading

Generative AI disclosure:
This code was developed with assistance from ChatGPT.
The code was reviewed, tested, and modified by the student.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import time


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


class FutoshikiGUI:
    """
    Main GUI application for Assignment 1.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Futoshiki Puzzle Solver - Assignment 1")
        self.root.geometry("850x700")

        self.puzzle = FutoshikiPuzzle()

        # Store references to grid cells
        self.cells = {}

        # -----------------------------
        # Top title
        # -----------------------------

        title = tk.Label(
            root,
            text="Futoshiki Puzzle Solver",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=10)

        # -----------------------------
        # Control frame
        # -----------------------------

        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)

        self.load_button = tk.Button(
            control_frame,
            text="Load Puzzle",
            width=15,
            command=self.load_puzzle
        )
        self.load_button.grid(row=0, column=0, padx=5)

        self.solve_button = tk.Button(
            control_frame,
            text="Solve",
            width=15,
            command=self.solve
        )
        self.solve_button.grid(row=0, column=1, padx=5)

        # -----------------------------
        # Solver selection
        # -----------------------------

        solver_label = tk.Label(
            control_frame,
            text="Solver:"
        )
        solver_label.grid(row=0, column=2, padx=(20, 5))

        self.solver_var = tk.StringVar()
        self.solver_var.set("Basic Backtracking")

        self.solver_menu = tk.OptionMenu(
            control_frame,
            self.solver_var,
            "Basic Backtracking",
            "AC-3 Enhanced Backtracking"
        )
        self.solver_menu.grid(row=0, column=3, padx=5)

        # -----------------------------
        # Status
        # -----------------------------

        status_frame = tk.Frame(root)
        status_frame.pack(pady=5)

        tk.Label(
            status_frame,
            text="Status:",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, padx=5)

        self.status_label = tk.Label(
            status_frame,
            text="No puzzle loaded",
            font=("Arial", 11)
        )
        self.status_label.grid(row=0, column=1, padx=5)

        # -----------------------------
        # Metrics
        # -----------------------------

        metrics_frame = tk.Frame(root)
        metrics_frame.pack(pady=5)

        tk.Label(
            metrics_frame,
            text="Runtime:"
        ).grid(row=0, column=0, padx=5)

        self.runtime_label = tk.Label(
            metrics_frame,
            text="-"
        )
        self.runtime_label.grid(row=0, column=1, padx=5)

        tk.Label(
            metrics_frame,
            text="Nodes Visited:"
        ).grid(row=0, column=2, padx=5)

        self.nodes_label = tk.Label(
            metrics_frame,
            text="-"
        )
        self.nodes_label.grid(row=0, column=3, padx=5)

        # -----------------------------
        # Puzzle area
        # -----------------------------

        self.puzzle_frame = tk.Frame(root)
        self.puzzle_frame.pack(pady=20)

        # -----------------------------
        # Information area
        # -----------------------------

        self.info_label = tk.Label(
            root,
            text="Load a Futoshiki puzzle TXT file.",
            font=("Arial", 10)
        )
        self.info_label.pack(pady=10)

    # ==========================================================
    # TASK 1 - LOAD PUZZLE
    # ==========================================================

    def load_puzzle(self):
        """
        Open a file picker and load a Futoshiki TXT file.
        """

        filename = filedialog.askopenfilename(
            title="Select Futoshiki Puzzle",
            filetypes=[
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )

        if not filename:
            return

        try:
            puzzle = self.parse_puzzle_file(filename)

            self.puzzle = puzzle

            self.display_puzzle()

            self.status_label.config(
                text="Puzzle loaded successfully"
            )

            self.runtime_label.config(text="-")
            self.nodes_label.config(text="-")

            self.info_label.config(
                text=f"Puzzle size: {puzzle.size} x {puzzle.size}"
            )

        except ValueError as error:
            self.status_label.config(
                text="Invalid puzzle"
            )

            messagebox.showerror(
                "Invalid Puzzle",
                str(error)
            )

    # ==========================================================
    # PARSE PUZZLE FILE
    # ==========================================================

    def parse_puzzle_file(self, filename):

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

    # ==========================================================
    # DISPLAY PUZZLE
    # ==========================================================

    def display_puzzle(self):

        # Remove old puzzle
        for widget in self.puzzle_frame.winfo_children():
            widget.destroy()

        self.cells = {}

        n = self.puzzle.size

        # ------------------------------------------------------
        # Create grid
        # ------------------------------------------------------

        for row in range(1, n + 1):

            for col in range(1, n + 1):

                value = self.puzzle.givens.get(
                    (row, col),
                    ""
                )

                cell = tk.Label(
                    self.puzzle_frame,
                    text=str(value),
                    width=5,
                    height=2,
                    font=("Arial", 16, "bold"),
                    relief="solid",
                    borderwidth=1
                )

                cell.grid(
                    row=(row - 1) * 2,
                    column=(col - 1) * 2,
                    padx=2,
                    pady=2
                )

                self.cells[(row, col)] = cell

        # ------------------------------------------------------
        # Display inequalities
        # ------------------------------------------------------

        for row1, col1, operator, row2, col2 in self.puzzle.inequalities:

            # Horizontal inequality
            if row1 == row2:

                if col2 == col1 + 1:
                    symbol = operator

                else:
                    # Reverse direction
                    symbol = "<" if operator == ">" else ">"

                symbol_label = tk.Label(
                    self.puzzle_frame,
                    text=symbol,
                    font=("Arial", 14, "bold")
                )

                symbol_label.grid(
                    row=(row1 - 1) * 2,
                    column=(min(col1, col2) - 1) * 2 + 1
                )

            # Vertical inequality
            else:

                if row2 == row1 + 1:
                    symbol = operator

                else:
                    symbol = "<" if operator == ">" else ">"

                symbol_label = tk.Label(
                    self.puzzle_frame,
                    text=symbol,
                    font=("Arial", 14, "bold")
                )

                symbol_label.grid(
                    row=(min(row1, row2) - 1) * 2 + 1,
                    column=(col1 - 1) * 2
                )

    # ==========================================================
    # SOLVE BUTTON
    # ==========================================================

    def solve(self):

        if self.puzzle.size == 0:

            messagebox.showwarning(
                "No Puzzle",
                "Please load a puzzle first."
            )

            return

        # Task 1 placeholder
        #
        # Tasks 2 and 3 will implement the actual solvers.

        selected_solver = self.solver_var.get()

        self.status_label.config(
            text="Solving..."
        )

        self.root.update_idletasks()

        start_time = time.perf_counter()

        # Temporary result for Task 1
        time.sleep(0.05)

        elapsed = time.perf_counter() - start_time

        self.runtime_label.config(
            text=f"{elapsed:.6f} seconds"
        )

        self.nodes_label.config(
            text="0"
        )

        self.status_label.config(
            text=f"{selected_solver} selected"
        )

        messagebox.showinfo(
            "Task 1",
            "GUI and puzzle loading are working.\n\n"
            "The actual solver will be implemented in "
            "Tasks 2 and 3."
        )


# ==============================================================
# MAIN PROGRAM
# ==============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = FutoshikiGUI(root)

    root.mainloop()