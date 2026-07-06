import math
import time
from threading import Thread

import pygame as pg

from Gomoku_Game import Gomoku, get_winning_move
from miniZero import miniZero_player


# Class WorkerThread and ProgressThread are referenced & modified from
# https://stackoverflow.com/questions/12658651/how-can-i-print-to-console-while-the-program-is-running-in-python
# The two classes are for displaying while the Minimax search algorithm is running is the background


class WorkerThread(Thread):
    """displaying while the Minimax search algorithm is running is the background"""

    def __init__(self, AI: miniZero_player):
        super(WorkerThread, self).__init__()
        self.AI = AI

    def load_game(self, game: Gomoku): self.game = game

    def run(self): self.result = self.AI.think(self.game)

    def get_result(self) -> (): return self.result


class ProgressThread(Thread):
    """displaying while the Minimax search algorithm is running is the background"""

    def __init__(self, worker: Thread, window: pg.Surface, board_size: int, grid_size: int, boarder_size: int):
        super(ProgressThread, self).__init__()
        self.worker = worker
        self.window = window

        # Declare captions
        self.dots = []
        font = pg.font.SysFont('arialms', 30)
        self.caption = font.render("CPU is Thinking", True, (91, 143, 219))
        self.dots.append(font.render(".", True, (91, 143, 219)))
        self.dots.append(font.render(". .", True, (91, 143, 219)))
        self.dots.append(font.render(". . .", True, (91, 143, 219)))
        self.x_base_offset = board_size * grid_size + grid_size + boarder_size + 10

    def run(self):
        """Display: CPU is thinking..."""
        self.window.blit(self.caption, (self.x_base_offset, 35))
        count = 0
        start_time = time.time()
        while True:
            if not self.worker.is_alive():
                pg.draw.rect(self.window, (255, 255, 255), (self.x_base_offset, 35, 250, 35), 0)
                pg.display.update()
                return True

            if time.time() - start_time > 1:
                pg.draw.rect(self.window, (255, 255, 255), (self.x_base_offset + 160, 35, 250, 70), 0)
                self.window.blit(self.dots[count % 3], (self.x_base_offset + 160, 35))
                pg.display.update()
                count += 1
            time.sleep(0.1)


# Class Button is referenced & modified from Tech with Tim's tutorial on Youtube
# https://www.youtube.com/watch?v=4_9twnEduFA


class round_button:
    """A class object for a round button"""

    def __init__(self, color, x, y, radius):
        self.color = color
        self.x = x
        self.y = y
        self.radius = radius

    def draw(self, win):
        # Call this method to draw the button on the screen
        pg.draw.circle(win, self.color, (self.x, self.y), self.radius)
        pg.draw.polygon(win, (255, 255, 255),
                        [(self.x + 12, self.y), (self.x - 8, self.y + 12), (self.x - 8, self.y - 12)])

    def isOver(self, pos):
        # Pos is the mouse position or a tuple of (x,y) coordinates
        if self.radius > math.sqrt((pos[0] - self.x) ** 2 + (pos[1] - self.y) ** 2):
            return True
        return False


class button:
    """A class object for a regular button"""

    def __init__(self, color, x, y, width, height, text_size, text=''):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text_size = text_size
        self.text = text

    def draw(self, win, chosen: bool):
        # Call this method to draw the button on the screen
        if chosen:
            pg.draw.rect(win, self.color, (self.x, self.y, self.width, self.height), 0, border_radius=10)
        else:
            pg.draw.rect(win, (192, 198, 211), (self.x, self.y, self.width, self.height), 0, border_radius=10)

        if self.text != '':
            font = pg.font.SysFont('arialms', self.text_size)
            text = font.render(self.text, 1, (255, 255, 255))
            win.blit(text, (
                self.x + (self.width / 2 - text.get_width() / 2), self.y + (self.height / 2 - text.get_height() / 2)))

    def isOver(self, pos):
        # Pos is the mouse position or a tuple of (x,y) coordinates
        if self.x < pos[0] < self.x + self.width:
            if self.y < pos[1] < self.y + self.height:
                return True
        return False


