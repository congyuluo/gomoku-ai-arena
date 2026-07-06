import unittest

from serve import ApiError, handle_ai_move, parse_board


class ServerApiTests(unittest.TestCase):
    def test_parse_board_rejects_non_square_board(self):
        with self.assertRaises(ApiError):
            parse_board([[0, 0], [0]])

    def test_first_agent_returns_legal_ai_move(self):
        payload = {
            "agent": "first",
            "player": 1,
            "board": [[0 for _ in range(5)] for _ in range(5)],
            "seed": 3,
        }

        result = handle_ai_move(payload)

        self.assertEqual(result["move"], [0, 0])
        self.assertEqual(result["player"], 1)
        self.assertFalse(result["game_over"])

    def test_finished_board_returns_no_move(self):
        board = [[0 for _ in range(5)] for _ in range(5)]
        for x in range(5):
            board[x][0] = 1

        result = handle_ai_move({"agent": "first", "player": 2, "board": board})

        self.assertIsNone(result["move"])
        self.assertEqual(result["winner"], 1)
        self.assertTrue(result["game_over"])


if __name__ == "__main__":
    unittest.main()
