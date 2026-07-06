from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from Gomoku_Game import Gomoku

Move = Tuple[int, int]
Predictor = Callable[[Sequence[float]], float]

BLACK = 1
WHITE = 2
DRAW = 0

WEIGHT_ALIASES = {
    "current": "numpy_network_weights.npz",
    "default": "numpy_network_weights.npz",
    "original": "numpy_network_weights original.npz",
    "65": "numpy_network_weights 65.npz",
}


class IllegalMove(ValueError):
    """Raised when an agent returns a move the arena cannot apply."""


class Agent:
    name = "agent"

    def select_move(self, game: Gomoku, player: int, rng: random.Random) -> Move:
        raise NotImplementedError


@dataclass
class MoveRecord:
    turn: int
    player: int
    agent: str
    move: Move
    elapsed_sec: float


@dataclass
class GameResult:
    black: str
    white: str
    winner: int
    reason: str
    moves: List[MoveRecord]
    illegal_player: Optional[int] = None

    @property
    def winner_name(self) -> str:
        if self.winner == BLACK:
            return self.black
        if self.winner == WHITE:
            return self.white
        return "draw"


@dataclass
class Score:
    name: str
    games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    illegal_losses: int = 0
    moves: int = 0
    thinking_sec: float = 0.0

    @property
    def win_rate(self) -> float:
        return self.wins / self.games if self.games else 0.0

    @property
    def avg_ms_per_move(self) -> float:
        return (self.thinking_sec / self.moves * 1000.0) if self.moves else 0.0


@dataclass
class FirstLegalAgent(Agent):
    name: str = "first"

    def select_move(self, game: Gomoku, player: int, rng: random.Random) -> Move:
        moves = legal_moves(game)
        if not moves:
            raise IllegalMove("no legal moves remain")
        return moves[0]


@dataclass
class RandomAgent(Agent):
    name: str = "random"

    def select_move(self, game: Gomoku, player: int, rng: random.Random) -> Move:
        moves = legal_moves(game)
        if not moves:
            raise IllegalMove("no legal moves remain")
        return rng.choice(moves)


@dataclass
class CenterAgent(Agent):
    name: str = "center"

    def select_move(self, game: Gomoku, player: int, rng: random.Random) -> Move:
        moves = legal_moves(game)
        if not moves:
            raise IllegalMove("no legal moves remain")
        center = (len(game.board[0]) - 1) / 2.0
        return min(moves, key=lambda move: ((move[0] - center) ** 2 + (move[1] - center) ** 2, move))


class MiniZeroAgent(Agent):
    def __init__(self, level: str = "EASY", weights: str = "current"):
        from miniZero import miniZero_player

        self.level = normalize_level(level)
        self.weights_label = weights
        predictor = load_numpy_predictor(resolve_weights(weights))
        self.player = miniZero_player(self.level, predictor=predictor)
        self.name = f"minizero:{self.level.lower()}"
        if weights not in ("current", "default"):
            self.name += f":{weights}"

    def select_move(self, game: Gomoku, player: int, rng: random.Random) -> Move:
        normalized = normalize_for_player(game, player)

        # miniZero_player uses the module-level random generator for its empty-board move.
        # Bridge it to the arena RNG so repeated seeded runs are reproducible.
        global_state = random.getstate()
        random.setstate(rng.getstate())
        try:
            move = self.player.think(normalized)
        finally:
            rng.setstate(random.getstate())
            random.setstate(global_state)

        return int(move[0]), int(move[1])


def legal_moves(game: Gomoku) -> List[Move]:
    xs, ys = np.where(game.board == 0)
    return [(int(x), int(y)) for x, y in zip(xs, ys)]


def copy_game(game: Gomoku) -> Gomoku:
    copied = Gomoku(size=len(game.board[0]))
    copied.board = np.array(game.board, copy=True)
    return copied


def normalize_for_player(game: Gomoku, player: int) -> Gomoku:
    normalized = copy_game(game)
    if player == BLACK:
        return normalized
    if player != WHITE:
        raise ValueError(f"unknown player id {player}")

    board = normalized.board
    normalized.board = np.where(board == BLACK, WHITE, np.where(board == WHITE, BLACK, board))
    return normalized