def _draw(window, game: Gomoku, player_color: str, grid_size=40, display_offset=0):
    """Draws the game board and all of the dots"""
    game_width = len(game.board[0])
    game_height = len(game.board[0])

    # Draw grid
    for index in range(1, game_height + 1):
        pg.draw.line(window, (192, 198, 211), (0 + display_offset + grid_size, index * grid_size + display_offset),
                     (game_width * grid_size + display_offset, grid_size * index + display_offset), 1)
    for index in range(1, game_width + 1):
        pg.draw.line(window, (192, 198, 211), (index * grid_size + display_offset, 0 + display_offset + grid_size),
                     (index * grid_size + display_offset, game_height * grid_size + display_offset), 1)
    offset = grid_size

    # Draw points
    # If player chose white dots
    if player_color == "WHITE":
        for xx in range(game_width):
            for yy in range(game_height):
                if game.board[xx, yy] == 1:
                    pg.draw.circle(window, (0, 0, 0),
                                   ((xx * grid_size) + offset + display_offset,
                                    (yy * grid_size) + offset + display_offset),
                                   16)
                elif game.board[xx, yy] == 2:
                    pg.draw.circle(window, (0, 0, 0),
                                   ((xx * grid_size) + offset + display_offset,
                                    (yy * grid_size) + offset + display_offset),
                                   16)
                    pg.draw.circle(window, (255, 255, 255),
                                   ((xx * grid_size) + offset + display_offset,
                                    (yy * grid_size) + offset + display_offset),
                                   14)
    # If player chose black dots
    else:
        for xx in range(game_width):
            for yy in range(game_height):
                if game.board[xx, yy] == 1:
                    pg.draw.circle(window, (0, 0, 0),
                                   ((xx * grid_size) + offset + display_offset,
                                    (yy * grid_size) + offset + display_offset),
                                   16)
                    pg.draw.circle(window, (255, 255, 255),
                                   ((xx * grid_size) + offset + display_offset,
                                    (yy * grid_size) + offset + display_offset),
                                   14)
                elif game.board[xx, yy] == 2:
                    pg.draw.circle(window, (0, 0, 0),
                                   ((xx * grid_size) + offset + display_offset,
                                    (yy * grid_size) + offset + display_offset),
                                   16)


def _draw_start_board(window, game, grid_size=40, display_offset=0):
    """Draw board without dots on it"""
    game_width = len(game.board[0])
    game_height = len(game.board[0])
    # Draw grid
    for index in range(1, game_height + 1):
        pg.draw.line(window, (192, 198, 211), (0 + display_offset + grid_size, index * grid_size + display_offset),
                     (game_width * grid_size + display_offset, grid_size * index + display_offset), 1)
    for index in range(1, game_width + 1):
        pg.draw.line(window, (192, 198, 211), (index * grid_size + display_offset, 0 + display_offset + grid_size),
                     (index * grid_size + display_offset, game_height * grid_size + display_offset), 1)


def _get_intersection_locations(grid_size: int, display_offset: int, board_size: int) -> (list, list):
    """Returns with the locations of all intersection of grids"""
    intersections = []
    index = []
    for x in range(1, board_size + 1):
        for y in range(1, board_size + 1):
            intersections.append([x * grid_size + display_offset, y * grid_size + display_offset])
            index.append([x - 1, y - 1])
    return intersections, index


def _draw_info(window, x_base_offset: int):
    """Draws the info window on the bottom left of the UI"""
    # Draw rect
    pg.draw.rect(window, (192, 198, 211), (x_base_offset, 350, 250, 100), 0)
    pg.draw.rect(window, (255, 255, 255), (x_base_offset + 5, 355, 240, 90), 0)

    # Draw words
    font = pg.font.SysFont('arialms', 25)
    caption_1 = font.render("By Congyu Luo. 2021.", True, (43, 43, 43))
    caption_2 = font.render("Project miniZero", True, (43, 43, 43))
    caption_3 = font.render("congyul3@uci.edu", True, (43, 43, 43))

    window.blit(caption_1, (x_base_offset + 10, 360))
    window.blit(caption_2, (x_base_offset + 10, 380))
    window.blit(caption_3, (x_base_offset + 10, 400))


