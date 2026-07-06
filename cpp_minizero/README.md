# Native miniZero Engine

This directory contains a C++ implementation of the legacy Python `miniZero`
move selector. It uses the same active NumPy value-network weights exported from
`../numpy_network_weights.npz`.

The implementation intentionally mirrors the original code, including move
ordering, pattern-count features, and the legacy minimax recursion shape.

## Build

```bash
make -C cpp_minizero
```

## Single Move

Board strings are x-major flattened digits from `board[x][y]`.

```bash
cpp_minizero/minizero_native --level test --size 9 --board 000000000000000000000000000000100000000000000000000000000000000000000000000000000
```

## Parity And Speed Check

```bash
.venv/bin/python cpp_minizero/tools/compare_native.py --positions 100 --levels test EASY --board-size 9
```

The comparison script skips empty positions because the original Python
miniZero intentionally chooses its first move with Python's global random
generator.
