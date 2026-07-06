# Gomoku AI Arena

Headless Gomoku AI-vs-AI arena built around the legacy `miniZero` implementation.
It lets agents play legal, timed matches on the same `Gomoku` board and reports
score summaries for quick model or heuristic comparisons.

The original Pygame UI remains available in `run.py`; the arena entry point is
`arena.py`.

## Browser UI

Start the web UI on all interfaces so another device on your Tailscale network
can open it:

```bash
.venv/bin/python serve.py --host 0.0.0.0 --port 8765
```

Then open `http://<tailscale-ip>:8765` from your Mac. The UI supports the same
arena agent specs, board sizes, independent Black/White player selection,
human-vs-AI, AI-vs-AI, pause/resume, mid-game model swapping, move history,
undo, and persistent score counters.

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

For headless arena runs, NumPy is enough. Pygame is only needed for the original
interactive UI:

```bash
.venv/bin/python -m pip install -r requirements-ui.txt
```

## Quick Start

List built-in agent specs:

```bash
.venv/bin/python arena.py --list-agents
```

Run a round robin:

```bash
.venv/bin/python arena.py --agents random,center,first --games 4 --seed 7
```

Run a fixed head-to-head:

```bash
.venv/bin/python arena.py --black minizero:test --white random --games 2 --board-size 15 --seed 7 --verbose
```

Compare bundled miniZero weight snapshots:

```bash
.venv/bin/python arena.py --agents minizero:test:current,minizero:test:original,minizero:test:65 --games 2 --seed 7
```

## Built-In Agents

- `first`: first legal board point in scan order.
- `random`: uniformly random legal point.
- `center`: closest legal point to the board center.
- `minizero:EASY[:current|original|65]`: legacy miniZero at depth 2.
- `minizero:MEDIUM[:current|original|65]`: legacy miniZero at depth 3.
- `minizero:test[:current|original|65]`: legacy miniZero at depth 1.

The miniZero wrapper normalizes board perspective, so the original player-1-only
AI can play as either black/player 1 or white/player 2.

## Output

The summary includes games, wins, losses, draws, win rate, average milliseconds
per move, and illegal-move losses. Illegal or out-of-bounds moves immediately
forfeit the game, which makes adapters easier to debug.

## Agent Skill

Future Codex agents should use the bundled skill at
`skills/gomoku-ai-arena/SKILL.md` when modifying the arena, adding competitors,
or running benchmark reports.
