"""
ui_components.py — Streamlit UI Helper Components
===================================================

This file handles how the game LOOKS in the browser.

It renders:
1. The 3x3 game board with quantum marks and classical marks
2. Color coding: X = blue, O = red, quantum marks = gray
3. The quantum circuit diagram
4. Game status messages
5. Collapse choice buttons
"""

import streamlit as st
from game_logic import GameState


# ─── COLOR SCHEME ──────────────────────────────────────────────────
# Colors for marks (makes the board easy to read)
X_COLOR = "#4A90D9"      # Blue for X
O_COLOR = "#D94A4A"      # Red for O
QUANTUM_COLOR = "#888888" # Gray for quantum (unresolved) marks
EMPTY_COLOR = "#333333"   # Dark for empty cells
BG_CLASSICAL = "#1a1a2e"  # Dark background for collapsed cells
BG_QUANTUM = "#16213e"    # Slightly different for quantum cells
BG_EMPTY = "#0f3460"      # Empty cell background
HIGHLIGHT = "#e94560"     # Highlight color for cycles


def render_board(game: GameState, on_cell_click=None):
    """
    Render the 3x3 game board using Streamlit columns and buttons.

    The board layout:
        [Cell 0] [Cell 1] [Cell 2]
        [Cell 3] [Cell 4] [Cell 5]
        [Cell 6] [Cell 7] [Cell 8]

    Each cell shows:
    - Classical mark (big X or O) if collapsed
    - Quantum marks (small X₁ O₂ etc.) if in superposition
    - Empty if no marks placed yet

    Cells that are part of an active collapse cycle are highlighted.
    """
    # Custom CSS for the board
    st.markdown("""
    <style>
    .board-cell {
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        min-height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 2px;
    }
    .classical-mark {
        font-size: 2.5em;
        font-weight: bold;
    }
    .quantum-marks {
        font-size: 0.9em;
        line-height: 1.4;
        color: #aaa;
    }
    .cell-highlight {
        border: 3px solid #e94560;
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0%, 100% { border-color: #e94560; }
        50% { border-color: #ff6b6b; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Render 3 rows of 3 cells
    for row in range(3):
        cols = st.columns(3, gap="small")
        for col_idx in range(3):
            cell = row * 3 + col_idx
            with cols[col_idx]:
                _render_cell(game, cell)


def _render_cell(game: GameState, cell: int):
    """
    Render a single cell of the board.

    Three possible states:
    1. CLASSICAL (collapsed): Show big X or O with color
    2. QUANTUM (has marks but not collapsed): Show small quantum marks
    3. EMPTY: Show the cell number as a placeholder
    """
    display = game.get_cell_display(cell)
    is_classical = game.classical_cells[cell] is not None
    is_in_cycle = cell in game.collapse_cycle
    has_quantum = len(game.quantum_cells[cell]) > 0

    if is_classical:
        # ── COLLAPSED CELL ──
        # Show the definite mark (big bold X or O)
        mark = game.classical_cells[cell]
        color = X_COLOR if mark == 'X' else O_COLOR
        st.markdown(
            f'<div class="board-cell" style="background:{BG_CLASSICAL};">'
            f'<span class="classical-mark" style="color:{color};">{mark}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    elif has_quantum:
        # ── QUANTUM CELL ──
        # Show all quantum marks floating in this cell
        border = f"border: 3px solid {HIGHLIGHT};" if is_in_cycle else ""
        st.markdown(
            f'<div class="board-cell" style="background:{BG_QUANTUM};{border}">'
            f'<span class="quantum-marks">{display}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        # ── EMPTY CELL ──
        # Show cell number as placeholder
        st.markdown(
            f'<div class="board-cell" style="background:{BG_EMPTY};">'
            f'<span style="color:#555;font-size:1.2em;">{cell}</span>'
            f'</div>',
            unsafe_allow_html=True
        )


def render_game_status(game: GameState):
    """
    Display the current game status.

    Shows:
    - Whose turn it is
    - If a collapse is pending (and who needs to choose)
    - If the game is over (and who won)
    """
    if game.game_over:
        if game.winner == 'Draw':
            st.success("🤝 **Game Over — It's a Draw!**")
        else:
            color = X_COLOR if game.winner == 'X' else O_COLOR
            st.success(f"🎉 **Game Over — Player {game.winner} Wins!**")
    elif game.pending_collapse:
        # The opponent of the current player must choose
        chooser = 'O' if game.current_player == 'X' else 'X'
        st.warning(
            f"⚡ **Entanglement Cycle Detected!** "
            f"Player **{chooser}** must choose how to collapse the board."
        )
    else:
        marker = "🔵" if game.current_player == 'X' else "🔴"
        st.info(
            f"{marker} **Player {game.current_player}'s Turn** "
            f"(Move #{game.move_number}) — "
            f"Select two cells for your quantum mark."
        )


def render_move_history(game: GameState):
    """
    Display the history of all moves made.

    Shows each move as: "Move 1: X₁ → cells (0, 3)"
    This helps players understand the entanglement web.
    """
    if not game.all_marks:
        st.caption("No moves yet.")
        return

    st.markdown("##### 📜 Move History")
    for mark in game.all_marks:
        subscripts = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        num_str = str(mark.move_number).translate(subscripts)
        color = X_COLOR if mark.player == 'X' else O_COLOR
        st.markdown(
            f'<span style="color:{color};">**{mark.player}{num_str}**</span>'
            f' → cells **{mark.cells[0]}** & **{mark.cells[1]}**',
            unsafe_allow_html=True
        )


def render_quantum_info():
    """
    Display educational information about the quantum mechanics used.

    This section explains the quantum principles to the player,
    making the game educational as well as fun.
    """
    with st.expander("🔬 How Quantum Mechanics Works in This Game"):
        st.markdown("""
        ### Quantum Principles at Play

        **1. Superposition (H Gate)**
        When you place a mark, it exists in TWO cells simultaneously —
        like Schrödinger's cat being both alive and dead.
        The Hadamard (H) gate puts the qubit into a 50/50 state.

        **2. Entanglement (CNOT Gate)**
        Your two chosen cells become "entangled" — measuring one
        instantly determines the other. Einstein called this
        "spooky action at a distance"!

        **3. Measurement Collapse**
        When an entanglement cycle forms, the quantum state MUST collapse.
        All the superpositions resolve into definite marks.
        This is like opening the box and seeing if the cat is alive or dead.

        **4. Strategic Interference**
        The opponent chooses HOW the collapse resolves,
        adding a strategic layer that doesn't exist in classical games.
        """)
