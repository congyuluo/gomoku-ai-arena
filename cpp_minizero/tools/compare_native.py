from __future__ import annotations

import argparse
import random
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CPP_DIR = Path(__file__).resolve().parents[1]
ENGINE = CPP_DIR / "minizero_native"

import sys

sys.path.insert(0, str(ROOT))

from Gomoku_Game import Gomoku
from miniZero import miniZero_player


@dataclass
class Case:
    level: str
    board: np.ndarray


def legal_moves(board: np.ndarray) -> list[tuple[int, int]]:
    xs, ys = np.where(board == 0)
    return [(int(x), int(y)) for x, y in zip(xs, ys)]


def flatten_board(board: np.ndarray) -> str:
    return "".join(str(int(value)) for value in board.reshape(-1))


def make_game(board: np.ndarray) -> Gomoku:
    game = Gomoku(size=len(board))
    game.board = np.array(board, copy=True)
    return game


def random_nonterminal_board(size: int, rng: random.Random, min_moves: int, max_moves: int) -> np.ndarray:
    game = Gomoku(size=size)
    player = 1
    target_moves = rng.randint(min_moves, max_moves)
    for _ in range(target_moves):
        moves = legal_moves(game.board)
        if not moves or game.check_game_over():
            break
        x, y = rng.choice(moves)
        game.board[x, y] = player
        player = 2 if player == 1 else 1
    if np.count_nonzero(game.board) == 0 or game.check_game_over():
        return random_nonterminal_board(size, rng, min_moves, max_moves)
    return game.board


def generate_cases(levels: Iterable[str], positions: int, board_size: int, seed: int) -> list[Case]:
    rng = random.Random(seed)
    cases: list[Case] = []
    max_moves = min(board_size * board_size // 3, 18)
    for level in levels:
        for _ in range(positions):
            board = random_nonterminal_board(board_size, rng, min_moves=1, max_moves=max_moves)
            cases.append(Case(level=level, board=board))
    return cases


def python_move(level: str, board: np.ndarray) -> tuple[tuple[int, int], float]:
    player = miniZero_player(level)
    game = make_game(board)
    start = time.perf_counter()
    move = player.think(game)
    elapsed = time.perf_counter() - start
    return (int(move[0]), int(move[1])), elapsed


def native_moves(cases: list[Case]) -> list[tuple[tuple[int, int], float]]:
    if not ENGINE.exists():
        subprocess.run(["make", "-C", str(CPP_DIR)], check=True)
    input_text = "".join(f"{case.level} {len(case.board)} {flatten_board(case.board)}\n" for case in cases)
    proc = subprocess.run(
        [str(ENGINE), "--batch"],
        input=input_text,
        text=True,
        capture_output=True,
        check=True,
    )
    results = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if parts[0] == "ERR":
            raise RuntimeError(line)
        results.append(((int(parts[0]), int(parts[1])), int(parts[2]) / 1_000_000.0))
    if len(results) != len(cases):
        raise RuntimeError(f"native engine returned {len(results)} results for {len(cases)} cases")
    return results


def compare(cases: list[Case]) -> None:
    native = native_moves(cases)
    mismatches = []
    python_total = 0.0
    native_total = 0.0

    for index, (case, native_result) in enumerate(zip(cases, native), 1):
        py_move, py_elapsed = python_move(case.level, case.board)
        native_move, native_elapsed = native_result
        python_total += py_elapsed
        native_total += native_elapsed
        if py_move != native_move:
            mismatches.append((index, case.level, py_move, native_move, flatten_board(case.board)))
            if len(mismatches) >= 10:
                break

    if mismatches:
        print("MISMATCHES")
        for index, level, py_move, native_move, board in mismatches:
            print(f"case={index} level={level} python={py_move} native={native_move} board={board}")
        raise SystemExit(1)

    print(f"matched_cases={len(cases)}")
    print(f"python_total_sec={python_total:.6f}")
    print(f"native_total_sec={native_total:.6f}")
    if native_total > 0:
        print(f"speedup={python_total / native_total:.2f}x")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Python miniZero and native C++ miniZero moves.")
    parser.add_argument("--positions", type=int, default=100, help="Positions per level.")
    parser.add_argument("--levels", nargs="+", default=["test"], choices=["test", "EASY", "MEDIUM"])
    parser.add_argument("--board-size", type=int, default=9)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases = generate_cases(args.levels, args.positions, args.board_size, args.seed)
    compare(cases)


if __name__ == "__main__":
    main()
