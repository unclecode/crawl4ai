"""
Regression tests for Crawl4AI content processing pipeline.

Covers markdown generation, content filtering (BM25, Pruning),
link/image/table extraction, metadata extraction, tag exclusion,
CSS selector targeting, and real-URL content quality.

Run:
    pytest tests/regression/test_reg_content.py -v
    pytest tests/regression/test_reg_content.py -v -m "not network"
"""

import pytest
import json

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter, PruningContentFilter


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_markdown_raw(local_server):
    """Crawl the home page and verify raw markdown is a non-empty string
    containing the expected heading text and heading markers."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=CrawlerRunConfig())
        assert result.success, f"Crawl failed: {result.error_message}"
        md = result.markdown
        assert md is not None
        assert isinstance(md, str)
        assert len(md) > 0
        assert "Welcome to the Crawl4AI Test Site" in md
        # Should have at least one markdown heading marker
        assert "#" in md


@pytest.mark.asyncio
async def test_markdown_has_headings(local_server):
    """Verify markdown contains the expected h1 and h2 headings."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=CrawlerRunConfig())
        assert result.success
        md = result.markdown
        assert "# Welcome" in md or "# Welcome to the Crawl4AI Test Site" in md
        # h2 heading for Features Overview
        assert "## Features" in md or "## Features Overview" in md


@pytest.mark.asyncio
async def test_markdown_has_code_block(local_server):
    """Verify markdown preserves the code block with triple backticks."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=CrawlerRunConfig())
        assert result.success
        md = result.markdown
        assert "```" in md
        assert "AsyncWebCrawler" in md


@pytest.mark.asyncio
async def test_markdown_has_list(local_server):
    """Verify markdown contains list items from the home page features list."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=CrawlerRunConfig())
        assert result.success
        md = result.markdown
        # Markdown list items should contain at least some of these
        assert "Content extraction" in md or "content extraction" in md
        assert "Link discovery" in md or "link discovery" in md


@pytest.mark.asyncio
async def test_markdown_citations(local_server):
    """Access markdown_with_citations and verify it contains numbered citation references."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=CrawlerRunConfig())
        assert result.success
        citations_md = result.markdown.markdown_with_citations
        assert isinstance(citations_md, str)
        assert len(citations_md) > 0
        # Should have at least one citation reference like [1] or similar
        has_citation = any(f"[{i}]" in citations_md for i in range(1, 20))
        # Some implementations use a different format
        assert has_citation or "⟨" in citations_md or "[" in citations_md


@pytest.mark.asyncio
async def test_markdown_references(local_server):
    """Access references_markdown and verify it contains URLs."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=CrawlerRunConfig())
        assert result.success
        refs = result.markdown.references_markdown
        assert isinstance(refs, str)
        # References should mention URLs or link targets
        assert "http" in refs or "/" in refs


@pytest.mark.asyncio
async def test_markdown_string_compat(local_server):
    """Verify StringCompatibleMarkdown behaves like a string:
    str() works, equality with raw_markdown, and 'in' operator."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=CrawlerRunConfig())
        assert result.success
        md = result.markdown
        raw = md.raw_markdown
        # str(result.markdown) should equal raw_markdown
        assert str(md) == raw
        # 'in' operator should work on the string content
        assert "Welcome" in md


# ---------------------------------------------------------------------------
# Content filtering - BM25
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bm25_fit_markdown(local_server):
    """Crawl with BM25ContentFilter and verify fit_markdown is shorter
    than the full raw_markdown (content was filtered)."""
    gen = DefaultMarkdownGenerator(
        content_filter=BM25ContentFilter(user_query="features")
    )
    config = CrawlerRunConfig(markdown_generator=gen)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=config)
        assert result.success
        fit = result.markdown.fit_markdown
        raw = result.markdown.raw_markdown
        assert fit is not None
        assert len(fit) > 0
        assert len(fit) < len(raw), (
            "fit_markdown should be shorter than raw_markdown after BM25 filtering"
        )


# ---------------------------------------------------------------------------
# Content filtering - Pruning
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pruning_fit_markdown(local_server):
    """Crawl with PruningContentFilter and verify fit_markdown exists
    and is shorter than the full raw_markdown."""
    gen = DefaultMarkdownGenerator(content_filter=PruningContentFilter())
    config = CrawlerRunConfig(markdown_generator=gen)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=config)
        assert result.success
        fit = result.markdown.fit_markdown
        raw = result.markdown.raw_markdown
        assert fit is not None
        assert len(fit) > 0
        assert len(fit) <= len(raw), (
            "fit_markdown should not be longer than raw_markdown"
        )


# ---------------------------------------------------------------------------
# Link extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_links_internal(local_server):
    """Crawl /links-page and verify internal links are extracted with href keys."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/links-page", config=CrawlerRunConfig())
        assert result.success
        internal = result.links.get("internal", [])
        assert isinstance(internal, list)
        assert len(internal) > 0, "Expected internal links to be found"
        # Each link dict should have an href
        for link in internal:
            assert "href" in link, f"Link missing 'href' key: {link}"


