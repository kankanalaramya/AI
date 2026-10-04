# -*- coding: utf-8 -*-
"""
CPSC-4117EL-01 Artificial Intelligence
Assignment 1 - Futoshiki Puzzle Solver

Task 1:
GUI and Puzzle Loading

Generative AI disclosure:
This file was developed with assistance from ChatGPT.
The file was reviewed, tested, and modified by the student.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import time

from puzzle import FutoshikiPuzzle, load_puzzle
from tkinter import font as tkfont

class FutoshikiGUI:
    """
    Main GUI application for Assignment 1.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Futoshiki Puzzle Solver - Assignment 1")
        window_system = self.root.tk.call("tk", "windowingsystem")

        if window_system == "win32":
            self.root.state("zoomed")
        elif window_system == "x11":
            self.root.attributes("-zoomed", True)
        # Shared font for interface text.
        self.body_font = tkfont.nametofont("TkDefaultFont")
        self.body_font.configure(size=14)

        # Use this font for widgets created below.
        self.root.option_add("*Font", self.body_font)

        # A separate bold version for emphasized labels.
        self.bold_font = self.body_font.copy()
        self.bold_font.configure(weight="bold")

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
            puzzle = load_puzzle(filename)

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
    # DISPLAY PUZZLE
    # ==========================================================

    def display_puzzle(self):

        # Clear spacing settings left by the previous puzzle.
        old_columns, old_rows = self.puzzle_frame.grid_size()

        for column in range(old_columns):
            self.puzzle_frame.grid_columnconfigure(column, minsize=0)

        for row in range(old_rows):
            self.puzzle_frame.grid_rowconfigure(row, minsize=0)

        # Remove old puzzle
        for widget in self.puzzle_frame.winfo_children():
            widget.destroy()

        self.cells = {}

        n = self.puzzle.size

        # Leave room for a clue between every pair of rows and columns.
        gap = self.bold_font.metrics("linespace") + 12

        for position in range(1, 2 * n - 1, 2):
            self.puzzle_frame.grid_rowconfigure(position, minsize=gap)
            self.puzzle_frame.grid_columnconfigure(position, minsize=gap)

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
                    font=self.bold_font
                )

                symbol_label.grid(
                    row=(row1 - 1) * 2,
                    column=(min(col1, col2) - 1) * 2 + 1
                )

            # Vertical inequality
            else:

                # First express the relationship from top to bottom.
                if row1 < row2:
                    top_operator = operator
                else:
                    top_operator = "<" if operator == ">" else ">"

                # The pointed end faces the smaller value.
                symbol = "^" if top_operator == "<" else "v"

                symbol_label = tk.Label(
                    self.puzzle_frame,
                    text=symbol,
                    font=self.bold_font
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