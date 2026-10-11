"""
classical_baseline.py — Classical Random Player for Comparison
==============================================================

WHY THIS FILE EXISTS:
The hackathon rubric requires a "Classical vs Quantum Comparison".
We need to show that quantum mechanics adds something MEANINGFUL
to the game — not just randomness.

This file provides:
1. A RANDOM classical player (picks moves randomly)
2. A SMART classical player (uses basic strategy)
3. A simulation function to run many games and collect statistics

The comparison shows:
- How often X wins vs O wins vs draws
- Whether quantum mechanics creates different gameplay patterns
  compared to classical randomness
"""

import random
from game_logic import GameState


class ClassicalRandomPlayer:
    """
    A player that makes random moves.

    This represents the "classical baseline" — a player with NO quantum
    strategy whatsoever. They just pick two random available cells.

    We compare this against the quantum game to show that quantum
    mechanics creates fundamentally different gameplay patterns.
    """

    def __init__(self, player: str):
        """
        Args:
            player: 'X' or 'O'
        """
        self.player = player

    def choose_move(self, game: GameState) -> tuple[int, int]:
        """
        Pick two random available cells for the quantum mark.

        This is as "dumb" as possible — no strategy at all.
        Just randomly picks from whatever cells are available.

        Returns:
            Tuple of (cell_a, cell_b)
        """
        available = game.get_available_cells()
        if len(available) < 2:
            # Not enough cells — shouldn't happen in a normal game
            return available[0], available[0]

        # Pick two different random cells
        chosen = random.sample(available, 2)
        return chosen[0], chosen[1]

    def choose_collapse(self, game: GameState) -> int:
        """
        Randomly choose a collapse option.

        In a real game, the opponent strategically picks the collapse
        that benefits them most. The random player just picks randomly.

        Returns:
            Index of the chosen collapse option (0 or 1)
        """
        if len(game.collapse_options) == 0:
            return 0
        return random.randint(0, len(game.collapse_options) - 1)


class ClassicalSmartPlayer:
    """
    A player with basic strategic thinking.

    Strategy (simple heuristic):
    1. Prefer the CENTER cell (cell 4) — it's part of the most winning lines
    2. Prefer CORNER cells (0, 2, 6, 8) — they're part of 3 winning lines
    3. Avoid EDGE cells (1, 3, 5, 7) — they're part of only 2 winning lines
    4. For collapse, choose the option that gives THEM more 3-in-a-row potential

    This is NOT a perfect AI — it's just smarter than random.
    """

    # How "valuable" each cell is (center > corners > edges)
    CELL_PRIORITY = {
        4: 4,              # Center: part of 4 winning lines
        0: 3, 2: 3,        # Corners: part of 3 winning lines
        6: 3, 8: 3,
        1: 2, 3: 2,        # Edges: part of 2 winning lines
        5: 2, 7: 2,
    }

    def __init__(self, player: str):
        self.player = player

    def choose_move(self, game: GameState) -> tuple[int, int]:
        """
        Pick two cells using strategic priority.

        Picks the two highest-priority available cells.
        """
        available = game.get_available_cells()
        if len(available) < 2:
            return available[0], available[0]

        # Sort by priority (highest first)
        sorted_cells = sorted(available,
                              key=lambda c: self.CELL_PRIORITY.get(c, 0),
                              reverse=True)

        # Pick the top 2
        return sorted_cells[0], sorted_cells[1]

    def choose_collapse(self, game: GameState) -> int:
        """
        Choose the collapse option that benefits this player most.

        Strategy: Pick the option where THIS player gets more cells.
        """
        if len(game.collapse_options) <= 1:
            return 0

        best_option = 0
        best_score = -1

        for i, option in enumerate(game.collapse_options):
            # Count how many cells go to THIS player
            score = sum(1 for player in option.values() if player == self.player)
            if score > best_score:
                best_score = score
                best_option = i

        return best_option


def simulate_games(num_games: int = 100,
                   x_type: str = "random",
                   o_type: str = "random") -> dict:
    """
    Simulate many games and collect statistics.

    This function runs num_games games with the specified player types
    and returns win/loss/draw statistics.

    HOW IT WORKS:
    1. Create two AI players (random or smart)
    2. Play a full game loop: place marks, detect cycles, resolve collapses
    3. Record who wins
    4. Repeat num_games times
    5. Return the statistics

    Args:
        num_games: How many games to simulate
        x_type: Type of player X ('random' or 'smart')
        o_type: Type of player O ('random' or 'smart')

    Returns:
        Dict with keys: 'x_wins', 'o_wins', 'draws', 'total'
    """
    # Create players based on type
    player_x = (ClassicalSmartPlayer('X') if x_type == "smart"
                else ClassicalRandomPlayer('X'))
    player_o = (ClassicalSmartPlayer('O') if o_type == "smart"
                else ClassicalRandomPlayer('O'))

    stats = {'x_wins': 0, 'o_wins': 0, 'draws': 0, 'total': num_games}

    for _ in range(num_games):
        game = GameState()
        max_moves = 50  # Safety limit to prevent infinite loops

        move_count = 0
        while not game.game_over and move_count < max_moves:
            move_count += 1

            # Determine current player's AI
            current_ai = player_x if game.current_player == 'X' else player_o

            if game.pending_collapse:
                # The OTHER player chooses how to collapse
                collapse_ai = player_o if game.current_player == 'X' else player_x
                choice = collapse_ai.choose_collapse(game)
                choice = min(choice, len(game.collapse_options) - 1)
                if game.collapse_options:
                    game.apply_collapse(choice)
                continue

            # Get available cells
            available = game.get_available_cells()
            if len(available) < 2:
                # Not enough cells for a quantum move — game is effectively done
                game.game_over = True
                game.winner = 'Draw'
                break

            # Make a move
            try:
                cell_a, cell_b = current_ai.choose_move(game)
                game.place_quantum_mark(cell_a, cell_b)
            except (ValueError, IndexError):
                # Invalid move — skip
                break

        # Record result
        if game.winner == 'X':
            stats['x_wins'] += 1
        elif game.winner == 'O':
            stats['o_wins'] += 1
        else:
            stats['draws'] += 1

    return stats
