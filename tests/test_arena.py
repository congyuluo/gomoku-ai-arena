import unittest

from Gomoku_Game import Gomoku
from arena import BLACK, WHITE, IllegalMove, apply_move, normalize_for_player


class ArenaTests(unittest.TestCase):
    def test_apply_move_rejects_occupied_points(self):
        game = Gomoku(size=5)
        apply_move(game, (2, 2), BLACK)

        with self.assertRaises(IllegalMove):
            apply_move(game, (2, 2), WHITE)

    def test_apply_move_rejects_out_of_bounds_points(self):
        game = Gomoku(size=5)

        with self.assertRaises(IllegalMove):
            apply_move(game, (5, 0), BLACK)

    def test_normalize_for_white_swaps_players(self):
        game = Gomoku(size=5)
        game.board[1, 1] = BLACK
        game.board[2, 2] = WHITE

        normalized = normalize_for_player(game, WHITE)

        self.assertEqual(normalized.board[1, 1], WHITE)
        self.assertEqual(normalized.board[2, 2], BLACK)
        self.assertEqual(game.board[1, 1], BLACK)


if __name__ == "__main__":
    unittest.main()