def apply_move(game: Gomoku, move: Move, player: int) -> None:
    if len(move) != 2:
        raise IllegalMove(f"move must be an (x, y) pair, got {move!r}")
    x, y = move
    size = len(game.board[0])
    if not (0 <= x < size and 0 <= y < size):
        raise IllegalMove(f"move {move!r} is outside a {size}x{size} board")
    if game.board[x, y] != 0:
        raise IllegalMove(f"move {move!r} targets an occupied point")
    game.board[x, y] = player


def other_player(player: int) -> int:
    return WHITE if player == BLACK else BLACK


def play_game(
    black: Agent,
    white: Agent,
    board_size: int = 15,
    seed: Optional[int] = None,
    max_moves: Optional[int] = None,
) -> GameResult:
    game = Gomoku(size=board_size)
    agents = {BLACK: black, WHITE: white}
    rng = random.Random(seed)
    current = BLACK
    moves: List[MoveRecord] = []
    max_turns = max_moves or board_size * board_size

    for turn in range(1, max_turns + 1):
        agent = agents[current]
        think_game = copy_game(game)
        started = time.perf_counter()
        try:
            move = agent.select_move(think_game, current, rng)
            elapsed = time.perf_counter() - started
            apply_move(game, move, current)
        except Exception as exc:
            elapsed = time.perf_counter() - started
            moves.append(MoveRecord(turn, current, agent.name, (-1, -1), elapsed))
            return GameResult(
                black=black.name,
                white=white.name,
                winner=other_player(current),
                reason=f"illegal move by {agent.name}: {exc}",
                moves=moves,
                illegal_player=current,
            )

        moves.append(MoveRecord(turn, current, agent.name, move, elapsed))
        winner = game.check_win()
        if winner:
            return GameResult(black=black.name, white=white.name, winner=winner, reason="five in a row", moves=moves)
        if game.check_game_over():
            return GameResult(black=black.name, white=white.name, winner=DRAW, reason="draw", moves=moves)
        current = other_player(current)

    return GameResult(black=black.name, white=white.name, winner=DRAW, reason="max moves reached", moves=moves)


def run_round_robin(agents: Sequence[Agent], games: int, board_size: int, seed: int) -> Tuple[List[GameResult], Dict[str, Score]]:
    if len(agents) < 2:
        raise ValueError("round robin needs at least two agents")

    scores = {agent.name: Score(agent.name) for agent in agents}
    results: List[GameResult] = []
    master_rng = random.Random(seed)

    for left_index in range(len(agents)):
        for right_index in range(left_index + 1, len(agents)):
            left = agents[left_index]
            right = agents[right_index]
            for game_index in range(games):
                black, white = (left, right) if game_index % 2 == 0 else (right, left)
                result = play_game(
                    black,
                    white,
                    board_size=board_size,
                    seed=master_rng.randrange(2**63),
                )
                results.append(result)
                update_scores(scores, result)

    return results, scores


def run_head_to_head(
    black: Agent,
    white: Agent,
    games: int,
    board_size: int,
    seed: int,
    alternate_sides: bool,
) -> Tuple[List[GameResult], Dict[str, Score]]:
    scores = {black.name: Score(black.name), white.name: Score(white.name)}
    results: List[GameResult] = []
    master_rng = random.Random(seed)

    for game_index in range(games):
        game_black, game_white = black, white
        if alternate_sides and game_index % 2 == 1:
            game_black, game_white = white, black
        result = play_game(
            game_black,
            game_white,
            board_size=board_size,
            seed=master_rng.randrange(2**63),
        )
        results.append(result)
        update_scores(scores, result)

    return results, scores


def update_scores(scores: Dict[str, Score], result: GameResult) -> None:
    black_score = scores.setdefault(result.black, Score(result.black))
    white_score = scores.setdefault(result.white, Score(result.white))
    black_score.games += 1
    white_score.games += 1

    for record in result.moves:
        score = black_score if record.player == BLACK else white_score
        score.moves += 1
        score.thinking_sec += record.elapsed_sec

    if result.winner == DRAW:
        black_score.draws += 1
        white_score.draws += 1
    elif result.winner == BLACK:
        black_score.wins += 1
        white_score.losses += 1
    else:
        white_score.wins += 1
        black_score.losses += 1

    if result.illegal_player == BLACK:
        black_score.illegal_losses += 1
    elif result.illegal_player == WHITE:
        white_score.illegal_losses += 1


