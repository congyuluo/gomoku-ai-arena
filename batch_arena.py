from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from arena import DRAW, GameResult, Score, make_agent, play_game, print_results, print_scores, update_scores


@dataclass(frozen=True)
class GameJob:
    index: int
    black_spec: str
    white_spec: str
    board_size: int
    seed: int


@dataclass
class TimedResult:
    index: int
    elapsed_sec: float
    result: GameResult


def make_head_to_head_jobs(
    black_spec: str,
    white_spec: str,
    games: int,
    board_size: int,
    seed: int,
    alternate_sides: bool,
) -> List[GameJob]:
    rng = random.Random(seed)
    jobs = []
    for index in range(games):
        black, white = black_spec, white_spec
        if alternate_sides and index % 2 == 1:
            black, white = white_spec, black_spec
        jobs.append(
            GameJob(
                index=index + 1,
                black_spec=black,
                white_spec=white,
                board_size=board_size,
                seed=rng.randrange(2**63),
            )
        )
    return jobs


def make_round_robin_jobs(agent_specs: Sequence[str], games: int, board_size: int, seed: int) -> List[GameJob]:
    if len(agent_specs) < 2:
        raise ValueError("round robin needs at least two agents")

    rng = random.Random(seed)
    jobs = []
    index = 1
    for left_index in range(len(agent_specs)):
        for right_index in range(left_index + 1, len(agent_specs)):
            left = agent_specs[left_index]
            right = agent_specs[right_index]
            for game_index in range(games):
                black, white = (left, right) if game_index % 2 == 0 else (right, left)
                jobs.append(
                    GameJob(
                        index=index,
                        black_spec=black,
                        white_spec=white,
                        board_size=board_size,
                        seed=rng.randrange(2**63),
                    )
                )
                index += 1
    return jobs


def chunk_jobs(jobs: Sequence[GameJob], chunk_size: int) -> List[List[GameJob]]:
    return [list(jobs[index : index + chunk_size]) for index in range(0, len(jobs), chunk_size)]


def close_cached_agents(cache: Dict[str, object]) -> None:
    for agent in cache.values():
        close = getattr(agent, "close", None)
        if callable(close):
            close()


def cached_agent(cache: Dict[str, object], spec: str) -> object:
    agent = cache.get(spec)
    if agent is None:
        agent = make_agent(spec)
        cache[spec] = agent
    return agent


def run_job_chunk(jobs: Sequence[GameJob]) -> List[TimedResult]:
    agent_cache: Dict[str, object] = {}
    results: List[TimedResult] = []
    try:
        for job in jobs:
            black = cached_agent(agent_cache, job.black_spec)
            white = cached_agent(agent_cache, job.white_spec)
            started = time.perf_counter()
            result = play_game(black, white, board_size=job.board_size, seed=job.seed)
            elapsed = time.perf_counter() - started
            results.append(TimedResult(index=job.index, elapsed_sec=elapsed, result=result))
    finally:
        close_cached_agents(agent_cache)
    return results


def resolve_workers(requested_workers: Optional[int], job_count: int) -> int:
    detected = os.cpu_count() or 1
    workers = requested_workers if requested_workers is not None else detected
    if workers < 1:
        workers = detected
    return max(1, min(workers, job_count))


def resolve_chunk_size(requested_chunk_size: Optional[int], job_count: int, workers: int) -> int:
    if requested_chunk_size is not None:
        return max(1, requested_chunk_size)
    return max(1, math.ceil(job_count / workers))


def summarize_scores(results: Iterable[TimedResult]) -> Dict[str, Score]:
    scores: Dict[str, Score] = {}
    for timed in sorted(results, key=lambda item: item.index):
        update_scores(scores, timed.result)
    return scores


def result_to_dict(timed: TimedResult) -> dict:
    result = timed.result
    return {
        "index": timed.index,
        "elapsed_sec": timed.elapsed_sec,
        "black": result.black,
        "white": result.white,
        "winner": result.winner,
        "winner_name": result.winner_name,
        "reason": result.reason,
        "moves": len(result.moves),
        "illegal_player": result.illegal_player,
        "draw": result.winner == DRAW,
    }


