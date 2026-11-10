"""Regression tests for the window/overlap validation in OverlappingWindowChunking."""

import pytest

from crawl4ai.chunking_strategy import OverlappingWindowChunking


def _words(count: int) -> str:
    return " ".join(str(i) for i in range(count))


def test_overlap_equal_to_window_is_rejected():
    # `start = end - overlap` never advances when overlap == window_size, so chunk()
    # used to loop forever while appending the same window.
    with pytest.raises(ValueError, match="overlap must be between"):
        OverlappingWindowChunking(window_size=5, overlap=5)


def test_overlap_larger_than_window_is_rejected():
    # A larger overlap walks `start` backwards through the text and never terminates.
    with pytest.raises(ValueError, match="overlap must be between"):
        OverlappingWindowChunking(window_size=5, overlap=6)


def test_non_positive_window_is_rejected():
    with pytest.raises(ValueError, match="window_size must be at least 1"):
        OverlappingWindowChunking(window_size=0, overlap=0)


def test_valid_overlap_still_slides_one_word_at_a_time():
    chunking = OverlappingWindowChunking(window_size=5, overlap=4)
    assert len(chunking.chunk(_words(20))) == 16


def test_overlap_mutated_after_construction_still_terminates():
    chunking = OverlappingWindowChunking(window_size=5, overlap=1)
    chunking.overlap = 5
    assert len(chunking.chunk(_words(20))) == 16
