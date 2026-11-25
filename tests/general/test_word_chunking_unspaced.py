import random

import pytest

from crawl4ai.chunking_strategy import (
    FixedLengthWordChunking,
    OverlappingWindowChunking,
    SlidingWindowChunking,
)

CHINESE = "今天天气很好我们去公园散步然后回家吃饭。" * 40  # 800 characters, no spaces


def _old_fixed(text, size):
    words = text.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


def _old_sliding(text, window, step):
    words = text.split()
    if len(words) <= window:
        return [text]
    chunks = [" ".join(words[i : i + window]) for i in range(0, len(words) - window + 1, step)]
    last = len(range(0, len(words) - window + 1, step)) - 1
    if last * step + window < len(words):
        chunks.append(" ".join(words[-window:]))
    return chunks


def _old_overlapping(text, window, overlap):
    words = text.split()
    if len(words) <= window:
        return [text]
    chunks, start = [], 0
    while start < len(words):
        end = start + window
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - overlap
    return chunks


def test_text_written_with_spaces_is_chunked_exactly_as_before():
    rng = random.Random(7)
    vocabulary = ["alpha", "beta", "gamma", "delta", "x-ray", "e.g.", "don't", "naïve", "café", "안녕하세요"]
    for _ in range(200):
        text = "".join(
            rng.choice(vocabulary) + rng.choice([" ", "  ", "\n", "\t", " \n "])
            for _ in range(rng.randint(0, 120))
        )
        if rng.random() < 0.5:
            text = "  " + text
        size = rng.randint(1, 30)
        assert FixedLengthWordChunking(chunk_size=size).chunk(text) == _old_fixed(text, size)
        assert SlidingWindowChunking(window_size=size, step=max(1, size // 2)).chunk(text) == _old_sliding(
            text, size, max(1, size // 2)
        )
        assert OverlappingWindowChunking(window_size=size, overlap=size // 3).chunk(text) == _old_overlapping(
            text, size, size // 3
        )


def test_fixed_length_chunks_text_without_spaces_by_character_count():
    chunks = FixedLengthWordChunking(chunk_size=100).chunk(CHINESE)

    assert len(chunks) == 8
    assert all(len(chunk) == 100 for chunk in chunks)
    assert "".join(chunks) == CHINESE


def test_sliding_and_overlapping_windows_split_text_without_spaces():
    sliding = SlidingWindowChunking(window_size=100, step=50).chunk(CHINESE)
    overlapping = OverlappingWindowChunking(window_size=100, overlap=20).chunk(CHINESE)

    assert len(sliding) > 1 and all(len(chunk) == 100 for chunk in sliding)
    assert len(overlapping) > 1 and all(len(chunk) <= 100 for chunk in overlapping)
    assert overlapping[0][-20:] == overlapping[1][:20]


@pytest.mark.parametrize(
    "text",
    [
        "Python是一种编程语言",
        "hello 世界 foo",
        "第1章 Introduction 概述",
        "ไทยภาษา ทดสอบ test",
    ],
)
def test_mixed_text_keeps_the_spacing_of_the_source(text):
    assert FixedLengthWordChunking(chunk_size=1000).chunk(text) == [" ".join(text.split())]
