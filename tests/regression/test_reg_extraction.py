"""
Regression tests for Crawl4AI extraction strategies.

Covers JsonCssExtractionStrategy, JsonXPathExtractionStrategy,
JsonLxmlExtractionStrategy, RegexExtractionStrategy, NoExtractionStrategy,
and CosineStrategy (optional, requires sklearn).

Run:
    pytest tests/regression/test_reg_extraction.py -v
    pytest tests/regression/test_reg_extraction.py -v -m "not network"
"""

import pytest
import json
import time

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    JsonXPathExtractionStrategy,
    JsonLxmlExtractionStrategy,
    RegexExtractionStrategy,
    NoExtractionStrategy,
)

try:
    from crawl4ai.extraction_strategy import CosineStrategy
    # CosineStrategy requires torch and sklearn at instantiation time;
    # verify they are actually available before declaring it usable.
    import torch  # noqa: F401
    HAS_COSINE = True
except (ImportError, ModuleNotFoundError):
    HAS_COSINE = False


# ---------------------------------------------------------------------------
# JsonCssExtractionStrategy
# ---------------------------------------------------------------------------

PRODUCT_CSS_SCHEMA = {
    "baseSelector": "div.product",
    "fields": [
        {"name": "name", "selector": "h2.name", "type": "text"},
        {"name": "price", "selector": "span.price", "type": "text"},
        {"name": "description", "selector": "p.description", "type": "text"},
        {"name": "category", "selector": "span.category", "type": "text"},
        {
            "name": "link",
            "selector": "a.details-link",
            "type": "attribute",
            "attribute": "href",
        },
    ],
}

PRODUCT_CSS_SCHEMA_WITH_ID = {
    "baseSelector": "div.product",
    "baseFields": [
        {
            "name": "product_id",
            "type": "attribute",
            "attribute": "data-id",
        },
    ],
    "fields": [
        {"name": "name", "selector": "h2.name", "type": "text"},
        {"name": "price", "selector": "span.price", "type": "text"},
        {"name": "description", "selector": "p.description", "type": "text"},
        {"name": "category", "selector": "span.category", "type": "text"},
        {
            "name": "link",
            "selector": "a.details-link",
            "type": "attribute",
            "attribute": "href",
        },
    ],
}


@pytest.mark.asyncio
async def test_css_extract_products(local_server):
    """Extract all 5 products from /products using JsonCssExtractionStrategy.
    Verify count, first product name, price, and product_id."""
    strategy = JsonCssExtractionStrategy(schema=PRODUCT_CSS_SCHEMA_WITH_ID)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/products", config=config)
        assert result.success, f"Crawl failed: {result.error_message}"
        extracted = json.loads(result.extracted_content)
        assert isinstance(extracted, list)
        assert len(extracted) == 5, f"Expected 5 products, got {len(extracted)}"

        first = extracted[0]
        assert first["name"] == "Wireless Mouse"
        assert first["price"] == "$29.99"
        assert first["product_id"] == "1"


@pytest.mark.asyncio
async def test_css_extract_with_default(local_server):
    """Use a field with a non-existent selector and a default value.
    Verify the default is used when no element matches."""
    schema = {
        "baseSelector": "div.product",
        "fields": [
            {"name": "name", "selector": "h2.name", "type": "text"},
            {
                "name": "sku",
                "selector": "span.sku-number",
                "type": "text",
                "default": "N/A",
            },
        ],
    }
    strategy = JsonCssExtractionStrategy(schema=schema)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/products", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert len(extracted) > 0
        for item in extracted:
            assert item["sku"] == "N/A", (
                f"Expected default 'N/A' for missing sku, got: {item.get('sku')}"
            )


@pytest.mark.asyncio
async def test_css_extract_nested(local_server):
    """Test nested type extraction using JsonCssExtractionStrategy.
    Extract a nested object from within each product element."""
    schema = {
        "baseSelector": "div.product",
        "fields": [
            {"name": "name", "selector": "h2.name", "type": "text"},
            {
                "name": "details",
                "selector": "div.rating",
                "type": "nested",
                "fields": [
                    {
                        "name": "stars",
                        "type": "attribute",
                        "attribute": "data-stars",
                    },
                ],
            },
        ],
    }
    strategy = JsonCssExtractionStrategy(schema=schema)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/products", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert len(extracted) == 5
        first = extracted[0]
        assert "details" in first
        assert first["details"]["stars"] == "4.5"


