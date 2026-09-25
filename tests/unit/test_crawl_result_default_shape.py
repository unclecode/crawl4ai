"""A CrawlResult built without links/media must still have their keys.

Successful crawls fill `links` and `media` from the scraper's result (arun moves
media's "tables" to CrawlResult.tables). Results built without them -- the
robots.txt refusal, the "all proxies failed" and exception paths in
AsyncWebCrawler.arun -- used to default to `{}`, so `result.links["internal"]`
raised KeyError on exactly the results a batch caller has to handle, and the
Docker API returned `"links": {}` / `"media": {}` for them.
"""

from crawl4ai.models import CrawlResult

LINKS = {"internal": [], "external": []}
MEDIA = {"images": [], "videos": [], "audios": []}


def _refused(url="https://example.com/private"):
    # The shape AsyncWebCrawler.arun returns when robots.txt disallows a URL.
    return CrawlResult(
        url=url,
        html="",
        success=False,
        status_code=403,
        error_message="Access denied by robots.txt",
    )


def test_result_without_links_or_media_has_the_scraped_shape():
    result = _refused()

    assert result.links == LINKS
    assert result.media == MEDIA


def test_default_is_not_shared_between_results():
    first, second = _refused(), _refused("https://example.com/other")

    first.links["internal"].append({"href": "https://example.com/a"})
    first.media["images"].append({"src": "https://example.com/a.png"})

    assert second.links == LINKS
    assert second.media == MEDIA


def test_serialized_result_keeps_the_keys():
    dumped = _refused().model_dump()

    assert dumped["links"] == LINKS
    assert dumped["media"] == MEDIA


def test_explicit_values_are_kept():
    links = {"internal": [{"href": "https://example.com/a"}], "external": []}
    result = CrawlResult(
        url="https://example.com/", html="<p></p>", success=True, links=links
    )

    assert result.links == links
