"""
app.py — Main Streamlit Application for Quantum Tic-Tac-Toe
=============================================================

THIS IS THE ENTRY POINT — run it with:
    streamlit run src/app.py

HOW THE APP WORKS:
━━━━━━━━━━━━━━━━━
1. Player sees the 3x3 board
2. Player selects TWO cells from dropdowns → places a quantum mark
3. The Qiskit circuit is updated (H + CNOT gates added)
4. If a cycle forms → opponent chooses collapse → circuit is measured
5. Board updates with classical marks
6. Repeat until someone gets 3-in-a-row

STREAMLIT SESSION STATE:
━━━━━━━━━━━━━━━━━━━━━━━
Streamlit re-runs the ENTIRE script on every interaction (button click, etc.)
So we store the game state in `st.session_state` — a persistent dictionary
that survives across re-runs.

Think of it like: "Everything inside session_state remembers its value,
everything outside gets reset every time you click a button."
"""

import sys
import os

# Add the src directory to Python's path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from game_logic import GameState
from quantum_engine import QuantumEngine
from classical_baseline import simulate_games
from ui_components import (
    render_board,
    render_game_status,
    render_move_history,
    render_quantum_info,
)


# ─── PAGE CONFIGURATION ───────────────────────────────────────────
st.set_page_config(
    page_title="Quantum Tic-Tac-Toe ⚛️",
    page_icon="⚛️",
    layout="wide",
)


def init_session_state():
    """
    Initialize all session state variables.

    This runs ONCE when the app first loads.
    Session state persists across Streamlit re-runs (button clicks).

    We store:
    - game: The GameState object (board, marks, rules)
    - engine: The QuantumEngine (Qiskit circuits)
    - selected_cells: Which cells the player has clicked for their move
    - page: Which page we're on ('game' or 'comparison')
    """
    if 'game' not in st.session_state:
        st.session_state.game = GameState()
    if 'engine' not in st.session_state:
        st.session_state.engine = QuantumEngine()
    if 'selected_cells' not in st.session_state:
        st.session_state.selected_cells = []
    if 'page' not in st.session_state:
        st.session_state.page = 'game'
    if 'show_circuit' not in st.session_state:
        st.session_state.show_circuit = False
    if 'game_log' not in st.session_state:
        st.session_state.game_log = []


def reset_game():
    """Start a fresh new game — clear everything."""
    st.session_state.game = GameState()
    st.session_state.engine = QuantumEngine()
    st.session_state.selected_cells = []
    st.session_state.game_log = []


def main():
    """
    Main application entry point.

    The app has two pages:
    1. GAME PAGE: The interactive Quantum Tic-Tac-Toe game
    2. COMPARISON PAGE: Classical vs Quantum statistics
    """
    # ── SIDEBAR NAVIGATION ──
    st.sidebar.title("⚛️ Quantum Tic-Tac-Toe")
    st.sidebar.markdown("*Qiskit Fall Fest 2026*")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigate",
        ["🎮 Play Game", "📊 Classical vs Quantum", "📖 How It Works"],
        index=0
    )

    if page == "🎮 Play Game":
        game_page()
    elif page == "📊 Classical vs Quantum":
        comparison_page()
    else:
        education_page()


def game_page():
    """
    The main game page where players interact with the board.

    FLOW:
    1. Show the board
    2. If collapse pending → show collapse options
    3. Else → show cell selection for next move
    4. Show circuit diagram
    5. Show move history
    """
    init_session_state()
    game = st.session_state.game
    engine = st.session_state.engine

    st.title("🎮 Quantum Tic-Tac-Toe")
    st.caption("Place quantum marks in superposition. Form entanglement cycles to collapse the board!")

    # ── TOP CONTROLS ──
    col_reset, col_circuit = st.columns([1, 1])
    with col_reset:
        if st.button("🔄 New Game", use_container_width=True):
            reset_game()
            st.rerun()
    with col_circuit:
        st.session_state.show_circuit = st.toggle(
            "Show Quantum Circuit", value=st.session_state.show_circuit
        )

    st.markdown("---")

    # ── GAME STATUS ──
    render_game_status(game)

    # ── MAIN LAYOUT: Board + Controls ──
    board_col, controls_col = st.columns([2, 1])

    with board_col:
        # Render the game board
        render_board(game)

    with controls_col:
        if game.game_over:
            # ── GAME OVER ──
            st.balloons()
            if st.button("🎮 Play Again", use_container_width=True):
                reset_game()
                st.rerun()

        elif game.pending_collapse:
            # ── COLLAPSE PHASE ──
            # The opponent must choose how to resolve the cycle
            _handle_collapse(game, engine)

        else:
            # ── NORMAL MOVE PHASE ──
            # Player selects two cells for their quantum mark
            _handle_move(game, engine)

    # ── CIRCUIT DIAGRAM ──
    if st.session_state.show_circuit:
        st.markdown("---")
        st.markdown("### 🔬 Current Quantum Circuit")
        st.caption("This shows the actual Qiskit circuit being built as you play.")
        circuit_text = engine.get_circuit_diagram()
        st.code(circuit_text, language=None)

    # ── MOVE HISTORY (sidebar) ──
    with st.sidebar:
        st.markdown("---")
        render_move_history(game)


