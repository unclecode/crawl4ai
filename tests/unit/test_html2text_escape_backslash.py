"""Unit tests for CustomHTML2Text's escape_backslash config flag.

escape_backslash is threaded from config.py -> HTML2Text.__init__ -> instance
attribute, and sibling flags (escape_dot/escape_plus/escape_dash) are all
forwarded into escape_md_section() at its call site in handle_data(). This
tests that escape_backslash is forwarded the same way, so that setting it to
False actually disables backslash escaping in the generated markdown.
"""
from crawl4ai.html2text import CustomHTML2Text


def _convert(html: str, escape_backslash: bool) -> str:
    h = CustomHTML2Text()
    h.body_width = 0
    h.escape_backslash = escape_backslash
    return h.handle(html)


# RE_MD_BACKSLASH_MATCHER (html2text/config.py) only fires on a backslash
# followed by a markdown-special char (`*_{}[]()#+-.!), so the repro text
# must contain a literal backslash immediately before one of those chars.
HTML_WITH_BACKSLASH = r"<p>Use \* for multiplication</p>"


class TestEscapeBackslashConfig:
    def test_escape_backslash_false_leaves_backslashes_alone(self):
        """escape_backslash=False must not double the literal backslash."""
        out = _convert(HTML_WITH_BACKSLASH, escape_backslash=False)
        assert r"\*" in out
        assert r"\\*" not in out

    def test_escape_backslash_true_still_escapes(self):
        """escape_backslash=True (the escape_md_section default) must still escape."""
        out = _convert(HTML_WITH_BACKSLASH, escape_backslash=True)
        assert r"\\*" in out