def write_json(path: Path, results: Sequence[TimedResult], scores: Dict[str, Score], config: dict) -> None:
    payload = {
        "config": config,
        "results": [result_to_dict(result) for result in sorted(results, key=lambda item: item.index)],
        "scores": {name: asdict(score) for name, score in sorted(scores.items())},
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_parallel(jobs: Sequence[GameJob], workers: int, chunk_size: int, progress: bool) -> List[TimedResult]:
    chunks = chunk_jobs(jobs, chunk_size)
    results: List[TimedResult] = []
    completed = 0

    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_count = {executor.submit(run_job_chunk, chunk): len(chunk) for chunk in chunks}
        for future in concurrent.futures.as_completed(future_to_count):
            chunk_results = future.result()
            results.extend(chunk_results)
            completed += future_to_count[future]
            if progress:
                print(f"completed {completed}/{len(jobs)} games", flush=True)

    return sorted(results, key=lambda item: item.index)


def parse_agent_specs(raw: str) -> List[str]:
    specs = [spec.strip() for spec in raw.split(",") if spec.strip()]
    if not specs:
        raise ValueError("at least one agent spec is required")
    return specs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gomoku arena games in parallel across CPU workers.")
    parser.add_argument("--agents", default="random,center", help="Comma-separated specs for round-robin mode.")
    parser.add_argument("--black", help="Black agent spec for head-to-head mode.")
    parser.add_argument("--white", help="White agent spec for head-to-head mode.")
    parser.add_argument("--games", type=int, default=16, help="Games per pairing.")
    parser.add_argument("--board-size", type=int, default=15)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, help="Parallel worker processes. Defaults to detected CPU cores.")
    parser.add_argument("--chunk-size", type=int, help="Games per worker task. Defaults to balanced chunks.")
    parser.add_argument("--alternate-sides", action="store_true", help="Alternate sides in head-to-head mode.")
    parser.add_argument("--verbose", action="store_true", help="Print each game result before the summary.")
    parser.add_argument("--progress", action="store_true", help="Print progress as chunks finish.")
    parser.add_argument("--json-out", type=Path, help="Write machine-readable results to this JSON file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.games < 1:
        raise ValueError("--games must be at least 1")
    if args.board_size < 5:
        raise ValueError("--board-size must be at least 5")

    if args.black or args.white:
        if not (args.black and args.white):
            raise ValueError("--black and --white must be provided together")
        jobs = make_head_to_head_jobs(
            args.black,
            args.white,
            games=args.games,
            board_size=args.board_size,
            seed=args.seed,
            alternate_sides=args.alternate_sides,
        )
        mode = "head-to-head"
    else:
        specs = parse_agent_specs(args.agents)
        jobs = make_round_robin_jobs(specs, games=args.games, board_size=args.board_size, seed=args.seed)
        mode = "round-robin"

    workers = resolve_workers(args.workers, len(jobs))
    chunk_size = resolve_chunk_size(args.chunk_size, len(jobs), workers)
    config = {
        "mode": mode,
        "games": args.games,
        "board_size": args.board_size,
        "seed": args.seed,
        "workers": workers,
        "detected_cpus": os.cpu_count() or 1,
        "chunk_size": chunk_size,
        "total_jobs": len(jobs),
    }

    print(
        f"running {len(jobs)} games with {workers} worker(s), "
        f"chunk_size={chunk_size}, detected_cpus={config['detected_cpus']}"
    )
    started = time.perf_counter()
    timed_results = run_parallel(jobs, workers=workers, chunk_size=chunk_size, progress=args.progress)
    wall_sec = time.perf_counter() - started
    scores = summarize_scores(timed_results)

    print_results([timed.result for timed in timed_results], args.verbose)
    print_scores(scores)
    print(f"wall_sec={wall_sec:.3f}")
    print(f"games_per_sec={len(jobs) / wall_sec:.3f}" if wall_sec > 0 else "games_per_sec=inf")

    if args.json_out:
        write_json(args.json_out, timed_results, scores, config)
        print(f"wrote {args.json_out}")


if __name__ == "__main__":
    main()
