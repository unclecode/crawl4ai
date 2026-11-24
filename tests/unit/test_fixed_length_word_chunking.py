import pytest

from crawl4ai.chunking_strategy import FixedLengthWordChunking


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_fixed_length_word_chunking_rejects_nonpositive_sizes(chunk_size):
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        FixedLengthWordChunking(chunk_size=chunk_size)


def test_fixed_length_word_chunking_keeps_partial_final_chunk():
    chunker = FixedLengthWordChunking(chunk_size=2)

    assert chunker.chunk("one two three") == ["one two", "three"]
    assert chunker.chunk("") == []
