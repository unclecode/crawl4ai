"""
html2text compatibility layer — wraps markdownify (MIT) to provide the same
interface that crawl4ai's codebase expects (CustomHTML2Text, html2text(), etc.).

Replaces the previous vendored GPLv3 html2text library.
"""

from typing import Optional, Dict, Any
from markdownify import markdownify as md, MarkdownConverter


class HTML2Text:
    """Drop-in replacement for html2text.HTML2Text using markdownify."""

    def __init__(self, baseurl: str = "", bodywidth: Optional[int] = None, **kwargs):
        self.baseurl = baseurl
        self.body_width = bodywidth or 0

        # Options matching the old html2text interface
        self.ignore_links = False
        self.ignore_images = False
        self.ignore_emphasis = False
        self.protect_links = False
        self.single_line_break = False
        self.mark_code = False
        self.escape_snob = False
        self.skip_internal_links = False
        self.ignore_mailto_links = True
        self.escape_backslash = False
        self.escape_dot = False
        self.escape_plus = False
        self.escape_dash = False
        self.include_sup_sub = False

    def handle(self, html: str) -> str:
        """Convert HTML to markdown string."""
        if not html:
            return ""

        kwargs: Dict[str, Any] = {
            "heading_style": "ATX",
            "wrap": False if self.body_width == 0 else True,
            "wrap_width": self.body_width if self.body_width else 80,
            "strip": ["img"] if self.ignore_images else None,
            "convert": None if not self.ignore_links else None,
        }

        # Handle link stripping
        if self.ignore_links:
            kwargs["strip"] = (kwargs.get("strip") or [])
            if "a" not in kwargs["strip"]:
                kwargs["strip"].append("a")

        # Clean None values
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        result = md(html, **kwargs)
        return result if result else ""


class CustomHTML2Text(HTML2Text):
    """
    Extended HTML2Text with crawl4ai-specific features:
    preserve_tags, code block handling, and update_params().
    """

    def __init__(self, *args, handle_code_in_pre=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.preserve_tags = set()
        self.handle_code_in_pre = handle_code_in_pre

    def update_params(self, **kwargs):
        """Update parameters, matching the old html2text interface."""
        for key, value in kwargs.items():
            if key == "preserve_tags":
                self.preserve_tags = set(value)
            else:
                setattr(self, key, value)

    def handle(self, html: str) -> str:
        """Convert HTML to markdown, preserving specified tags."""
        if not html:
            return ""

        # Handle preserve_tags: extract them before conversion, re-inject after
        if self.preserve_tags:
            import re
            import hashlib
            preserved = {}
            for tag in self.preserve_tags:
                pattern = re.compile(
                    rf'(<{tag}[^>]*>.*?</{tag}>)',
                    re.DOTALL | re.IGNORECASE,
                )
                for i, match in enumerate(pattern.finditer(html)):
                    # Use a hex hash as placeholder — no underscores to escape
                    key = hashlib.md5(f"{tag}{i}".encode()).hexdigest()[:16]
                    placeholder = f"PRESERVED{key}"
                    preserved[placeholder] = match.group(0)
                    html = html.replace(match.group(0), placeholder, 1)

            result = super().handle(html)

            for placeholder, original in preserved.items():
                result = result.replace(placeholder, "\n" + original + "\n")

            return result

        return super().handle(html)


def html2text(html: str, baseurl: str = "", bodywidth: Optional[int] = None) -> str:
    """Convenience function matching the old html2text.html2text() interface."""
    h = HTML2Text(baseurl=baseurl, bodywidth=bodywidth)
    return h.handle(html)
