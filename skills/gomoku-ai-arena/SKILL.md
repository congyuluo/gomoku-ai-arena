---
name: gomoku-ai-arena
description: Use this skill when working with the Gomoku AI Arena repository: running AI-vs-AI benchmarks, adding or adapting Gomoku agents, comparing miniZero weight snapshots, validating legal move handling, or reporting arena results.
metadata:
  short-description: Run and extend the Gomoku AI arena
---

# Gomoku AI Arena

## Purpose

Use this skill to operate the headless Gomoku arena in this repository. The arena
compares agents on the same board implementation, validates all moves, times
each move, alternates sides when requested, and reports scores.

## Repository Map

- `arena.py`: headless match runner, built-in agents, miniZero adapter, CLI.
- `batch_arena.py`: multiprocessing batch runner for parallel AI-vs-AI games
  across CPU workers.
- `serve.py`: standard-library HTTP server for the browser UI and JSON AI move
  endpoint.
- `web/`: static HTML/CSS/JS browser UI for human-vs-AI play.
- `cpp_minizero/`: C++ miniZero implementation using exported active weights,
  plus a Python parity/speed harness.
- `Gomoku_Game.py`: board state, win detection, game-over detection.
- `miniZero.py`: legacy minimax/value-network AI. It assumes its own stones are
  player `1`; use the arena adapter rather than calling it directly for white.
- `feature_extraction.py`: feature counts consumed by the value network.
- `numpy_network.py` and `numpy_network_weights*.npz`: bundled legacy value
  networks.
- `run.py` and `Display.py`: original Pygame human-vs-AI UI; not required for
  arena benchmarks.

## Environment

Create a local virtualenv and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

For headless benchmarking, NumPy is the required dependency. Pygame is only for
the original UI and lives in `requirements-ui.txt`.

## Standard Commands

List available agent specs:

```bash
.venv/bin/python arena.py --list-agents
```

Smoke test non-network agents:

```bash
.venv/bin/python arena.py --agents random,center,first --games 2 --seed 7 --verbose
```

Smoke test the legacy miniZero adapter:

```bash
.venv/bin/python arena.py --black minizero:test --white random --games 1 --board-size 9 --seed 7 --verbose
```

Run a parallel batch using CPU workers:

```bash
.venv/bin/python batch_arena.py --black native-minizero:test --white random --games 100 --workers 8 --alternate-sides --seed 7
```

If `--workers` is omitted, `batch_arena.py` uses the detected CPU count. The
default `--chunk-size` creates one task per worker so native agents are reused
inside each worker. Use smaller chunks for finer load balancing when games have
very uneven runtimes.

For RL datasets, prefer `--rl-out results/name.jsonl`. It streams compact records
as games finish, so interrupted long runs keep completed games. Moves are encoded
as `x * board_size + y`; black moves first and players alternate by index.

Start the browser UI on a Tailscale-accessible interface:

```bash
.venv/bin/python serve.py --host 0.0.0.0 --port 8765
```

Then use `tailscale ip -4` to find the URL: `http://<tailscale-ip>:8765`.

The browser UI supports independent Black/White controllers. Each side can be
`Human` or any arena agent, so agents can validate human-vs-AI, AI-vs-AI, and
mixed handoff flows. Player selector changes affect the next move without
resetting the board. The center swap button exchanges the Black/White
controllers. Pause invalidates in-flight AI responses and stops automatic
AI-vs-AI play until resumed.

Compare miniZero weight snapshots:

```bash
.venv/bin/python arena.py --agents minizero:test:current,minizero:test:65 --games 2 --seed 7
```

Build and verify native miniZero:

```bash
make -C cpp_minizero
.venv/bin/python cpp_minizero/tools/compare_native.py --positions 100 --levels test EASY --board-size 9 --seed 123
```

Use native specs such as `native-minizero:test` and `native-minizero:EASY` in
the CLI or browser UI when speed matters. The parity harness compares non-empty
positions because Python miniZero's empty-board first move is random; the arena
wrapper preserves that first-move behavior with the arena RNG.

Do not expose `numpy_network_weights original.npz` as a normal playable model
unless a matching 69-feature extractor is recovered. The file is archived in the
repo, but the current extractor produces 66 features.

Use `minizero:test` for quick validation. `minizero:EASY` and especially
`minizero:MEDIUM` can be much slower because the legacy minimax branches heavily.

## Agent Contract

Every arena agent should implement:

```python
class MyAgent(Agent):
    name = "my-agent"

    def select_move(self, game: Gomoku, player: int, rng: random.Random) -> tuple[int, int]:
        ...
```

Rules:

- `game` is a copy. Mutating it will not update the real match board.
- `player` is `1` for black and `2` for white.
- Return `(x, y)` using the repository's board indexing: `game.board[x, y]`.
- Return only empty, in-bounds points. Illegal moves forfeit immediately.
- Use the provided `rng` for stochastic choices so seeded runs are reproducible.
- Give each competitor a stable, unique `name`, especially when comparing model
  checkpoints or parameter settings.

Register simple built-in agents in `make_agent()`. For external or heavier
agents, prefer a small adapter class that keeps loading/caching in `__init__`
and only chooses a move in `select_move()`.

## Perspective Handling

The legacy miniZero code evaluates itself as player `1`. The arena's
`MiniZeroAgent` calls `normalize_for_player()` before asking miniZero to move.
Do not bypass this when miniZero plays white.

When adding another player-1-only engine, use the same pattern:

1. Copy the game.
2. If the engine is playing white/player `2`, swap `1` and `2` on the copied
   board.
3. Ask the engine for a coordinate in the normalized board.
4. Apply that same coordinate as the actual player on the real board.

## Benchmark Practice

For fair comparisons:

- Use an even `--games` count or `--alternate-sides` in head-to-head mode.
- Set `--seed` and include it in the report.
- Report board size, agent specs, number of games, and whether sides alternated.
- Include illegal losses separately from ordinary losses.
- Treat very small match counts as smoke tests, not strength estimates.

## Validation Checklist

Before reporting that an arena change works:

1. Run `arena.py --list-agents`.
2. Run the non-network smoke test.
3. Run at least one `minizero:test` game.
4. If agent behavior changed, run a deterministic seeded command twice and check
   that the game summaries match.
5. Check `git diff` for accidental changes to bundled weights or unrelated UI
   code.

## Common Failure Modes

- `ModuleNotFoundError: numpy`: create the virtualenv and install requirements.
- MiniZero is slow: use `minizero:test` or a smaller `--board-size` for smoke
  tests.
- Illegal move loss: inspect the verbose game line, then validate adapter bounds
  and occupied-point handling.
- Different seeded results: ensure the agent uses the provided `rng`, not the
  global `random` module or an unseeded NumPy RNG.