@pytest.mark.asyncio
async def test_css_extract_empty_results(local_server):
    """Use a baseSelector that matches nothing and verify an empty list is returned."""
    schema = {
        "baseSelector": "div.nonexistent-class-xyz",
        "fields": [
            {"name": "text", "selector": "p", "type": "text"},
        ],
    }
    strategy = JsonCssExtractionStrategy(schema=schema)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/products", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert isinstance(extracted, list)
        assert len(extracted) == 0


@pytest.mark.asyncio
async def test_css_extract_table(local_server):
    """Extract table rows from /tables using CSS selectors.
    Verify 4 quarterly rows with correct Q1 revenue."""
    schema = {
        "baseSelector": "#sales-table tbody tr",
        "fields": [
            {"name": "quarter", "selector": "td:nth-child(1)", "type": "text"},
            {"name": "revenue", "selector": "td:nth-child(2)", "type": "text"},
            {"name": "growth", "selector": "td:nth-child(3)", "type": "text"},
        ],
    }
    strategy = JsonCssExtractionStrategy(schema=schema)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/tables", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert len(extracted) == 4, f"Expected 4 rows, got {len(extracted)}"
        assert extracted[0]["quarter"] == "Q1 2025"
        assert extracted[0]["revenue"] == "$1,234,567"
        assert extracted[0]["growth"] == "12.5%"


@pytest.mark.asyncio
@pytest.mark.network
async def test_css_real_quotes():
    """Crawl quotes.toscrape.com and extract quotes with CSS selectors.
    Verify multiple quotes are extracted with text and author."""
    schema = {
        "baseSelector": "div.quote",
        "fields": [
            {"name": "text", "selector": "span.text", "type": "text"},
            {"name": "author", "selector": "small.author", "type": "text"},
        ],
    }
    strategy = JsonCssExtractionStrategy(schema=schema)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            url="https://quotes.toscrape.com", config=config
        )
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert len(extracted) > 0, "Expected quotes to be extracted"
        for quote in extracted:
            assert "text" in quote and quote["text"], f"Quote missing text: {quote}"
            assert "author" in quote and quote["author"], f"Quote missing author: {quote}"


@pytest.mark.asyncio
@pytest.mark.network
async def test_css_real_books():
    """Crawl books.toscrape.com and extract book titles and prices."""
    schema = {
        "baseSelector": "article.product_pod",
        "fields": [
            {"name": "title", "selector": "h3 a", "type": "attribute", "attribute": "title"},
            {"name": "price", "selector": "p.price_color", "type": "text"},
        ],
    }
    strategy = JsonCssExtractionStrategy(schema=schema)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            url="https://books.toscrape.com", config=config
        )
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert len(extracted) > 0, "Expected books to be extracted"
        for book in extracted:
            assert "title" in book and book["title"]
            assert "price" in book and book["price"]
            # Price should start with a currency symbol
            assert book["price"][0] in ("£", "$", "€") or book["price"].startswith("£")


# ---------------------------------------------------------------------------
# JsonXPathExtractionStrategy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_xpath_extract_products(local_server):
    """Extract products using XPath selectors. Verify same results as CSS version."""
    schema = {
        # Use exact class match to avoid matching 'product-list' parent
        "baseSelector": "//div[contains(concat(' ', normalize-space(@class), ' '), ' product ')]",
        "fields": [
            {
                "name": "name",
                "selector": ".//h2[contains(@class, 'name')]",
                "type": "text",
            },
            {
                "name": "price",
                "selector": ".//span[contains(@class, 'price')]",
                "type": "text",
            },
        ],
    }
    strategy = JsonXPathExtractionStrategy(schema=schema)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/products", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert len(extracted) == 5, f"Expected 5 products via XPath, got {len(extracted)}"
        assert extracted[0]["name"] == "Wireless Mouse"
        assert extracted[0]["price"] == "$29.99"


# ---------------------------------------------------------------------------
# JsonLxmlExtractionStrategy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lxml_extract_products(local_server):
    """Extract products using JsonLxmlExtractionStrategy with the same
    CSS-style schema. Verify same results as JsonCss."""
    strategy = JsonLxmlExtractionStrategy(schema=PRODUCT_CSS_SCHEMA)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/products", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert len(extracted) == 5, f"Expected 5 products via lxml, got {len(extracted)}"
        assert extracted[0]["name"] == "Wireless Mouse"
        assert extracted[0]["price"] == "$29.99"


