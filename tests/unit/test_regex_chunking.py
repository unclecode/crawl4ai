import pytest

from crawl4ai.chunking_strategy import RegexChunking


@pytest.mark.parametrize(
    ("extra_patterns", "expected_tail"),
    [([], ["gamma | delta"]), ([r" \| "], ["gamma", "delta"])],
)
def test_optional_regex_group_adds_only_participating_captures(
    extra_patterns, expected_tail
):
    chunker = RegexChunking(patterns=[r"\n([A-Z]+)?\n", *extra_patterns])

    assert chunker.chunk("alpha\n\nbeta\nHEADER\ngamma | delta") == [
        "alpha",
        "beta",
        "HEADER",
        *expected_tail,
    ]