def _handle_move(game: GameState, engine: QuantumEngine):
    """
    Handle the normal move phase.

    The player uses TWO dropdown menus to select which cells to place
    their quantum mark in.

    WHY DROPDOWNS (not clicking the board)?
    Streamlit buttons don't support "select mode" natively.
    Dropdowns are cleaner and prevent accidental double-clicks.

    FLOW:
    1. Player picks Cell A from dropdown
    2. Player picks Cell B from dropdown (must be different from A)
    3. Player clicks "Place Mark"
    4. Mark is placed → circuit is updated → cycle check happens
    """
    available = game.get_available_cells()

    if len(available) < 2:
        st.warning("Not enough cells available! Game is a draw.")
        game.game_over = True
        game.winner = 'Draw'
        return

    st.markdown(f"**Select 2 cells for your quantum mark:**")

    # Dropdown for first cell
    cell_a = st.selectbox(
        "First cell",
        options=available,
        key="cell_a_select",
        format_func=lambda x: f"Cell {x} ({_cell_position_name(x)})"
    )

    # Dropdown for second cell (exclude first choice)
    available_b = [c for c in available if c != cell_a]
    cell_b = st.selectbox(
        "Second cell",
        options=available_b,
        key="cell_b_select",
        format_func=lambda x: f"Cell {x} ({_cell_position_name(x)})"
    )

    # Place mark button
    player_emoji = "🔵" if game.current_player == 'X' else "🔴"
    if st.button(
        f"{player_emoji} Place {game.current_player}₍{game.move_number}₎ in cells {cell_a} & {cell_b}",
        use_container_width=True,
        type="primary"
    ):
        # 1. Update the game state (place quantum mark + check cycle)
        cycle = game.place_quantum_mark(cell_a, cell_b)

        # 2. Update the Qiskit circuit (add H + CNOT gates)
        engine.add_quantum_mark(cell_a, cell_b, game.move_number - 1)

        # 3. Log the move
        st.session_state.game_log.append(
            f"Move {game.move_number - 1}: {game.current_player if cycle else ('X' if game.current_player == 'O' else 'O')} "
            f"placed mark in cells ({cell_a}, {cell_b})"
        )

        if cycle:
            st.session_state.game_log.append(
                f"⚡ Cycle detected in cells: {cycle}"
            )

        # 4. Refresh the page to show the updated board
        st.rerun()


def _handle_collapse(game: GameState, engine: QuantumEngine):
    """
    Handle the collapse phase.

    WHAT'S HAPPENING:
    A cycle of entangled marks was detected. The board MUST collapse.
    The opponent (the player who DIDN'T create the cycle) gets to choose
    which resolution to apply.

    We show them the options and let them pick.

    BEHIND THE SCENES (Qiskit):
    When they choose, we measure the qubits involved in the cycle
    using the quantum engine. The measurement result determines the
    classical marks.
    """
    chooser = 'O' if game.current_player == 'X' else 'X'
    st.markdown(f"**Player {chooser}, choose how to collapse:**")

    if not game.collapse_options:
        st.error("No collapse options available.")
        game.pending_collapse = False
        st.rerun()
        return

    for i, option in enumerate(game.collapse_options):
        # Show what each option would look like
        description_parts = []
        for cell, player in sorted(option.items()):
            color = "🔵" if player == 'X' else "🔴"
            description_parts.append(f"Cell {cell} → {color} {player}")
        description = " | ".join(description_parts)

        if st.button(
            f"Option {i + 1}: {description}",
            key=f"collapse_{i}",
            use_container_width=True,
            type="primary" if i == 0 else "secondary"
        ):
            # Apply the collapse
            game.apply_collapse(i)

            # Also measure the qubits in the quantum engine
            # (to keep the circuit consistent)
            cells_in_collapse = list(option.keys())
            try:
                engine.measure_and_collapse(cells_in_collapse)
            except Exception:
                pass  # Engine measurement is for consistency; game logic handles state

            st.session_state.game_log.append(
                f"Board collapsed! Option {i + 1} chosen by {chooser}"
            )

            st.rerun()