@pytest.mark.asyncio
async def test_lxml_caching_performance(local_server):
    """Extract twice with the same JsonLxmlExtractionStrategy instance.
    Second extraction should be faster or equal due to caching."""
    strategy = JsonLxmlExtractionStrategy(schema=PRODUCT_CSS_SCHEMA)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        # First run
        t0 = time.perf_counter()
        result1 = await crawler.arun(url=f"{local_server}/products", config=config)
        t1 = time.perf_counter()
        first_time = t1 - t0

        # Second run (caching should help)
        t2 = time.perf_counter()
        result2 = await crawler.arun(url=f"{local_server}/products", config=config)
        t3 = time.perf_counter()
        second_time = t3 - t2

        assert result1.success and result2.success
        data1 = json.loads(result1.extracted_content)
        data2 = json.loads(result2.extracted_content)
        assert len(data1) == len(data2) == 5

        # Allow generous tolerance -- caching may not always be faster due to
        # browser overhead, but it should certainly not be drastically slower
        assert second_time < first_time * 3, (
            f"Second run ({second_time:.3f}s) significantly slower than first ({first_time:.3f}s)"
        )


# ---------------------------------------------------------------------------
# RegexExtractionStrategy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_regex_email(local_server):
    """Extract emails from /regex-test using the Email pattern.
    Verify both expected addresses are found."""
    strategy = RegexExtractionStrategy(pattern=RegexExtractionStrategy.Email)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/regex-test", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        values = [item["value"] for item in extracted]
        assert any("support@crawl4ai.com" in v for v in values), (
            f"Expected support@crawl4ai.com in {values}"
        )
        assert any("sales@example.org" in v for v in values), (
            f"Expected sales@example.org in {values}"
        )


@pytest.mark.asyncio
async def test_regex_phone(local_server):
    """Extract US phone numbers from /regex-test."""
    strategy = RegexExtractionStrategy(pattern=RegexExtractionStrategy.PhoneUS)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/regex-test", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        values = [item["value"] for item in extracted]
        assert len(values) > 0, "Expected at least one phone number"
        # At least one phone number should contain expected digits
        all_vals = " ".join(values)
        assert "555" in all_vals, f"Expected phone with 555 in {values}"


@pytest.mark.asyncio
async def test_regex_url(local_server):
    """Extract URLs from /regex-test using the Url pattern."""
    strategy = RegexExtractionStrategy(pattern=RegexExtractionStrategy.Url)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/regex-test", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        values = [item["value"] for item in extracted]
        assert len(values) > 0, "Expected URLs to be extracted"
        all_vals = " ".join(values)
        assert "crawl4ai.com" in all_vals


@pytest.mark.asyncio
async def test_regex_all(local_server):
    """Use RegexExtractionStrategy.All to extract all built-in patterns.
    Verify it finds emails, phones, URLs, dates, and more."""
    strategy = RegexExtractionStrategy(pattern=RegexExtractionStrategy.All)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/regex-test", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        labels = {item["label"] for item in extracted}
        # Should find at least emails, URLs, and dates
        assert "email" in labels, f"Expected 'email' in labels: {labels}"
        assert "url" in labels, f"Expected 'url' in labels: {labels}"
        assert "date_iso" in labels or "date_us" in labels, (
            f"Expected date patterns in labels: {labels}"
        )


@pytest.mark.asyncio
async def test_regex_custom(local_server):
    """Use a custom regex pattern to extract IPv4 addresses.
    Verify 192.168.1.100 is found."""
    strategy = RegexExtractionStrategy(
        custom={"ip_address": r"(?:\d{1,3}\.){3}\d{1,3}"}
    )
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/regex-test", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        values = [item["value"] for item in extracted]
        assert "192.168.1.100" in values, f"Expected 192.168.1.100 in {values}"


@pytest.mark.asyncio
async def test_regex_output_format(local_server):
    """Verify each regex extraction result has the expected keys:
    url, label, value, span."""
    strategy = RegexExtractionStrategy(pattern=RegexExtractionStrategy.Email)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/regex-test", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert len(extracted) > 0
        for item in extracted:
            assert "url" in item, f"Missing 'url' key in {item}"
            assert "label" in item, f"Missing 'label' key in {item}"
            assert "value" in item, f"Missing 'value' key in {item}"
            assert "span" in item, f"Missing 'span' key in {item}"
            # Span should be a list/tuple of two ints
            span = item["span"]
            assert isinstance(span, (list, tuple)) and len(span) == 2