def start_screen(window, game: Gomoku, grid_size: int, boarder_size: int) -> ():
    """Draws the start screen"""
    run = True

    # Set display parameter
    game_width = len(game.board[0])
    game_height = len(game.board[0])
    window_center = [(game_width * grid_size + grid_size + boarder_size) / 2,
                     (game_height * grid_size + grid_size + boarder_size) / 2]
    x_base_offset = game_width * grid_size + grid_size + boarder_size + 10

    # Declare buttons
    start_button = round_button((91, 143, 219), window_center[0], window_center[1], 30)
    black_button = button((91, 143, 219), x_base_offset, 210, 125, 70, 35, text="BLACK")
    white_button = button((91, 143, 219), x_base_offset + 125, 210, 125, 70, 35, text="WHITE")

    # Declare captions
    font = pg.font.SysFont('arialms', 35)
    Color_caption = font.render("COLOR", True, (0, 0, 0))

    font = pg.font.SysFont('arialms', 25)
    play_first_caption = font.render("YOU WILL PLAY FIRST", True, (91, 143, 219))
    play_second_caption = font.render("CPU WILL PLAY FIRST", True, (229, 98, 96))

    # Setup booleans to store settings
    is_black = True

    while run:

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                break

        # Draw white background
        window.fill((255, 255, 255))
        # Draw preview of the chess board
        _draw_start_board(window, game)
        # Draw start button
        start_button.draw(window)
        # Draw backgrounds for buttons on the right
        pg.draw.rect(window, (192, 198, 211), (x_base_offset, 210, 250, 70), 0, border_radius=10)

        # Draw Captions
        window.blit(Color_caption, (x_base_offset, 175))
        if is_black:
            window.blit(play_first_caption, (x_base_offset, 295))
        else:
            window.blit(play_second_caption, (x_base_offset, 295))

        # Draw buttons
        black_button.draw(window, is_black)
        white_button.draw(window, not is_black)

        # Draw Info
        _draw_info(window, x_base_offset)

        # Check for mouse click
        if pg.mouse.get_pressed()[0]:
            mouse_position = pg.mouse.get_pos()
            if black_button.isOver(mouse_position):
                is_black = True
            elif white_button.isOver(mouse_position):
                is_black = False
            elif start_button.isOver(mouse_position):
                run = False

        pg.display.update()

    # return settings
    return True, is_black


def get_user_input(window, game: Gomoku, player_color: str, last_move: (), turn_count: int, player_score: int,
                   AI_score: int, grid_size: int, boarder_size: int) -> ():
    """Draws the window while waiting for a user input"""

    # Setup display parameters
    x_base_offset = len(game.board[0]) * grid_size + grid_size + boarder_size + 10

    # Get locations of all intersections
    intersections, index = _get_intersection_locations(grid_size, boarder_size / 2, len(game.board[0]))

    # Declare captions
    font = pg.font.SysFont('arialms', 35)
    round_string = "ROUND: " + str(int(turn_count))
    turn_caption = font.render(round_string, True, (0, 0, 0))

    AI_score_string = "CPU SCORE: " + str(AI_score)
    AI_score_caption = font.render(AI_score_string, True, (0, 0, 0))

    Player_score_string = "Your SCORE: " + str(player_score)
    Player_score_caption = font.render(Player_score_string, True, (0, 0, 0))

    # Declare button
    restart_button = button((229, 98, 96), x_base_offset + 135, 235, 125, 70, 35, text="RESTART")

    # Declare variable for storing AI suggestion
    suggest_x = -1
    suggest_y = -1

    while True:

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                break

        # Draw white background
        window.fill((255, 255, 255))

        # Draw captions
        window.blit(turn_caption, (x_base_offset, 85))
        window.blit(AI_score_caption, (x_base_offset, 135))
        window.blit(Player_score_caption, (x_base_offset, 185))

        # Draw button
        restart_button.draw(window, True)

        # Draw board
        _draw(window, game, player_color)

        # Draw Info
        _draw_info(window, x_base_offset)

        # Draw last AI move if possible
        AI_x, AI_y = last_move
        if not AI_x == -1:
            pg.draw.circle(window, (255, 0, 0), (
                (AI_x * grid_size) + grid_size + boarder_size / 2, (AI_y * grid_size) + grid_size + boarder_size / 2),
                           5)

        # Draw AI suggestion if possible
        if not suggest_x == -1:
            pg.draw.circle(window, (91, 143, 219), (
                (suggest_x * grid_size) + grid_size + boarder_size / 2,
                (suggest_y * grid_size) + grid_size + boarder_size / 2),
                           16)
            pg.draw.circle(window, (255, 255, 255), (
                (suggest_x * grid_size) + grid_size + boarder_size / 2,
                (suggest_y * grid_size) + grid_size + boarder_size / 2), 14)

        # Check if the mouse is near any of the dots
        mouse_x, mouse_y = pg.mouse.get_pos()
        for i, intersection in enumerate(intersections):
            if 18 > math.sqrt((mouse_x - intersection[0]) ** 2 + (mouse_y - intersection[1]) ** 2) and game.board[
                index[i][0], index[i][1]] == 0:
                # draw virtual dot at coordinate of intersection
                if player_color == "BLACK":
                    pg.draw.circle(window, (0, 0, 0), (intersection[0], intersection[1]), 16)
                else:
                    pg.draw.circle(window, (0, 0, 0), (intersection[0], intersection[1]), 16)
                    pg.draw.circle(window, (255, 255, 255), (intersection[0], intersection[1]), 14)

                if pg.mouse.get_pressed()[0]:
                    return index[i][0], index[i][1]
                break

        # Check if user clicks button
        if pg.mouse.get_pressed()[0]:
            mouse_position = pg.mouse.get_pos()
            # Restart Game
            if restart_button.isOver(mouse_position):
                return -1, -1

        pg.display.update()


