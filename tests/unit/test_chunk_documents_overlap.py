"""Chunk overlap is present in the emitted text, including across documents."""

import pytest

from crawl4ai.utils import chunk_documents


@pytest.mark.parametrize(
    "documents",
    [
        ["one two three four five six seven"],
        ["one two", "three four five", "six seven"],
    ],
)
def test_emitted_chunks_share_the_requested_overlap(documents):
    assert list(chunk_documents(documents, 3, 1, word_token_rate=1.0)) == [
        "one two three",
        "three four five",
        "five six seven",
    ]


def test_emitted_chunks_keep_a_partial_tail():
    assert list(chunk_documents(["one two three four"], 3, 1, tokenizer=str.split)) == [
        "one two three",
        "three four",
    ]


def test_zero_overlap_keeps_all_words():
    assert list(chunk_documents(["one two three four"], 3, 0, word_token_rate=1.0)) == [
        "one two three",
        "four",
    ]


def test_input_shorter_than_the_threshold_is_preserved():
    assert list(chunk_documents(["one two"], 3, 1, word_token_rate=1.0)) == ["one two"]


def test_empty_documents_produce_no_chunks():
    assert list(chunk_documents(["", "  "], 3, 1, word_token_rate=1.0)) == []


def test_default_token_estimate_keeps_overlap():
    assert list(
        chunk_documents(["one two three four five six seven eight nine"], 3, 0.75)
    ) == [
        "one two three four",
        "four five six seven",
        "seven eight nine",
    ]


@pytest.mark.parametrize("overlap", [1, 2])
def test_chunks_cover_the_input_without_gaps_or_an_overlap_only_tail(overlap):
    for length in range(1, 31):
        words = [f"word{index}" for index in range(length)]
        chunks = list(
            chunk_documents([" ".join(words)], 4, overlap, word_token_rate=1.0)
        )
        reconstructed = chunks[0].split()
        for previous, current in zip(chunks, chunks[1:]):
            assert previous.split()[-overlap:] == current.split()[:overlap]
            assert len(current.split()) > overlap
            reconstructed.extend(current.split()[overlap:])
        assert reconstructed == words
        assert all(len(chunk.split()) <= 4 for chunk in chunks)