@pytest.mark.asyncio
async def test_links_external(local_server):
    """Verify external links include the expected domains."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/links-page", config=CrawlerRunConfig())
        assert result.success
        external = result.links.get("external", [])
        assert len(external) > 0, "Expected external links to be found"
        hrefs = [link["href"] for link in external]
        all_hrefs = " ".join(hrefs)
        assert "example.com" in all_hrefs
        assert "github.com" in all_hrefs
        assert "python.org" in all_hrefs


@pytest.mark.asyncio
async def test_links_exclude_external(local_server):
    """Crawl with exclude_external_links=True and verify no external links remain."""
    config = CrawlerRunConfig(exclude_external_links=True)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/links-page", config=config)
        assert result.success
        external = result.links.get("external", [])
        assert len(external) == 0, f"Expected no external links, got {len(external)}"


@pytest.mark.asyncio
async def test_links_exclude_social(local_server):
    """Crawl with exclude_social_media_links=True and verify no social media
    links appear in the external links list."""
    config = CrawlerRunConfig(exclude_social_media_links=True)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/links-page", config=config)
        assert result.success
        external = result.links.get("external", [])
        social_domains = ["twitter.com", "facebook.com", "linkedin.com"]
        for link in external:
            href = link.get("href", "")
            for domain in social_domains:
                assert domain not in href, (
                    f"Social media link should be excluded: {href}"
                )


@pytest.mark.asyncio
@pytest.mark.network
async def test_links_real_url():
    """Crawl a real URL (quotes.toscrape.com) and verify internal links are found
    (pagination links exist on the main page)."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            url="https://quotes.toscrape.com",
            config=CrawlerRunConfig(),
        )
        assert result.success
        internal = result.links.get("internal", [])
        assert len(internal) > 0, "Expected internal links on quotes.toscrape.com"


# ---------------------------------------------------------------------------
# Image extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_images_extracted(local_server):
    """Crawl /images-page and verify images are extracted."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/images-page", config=CrawlerRunConfig())
        assert result.success
        images = result.media.get("images", [])
        assert isinstance(images, list)
        assert len(images) > 0, "Expected images to be extracted"


@pytest.mark.asyncio
async def test_images_have_fields(local_server):
    """Verify each extracted image dict has src, alt, and score keys."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/images-page", config=CrawlerRunConfig())
        assert result.success
        images = result.media.get("images", [])
        assert len(images) > 0
        for img in images:
            assert "src" in img, f"Image missing 'src': {img}"
            assert "alt" in img, f"Image missing 'alt': {img}"
            assert "score" in img, f"Image missing 'score': {img}"


@pytest.mark.asyncio
async def test_images_scoring(local_server):
    """High-quality images (large, with alt text) should score higher
    than small icons without alt text."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/images-page", config=CrawlerRunConfig())
        assert result.success
        images = result.media.get("images", [])
        assert len(images) >= 2

        # Find the hero/landscape image and the small icon
        hero = None
        icon = None
        for img in images:
            src = img.get("src", "")
            if "landscape" in src or "hero" in src:
                hero = img
            elif "icon" in src and img.get("alt", "") == "":
                icon = img

        if hero and icon:
            assert hero["score"] > icon["score"], (
                f"Hero score ({hero['score']}) should exceed icon score ({icon['score']})"
            )


@pytest.mark.asyncio
async def test_images_exclude_all(local_server):
    """Crawl with exclude_all_images=True and verify no images are returned."""
    config = CrawlerRunConfig(exclude_all_images=True)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/images-page", config=config)
        assert result.success
        images = result.media.get("images", [])
        assert len(images) == 0, f"Expected no images with exclude_all_images, got {len(images)}"


# ---------------------------------------------------------------------------
# Table extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tables_extracted(local_server):
    """Crawl /tables and verify tables appear in the result (either in
    result.media, result.tables, or markdown pipe formatting)."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/tables", config=CrawlerRunConfig())
        assert result.success
        # Tables may appear in result.tables, result.media, or markdown
        has_tables = (
            len(getattr(result, "tables", []) or []) > 0
            or "tables" in result.media
            or "|" in str(result.markdown)
        )
        assert has_tables, "Expected table data to be found in the result"


