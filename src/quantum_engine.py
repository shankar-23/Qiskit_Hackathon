"""
quantum_engine.py — Qiskit Quantum Circuit Engine
==================================================

THIS FILE CONNECTS THE GAME TO REAL QUANTUM MECHANICS.

HOW IT WORKS (The Big Picture):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. The game board has 9 cells → we use 9 QUBITS (one per cell)
2. When a player places a quantum mark in cells (A, B):
   → We apply a Hadamard (H) gate to qubit A (creates superposition)
   → We apply a CNOT gate from A to B (creates entanglement)
3. When a collapse is triggered:
   → We MEASURE the relevant qubits
   → The superposition "collapses" into definite 0s and 1s
   → These outcomes determine which cell gets which mark

QUANTUM GATES EXPLAINED:
━━━━━━━━━━━━━━━━━━━━━━━━
• H (Hadamard): Takes |0⟩ → (|0⟩ + |1⟩)/√2
  Think of it as: "The qubit is now 50/50 — could be 0 or 1"
  In our game: "The mark could be in either cell"

• CNOT (Controlled-NOT): If control qubit is |1⟩, flip the target qubit.
  When applied after H, it creates a BELL STATE:
    (|00⟩ + |11⟩)/√2
  This means: "Both qubits are linked — they'll ALWAYS give the same result"
  In our game: "The two cells are entangled — if one has the mark, the other
  is guaranteed to have (or not have) a corresponding mark"

• X (NOT gate): Flips |0⟩ → |1⟩ and |1⟩ → |0⟩
  In our game: Used to set up initial states.

• Measure: Collapses the quantum state into a definite classical bit (0 or 1).
  In our game: "Open the box and see what's actually there!"
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

# Try to import visualization tools (optional — for circuit diagrams)
try:
    from qiskit.visualization import circuit_drawer
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False


class QuantumEngine:
    """
    Builds and runs Qiskit quantum circuits that model the game board.

    This engine translates game moves into quantum operations:
    - Quantum mark placement → H + CNOT gates
    - Board collapse → Measurement of entangled qubits

    The circuit uses 9 qubits (q₀ through q₈), one for each cell:

        q₀ | q₁ | q₂
        ─────────────
        q₃ | q₄ | q₅
        ─────────────
        q₆ | q₇ | q₈
    """

    def __init__(self):
        """Initialize a fresh 9-qubit circuit."""
        # 9 qubits for the board + 9 classical bits for measurement results
        self.circuit = QuantumCircuit(9, 9)

        # Track which qubit pairs are entangled (for visualization/debugging)
        self.entangled_pairs: list[tuple[int, int]] = []

        # The sampler executes our circuit using statevector simulation
        # (exact simulation, no noise — perfect for a game!)
        self.sampler = StatevectorSampler()

    def add_quantum_mark(self, cell_a: int, cell_b: int, move_number: int):
        """
        Add a quantum mark to the circuit by entangling two cells.

        WHAT HAPPENS STEP BY STEP:
        ━━━━━━━━━━━━━━━━━━━━━━━━━
        Let's say player X places mark X₁ in cells 0 and 3.

        Step 1: Apply H gate to qubit 0 (cell_a)
                |0⟩ → (|0⟩ + |1⟩) / √2
                "Qubit 0 is now in superposition — 50% chance of 0, 50% chance of 1"

        Step 2: Apply CNOT from qubit 0 to qubit 3 (cell_a → cell_b)
                (|0⟩ + |1⟩)/√2 ⊗ |0⟩  →  (|00⟩ + |11⟩)/√2
                "Now qubits 0 and 3 are ENTANGLED — if one is 1, the other is 1 too"

        In game terms:
        - If we measure and qubit 0 = 1 → mark goes to cell 0
        - If we measure and qubit 0 = 0 → mark goes to cell 3 (qubit 3 = 0 too,
          but the ABSENCE in cell 0 means PRESENCE in cell 3)

        Actually, the mapping is:
        - |1⟩ on a qubit = "this cell has the mark"
        - |0⟩ on a qubit = "this cell does NOT have the mark"

        Args:
            cell_a: First cell index (0-8)
            cell_b: Second cell index (0-8)
            move_number: The move number (for circuit labeling)
        """
        # Add a visual barrier for readability in the circuit diagram
        self.circuit.barrier(label=f"Move {move_number}")

        # Step 1: Put cell_a's qubit into superposition
        # H gate: |0⟩ → (|0⟩ + |1⟩)/√2
        self.circuit.h(cell_a)

        # Step 2: Entangle cell_a with cell_b
        # CNOT: control=cell_a, target=cell_b
        # Result: (|00⟩ + |11⟩)/√2 — a Bell state!
        self.circuit.cx(cell_a, cell_b)

        # Record this entanglement
        self.entangled_pairs.append((cell_a, cell_b))

    def measure_and_collapse(self, cells_to_measure: list[int]) -> dict[int, int]:
        """
        Measure specific qubits to collapse the quantum state.

        WHAT HAPPENS:
        ━━━━━━━━━━━━━
        Before measurement, the qubits are in superposition — no definite value.
        After measurement, each qubit collapses to either 0 or 1.

        Because entangled qubits are correlated, measuring one instantly
        determines the other. This is the "spooky action at a distance"
        that Einstein famously complained about!

        We run the circuit with shots=1 (a single measurement) because
        in a game, we want ONE definite outcome, not statistics.

        Args:
            cells_to_measure: List of cell indices (0-8) to measure

        Returns:
            Dict mapping cell_index → measurement result (0 or 1)
            Example: {0: 1, 3: 1, 1: 0} means cells 0,3 got a "1" (mark present)
                     and cell 1 got a "0" (no mark here)
        """
        # Create a copy of the circuit so we don't modify the original
        measure_circuit = self.circuit.copy()

        # Add measurement gates for the specified qubits
        measure_circuit.barrier(label="COLLAPSE!")
        for cell in cells_to_measure:
            measure_circuit.measure(cell, cell)

        # Run the circuit — ONE shot = ONE definite outcome
        job = self.sampler.run([measure_circuit], shots=1)
        result = job.result()[0]

        # Extract the measurement results
        # Qiskit returns bitstrings in REVERSE order (little-endian)
        # So for 9 qubits, bitstring[0] = qubit 8, bitstring[8] = qubit 0
        counts = result.data.c.get_counts()
        bitstring = list(counts.keys())[0]

        # Parse the bitstring into a dict: cell → 0 or 1
        outcomes = {}
        for cell in cells_to_measure:
            # Qiskit uses little-endian: bit position from the RIGHT
            bit_position = len(bitstring) - 1 - cell
            outcomes[cell] = int(bitstring[bit_position])

        return outcomes

    def get_collapse_probabilities(self, cells: list[int]) -> dict[str, float]:
        """
        Get the probability distribution WITHOUT collapsing.

        This is useful for showing players what the CHANCES are before
        they decide to measure. It runs 1000 shots and counts how often
        each outcome occurs.

        Example return: {'001': 0.5, '110': 0.5}
        Meaning: 50% chance of outcome 001, 50% chance of outcome 110

        Args:
            cells: List of cell indices to analyze

        Returns:
            Dict mapping bitstring → probability (0.0 to 1.0)
        """
        measure_circuit = self.circuit.copy()
        measure_circuit.barrier(label="Probability Check")
        for cell in cells:
            measure_circuit.measure(cell, cell)

        job = self.sampler.run([measure_circuit], shots=1000)
        result = job.result()[0]
        counts = result.data.c.get_counts()

        # Convert counts to probabilities
        total = sum(counts.values())
        probabilities = {bitstring: count / total for bitstring, count in counts.items()}
        return probabilities

    def get_circuit_diagram(self) -> str:
        """
        Get a text representation of the current quantum circuit.

        This shows all the gates that have been applied so far.
        Useful for the Streamlit UI and for debugging.

        Returns:
            String containing the ASCII circuit diagram
        """
        return self.circuit.draw(output='text').__str__()

    def get_circuit_image(self):
        """
        Get the circuit diagram as a matplotlib figure.

        Returns a figure object that can be displayed in Streamlit
        using st.pyplot().
        """
        try:
            fig = self.circuit.draw(output='mpl')
            return fig
        except Exception:
            return None

    def reset(self):
        """Reset the engine for a new game."""
        self.circuit = QuantumCircuit(9, 9)
        self.entangled_pairs = []