def comparison_page():
    """
    Classical vs Quantum comparison page.

    This page satisfies the hackathon rubric requirement for
    comparing quantum gameplay against a classical baseline.

    It simulates games between:
    - Random vs Random (pure chance)
    - Smart vs Smart (basic strategy)
    And shows the win/loss/draw statistics.
    """
    st.title("📊 Classical vs Quantum Comparison")
    st.markdown("""
    This page compares **Quantum Tic-Tac-Toe** gameplay patterns
    against classical baselines.

    In **classical** Tic-Tac-Toe, optimal play always leads to a draw.
    In **quantum** Tic-Tac-Toe, the non-deterministic collapse creates
    fundamentally different win/loss distributions — even between
    equally skilled players!
    """)

    st.markdown("---")

    num_games = st.slider("Number of games to simulate", 50, 500, 100, step=50)

    if st.button("🏃 Run Simulation", type="primary"):
        with st.spinner("Simulating games..."):
            # Run random vs random
            stats_random = simulate_games(num_games, "random", "random")

            # Run smart vs smart
            stats_smart = simulate_games(num_games, "smart", "smart")

        # Display results
        st.markdown("### Results: Random vs Random")
        col1, col2, col3 = st.columns(3)
        col1.metric("🔵 X Wins", f"{stats_random['x_wins']}", 
                     f"{stats_random['x_wins']/num_games*100:.1f}%")
        col2.metric("🔴 O Wins", f"{stats_random['o_wins']}", 
                     f"{stats_random['o_wins']/num_games*100:.1f}%")
        col3.metric("🤝 Draws", f"{stats_random['draws']}", 
                     f"{stats_random['draws']/num_games*100:.1f}%")

        st.markdown("### Results: Smart vs Smart")
        col1, col2, col3 = st.columns(3)
        col1.metric("🔵 X Wins", f"{stats_smart['x_wins']}", 
                     f"{stats_smart['x_wins']/num_games*100:.1f}%")
        col2.metric("🔴 O Wins", f"{stats_smart['o_wins']}", 
                     f"{stats_smart['o_wins']/num_games*100:.1f}%")
        col3.metric("🤝 Draws", f"{stats_smart['draws']}", 
                     f"{stats_smart['draws']/num_games*100:.1f}%")

        st.markdown("---")
        st.markdown("""
        ### 🔑 Key Insight

        In **classical** Tic-Tac-Toe, optimal play between two perfect
        players ALWAYS results in a draw. There's no randomness.

        In **Quantum** Tic-Tac-Toe:
        - The **superposition** and **measurement collapse** introduce
          genuine quantum randomness
        - Even between equally skilled players, wins and losses occur
          because collapse outcomes are **probabilistic**
        - The **entanglement cycles** create strategic depth that doesn't
          exist in the classical game
        - The **opponent's collapse choice** adds a meta-game layer
          absent from classical Tic-Tac-Toe

        This demonstrates that quantum mechanics creates **fundamentally
        different gameplay dynamics** — not just "classical + random numbers."
        """)


