# Gomoku AI Arena

`arena.py` runs headless AI-vs-AI Gomoku matches using the existing `Gomoku`
state and win detection. The original Pygame UI in `run.py` is unchanged.

For browser-based human-vs-AI play, run:

```bash
python3 serve.py --host 0.0.0.0 --port 8765
```

The browser UI can also run AI-vs-AI games. Set each side independently in the
Black and White selectors, use the center swap button to exchange side
controllers, and use pause/resume to stop or continue automatic AI play.

## Agents

Built-in specs:

- `first`: first legal point in board scan order.
- `random`: uniformly random legal point.
- `center`: closest legal point to the board center.
- `minizero:EASY[:current|original|65]`: legacy miniZero at depth 2.
- `minizero:MEDIUM[:current|original|65]`: legacy miniZero at depth 3.
- `minizero:test[:current|original|65]`: legacy miniZero at depth 1.

The miniZero wrapper normalizes board perspective, so miniZero can play as
either black/player 1 or white/player 2 even though the original code assumes
it is always player 1.

## Examples

List available agent specs:

```bash
python3 arena.py --list-agents
```

Run a quick round robin:

```bash
python3 arena.py --agents random,center,first --games 4 --seed 7
```

Run a fixed head-to-head:

```bash
python3 arena.py --black minizero:test --white random --games 2 --board-size 15 --seed 7 --verbose
```

Compare bundled miniZero weight snapshots:

```bash
python3 arena.py --agents minizero:test:current,minizero:test:original,minizero:test:65 --games 2 --seed 7
```

The summary reports games, wins, losses, draws, win rate, average milliseconds
per move, and illegal-move losses.
