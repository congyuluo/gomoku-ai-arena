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
- `minizero:EASY[:current|65]`: legacy miniZero at depth 2.
- `minizero:MEDIUM[:current|65]`: legacy miniZero at depth 3.
- `minizero:test[:current|65]`: legacy miniZero at depth 1.
- `native-minizero:test`: C++ miniZero at depth 1 using the active weights.
- `native-minizero:EASY`: C++ miniZero at depth 2 using the active weights.
- `native-minizero:MEDIUM`: C++ miniZero at depth 3 using the active weights.

The miniZero wrapper normalizes board perspective, so miniZero can play as
either black/player 1 or white/player 2 even though the original code assumes
it is always player 1.

The native miniZero wrapper applies the same perspective normalization and uses
the same random first-move behavior as the Python wrapper. Use
`cpp_minizero/tools/compare_native.py` to verify exact move parity on sampled
non-empty positions.

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

Run a parallel head-to-head batch:

```bash
python3 batch_arena.py --black native-minizero:test --white random --games 100 --workers 8 --alternate-sides --seed 7
```

Omit `--workers` to use the detected CPU count. The default chunk size creates
one task per worker to reuse agent instances; set `--chunk-size` manually when
you want finer load balancing.

For RL training data, add `--rl-out results/file.jsonl`. This streams one compact
JSON object per completed game, with moves encoded as `x * board_size + y` and
players implied by alternating turns from black.

Compare bundled miniZero weight snapshots:

```bash
python3 arena.py --agents minizero:test:current,minizero:test:65 --games 2 --seed 7
```

The summary reports games, wins, losses, draws, win rate, average milliseconds
per move, and illegal-move losses.

The archived `numpy_network_weights original.npz` file is present in the repo
but not listed as playable because it has a 69-feature input shape, unlike the
current 66-feature miniZero extractor.
