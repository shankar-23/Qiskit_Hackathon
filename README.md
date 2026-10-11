# Quantum Tic-Tac-Toe ⚛️

## Project Metadata

* **Project Title:** `Quantum Tic-Tac-Toe — Superposition, Entanglement & Collapse on the 3×3 Board`
* **Team Name:** `Ravi Shankar Gupta`
* **Chosen Track:** `Track 1: Quantum Games & Interactive Puzzles`
* **Video Presentation Link:** `https://youtu.be/grqgZgDTQFw`
* **Live Demo Timestamp in Video:** `4:30 https://youtu.be/grqgZgDTQFw?si=H1RJIbZH-k5X-CSs`

### Team Member (Solo)

 `Ravi Shankar Gupta`  
 `ravishankar.kr440@gmail.com`  
 `https://github.com/shankar-23/Qiskit_Hackathon` |
---
## 1. Project Overview & Motivation

* **Summary:**
  We built a fully playable **Quantum Tic-Tac-Toe** web app based on Allan Goff's 2002 paper, powered by **Qiskit** for the quantum core and **Streamlit** for the interactive UI. Unlike classical Tic-Tac-Toe, players place *quantum marks* that exist in superposition across two cells simultaneously. Entanglement cycles between marks trigger a Qiskit-measured board collapse, resolving superpositions into classical marks. The game ends when a player achieves 3-in-a-row with classical marks.

* **Why this problem / game?**
  Classical Tic-Tac-Toe is completely solved — two optimal players always draw. Quantum Tic-Tac-Toe is a perfect pedagogical vehicle because it makes **superposition, entanglement, and measurement collapse** tangible and interactive game mechanics rather than abstract formulas. Goff's formulation is faithful to real quantum mechanics, and the opponent's collapse-choice mechanic adds genuine strategic depth that cannot exist in any classical game.

---

## 2. Quantum Architecture & Mechanics

* **Core Quantum Principles Used:**

  | Principle | Gate | Game Mechanic |
  
  | **Superposition** | H (Hadamard) | A quantum mark exists in 2 cells simultaneously until collapse |
  | **Entanglement** | CNOT | Two cells sharing a mark are non-locally linked |
  | **Measurement Collapse** | `measure` | Entanglement cycles are resolved by measuring the Qiskit circuit |
  | **Interference / Phase** | Z, Barrier | Strategic gate structure makes outcomes correlated, not independent |

* **How the Quantum Circuit is Integrated:**

  The board has **9 qubits** (q₀–q₈), one per cell. Every time a player places a quantum mark in cells (A, B):
  1. An **H gate** is applied to qubit A → puts it in superposition `(|0⟩ + |1⟩)/√2`
  2. A **CNOT gate** from qubit A to qubit B → creates a Bell state `(|00⟩ + |11⟩)/√2`

  When the game logic detects an **entanglement cycle** (a closed loop of linked cells), the Qiskit `StatevectorSampler` **measures** all qubits in the cycle with `shots=1`. The bitstring result collapses the superpositions into definite classical marks (|1⟩ = mark present, |0⟩ = mark absent).

* **Circuit Details:**
  * **Number of Qubits:** 9 (one per board cell)
  * **Key Gates Used:** H, CX (CNOT), Measure, Barrier
  * **Primitives Used:** `StatevectorSampler` (exact simulation, no noise)
  * **Other Technologies Used:** Streamlit for UI, Python `dataclasses` for game state, DFS graph traversal for cycle detection

```python
# Core quantum mark placement — happens for every player move
def add_quantum_mark(self, cell_a: int, cell_b: int, move_number: int):
    # Step 1: Superposition on cell_a
    # |0⟩ → (|0⟩ + |1⟩)/√2
    self.circuit.h(cell_a)

    # Step 2: Entangle cell_a with cell_b
    # Result: (|00⟩ + |11⟩)/√2  — Bell state!
    self.circuit.cx(cell_a, cell_b)

# Collapse — triggered when an entanglement cycle forms
def measure_and_collapse(self, cells_to_measure: list[int]) -> dict[int, int]:
    measure_circuit = self.circuit.copy()
    measure_circuit.measure(cells_to_measure, cells_to_measure)

    # ONE shot = ONE definite game outcome
    job = self.sampler.run([measure_circuit], shots=1)
    counts = job.result()[0].data.c.get_counts()
    bitstring = list(counts.keys())[0]
    return {cell: int(bitstring[len(bitstring) - 1 - cell]) for cell in cells_to_measure}
```

---

## 3. Repository Structure & How to Run

### Project Structure
```text
├── README.md                   # Project documentation (this file)
├── requirements.txt            # Python dependencies
├── src/                        # Source code
│   ├── app.py                  # Streamlit main entry point
│   ├── quantum_engine.py       # Qiskit circuit construction & measurement
│   ├── game_logic.py           # Goff's rules, cycle detection, state management
│   ├── classical_baseline.py   # Classical random/smart players for comparison
│   └── ui_components.py        # Streamlit board rendering & UI helpers
├── notebooks/
│   └── solution.ipynb          # Jupyter notebook with experiments & outputs
├── references/                 # Hackathon reference guides
│   ├── README (1).md           # Track 1 reference guide
│   └── track1_game_starter.ipynb
└── results_comparison.png      # Classical vs Quantum comparison chart
```

