"""
game_logic.py — Core Game State & Goff's Quantum Tic-Tac-Toe Rules
==================================================================

THE BIG PICTURE:
In classical Tic-Tac-Toe, you place one mark (X or O) in one square.
In Quantum Tic-Tac-Toe (Goff's version), each move places a mark in
TWO squares simultaneously — the mark is in a "superposition" of being
in either square. We don't know which square it'll end up in until
a "collapse" happens.

KEY CONCEPTS:
1. QUANTUM MARK: A single move like X₁ that exists in 2 squares at once.
2. ENTANGLEMENT: The two squares sharing a mark are "linked" — if the mark
   ends up in square A, it can't be in square B.
3. CYCLE: When a chain of entangled marks forms a closed loop.
   Example: X₁ is in cells (0,1), O₂ is in cells (1,2), X₃ is in cells (2,0)
   → This forms a cycle: 0→1→2→0. Collapse is triggered!
4. COLLAPSE: When a cycle forms, all marks in the cycle must "decide"
   which square they actually belong to. The opponent chooses the resolution.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QuantumMark:
    """
    Represents a single quantum move.

    Example: Player X's 3rd move (move_number=3) placed in cells 2 and 5.
    This means "X₃ is in a superposition of being in cell 2 OR cell 5".

    Attributes:
        player: 'X' or 'O' — who made this move
        move_number: Which move this is (1st, 2nd, 3rd, etc.)
        cells: Tuple of 2 cell indices (0-8) where this mark lives
    """
    player: str          # 'X' or 'O'
    move_number: int     # 1, 2, 3, 4, ...
    cells: tuple         # (cell_a, cell_b) — the two squares it occupies


class GameState:
    """
    Manages the entire Quantum Tic-Tac-Toe game.

    The board has 9 cells (indexed 0-8), laid out as:
        0 | 1 | 2
        ---------
        3 | 4 | 5
        ---------
        6 | 7 | 8

    Each cell can contain:
    - Multiple QUANTUM marks (before collapse) — e.g., cell 0 might have [X₁, O₂, X₅]
    - One CLASSICAL mark (after collapse) — e.g., cell 0 is definitively "X"
    """

    def __init__(self):
        # ---- QUANTUM LAYER ----
        # For each cell (0-8), store a list of quantum marks present there.
        # Example: quantum_cells[0] = [QuantumMark('X',1,(0,3)), QuantumMark('O',2,(0,5))]
        # means cell 0 has X₁ and O₂ floating in it (not yet collapsed).
        self.quantum_cells: list[list[QuantumMark]] = [[] for _ in range(9)]

        # ---- CLASSICAL LAYER ----
        # After collapse, a cell gets a definite mark. None means not yet collapsed.
        # Example: classical_cells[0] = 'X' means cell 0 is definitively X.
        self.classical_cells: list[Optional[str]] = [None] * 9

        # ---- GAME TRACKING ----
        self.move_number = 1                    # Current move number (starts at 1)
        self.current_player = 'X'               # X always goes first
        self.all_marks: list[QuantumMark] = []   # History of all quantum marks placed
        self.game_over = False
        self.winner: Optional[str] = None        # 'X', 'O', or 'Draw'

        # ---- COLLAPSE STATE ----
        # When a cycle is detected, we pause the game and ask the opponent
        # to choose how to resolve it.
        self.pending_collapse = False
        self.collapse_cycle: list[int] = []      # Cells involved in the cycle
        self.collapse_options: list[dict] = []    # Possible collapse resolutions

    def is_cell_available(self, cell: int) -> bool:
        """
        A cell is available for quantum marks if it hasn't been collapsed
        into a classical mark yet.

        Note: A cell CAN have multiple quantum marks in it — that's fine!
        It's only blocked once it collapses to a definite X or O.
        """
        return self.classical_cells[cell] is None

    def place_quantum_mark(self, cell_a: int, cell_b: int) -> Optional[list[int]]:
        """
        Place a quantum mark in two cells simultaneously.

        This is the core move in Quantum Tic-Tac-Toe:
        - The current player chooses 2 different available cells.
        - A quantum mark (e.g., X₁) is placed in BOTH cells.
        - This represents superposition: the mark is "in both places at once".

        After placing, we check if this move created an entanglement CYCLE.

        Args:
            cell_a: First cell index (0-8)
            cell_b: Second cell index (0-8)

        Returns:
            List of cells forming a cycle (if one was created), or None.
        """
        # Validate the move
        if cell_a == cell_b:
            raise ValueError("Must choose two DIFFERENT cells!")
        if not self.is_cell_available(cell_a) or not self.is_cell_available(cell_b):
            raise ValueError("One or both cells are already collapsed (classical)!")

        # Create the quantum mark
        mark = QuantumMark(
            player=self.current_player,
            move_number=self.move_number,
            cells=(cell_a, cell_b)
        )

        # Place it in both cells
        self.quantum_cells[cell_a].append(mark)
        self.quantum_cells[cell_b].append(mark)
        self.all_marks.append(mark)

        # Check if this move created a cycle
        cycle = self._detect_cycle()

        if cycle:
            # A cycle was found! Prepare for collapse.
            self.pending_collapse = True
            self.collapse_cycle = cycle
            self.collapse_options = self._generate_collapse_options(mark, cycle)
        else:
            # No cycle — just advance to the next move.
            self._advance_turn()

        return cycle

    def _detect_cycle(self) -> Optional[list[int]]:
        """
        Detect if there's a cycle (closed loop) in the entanglement graph.

        HOW THIS WORKS (Graph Theory):
        Think of cells as NODES and quantum marks as EDGES in a graph.
        If mark X₁ is in cells (0, 3), there's an edge between node 0 and node 3.

        A CYCLE exists when you can follow edges and come back to where you started.
        Example:
            X₁ in (0, 1) → edge 0-1
            O₂ in (1, 2) → edge 1-2
            X₃ in (2, 0) → edge 2-0
            Cycle: 0 → 1 → 2 → 0  ✓

        We use DFS (Depth-First Search) to find cycles.

        Returns:
            List of cell indices forming the cycle, or None if no cycle exists.
        """
        # Build adjacency list — only for cells that haven't collapsed yet
        # (collapsed cells are "done" and don't participate in new cycles)
        adjacency: dict[int, set[int]] = {i: set() for i in range(9)}

        for mark in self.all_marks:
            a, b = mark.cells
            # Only consider marks where BOTH cells are still quantum (not collapsed)
            if self.classical_cells[a] is None and self.classical_cells[b] is None:
                adjacency[a].add(b)
                adjacency[b].add(a)

        # DFS to find a cycle
        visited = set()
        for start_node in range(9):
            if start_node in visited or not adjacency[start_node]:
                continue
            # DFS with parent tracking
            cycle = self._dfs_find_cycle(start_node, visited, adjacency)
            if cycle:
                return cycle

        return None

    def _dfs_find_cycle(self, start: int, visited: set, adjacency: dict) -> Optional[list[int]]:
        """
        DFS (Depth-First Search) to find a cycle starting from a given node.

        HOW DFS WORKS:
        1. Start at a node, mark it "visited"
        2. Go to each unvisited neighbor
        3. If we reach a node that's ALREADY visited (and it's not our parent),
           we've found a cycle!
        4. Backtrack to reconstruct the cycle path

        Args:
            start: The starting cell index
            visited: Set of already-visited cells (shared across all DFS calls)
            adjacency: Graph adjacency list

        Returns:
            List of cells forming the cycle, or None.
        """
        # Stack stores: (current_node, parent_node, path_so_far)
        stack = [(start, -1, [start])]
        local_visited = set()

        while stack:
            node, parent, path = stack.pop()
            if node in local_visited:
                # We've come back to a visited node → CYCLE FOUND!
                # Extract just the cycle portion from the path
                cycle_start_idx = path.index(node)
                return path[cycle_start_idx:]
            local_visited.add(node)
            visited.add(node)

            for neighbor in adjacency[node]:
                if neighbor == parent:
                    continue  # Don't go back to where we just came from
                if neighbor in local_visited:
                    # Found a cycle! Return the path + the repeated node
                    return path + [neighbor]
                stack.append((neighbor, node, path + [neighbor]))

        return None

    def _generate_collapse_options(self, triggering_mark: QuantumMark,
                                     cycle: list[int]) -> list[dict]:
        """
        Generate the possible ways to collapse the cycle.

        In Goff's rules, the OPPONENT (the player who did NOT create the cycle)
        gets to choose how the collapse resolves.

        The triggering mark is the one that completed the cycle.
        The opponent chooses which of its two cells becomes the "real" location.
        This choice then cascades through the cycle, forcing all other marks
        to resolve.

        Returns:
            List of dicts, each representing one possible collapse resolution.
            Each dict maps cell_index → 'X' or 'O' (the classical mark).
        """
        options = []

        # The triggering mark can go to either of its two cells.
        # Each choice creates a different cascade of collapses.
        for chosen_cell in triggering_mark.cells:
            resolution = {}
            self._resolve_cascade(triggering_mark, chosen_cell, resolution)
            if resolution:  # Only add if valid
                options.append(resolution)

        return options

    def _resolve_cascade(self, mark: QuantumMark, chosen_cell: int,
                         resolution: dict):
        """
        Resolve a collapse cascade starting from one mark's chosen cell.

        HOW CASCADE WORKS:
        1. Mark M is forced into cell A (its "chosen" cell).
        2. Mark M is removed from its other cell B.
        3. Now check cell B — are there other marks there?
        4. If another mark N was sharing cell B with mark M, and mark N's
           other cell is already resolved, then mark N is forced into cell B.
        5. Continue until all marks in the cycle are resolved.

        This is like dominoes falling — one choice triggers a chain reaction!
        """
        if chosen_cell in resolution:
            return  # Already resolved

        # Place this mark's player into the chosen cell
        resolution[chosen_cell] = mark.player

        # The OTHER cell of this mark is now "rejected" — the mark is NOT there
        other_cell = mark.cells[0] if mark.cells[1] == chosen_cell else mark.cells[1]

        # Find all other marks in the rejected cell
        for other_mark in self.quantum_cells[other_cell]:
            if other_mark is mark:
                continue  # Skip the mark we just resolved
            if other_mark.move_number == mark.move_number:
                continue  # Skip same mark

            # This other mark was also in the rejected cell.
            # Since our mark is NOT going to be there, this other mark
            # must go to its OTHER cell (if not already resolved).
            other_mark_other_cell = (other_mark.cells[0]
                                     if other_mark.cells[1] == other_cell
                                     else other_mark.cells[1])
            if other_mark_other_cell not in resolution:
                self._resolve_cascade(other_mark, other_mark_other_cell, resolution)

    def apply_collapse(self, option_index: int):
        """
        Apply the chosen collapse resolution to the board.

        The opponent has chosen how to resolve the cycle. Now we:
        1. Set the classical marks for all cells in the resolution
        2. Remove quantum marks from collapsed cells
        3. Check if anyone won
        4. Advance the turn

        Args:
            option_index: Which collapse option the opponent chose (0 or 1)
        """
        resolution = self.collapse_options[option_index]

        # Apply each resolved cell
        for cell, player in resolution.items():
            self.classical_cells[cell] = player
            self.quantum_cells[cell] = []  # Clear quantum marks from this cell

        # Also remove any quantum marks from OTHER cells that reference
        # the collapsed cells (since those marks are now resolved)
        for cell in range(9):
            if self.classical_cells[cell] is not None:
                continue
            self.quantum_cells[cell] = [
                m for m in self.quantum_cells[cell]
                if self.classical_cells[m.cells[0]] is None
                   and self.classical_cells[m.cells[1]] is None
            ]

        # Reset collapse state
        self.pending_collapse = False
        self.collapse_cycle = []
        self.collapse_options = []

        # Check for winner
        self._check_winner()

        # Advance turn
        self._advance_turn()

    def _advance_turn(self):
        """Switch to the next player and increment move number."""
        self.move_number += 1
        self.current_player = 'O' if self.current_player == 'X' else 'X'

    def _check_winner(self):
        """
        Check if someone has won using classical marks.

        Same as classical Tic-Tac-Toe win check — but ONLY using collapsed
        (classical) cells. Quantum marks don't count for winning!

        Winning lines (3-in-a-row):
            Rows:     (0,1,2), (3,4,5), (6,7,8)
            Columns:  (0,3,6), (1,4,7), (2,5,8)
            Diagonals:(0,4,8), (2,4,6)
        """
        win_lines = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),   # columns
            (0, 4, 8), (2, 4, 6)                 # diagonals
        ]

        for a, b, c in win_lines:
            if (self.classical_cells[a] is not None
                    and self.classical_cells[a] == self.classical_cells[b]
                    and self.classical_cells[b] == self.classical_cells[c]):
                self.game_over = True
                self.winner = self.classical_cells[a]
                return

        # Check for draw: all cells are classical and no winner
        if all(cell is not None for cell in self.classical_cells):
            self.game_over = True
            self.winner = 'Draw'

    def get_available_cells(self) -> list[int]:
        """Return list of cell indices that are still available for quantum marks."""
        return [i for i in range(9) if self.is_cell_available(i)]

    def get_cell_display(self, cell: int) -> str:
        """
        Get the display string for a cell.

        If collapsed (classical): returns 'X' or 'O'
        If quantum: returns all quantum marks, e.g., 'X₁ O₂ X₅'
        If empty: returns ''
        """
        if self.classical_cells[cell] is not None:
            return self.classical_cells[cell]

        if self.quantum_cells[cell]:
            # Convert move numbers to subscript digits for nice display
            subscripts = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
            marks = []
            for mark in self.quantum_cells[cell]:
                num_str = str(mark.move_number).translate(subscripts)
                marks.append(f"{mark.player}{num_str}")
            return " ".join(marks)

        return ""