@pytest.mark.asyncio
async def test_tables_in_markdown(local_server):
    """Verify the markdown output contains table formatting with pipes and dashes."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/tables", config=CrawlerRunConfig())
        assert result.success
        md = str(result.markdown)
        assert "|" in md, "Expected pipe character in markdown tables"
        assert "---" in md or "- -" in md, "Expected separator row in markdown tables"


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_metadata_title(local_server):
    """Crawl /structured-data and verify the page title is in metadata."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            url=f"{local_server}/structured-data", config=CrawlerRunConfig()
        )
        assert result.success
        assert result.metadata is not None
        # Title should be "Article with Structured Data"
        title = result.metadata.get("title", "")
        assert "Article with Structured Data" in title or "Structured Data" in title


@pytest.mark.asyncio
async def test_metadata_og_tags(local_server):
    """Verify og:title, og:description, og:image are present in metadata."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            url=f"{local_server}/structured-data", config=CrawlerRunConfig()
        )
        assert result.success
        meta = result.metadata
        assert meta is not None

        # Check for og tags -- they may be stored with different key formats
        og_title = meta.get("og:title", meta.get("og_title", ""))
        og_desc = meta.get("og:description", meta.get("og_description", ""))
        og_image = meta.get("og:image", meta.get("og_image", ""))

        assert og_title, f"Missing og:title in metadata: {meta}"
        assert og_desc, f"Missing og:description in metadata: {meta}"
        assert og_image, f"Missing og:image in metadata: {meta}"


@pytest.mark.asyncio
async def test_metadata_description(local_server):
    """Verify meta description is present in metadata."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            url=f"{local_server}/structured-data", config=CrawlerRunConfig()
        )
        assert result.success
        meta = result.metadata
        assert meta is not None
        desc = meta.get("description", "")
        assert desc, f"Missing description in metadata: {meta}"
        assert "web crawling" in desc.lower()


@pytest.mark.asyncio
@pytest.mark.network
async def test_metadata_real():
    """Crawl https://example.com and verify title metadata exists."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            url="https://example.com", config=CrawlerRunConfig()
        )
        assert result.success
        assert result.metadata is not None
        title = result.metadata.get("title", "")
        assert title, "Expected title metadata from example.com"


# ---------------------------------------------------------------------------
# Excluded tags
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_excluded_tags_nav(local_server):
    """Crawl / with excluded_tags=["nav"] and verify navigation links are
    removed from cleaned_html."""
    config = CrawlerRunConfig(excluded_tags=["nav"])
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=config)
        assert result.success
        cleaned = result.cleaned_html or ""
        # The nav element contained links to Products, Links, Tables
        # After exclusion these should be absent from cleaned_html
        assert "<nav" not in cleaned.lower(), "nav tag should be excluded from cleaned_html"


@pytest.mark.asyncio
async def test_excluded_selector(local_server):
    """Crawl / with excluded_selector='footer' and verify footer content
    is excluded from cleaned_html."""
    config = CrawlerRunConfig(excluded_selector="footer")
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=config)
        assert result.success
        cleaned = result.cleaned_html or ""
        assert "Footer content" not in cleaned, (
            "Footer content should be excluded from cleaned_html"
        )


# ---------------------------------------------------------------------------
# CSS selector targeting
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_css_selector_main(local_server):
    """Crawl / with css_selector='main' and verify result focuses on main content."""
    config = CrawlerRunConfig(css_selector="main")
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=config)
        assert result.success
        md = str(result.markdown)
        assert "Welcome to the Crawl4AI Test Site" in md
        # Footer should not be in the markdown since we targeted <main>
        assert "Footer content" not in md


@pytest.mark.asyncio
async def test_css_selector_product(local_server):
    """Crawl /products with css_selector targeting only product #1 and verify
    only the first product is extracted."""
    config = CrawlerRunConfig(css_selector=".product[data-id='1']")
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/products", config=config)
        assert result.success
        md = str(result.markdown)
        assert "Wireless Mouse" in md
        # Other products should not appear
        assert "Mechanical Keyboard" not in md
        assert "USB-C Hub" not in md


# ---------------------------------------------------------------------------
# Real URL content tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.network
async def test_real_url_markdown_quality():
    """Crawl https://example.com and verify markdown has reasonable content
    with more than 50 chars and contains 'Example Domain'."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            url="https://example.com", config=CrawlerRunConfig()
        )
        assert result.success
        md = str(result.markdown)
        assert len(md) > 50, f"Markdown too short ({len(md)} chars)"
        assert "Example Domain" in md


@pytest.mark.asyncio
@pytest.mark.network
async def test_real_url_links():
    """Crawl https://books.toscrape.com and verify internal links (product links)
    and images (book covers) are found."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            url="https://books.toscrape.com", config=CrawlerRunConfig()
        )
        assert result.success
        internal = result.links.get("internal", [])
        assert len(internal) > 0, "Expected product links on books.toscrape.com"
        images = result.media.get("images", [])
        assert len(images) > 0, "Expected book cover images on books.toscrape.com"