def load_numpy_predictor(weights_path: Path) -> Predictor:
    weights_bundle = np.load(weights_path, allow_pickle=True)
    weights, biases = weights_bundle["wb"]

    def predict(features: Sequence[float]) -> float:
        x = np.array(features, dtype=np.float32)
        layer_0 = np.dot(x, weights[0]) + biases[0]
        layer_0 = np.maximum(0, layer_0)
        layer_1 = np.dot(layer_0, weights[1]) + biases[1]
        return float(np.tanh(layer_1).reshape(-1)[0])

    return predict


def resolve_weights(weights: str) -> Path:
    repo_root = Path(__file__).resolve().parent
    filename = WEIGHT_ALIASES.get(weights, weights)
    path = Path(filename)
    if not path.is_absolute():
        path = repo_root / path
    if not path.exists():
        known = ", ".join(sorted(WEIGHT_ALIASES))
        raise FileNotFoundError(f"weights file not found: {path}. Known aliases: {known}")
    return path


def normalize_level(level: str) -> str:
    if level.lower() == "test":
        return "test"
    return level.upper()


def make_agent(spec: str) -> Agent:
    normalized = spec.strip()
    key = normalized.lower()
    if key in ("first", "first-legal"):
        return FirstLegalAgent()
    if key in ("random", "rand"):
        return RandomAgent()
    if key in ("center", "center-first"):
        return CenterAgent()
    if key.startswith("minizero"):
        parts = normalized.split(":")
        level = parts[1] if len(parts) > 1 and parts[1] else "EASY"
        weights = parts[2] if len(parts) > 2 and parts[2] else "current"
        return MiniZeroAgent(level=level, weights=weights)
    raise ValueError(f"unknown agent spec {spec!r}")


def print_results(results: Sequence[GameResult], verbose: bool) -> None:
    if not verbose:
        return
    for index, result in enumerate(results, 1):
        side = "draw" if result.winner == DRAW else ("black" if result.winner == BLACK else "white")
        print(
            f"game {index}: black={result.black} white={result.white} "
            f"winner={result.winner_name} side={side} moves={len(result.moves)} reason={result.reason}"
        )


def print_scores(scores: Dict[str, Score]) -> None:
    rows = sorted(scores.values(), key=lambda score: (-score.wins, score.losses, score.name))
    print("agent                         games  wins  losses  draws  win_rate  avg_ms/move  illegal")
    print("----------------------------  -----  ----  ------  -----  --------  -----------  -------")
    for score in rows:
        print(
            f"{score.name:<28}  {score.games:>5}  {score.wins:>4}  {score.losses:>6}  "
            f"{score.draws:>5}  {score.win_rate:>8.1%}  {score.avg_ms_per_move:>11.2f}  "
            f"{score.illegal_losses:>7}"
        )


def list_agents() -> None:
    print("Built-in agent specs:")
    print("  first")
    print("  random")
    print("  center")
    print("  minizero:EASY[:current|original|65]")
    print("  minizero:MEDIUM[:current|original|65]")
    print("  minizero:test[:current|original|65]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gomoku AI-vs-AI matches.")
    parser.add_argument("--agents", default="random,center", help="Comma-separated specs for round robin mode.")
    parser.add_argument("--black", help="Black agent spec for head-to-head mode.")
    parser.add_argument("--white", help="White agent spec for head-to-head mode.")
    parser.add_argument("--games", type=int, default=2, help="Games per pairing.")
    parser.add_argument("--board-size", type=int, default=15)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--alternate-sides", action="store_true", help="Alternate sides in head-to-head mode.")
    parser.add_argument("--verbose", action="store_true", help="Print each game result before the summary.")
    parser.add_argument("--list-agents", action="store_true", help="Show supported agent specs and exit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.list_agents:
        list_agents()
        return
    if args.games < 1:
        raise ValueError("--games must be at least 1")
    if args.board_size < 5:
        raise ValueError("--board-size must be at least 5")

    if args.black or args.white:
        if not (args.black and args.white):
            raise ValueError("--black and --white must be provided together")
        results, scores = run_head_to_head(
            make_agent(args.black),
            make_agent(args.white),
            games=args.games,
            board_size=args.board_size,
            seed=args.seed,
            alternate_sides=args.alternate_sides,
        )
    else:
        agent_specs = [spec.strip() for spec in args.agents.split(",") if spec.strip()]
        results, scores = run_round_robin(
            [make_agent(spec) for spec in agent_specs],
            games=args.games,
            board_size=args.board_size,
            seed=args.seed,
        )

    print_results(results, args.verbose)
    print_scores(scores)


if __name__ == "__main__":
    main()
