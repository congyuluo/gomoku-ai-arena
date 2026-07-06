import math
import random
from typing import List

import numpy as np

import numpy_network
from Gomoku_Game import Gomoku, remove_empty_array

from feature_extraction import get_feature

# Translate level of hardness into number of minimax layers
hardness = {'EASY': 2, 'MEDIUM': 3, 'test': 1}

# Patterns to look for
pattern_dict_self = {'00001': 0, '00010': 1, '00011': 2, '00100': 3, '00101': 4, '00110': 5, '00111': 6, '01001': 7,
                     '01010': 8, '01011': 9, '01101': 10, '01110': 11, '01111': 12, '10001': 13, '10011': 14,
                     '10101': 15, '10111': 16, '11011': 17, '11111': 18, '011110': 19, '011010': 20, '101110': 21}
pattern_dict_opponent = {'00002': 0, '00020': 1, '00022': 2, '00200': 3, '00202': 4, '00220': 5, '00222': 6, '02002': 7,
                         '02020': 8, '02022': 9, '02202': 10, '02220': 11, '02222': 12, '20002': 13, '20022': 14,
                         '20202': 15, '20222': 16, '22022': 17, '22222': 18, '022220': 19, '022020': 20, '202220': 21}

# Remove mirrored patterns to avoid counting twice in reversed counts
pattern_dict_self_no_mirror = {'00001': 0, '00010': 1, '00011': 2, '00101': 4, '00110': 5, '00111': 6, '01001': 7,
                               '01011': 9, '01101': 10, '01111': 12, '10011': 14, '10111': 16, '011010': 20,
                               '101110': 21}
pattern_dict_opponent_no_mirror = {'00002': 0, '00020': 1, '00022': 2, '00202': 4, '00220': 5, '00222': 6, '02002': 7,
                                   '02022': 9, '02202': 10, '02222': 12, '20022': 14, '20222': 16, '022020': 20,
                                   '202220': 21}


def _in_range_2(board: np.array, x: int, y: int) -> bool:
    """Returns True if the given coordinate is within two dots away from any exsisting point"""
    board_size = len(board[0])
    # Check all points in range two that are horizontal & vertical
    if x - 2 >= 0 and not board[x - 2, y] == 0:
        return True
    if x + 2 < board_size and not board[x + 2, y] == 0:
        return True
    if y - 2 >= 0 and not board[x, y - 2] == 0:
        return True
    if y + 2 < board_size and not board[x, y + 2] == 0:
        return True
    # Check all points in range one that are horizontal & vertical
    if x - 1 >= 0 and not board[x - 1, y] == 0:
        return True
    if x + 1 < board_size and not board[x + 1, y] == 0:
        return True
    if y - 1 >= 0 and not board[x, y - 1] == 0:
        return True
    if y + 1 < board_size and not board[x, y + 1] == 0:
        return True
    # Check all points in range one that are diagonal
    if x + 1 < board_size and y + 1 < board_size and not board[x + 1, y + 1] == 0:
        return True
    if x + 1 < board_size and y - 1 >= 0 and not board[x + 1, y - 1] == 0:
        return True
    if x - 1 >= 0 and y + 1 < board_size and not board[x - 1, y + 1] == 0:
        return True
    if x - 1 >= 0 and y - 1 >= 0 and not board[x - 1, y - 1] == 0:
        return True
    # Added
    if x + 2 < board_size and y + 2 < board_size and not board[x + 2, y + 2] == 0:
        return True
    if x + 2 < board_size and y - 2 >= 0 and not board[x + 2, y - 2] == 0:
        return True
    if x - 2 >= 0 and y + 2 < board_size and not board[x - 2, y + 2] == 0:
        return True
    if x - 2 >= 0 and y - 2 >= 0 and not board[x - 2, y - 2] == 0:
        return True
    return False


def get_positions_2(parent_position: Gomoku, player: int) -> List[Gomoku]:
    """Get a list of Gomoku objects with all possible locations of the given player"""
    # List to store all child objects
    child_positions, board = [], parent_position.board
    for x in range(len(board[0])):
        for y in range(len(board[0])):
            if board[x, y] == 0 and _in_range_2(board, x, y):
                # if the position is empty and is within the given range, create a new object with this position
                new_board = np.copy(board)
                new_board[x, y] = player
                new_position = Gomoku()
                new_position.board = new_board
                # add new position object to the list
                child_positions.append(new_position)
    return child_positions


def _find_difference(board1: np.array, board2: np.array) -> (int, int):
    """Finds the difference between two matrices"""
    for x in range(len(board1[0])):
        for y in range(len(board2[0])):
            if not board1[x, y] == board2[x, y]:
                return x, y


def _miniZero(position: Gomoku, depth: int, alpha: int, beta: int, maximizingPlayer: bool, is_first_layer=False,
              predictor=None):
    """A modified minimax algorithm to search for best move, with alpha-beta pruning and value network"""
    predictor = predictor or numpy_network.predict
    # Initial call minimax(position, 3, -math.inf, math.inf, True)
    # Return static evaluation of current position if target depth has been reached or game has came to an end
    game_over = position.check_game_over()
    if depth == 0 or game_over:
        if game_over:
            winner = position.check_win()
            if winner == 1:
                return 1
            if winner == 2:
                return -1
            return 0
        # Get pattern info
        if not maximizingPlayer:
            result = predictor(get_feature(position.board) + [1 for _ in range(22)])
        else:
            result = predictor(get_feature(position.board) + [0 for _ in range(22)])
        return result

    # First call
    if is_first_layer:
        # create object to store best move
        best_move, maxEvaluation = Gomoku(), -math.inf
        child_objects = get_positions_2(position, 1)
        # Objects added for miniZero
        child_to_evaluate, values = [], []
        for child in child_objects:
            evaluation = _miniZero(child, depth - 1, alpha, beta, False, predictor=predictor)
            # Append child and value
            child_to_evaluate.append(child)
            values.append(evaluation)
            # replace best_move if evaluation is higher
            best_move = child if evaluation > maxEvaluation else best_move
            maxEvaluation, alpha = max(maxEvaluation, evaluation), max(alpha, evaluation)
            if beta <= alpha:
                break
        # Pick a child for result
        return best_move

    # Minimizing AI score (Maximizing player score)
    else:
        minEvaluation = math.inf
        child_objects = get_positions_2(position, 2)
        for child in child_objects:
            evaluation = _miniZero(child, depth - 1, alpha, beta, True, predictor=predictor)
            minEvaluation, beta = min(minEvaluation, evaluation), min(beta, evaluation)
            if beta <= alpha:
                break
        return minEvaluation


class miniZero_player:

    def __init__(self, level: str, predictor=None):
        self.level = hardness[level]
        self.predictor = predictor or numpy_network.predict

    def think(self, game: Gomoku) -> ():
        """Calls the minimax algorithm for a result, then returns the chosen coordinate"""
        # first play
        if np.count_nonzero(game.board) == 0:
            return random.randint(2, len(game.board[0]) - 3), random.randint(2, len(game.board[0]) - 3)

        # Call Minimax to compute result
        result_game = _miniZero(game, self.level, -math.inf, math.inf, True, is_first_layer=True,
                                predictor=self.predictor)
        return _find_difference(game.board, result_game.board)
