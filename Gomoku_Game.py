from typing import List

import numpy as np


def remove_empty_array(arrays: List[np.array]) -> List[np.array]:
    """Remove arrays with only zeros or arrays with length under five"""
    result_arrays = []
    for array in arrays:
        if any(array) and len(array) >= 5:
            result_arrays.append(array)
    return result_arrays


class Gomoku:

    def __init__(self, size=10): self.board = np.zeros([size, size])

    def AI_play(self, x, y): self.board[x, y] = 1

    def Player_play(self, x, y): self.board[x, y] = 2

    def get_1D_arrays(self) -> List[np.array]:
        """Collect 1D arrays from all directions"""
        array_collection = []
        # Create flipped board for reversed diagonal
        flipped_board = np.fliplr(self.board.copy())
        for i in range(self.board[0].size):
            # Collect horizontal & vertical arrays
            array_collection.append(self.board[i])
            array_collection.append(self.board[:, i])
            # Collect diagonal & reversed diagonal arrays
            if i == 0:
                array_collection.append(self.board.diagonal())
                array_collection.append(flipped_board.diagonal())
            else:
                array_collection.append(self.board.diagonal(offset=i))
                array_collection.append(self.board.diagonal(offset=-i))
                array_collection.append(flipped_board.diagonal(offset=i))
                array_collection.append(flipped_board.diagonal(offset=-i))
        return array_collection

    def check_win(self) -> int:
        """Checks if a player has won the game"""
        """0 for no result, 1 for AI win, 2 for player win"""
        arrays = remove_empty_array(self.get_1D_arrays())
        for array in arrays:
            # first convert list of int to str
            converted = "".join([str(int(i)) for i in array])
            # If AI has five connected dots
            if "11111" in converted:
                return 1
            # If player has five connected dots
            if "22222" in converted:
                return 2
        return 0

    def check_game_over(self) -> bool: return False if (self.check_win() == 0 and 0 in self.board) else True

    def clear_board(self, size=10): self.board = np.zeros([size, size])


def get_winning_move(game: Gomoku) -> ():
    """Gets the coordinates of the two ends of the winning linkage"""
    # Get board_size
    board_size = len(game.board[0])
    # Test to see which move forms winning linkage
    linkage = []
    for x in range(board_size):
        for y in range(board_size):
            # Test points
            if not game.board[x, y] == 0:
                # Construct test board
                test_board = np.copy(game.board)
                # Set testing coordinate to zero
                test_board[x, y] = 0
                # Construct test object
                test_game = Gomoku()
                test_game.board = test_board
                # Check if the coordinate is part of the winning move
                if test_game.check_win() == 0:
                    linkage.append([x, y])
    return linkage[0], linkage[-1]
