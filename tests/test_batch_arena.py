import unittest

from arena import Score
from batch_arena import (
    agent_name_from_spec,
    chunk_jobs,
    make_head_to_head_jobs,
    make_round_robin_jobs,
    progress_line,
    resolve_chunk_size,
    resolve_workers,
)


class BatchArenaTests(unittest.TestCase):
    def test_head_to_head_alternates_sides(self):
        jobs = make_head_to_head_jobs("a", "b", games=3, board_size=9, seed=1, alternate_sides=True)

        self.assertEqual((jobs[0].black_spec, jobs[0].white_spec), ("a", "b"))
        self.assertEqual((jobs[1].black_spec, jobs[1].white_spec), ("b", "a"))
        self.assertEqual((jobs[2].black_spec, jobs[2].white_spec), ("a", "b"))

    def test_round_robin_pairs_and_alternates(self):
        jobs = make_round_robin_jobs(["a", "b", "c"], games=2, board_size=9, seed=1)

        self.assertEqual(len(jobs), 6)
        self.assertEqual((jobs[0].black_spec, jobs[0].white_spec), ("a", "b"))
        self.assertEqual((jobs[1].black_spec, jobs[1].white_spec), ("b", "a"))
        self.assertEqual((jobs[2].black_spec, jobs[2].white_spec), ("a", "c"))

    def test_worker_and_chunk_bounds(self):
        self.assertEqual(resolve_workers(100, job_count=3), 3)
        self.assertGreaterEqual(resolve_workers(None, job_count=3), 1)
        self.assertEqual(resolve_chunk_size(2, job_count=5, workers=2), 2)
        self.assertEqual(resolve_chunk_size(None, job_count=5, workers=2), 3)
        self.assertEqual([len(chunk) for chunk in chunk_jobs([1, 2, 3, 4, 5], 2)], [2, 2, 1])

    def test_agent_name_from_spec_matches_arena_names(self):
        self.assertEqual(agent_name_from_spec("native-minizero:MEDIUM"), "native-minizero:medium")
        self.assertEqual(agent_name_from_spec("minizero:test:65"), "minizero:test:65")

    def test_progress_line_respects_requested_order(self):
        easy = Score("native-minizero:easy", wins=3)
        medium = Score("native-minizero:medium", wins=1)

        line = progress_line(
            4,
            10,
            {"native-minizero:easy": easy, "native-minizero:medium": medium},
            score_order=["native-minizero:medium", "native-minizero:easy"],
        )

        self.assertIn("native-minizero:medium 1 - 3 native-minizero:easy", line)


if __name__ == "__main__":
    unittest.main()
