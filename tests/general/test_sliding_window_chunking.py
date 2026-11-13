"""SlidingWindowChunking must cover every word exactly as often as the step allows."""

import pytest

from crawl4ai.chunking_strategy import SlidingWindowChunking


def _words(count: int) -> str:
    return " ".join(f"w{i}" for i in range(count))


@pytest.mark.parametrize("window_size,step", [(4, 1), (4, 4), (100, 50), (2, 2)])
def test_every_word_lands_in_a_chunk(window_size, step):
    text = _words(23)
    chunks = SlidingWindowChunking(window_size=window_size, step=step).chunk(text)

    covered = {word for chunk in chunks for word in chunk.split()}
    assert covered == set(text.split())


def test_step_larger_than_window_is_rejected():
    # Regression: the words between two windows used to be dropped silently.
    with pytest.raises(ValueError, match="cannot exceed window_size"):
        SlidingWindowChunking(window_size=4, step=6)


@pytest.mark.parametrize("step", [0, -2])
def test_non_positive_step_is_rejected(step):
    # Regression: a negative step produced an empty range and then raised
    # UnboundLocalError on the first word of the trailing window.
    with pytest.raises(ValueError, match="step must be at least 1"):
        SlidingWindowChunking(window_size=4, step=step)


def test_text_shorter_than_window_is_returned_unchanged():
    text = "only three words"
    assert SlidingWindowChunking(window_size=4, step=2).chunk(text) == [text]
