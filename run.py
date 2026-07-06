import pygame as pg

from Display import start_screen, get_user_input, finish_screen, WorkerThread, ProgressThread
from Gomoku_Game import Gomoku
from miniZero import miniZero_player as AI_player

# _____Adjust board size here_____#
board_size = 15  # I only provided support for square boards

# _____Adjust display parameters here_____#
grid_size = 40
boarder_size = 0

# Don't touch these
window_center = [(board_size * grid_size + grid_size + boarder_size) / 2,
                 (board_size * grid_size + grid_size + boarder_size) / 2]


def run(player_color: str, player_score: int, AI_score: int, round_count: int) -> str:
    # Clear the game board
    game.clear_board(size=board_size)

    # Make AI play first if player chooses to play white
    if player_color == "WHITE":
        x, y = AI.think(game)
        game.AI_play(x, y)

    # Initiate counting variable & Make Variable to store last move of the AI
    turn_count, AI_last_x, AI_last_y = 0, -1, -1

    # Game Loop
    while 1:
        # Player turn
        if turn_count % 2 == 0:
            # Call Graphical user interface for user input
            x, y = get_user_input(window, game, player_color, (AI_last_x, AI_last_y), round_count, player_score,
                                  AI_score, grid_size, boarder_size)
            if not x == -1:
                game.Player_play(x, y)
                # If user clicks restart
            else:
                pg.time.delay(200)
                return "Restart"

        # AI turn
        else:
            # Construct WorkerThread and ProgressThread objects
            # AI object runs within the WorkerThread so that ProgressThread can display while minimax runs in a separate
            # thread
            worker = WorkerThread(AI)
            progress = ProgressThread(worker, window, board_size, grid_size, boarder_size)
            worker.load_game(game)
            worker.start()
            progress.start()
            progress.join()
            x, y = worker.get_result()
            # Play AI result
            game.AI_play(x, y)
            # Store AI move
            AI_last_x, AI_last_y = x, y

        # If the game has ended
        if game.check_game_over():
            if game.check_win() == 1:
                result = 'AI_win'
            elif game.check_win() == 2:
                result = 'Player_win'
            else:
                result = "Tie"

            if finish_screen(window, result, game, player_color, (AI_last_x, AI_last_y), round_count, player_score,
                             AI_score, grid_size, boarder_size):
                pg.time.delay(200)
                return result

        turn_count += 1


# Main Loop
if __name__ == '__main__':
    # Initiate game
    game = Gomoku(size=board_size)
    game_width, game_height = len(game.board[0]), len(game.board[0])
    window_center = [(game_width * grid_size + grid_size + boarder_size) / 2,
                     (game_height * grid_size + grid_size + boarder_size) / 2]

    # Initiate pygame & setup window
    pg.init()
    window = pg.display.set_mode(
        (game_width * grid_size + grid_size + boarder_size + 300,
         game_height * grid_size + grid_size + boarder_size))
    pg.display.set_caption('Gomoku')

    while 1:
        RUN = True
        # Initiate counting variable
        round_count, player_score, AI_score = 1, 0, 0
        # Call Graphical user interface for setup
        is_easy, is_black = start_screen(window, game, grid_size, boarder_size)
        pg.time.delay(200)
        # Declare AI object
        AI = AI_player('EASY') if is_easy else AI_player('MEDIUM')
        # Declare player colors
        player_color = "BLACK" if is_black else "WHITE"
        while RUN:
            game_result = run(player_color, player_score, AI_score, round_count)
            # Count scores
            if game_result == 'AI_win':
                AI_score += 1
            elif game_result == 'Player_win':
                player_score += 1
            elif game_result == "Restart":
                RUN = False
            # Swap colors
            is_black = not is_black
            player_color = "BLACK" if is_black else "WHITE"
            round_count += 1
