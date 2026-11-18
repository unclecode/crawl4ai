"""Unit tests for word-based chunking strategies."""

from crawl4ai.chunking_strategy import OverlappingWindowChunking


def _words(n):
    return " ".join(str(i) for i in range(n))


def test_overlapping_window_basic_overlap():
    chunks = OverlappingWindowChunking(window_size=100, overlap=20).chunk(_words(250))
    assert len(chunks) > 1
    assert chunks[0].split()[0] == "0"
    # The chunks must cover the text up to and including the final word.
    assert chunks[-1].split()[-1] == "249"


def test_overlapping_window_no_overlap():
    chunks = OverlappingWindowChunking(window_size=100, overlap=0).chunk(_words(250))
    assert len(chunks) == 3  # 0-100, 100-200, 200-250


def test_overlapping_window_short_text_single_chunk():
    chunks = OverlappingWindowChunking(window_size=100, overlap=10).chunk(_words(50))
    assert len(chunks) == 1


def test_overlapping_window_overlap_equal_to_window_terminates():
    # Regression: overlap >= window_size previously left `start` unchanged,
    # so chunk() looped forever. It must now terminate and still reach the end.
    chunks = OverlappingWindowChunking(window_size=100, overlap=100).chunk(_words(250))
    assert len(chunks) >= 1
    assert chunks[-1].split()[-1] == "249"


def test_overlapping_window_overlap_greater_than_window_terminates():
    chunks = OverlappingWindowChunking(window_size=50, overlap=80).chunk(_words(200))
    assert len(chunks) >= 1
    assert chunks[-1].split()[-1] == "199"
