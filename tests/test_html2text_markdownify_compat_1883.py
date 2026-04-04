"""
Tests for #1883: html2text replaced with markdownify (MIT) wrapper.

Verifies the compatibility layer preserves the same interface and output
quality that the rest of crawl4ai depends on.
"""
import pytest


class TestHTML2TextInterface:
    """Verify the old html2text interface still works."""

    def test_html2text_function(self):
        from crawl4ai.html2text import html2text
        result = html2text("<h1>Hello</h1><p>World</p>")
        assert "Hello" in result
        assert "World" in result

    def test_html2text_class(self):
        from crawl4ai.html2text import HTML2Text
        h = HTML2Text()
        result = h.handle("<p><strong>Bold</strong></p>")
        assert "Bold" in result
        assert "**" in result

    def test_custom_html2text_class(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        result = h.handle("<p>Test</p>")
        assert "Test" in result

    def test_custom_html2text_update_params(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        h.update_params(body_width=0, ignore_links=True)
        assert h.body_width == 0
        assert h.ignore_links is True

    def test_baseurl_param(self):
        from crawl4ai.html2text import HTML2Text
        h = HTML2Text(baseurl="https://example.com")
        assert h.baseurl == "https://example.com"

    def test_empty_input(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        assert h.handle("") == ""
        assert h.handle(None) == ""


class TestMarkdownOutput:
    """Verify markdown output quality."""

    def test_headings(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        result = h.handle("<h1>One</h1><h2>Two</h2><h3>Three</h3>")
        assert "# One" in result
        assert "## Two" in result
        assert "### Three" in result

    def test_bold_italic(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        result = h.handle("<strong>bold</strong> and <em>italic</em>")
        assert "**bold**" in result
        assert "*italic*" in result

    def test_links(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        result = h.handle('<a href="https://example.com">click</a>')
        assert "[click]" in result
        assert "https://example.com" in result

    def test_links_ignored(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        h.ignore_links = True
        result = h.handle('<a href="https://example.com">click</a>')
        assert "https://example.com" not in result

    def test_unordered_list(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        result = h.handle("<ul><li>A</li><li>B</li></ul>")
        assert "A" in result
        assert "B" in result

    def test_ordered_list(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        result = h.handle("<ol><li>First</li><li>Second</li></ol>")
        assert "First" in result
        assert "Second" in result

    def test_code_block(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        result = h.handle('<pre><code>print("hello")</code></pre>')
        assert "print" in result
        assert "hello" in result

    def test_inline_code(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        result = h.handle("Use <code>pip install</code> to install.")
        assert "`pip install`" in result

    def test_table(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        html = "<table><tr><th>Name</th><th>Price</th></tr><tr><td>Widget</td><td>$29</td></tr></table>"
        result = h.handle(html)
        assert "Name" in result
        assert "Widget" in result
        assert "|" in result

    def test_images_preserved(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        result = h.handle('<img src="pic.png" alt="photo">')
        assert "photo" in result

    def test_images_ignored(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        h.ignore_images = True
        result = h.handle('<img src="pic.png" alt="photo">')
        assert "photo" not in result

    def test_no_html_tags_in_output(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        html = "<div><p><strong>Text</strong> with <a href='#'>link</a></p></div>"
        result = h.handle(html)
        assert "<div>" not in result
        assert "<p>" not in result
        assert "<strong>" not in result


class TestPreserveTags:
    """Verify preserve_tags feature works."""

    def test_preserve_svg(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        h.update_params(preserve_tags=["svg"])
        html = '<p>Text</p><svg width="100"><circle r="50"/></svg><p>More</p>'
        result = h.handle(html)
        assert "<svg" in result
        assert "Text" in result
        assert "More" in result

    def test_no_preserve_tags(self):
        from crawl4ai.html2text import CustomHTML2Text
        h = CustomHTML2Text()
        html = '<p>Text</p><svg width="100"><circle r="50"/></svg>'
        result = h.handle(html)
        assert "<svg" not in result


class TestDefaultMarkdownGenerator:
    """Verify DefaultMarkdownGenerator works with the new wrapper."""

    def test_generate_markdown(self):
        from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
        gen = DefaultMarkdownGenerator()
        html = "<html><body><h1>Title</h1><p>Content here.</p></body></html>"
        result = gen.generate_markdown(html)
        assert "Title" in result.raw_markdown
        assert "Content" in result.raw_markdown

    def test_generate_with_options(self):
        from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
        gen = DefaultMarkdownGenerator()
        html = '<p><a href="https://example.com">link</a></p>'
        result = gen.generate_markdown(
            html,
            html2text_options={"ignore_links": True},
        )
        assert "https://example.com" not in result.raw_markdown

    def test_generate_with_base_url(self):
        from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
        gen = DefaultMarkdownGenerator()
        html = '<p><a href="/page">link</a></p>'
        result = gen.generate_markdown(html, base_url="https://example.com")
        assert "link" in result.raw_markdown


class TestImportPaths:
    """Verify all import paths still work."""

    def test_import_from_html2text(self):
        from crawl4ai.html2text import html2text, HTML2Text, CustomHTML2Text
        assert callable(html2text)
        assert HTML2Text is not None
        assert CustomHTML2Text is not None

    def test_import_in_utils(self):
        from crawl4ai.utils import CustomHTML2Text
        assert CustomHTML2Text is not None

    def test_import_in_markdown_strategy(self):
        from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
        assert DefaultMarkdownGenerator is not None
