import math
import subprocess
import unittest
from pathlib import Path

import numpy as np

from Gomoku_Game import Gomoku
import miniZero


ROOT = Path(__file__).resolve().parents[1]
NATIVE_ENGINE = ROOT / "cpp_minizero" / "minizero_native"


class MiniZeroTests(unittest.TestCase):
    def test_medium_recursive_search_alternates_players(self):
        game = Gomoku(size=5)
        game.board[2, 2] = 1
        calls = []
        placements = [(0, 0), (0, 1), (0, 2)]
        original_get_positions = miniZero.get_positions_2

        def fake_get_positions(parent_position, player):
            calls.append(player)
            index = min(len(calls) - 1, len(placements) - 1)
            x, y = placements[index]
            child = Gomoku(size=5)
            child.board = np.array(parent_position.board, copy=True)
            child.board[x, y] = player
            return [child]

        try:
            miniZero.get_positions_2 = fake_get_positions
            miniZero._miniZero(
                game,
                miniZero.hardness["MEDIUM"],
                -math.inf,
                math.inf,
                True,
                is_first_layer=True,
                predictor=lambda _features: 0.0,
            )
        finally:
            miniZero.get_positions_2 = original_get_positions

        self.assertEqual(calls[:3], [1, 2, 1])

    def test_native_medium_self_test(self):
        if not NATIVE_ENGINE.exists():
            subprocess.run(["make", "-C", str(ROOT / "cpp_minizero")], check=True)

        result = subprocess.run(
            [str(NATIVE_ENGINE), "--self-test"],
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertIn("OK medium alternates 1,2,1", result.stdout)


if __name__ == "__main__":
    unittest.main()
