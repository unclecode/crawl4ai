import pytest

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LinkPreviewConfig
from crawl4ai.async_configs import MatchMode
from tests.helpers import EXAMPLE_URL


def test_is_match_single_pattern():
    config = CrawlerRunConfig(
        url_matcher="*.pdf"
    )
    test_urls = [
        (f"{EXAMPLE_URL}/file.pdf", True),
        (f"{EXAMPLE_URL}/doc.PDF", False),  # Case sensitive
        (f"{EXAMPLE_URL}/file.txt", False),
        ("file.pdf", True),
    ]

    for url, expected in test_urls:    
        assert config.is_match(url) == expected
    
def test_is_match_with_or_mode():
    config = CrawlerRunConfig(
        url_matcher=["*/article/*", "*/blog/*", "*.html"],
        match_mode=MatchMode.OR
    )
    test_urls = [
        (f"{EXAMPLE_URL}/article/news", True),
        (f"{EXAMPLE_URL}/blog/post", True),
        (f"{EXAMPLE_URL}/page.html", True),
        (f"{EXAMPLE_URL}/page.php", False),
    ]
    for url, expected in test_urls:
        assert config.is_match(url) == expected
    
def test_is_match_custom_function():
    config = CrawlerRunConfig(
        url_matcher=lambda url: 'api' in url and (url.endswith('.json') or url.endswith('.xml'))
    )
    test_urls = [
        (f"{EXAMPLE_URL}/api/data.json", True),
        (f"{EXAMPLE_URL}/api/data.xml", True),
        (f"{EXAMPLE_URL}/data.html", False),
        (f"{EXAMPLE_URL}/data.json", False),  # No 'api'
    ]
    for url, expected in test_urls:
        assert config.is_match(url) == expected
    
def test_is_match_mixed_with_and_mode():
    config = CrawlerRunConfig(
        url_matcher=[
            "https://*",  # Must be HTTPS
            lambda url: '.com' in url,  # Must have .com
            lambda url: len(url) < 50  # Must be short
        ],
        match_mode=MatchMode.AND
    )
    test_urls = [
        (f"{EXAMPLE_URL}/page", True),
        ("http://example.com/page", False),  # Not HTTPS
        ("example.org/page", False),  # No .com
        (f"{EXAMPLE_URL}/" + "x" * 50, False),  # Too long
    ]
    for url, expected in test_urls:
        assert config.is_match(url) == expected
    
def test_is_match_mixed_with_or_mode():
    config = CrawlerRunConfig(
        url_matcher=[
            "*/api/v[0-9]/*",  # API versioned endpoints
            lambda url: 'graphql' in url,  # GraphQL endpoints
            "*.json"  # JSON files
        ],
        match_mode=MatchMode.OR
    )
    test_urls = [
        (f"{EXAMPLE_URL}/api/v1/users", True),
        (f"{EXAMPLE_URL}/api/v2/posts", True),
        (f"{EXAMPLE_URL}/graphql", True),
        (f"{EXAMPLE_URL}/data.json", True),
        (f"{EXAMPLE_URL}/api/users", False),  # No version
    ]
    for url, expected in test_urls:
        assert config.is_match(url) == expected
    
def test_is_match_no_matcher():
    config = CrawlerRunConfig()
    assert config.is_match(EXAMPLE_URL)
    
def test_is_match_empty_list():
    config = CrawlerRunConfig(url_matcher=[])
    assert not config.is_match(EXAMPLE_URL)
    
@pytest.mark.asyncio
async def test_link_preview():
    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(),
        score_links=True,
        exclude_external_links=True,
    )
    test_url = "https://docs.python.org/3/"

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(test_url, config=config)

    assert result.success
    assert result.links
    assert result.links["external"] == []

    internal_links = result.links["internal"]

    assert any(il["total_score"] for il in internal_links)
    assert all(il["href"] for il in internal_links)
    assert all("title" in il for il in internal_links)
    assert all("text" in il for il in internal_links)
    assert all("head_data" in il for il in internal_links)
    assert all("head_extraction_status" in il for il in internal_links)
    assert all("head_extraction_error" in il for il in internal_links)
    assert all("total_score" in il for il in internal_links)

@pytest.mark.asyncio
async def test_css_selector():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=EXAMPLE_URL, config=CrawlerRunConfig(
                css_selector="h1, title"
            )
        )

    assert result.success
    assert (
        "<h1" in result.cleaned_html
        and "<title" in result.cleaned_html
        and "<p" not in result.cleaned_html
    )

@pytest.mark.asyncio
async def test_js_code():
    async with AsyncWebCrawler() as crawler:
        url = "https://www.nbcnews.com/business"

        result_without_more = await crawler.arun(url=url)
        result_with_more = await crawler.arun(url=url, config=CrawlerRunConfig(
            js_code=[
                "const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"
            ]
        ))

    assert result_with_more.success
    assert len(result_with_more.markdown) > len(result_without_more.markdown)


@pytest.mark.asyncio
async def test_user_agent():
    url = "https://www.nbcnews.com/business"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Crawl4AI/1.0"
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url, config=CrawlerRunConfig(
                user_agent=user_agent
            )
        )

    assert result.success
    assert crawler.browser_config.user_agent == user_agent
