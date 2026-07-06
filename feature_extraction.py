import numpy as np
from typing import List

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


def remove_empty_array(arrays: List[np.array]) -> List[np.array]:
    """Remove arrays with only zeros or arrays with length under five"""
    result_arrays = []
    for array in arrays:
        if any(array) and len(array) >= 5:
            result_arrays.append(array)
    return result_arrays


def get_1D_arrays(board: np.array) -> List[np.array]:
    """Collect 1D arrays from all directions"""
    array_collection = []
    # Create flipped board for reversed diagonal
    flipped_board = np.fliplr(board.copy())
    for i in range(board[0].size):
        # Collect horizontal & vertical arrays
        array_collection.append(board[i])
        array_collection.append(board[:, i])
        # Collect diagonal & reversed diagonal arrays
        if i == 0:
            array_collection.append(board.diagonal())
            array_collection.append(flipped_board.diagonal())
        else:
            array_collection.append(board.diagonal(offset=i))
            array_collection.append(board.diagonal(offset=-i))
            array_collection.append(flipped_board.diagonal(offset=i))
            array_collection.append(flipped_board.diagonal(offset=-i))
    return array_collection


def get_feature(board: np.array) -> (List, List):
    """Returns counts of different patterns"""

    def _match_pattern_values(String: str, value_dict: {}, counts: []):
        """Adds to index of all matched key values"""
        for key in value_dict:
            if key in String:
                counts[value_dict[key]] += 1

    # Set initial counts to zero
    counts_self = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    counts_opponent = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # Different sets of values are used to evaluate under different situations. To maximise performance.
    for String in remove_empty_array(get_1D_arrays(board)):
        player = "".join([str(int(i)) for i in String])
        player_reversed = player[::-1]
        # match strings with rules, then add to counts
        # Self
        _match_pattern_values(player, pattern_dict_self, counts_self)
        _match_pattern_values(player_reversed, pattern_dict_self_no_mirror, counts_self)
        # Opponent
        _match_pattern_values(player, pattern_dict_opponent, counts_opponent)
        _match_pattern_values(player_reversed, pattern_dict_opponent_no_mirror, counts_opponent)
    return counts_self + counts_opponent
