from __future__ import annotations

import argparse
import json
import random
import time
from functools import lru_cache
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import numpy as np

from Gomoku_Game import Gomoku
from arena import BLACK, WHITE, apply_move, copy_game, make_agent

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"

AGENT_SPECS = [
    {"spec": "minizero:test", "label": "miniZero Test", "description": "Depth 1 miniZero, fastest legacy AI"},
    {"spec": "minizero:EASY", "label": "miniZero Easy", "description": "Depth 2 miniZero"},
    {"spec": "minizero:MEDIUM", "label": "miniZero Medium", "description": "Depth 3 miniZero, slower"},
    {"spec": "minizero:test:original", "label": "miniZero Test Original", "description": "Depth 1 with original weights"},
    {"spec": "minizero:test:65", "label": "miniZero Test 65", "description": "Depth 1 with 65 weights"},
    {"spec": "center", "label": "Center", "description": "Deterministic center-first baseline"},
    {"spec": "random", "label": "Random", "description": "Uniform random legal move"},
    {"spec": "first", "label": "First Legal", "description": "First legal point in scan order"},
]


class ApiError(ValueError):
    def __init__(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.status = status


@lru_cache(maxsize=32)
def cached_agent(spec: str):
    return make_agent(spec)


def parse_board(raw_board: Any) -> Gomoku:
    if not isinstance(raw_board, list) or not raw_board:
        raise ApiError("board must be a non-empty square list")
    size = len(raw_board)
    if size < 5 or size > 25:
        raise ApiError("board size must be between 5 and 25")
    if any(not isinstance(column, list) or len(column) != size for column in raw_board):
        raise ApiError("board must be square and indexed as board[x][y]")

    board = np.zeros((size, size), dtype=float)
    for x, column in enumerate(raw_board):
        for y, value in enumerate(column):
            if value not in (0, 1, 2):
                raise ApiError("board values must be 0, 1, or 2")
            board[x, y] = value

    game = Gomoku(size=size)
    game.board = board
    return game


def parse_payload(body: bytes) -> Dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ApiError(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ApiError("JSON payload must be an object")
    return payload


def winner_payload(game: Gomoku) -> Dict[str, Any]:
    winner = int(game.check_win())
    return {
        "winner": winner,
        "game_over": bool(game.check_game_over()),
        "reason": "five in a row" if winner else ("draw" if game.check_game_over() else ""),
    }


def handle_ai_move(payload: Dict[str, Any]) -> Dict[str, Any]:
    spec = str(payload.get("agent", "")).strip()
    if not spec:
        raise ApiError("agent is required")

    player = payload.get("player")
    if player not in (BLACK, WHITE):
        raise ApiError("player must be 1 or 2")

    game = parse_board(payload.get("board"))
    pre_result = winner_payload(game)
    if pre_result["game_over"]:
        return {"move": None, "agent": spec, "elapsed_ms": 0.0, **pre_result}

    seed = payload.get("seed")
    rng = random.Random(seed) if seed is not None else random.Random(random.SystemRandom().randrange(2**63))
    agent = cached_agent(spec)

    started = time.perf_counter()
    move = agent.select_move(copy_game(game), int(player), rng)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    apply_move(game, move, int(player))

    return {
        "move": [int(move[0]), int(move[1])],
        "player": int(player),
        "agent": agent.name,
        "elapsed_ms": elapsed_ms,
        **winner_payload(game),
    }


class ArenaRequestHandler(SimpleHTTPRequestHandler):
    server_version = "GomokuArenaHTTP/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/agents":
            self.write_json({"agents": AGENT_SPECS})
            return
        if path == "/api/health":
            self.write_json({"ok": True})
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = parse_payload(self.rfile.read(content_length))
            if path == "/api/ai-move":
                self.write_json(handle_ai_move(payload))
                return
            raise ApiError("unknown API endpoint", HTTPStatus.NOT_FOUND)
        except ApiError as exc:
            self.write_json({"error": str(exc)}, status=exc.status)
        except Exception as exc:
            self.write_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def write_json(self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the Gomoku AI Arena web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    address = (args.host, args.port)
    httpd = ThreadingHTTPServer(address, ArenaRequestHandler)
    print(f"Serving Gomoku AI Arena at http://{args.host}:{args.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
