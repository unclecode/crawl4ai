"""An inline element holding only whitespace must not become an empty marker pair.

`handle_data` strips whitespace-only content inside a stressed tag, so `<b> </b>`
reached the closing tag with nothing between the markers. The pair was emitted
anyway, which left `****` in the output and, between two stressed runs, dropped
the only space separating two words.
"""

import pytest

from crawl4ai.html2text import CustomHTML2Text


def _markdown(html: str) -> str:
    return CustomHTML2Text().handle(html).strip()


@pytest.mark.parametrize(
    "tag",
    ["b", "strong", "em", "i", "u", "s", "del", "strike"],
)
def test_whitespace_only_element_keeps_the_word_boundary(tag: str) -> None:
    assert _markdown(f"<p>Hello<{tag}> </{tag}>world</p>") == "Hello world"


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("b", "**First** **Last**"),
        ("strong", "**First** **Last**"),
        ("em", "_First_ _Last_"),
        ("i", "_First_ _Last_"),
        ("s", "~~First~~ ~~Last~~"),
    ],
)
def test_a_space_between_two_styled_runs_survives(tag: str, expected: str) -> None:
    """An editor that emits one element per styled run puts the space in its own element."""
    html = f"<p><{tag}>First</{tag}><{tag}> </{tag}><{tag}>Last</{tag}></p>"

    assert _markdown(html) == expected


def test_whitespace_already_outside_the_element_is_not_doubled() -> None:
    assert _markdown("<p>Hello <b> </b>world</p>") == "Hello world"
    assert _markdown("<p>Hello<b> </b> world</p>") == "Hello world"


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        ("<p>Hello <b>bold</b> world</p>", "Hello **bold** world"),
        ("<p>Hello <em>it</em> world</p>", "Hello _it_ world"),
        ("<p>Hello <s>gone</s> world</p>", "Hello ~~gone~~ world"),
        ("<p>Hello <b><i>x</i></b> world</p>", "Hello **_x_** world"),
        ("<p><b>a</b><b>b</b></p>", "**a****b**"),
    ],
)
def test_elements_with_content_are_unchanged(html: str, expected: str) -> None:
    """The control: only a marker pair with nothing inside it is taken back."""
    assert _markdown(html) == expected