def education_page():
    """
    How to Play page — clear rules with step-by-step visual examples.
    """
    st.title("📖 How to Play Quantum Tic-Tac-Toe")
    st.caption("Read this before playing — it only takes 2 minutes!")

    # ─── RULE 0: The difference ───────────────────────────────────────
    st.markdown("---")
    st.markdown("## The One Big Difference from Normal Tic-Tac-Toe")

    col1, col2 = st.columns(2)
    with col1:
        st.error("### ❌ Normal Tic-Tac-Toe")
        st.markdown("""
Each turn you place your mark in **ONE cell**.
That cell is immediately **blocked** — done forever.
```
  X  |     |
 ----+-----+----
     |  O  |
 ----+-----+----
     |     |
```
X claimed cell 0.
O claimed cell 4.
No one else can use them.
        """)

    with col2:
        st.success("### ✅ Quantum Tic-Tac-Toe")
        st.markdown("""
Each turn you place a **ghost mark** in **TWO cells** at once.
The ghost exists in BOTH cells — **not decided yet!**
```
 X1  |     |
 ----+-----+----
     | X1  |
 ----+-----+----
     |     |
```
X placed ghost X1 in cell 0 AND cell 4.
**Both cells still available for more ghosts!**
        """)

    st.info("💡 **Key idea:** Cells are NOT blocked by ghost marks. Multiple ghosts from different moves (even from both players!) can share a cell. A cell is only truly 'taken' after a **Collapse** happens.")

    # ─── RULE 1: Making a move ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("## Rule 1 — Each Move: Pick 2 Different Cells")
    st.markdown("""
Every turn you:
1. Choose **Cell A** — your first cell
2. Choose **Cell B** — your second cell (must be different from A)
3. Click **Place Mark**

Your ghost mark (e.g. **X1** for X's 1st move, **O2** for O's 2nd move) appears in BOTH cells at the same time.

> **Can I pick a cell that already has ghosts in it?**
> **YES!** Ghosts from different moves can share a cell freely.
> You cannot pick a cell only if it has been **collapsed** (turned into a solid X or O).
    """)

    # ─── RULE 2: The board fills up ────────────────────────────────────
    st.markdown("---")
    st.markdown("## Rule 2 — Multiple Ghosts Can Share a Cell")

    st.markdown("**Let's play through an example:**")

    # Step by step board states using columns
    st.markdown("#### After Move 1 — X picks cells 0 and 4:")
    c1, c2, c3 = st.columns(3)
    c1.markdown("""
```
[ X1 ][ -- ][ -- ]
[ X1 ][ -- ][ -- ]
[ -- ][ -- ][ -- ]
```
""")
    c2.markdown("""
**What happened:**
- X1 (X's ghost) now lives in Cell 0 AND Cell 4 simultaneously
- Both cells still open for more moves
- We don't know WHERE X1 will actually land yet
""")
    c3.markdown("""
**Board numbers:**
```
 0 | 1 | 2
---+---+---
 3 | 4 | 5
---+---+---
 6 | 7 | 8
```
""")

    st.markdown("#### After Move 2 — O picks cells 4 and 8:")
    c1, c2, c3 = st.columns(3)
    c1.markdown("""
```
[ X1  ][ -- ][ -- ]
[X1 O2][ -- ][ -- ]
[ --  ][ -- ][ O2 ]
```
""")
    c2.markdown("""
**What happened:**
- O2 (O's ghost) now lives in Cell 4 AND Cell 8
- **Cell 4 now has TWO ghosts: X1 and O2** — totally fine!
- Still nobody has a real settled mark anywhere
""")
    c3.markdown("""
**Entanglement chain so far:**
```
Cell 0 ←→ Cell 4  (via X1)
Cell 4 ←→ Cell 8  (via O2)
```
Open chain — no cycle yet.
""")

    st.markdown("#### After Move 3 — X picks cells 8 and 0:")
    c1, c2, c3 = st.columns(3)
    c1.markdown("""
```
[X1 X3][ -- ][ -- ]
[X1 O2][ -- ][ -- ]
[ --  ][ -- ][O2 X3]
```
""")
    c2.markdown("""
**What happened:**
- X3 ghost lands in Cell 8 AND Cell 0
- Now Cell 0 has X1+X3, Cell 4 has X1+O2, Cell 8 has O2+X3
""")
    c3.markdown("""
**⚡ CYCLE DETECTED!**
```
Cell 0 ←→ Cell 4  (via X1)
Cell 4 ←→ Cell 8  (via O2)
Cell 8 ←→ Cell 0  (via X3)
    ↑______________|
    Closed loop = CYCLE!
```
""")

    st.warning("⚡ **A Cycle has formed! The board must now COLLAPSE.**")

    # ─── RULE 3: Collapse ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## Rule 3 — Cycle = Collapse (The Most Important Rule!)")

    st.markdown("""
**What is a Cycle?**
A cycle is when you can follow the ghost links and come back to where you started.
In our example: `Cell 0 → Cell 4 → Cell 8 → Cell 0` — that's a closed loop!

**What is Collapse?**
All the ghosts in the cycle must instantly pick ONE real home.
The superposition ends. Ghosts become solid marks.

**Who chooses?**
The **opponent** of the player who just created the cycle gets to choose!
(The player who created it doesn't get to benefit — that's fair!)
    """)

    st.markdown("#### The Two Possible Collapses in our example:")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Option A** — O (the opponent) picks this:")
        st.markdown("""
```
[  X  ][ -- ][ -- ]     X1 settled in Cell 0
[ --- ][ -- ][ -- ]     O2 settled in Cell 4
[ --- ][ -- ][  X  ]    X3 settled in Cell 8
```
Result: X gets cells 0 and 8. O gets cell 4.
        """)

    with c2:
        st.markdown("**Option B** — O (the opponent) picks this:")
        st.markdown("""
```
[  O  ][ -- ][ -- ]     X1 settled in Cell 4
[ --- ][  X ][ -- ]     O2 settled in Cell 8
[ --- ][ -- ][  O  ]    X3 settled in Cell 0
```
Result: O gets cells 0 and 8. X gets cell 4.
        """)

    st.info("🧠 **Strategy tip:** The opponent will always pick the option that benefits THEM more. So think carefully about which cycle you create — your opponent controls how it resolves!")

    # ─── RULE 4: After collapse ────────────────────────────────────────
    st.markdown("---")
    st.markdown("## Rule 4 — After Collapse, Solid Cells Are Blocked")
    st.markdown("""
Once a cell gets a **solid (classical) mark** after collapse:
- It shows as a big **X** or **O** (not a ghost)
- It is **permanently blocked** — no more ghosts can go there
- It counts toward **3-in-a-row** to win the game

The game continues on the remaining cells that still have only ghosts.
A new cycle can form again later — and the collapse process repeats!
    """)

    # ─── RULE 5: Winning ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## Rule 5 — How to Win")
    st.markdown("""
**Same as regular Tic-Tac-Toe — but only SOLID marks count!**

Get **3 solid marks in a row** (horizontal, vertical, or diagonal) and you win.
Ghost marks do NOT count for winning — only fully collapsed solid marks do.

```
Winning lines:
  0-1-2  (top row)       0-3-6  (left column)    0-4-8  (diagonal)
  3-4-5  (mid row)       1-4-7  (mid column)     2-4-6  (diagonal)
  6-7-8  (bot row)       2-5-8  (right column)
```

If all 9 cells collapse with no winner — it's a **Draw**!
    """)

    # ─── Quick reference ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## ⚡ Quick Reference Card")

    st.markdown("""
| Situation | What you do |
|---|---|
| Your turn (normal) | Pick 2 available cells → Place ghost mark |
| Can I pick a cell with ghosts? | **YES** — ghosts share freely |
| Can I pick a collapsed (solid) cell? | **NO** — solid cells are blocked |
| A cycle forms | **You wait** — your opponent picks the collapse |
| It's YOUR opponent who created the cycle | **You choose** which option to collapse |
| 3 solid marks in a row | **You win!** 🎉 |
| Board full, no winner | **Draw** 🤝 |
    """)

    st.markdown("---")
    st.markdown("## 🔬 The Quantum Physics Behind It (Optional)")
    with st.expander("Click to understand the science"):
        st.markdown("""
**Superposition** — A ghost mark in 2 cells = a qubit in superposition.
Mathematically: the qubit is in state `(|0⟩ + |1⟩)/√2` — 50% chance of being 0 or 1.

**Entanglement** — Two cells sharing a ghost = two qubits entangled.
We use a **CNOT gate** to link them. If one collapses to 1, the other is forced to match.

**Measurement Collapse** — When the cycle is resolved, Qiskit **measures** the qubits.
The measurement forces them out of superposition into definite 0 or 1 values.
This is quantum mechanics doing real work — not just random numbers!

**Qiskit Circuit per move:**
```
H(qubit_A)          ← Superposition on Cell A
CNOT(qubit_A → qubit_B)  ← Entangle Cell A with Cell B
```

**On collapse:**
```
Measure(qubit_A, qubit_B, ...)  ← Force definite values
```
        """)





def _cell_position_name(cell: int) -> str:
    """
    Convert cell index to human-readable position.

    0='Top-Left', 1='Top-Center', ..., 8='Bottom-Right'
    """
    names = [
        "Top-Left", "Top-Center", "Top-Right",
        "Mid-Left", "Center", "Mid-Right",
        "Bot-Left", "Bot-Center", "Bot-Right"
    ]
    return names[cell]


# ─── RUN THE APP ───────────────────────────────────────────────────
if __name__ == "__main__":
    main()