def finish_screen(window, state: str, game: Gomoku, player_color: str, last_move: (), turn_count: int,
                  player_score: int, AI_score: int, grid_size: int, boarder_size: int):
    """Draws the window when a round has been completed"""
    # Set display parameter
    x_base_offset = len(game.board[0]) * grid_size + grid_size + boarder_size + 10

    # Calculate winning move coordinates
    win_start, win_end = get_winning_move(game)
    win_start_loc = [(win_start[0] * grid_size) + grid_size + boarder_size / 2,
                     (win_start[1] * grid_size) + grid_size + boarder_size / 2]
    win_end_loc = [(win_end[0] * grid_size) + grid_size + boarder_size / 2,
                   (win_end[1] * grid_size) + grid_size + boarder_size / 2]

    # Construct a Blank space
    pg.draw.rect(window, (192, 198, 211), (0, x_base_offset / 4 + 270, x_base_offset + 300, 70), 0)
    pg.draw.rect(window, (255, 255, 255), (0, x_base_offset / 4 + 273, x_base_offset + 300, 64), 0)
    pg.draw.rect(window, (192, 198, 211), (0, x_base_offset / 4 + 276, x_base_offset + 300, 58), 0)

    # Construct captions
    font = pg.font.SysFont('arialms', 40)
    player_won_caption = font.render("You Won!", True, (0, 0, 0))
    AI_won_caption = font.render("CPU Won!", True, (0, 0, 0))
    tie_caption = font.render("Tie Game!", True, (0, 0, 0))

    font = pg.font.SysFont('arialms', 35)
    round_string = "ROUND: " + str(int(turn_count))
    turn_caption = font.render(round_string, True, (0, 0, 0))

    AI_score_string = "CPU SCORE: " + str(AI_score)
    AI_score_caption = font.render(AI_score_string, True, (0, 0, 0))

    Player_score_string = "Your SCORE: " + str(player_score)
    Player_score_caption = font.render(Player_score_string, True, (0, 0, 0))

    font = pg.font.SysFont('arialms', 30)
    continue_caption = font.render("Click anywhere to continue", True, (91, 143, 219))

    if state == 'AI_win':
        window.blit(AI_won_caption, (45, x_base_offset / 4 + 293))
    elif state == 'Player_win':
        window.blit(player_won_caption, (45, x_base_offset / 4 + 293))
    else:
        window.blit(tie_caption, (45, x_base_offset / 4 + 293))

    pg.display.update()

    time.sleep(1.5)
    while True:

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                break

        # Draw white background
        window.fill((255, 255, 255))

        # Draw caption
        window.blit(continue_caption, (x_base_offset, 35))
        window.blit(turn_caption, (x_base_offset, 85))
        window.blit(AI_score_caption, (x_base_offset, 135))
        window.blit(Player_score_caption, (x_base_offset, 185))

        # Draw board
        _draw(window, game, player_color)

        # Draw Info
        _draw_info(window, x_base_offset)

        # Draw last AI move
        AI_x, AI_y = last_move
        if not AI_x == -1:
            pg.draw.circle(window, (255, 0, 0), (
                (AI_x * grid_size) + grid_size + boarder_size / 2,
                (AI_y * grid_size) + grid_size + boarder_size / 2), 5)

        # Connect winning moves
        pg.draw.line(window, (91, 143, 219), (win_start_loc[0], win_start_loc[1]),
                     (win_end_loc[0], win_end_loc[1]), 5)

        pg.display.update()

        if pg.mouse.get_pressed()[0]:
            return True