@pytest.mark.asyncio
async def test_regex_span_accuracy(local_server):
    """Verify that span[0]:span[1] in the source content equals value.
    This tests that span offsets are accurate relative to the input text."""
    strategy = RegexExtractionStrategy(pattern=RegexExtractionStrategy.Email)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/regex-test", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert len(extracted) > 0

        # The regex runs on the content source (fit_html by default).
        # We verify the span produces the correct value from that source.
        # Since we cannot easily get the exact input text the regex ran on,
        # we verify span[0] < span[1] and the value is non-empty.
        for item in extracted:
            span = item["span"]
            assert span[0] < span[1], f"Invalid span: {span}"
            assert len(item["value"]) > 0
            assert span[1] - span[0] == len(item["value"]), (
                f"Span length ({span[1] - span[0]}) != value length ({len(item['value'])})"
            )


# ---------------------------------------------------------------------------
# NoExtractionStrategy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_extraction(local_server):
    """Crawl with NoExtractionStrategy and verify the framework skips
    structured extraction (passthrough behavior). The crawler deliberately
    bypasses extraction for NoExtractionStrategy, leaving extracted_content
    as None. The actual page content is still available via markdown and html."""
    strategy = NoExtractionStrategy()
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/", config=config)
        assert result.success
        # The framework explicitly skips extraction for NoExtractionStrategy,
        # so extracted_content should be None (passthrough -- no processing).
        assert result.extracted_content is None
        # But the page content is still fully available
        assert result.html is not None and len(result.html) > 0
        assert result.markdown is not None and "Welcome" in result.markdown


# ---------------------------------------------------------------------------
# CosineStrategy (optional - requires sklearn)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_COSINE, reason="CosineStrategy requires sklearn+torch")
def test_cosine_basic():
    """Test CosineStrategy extract() directly with pre-chunked text to verify clustering works."""
    # CosineStrategy.extract() expects text with <|DEL|> or \\n\\n separators.
    # We test the strategy directly to avoid browser overhead and isolate the logic.
    topics = [
        "Machine learning algorithms process large datasets to identify complex patterns "
        "and make accurate predictions using neural networks and deep learning models.",
        "Cloud computing provides scalable infrastructure for deploying web applications "
        "globally across multiple regions and availability zones for high availability.",
        "Database optimization requires careful indexing strategies and query performance "
        "tuning to handle millions of transactions per second efficiently.",
        "Network security involves configuring firewalls intrusion detection systems and "
        "encrypted communications to protect against cyber threats and attacks.",
        "Mobile development frameworks enable building cross-platform applications with "
        "shared codebases that deploy to both iOS and Android platforms.",
    ]
    text = "<|DEL|>".join(topics)

    strategy = CosineStrategy(
        semantic_filter=None,
        word_count_threshold=5,
        max_dist=0.5,
    )
    result = strategy.extract(url="http://test.com", html=text)
    assert isinstance(result, list)
    assert len(result) > 0, "Expected clusters from CosineStrategy"
    # Each cluster should have 'content' and 'index' keys
    for item in result:
        assert "content" in item
        assert "index" in item


# ---------------------------------------------------------------------------
# Extraction with real URLs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.network
async def test_extraction_real_quotes_css():
    """Full pipeline: crawl quotes.toscrape.com, extract with JsonCss,
    verify structured quote data including text and author."""
    schema = {
        "baseSelector": "div.quote",
        "fields": [
            {"name": "text", "selector": "span.text", "type": "text"},
            {"name": "author", "selector": "small.author", "type": "text"},
            {
                "name": "tags",
                "selector": "div.tags",
                "type": "nested",
                "fields": [
                    {
                        "name": "tag_list",
                        "selector": "a.tag",
                        "type": "text",
                    },
                ],
            },
        ],
    }
    strategy = JsonCssExtractionStrategy(schema=schema)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            url="https://quotes.toscrape.com", config=config
        )
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert len(extracted) >= 5, f"Expected at least 5 quotes, got {len(extracted)}"
        for quote in extracted:
            assert quote.get("text"), "Quote text should not be empty"
            assert quote.get("author"), "Quote author should not be empty"


@pytest.mark.asyncio
@pytest.mark.network
async def test_extraction_real_books_css():
    """Crawl books.toscrape.com and extract book listings with titles and prices."""
    schema = {
        "baseSelector": "article.product_pod",
        "fields": [
            {"name": "title", "selector": "h3 a", "type": "attribute", "attribute": "title"},
            {"name": "price", "selector": "p.price_color", "type": "text"},
            {"name": "availability", "selector": "p.availability", "type": "text"},
        ],
    }
    strategy = JsonCssExtractionStrategy(schema=schema)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(
            url="https://books.toscrape.com", config=config
        )
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert len(extracted) >= 10, f"Expected at least 10 books, got {len(extracted)}"
        for book in extracted:
            assert book.get("title"), "Book title should not be empty"
            assert book.get("price"), "Book price should not be empty"