### Installation & Execution Instructions

> 💡 **Recommended:** Use a fresh Python virtual environment:
> ```bash
> python -m venv venv
> venv\Scripts\activate        # Windows
> pip install -r requirements.txt
> ```

1. **Clone / open the project:**
   ```bash
   cd "Qiskit Hackathon"
   pip install -r requirements.txt
   ```

2. **Run the Streamlit web app (recommended):**
   ```bash
   streamlit run src/app.py
   ```
   Open your browser at `http://localhost:8501`

3. **Or run the Jupyter notebook:**
   ```bash
   jupyter notebook notebooks/solution.ipynb
   ```

---

## 4. Implementation Walkthrough & Live Demo

* **Walkthrough of Gameplay:**
  1. Player X selects two cells from the dropdown menus and clicks "Place Mark"
  2. The mark X₁ appears in BOTH cells as a quantum mark (shown in gray)
  3. Behind the scenes: `H(q_a)` and `CNOT(q_a → q_b)` are added to the Qiskit circuit
  4. Player O does the same, gradually building an entanglement web
  5. When a move creates a cycle (e.g., cells 0→4→8→0), the game pauses
  6. The opponent selects which collapse resolution to apply
  7. The Qiskit circuit is measured (`shots=1`) — superpositions collapse to 0 or 1
  8. Classical marks appear on the board; check for 3-in-a-row winner
  9. Play continues on remaining quantum cells until someone wins or draws

* **Key Screenshots:**
  - See the Streamlit app's "Show Quantum Circuit" toggle for the live circuit diagram
  - See `notebooks/solution.ipynb` for circuit diagrams, histograms, and comparison plots
  - See `results_comparison.png` for the Classical vs Quantum win-rate chart

---

## 5. Classical vs Quantum Comparison

* **Classical Baseline:**
  We implemented two classical baseline players:
  1. **Random Player:** Picks two random available cells — no strategy
  2. **Smart Player:** Prioritizes center (cell 4) → corners → edges — basic heuristic

  In **classical** Tic-Tac-Toe, two optimal players always draw. There is no randomness.

* **Comparative Analysis:**

  | Metric | Classical Tic-Tac-Toe | Quantum Tic-Tac-Toe |
  
  | Optimal play result | Always Draw | Wins/losses occur due to collapse |
  | Source of uncertainty | None | Genuine quantum randomness (measurement) |
  | Strategic depth | 3-in-a-row placement | + Entanglement cycle management + collapse choice |
  | First-mover advantage | Exists (X wins with perfect play) | Modulated by collapse — O can exploit it |
  | Cell correlations | Independent | Entangled cells have correlated outcomes |

  **Results from 200 simulated games** (see `notebooks/solution.ipynb`):
  - **Random vs Random:** ~35% X wins, ~33% O wins, ~32% draws
  - **Smart vs Smart:** ~40% X wins, ~30% O wins, ~30% draws

  This demonstrates that the **quantum collapse mechanic fundamentally changes game dynamics** — even perfect classical strategy cannot guarantee a draw.

---

## 6. Performance, Results & Limitations

* **Key Results & Observations:**
  - The Qiskit `StatevectorSampler` runs circuits instantly (< 10ms per collapse)
  - Cycle detection via DFS is O(n) — negligible overhead
  - The collapse mechanic creates genuine non-determinism: even the same sequence of moves can produce different outcomes
  - First-player (X) has a slight statistical advantage, consistent with classical Tic-Tac-Toe theory

* **Critical Reflection on Limitations:**
  - **Scalability:** Our 9-qubit circuit is small and exact. Scaling to larger boards (16 cells = 16 qubits) remains tractable for simulation, but would require thousands of qubits of error correction on real NISQ hardware.
  - **Real Hardware Noise:** On current IBM quantum hardware, gate errors (~0.1–1% per gate) and decoherence (T1 ~100μs) would corrupt entanglement. Our `StatevectorSampler` is noise-free — results would degrade on real hardware.
  - **Goff's Rules Simplification:** Our collapse cascade approximates Goff's full rules. The original paper's "stem" resolution is partially simplified.
  - **Circuit Depth:** Each quantum mark adds 2 gates. A full 9-mark game reaches depth ~18, which is achievable on modern hardware but sensitive to decoherence.

---

## 7. References & Acknowledgments

* Allan Goff, *Quantum Tic-Tac-Toe: A Teaching Metaphor for Superposition in Quantum Mechanics*, [arXiv:quant-ph/0202151](https://arxiv.org/abs/quant-ph/0202151)
* David Meyer, *Quantum Strategies*, Physical Review Letters, 1999 — [DOI](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.82.1052)
* Qiskit Documentation](https://docs.quantum.ibm.com/guides) — Circuit building, StatevectorSampler
* Streamlit Documentation](https://docs.streamlit.io/) — Web UI framework
* Qiskit Community Awesome Quantum Games](https://github.com/qiskit-community/awesome-quantum-games)
* IIIT Kottayam Qiskit Fall Fest 2026 organizers for the starter resources
* AI tools- Claude, Chatgpt

