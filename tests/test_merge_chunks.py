import unittest
from crawl4ai.utils import merge_chunks

class TestMergeChunks(unittest.TestCase):

    def test_no_overlap_respects_target_size(self):
        docs = [f"word{i} " * 50 for i in range(200)]  # 10000 tokens total
        chunks = merge_chunks(docs, target_size=2048, overlap=0)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.split()), 2048)

    def test_overlap_does_not_overshoot_target_size(self):
        # chunk_token_threshold=2048 / overlap_rate=0.1 are this repo's own defaults.
        docs = [f"word{i} " * 50 for i in range(200)]  # 10000 tokens total
        chunks = merge_chunks(docs, target_size=2048, overlap=205)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.split()), 2048)

    def test_overlap_does_not_overshoot_on_longer_documents(self):
        # Regression guard: the pre-allocated-chunk-count bug made the last chunk grow
        # without bound as more documents were merged in.
        docs = [f"word{i} " * 50 for i in range(3200)]  # 160000 tokens total
        chunks = merge_chunks(docs, target_size=2048, overlap=205)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.split()), 2048)

    def test_overlap_tokens_are_repeated_at_chunk_boundary(self):
        docs = [f"word{i}" for i in range(10)]
        chunks = merge_chunks(docs, target_size=6, overlap=2)
        self.assertEqual(chunks[0].split()[-2:], chunks[1].split()[:2])

    def test_all_tokens_are_preserved_without_overlap(self):
        docs = [f"word{i}" for i in range(10)]
        chunks = merge_chunks(docs, target_size=6, overlap=0)
        merged = " ".join(chunks).split()
        self.assertEqual(merged, [f"word{i}" for i in range(10)])

    def test_empty_docs_returns_empty_list(self):
        self.assertEqual(merge_chunks([], target_size=100), [])
        self.assertEqual(merge_chunks(["", "  "], target_size=100), [])
