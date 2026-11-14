"""RSS permalink fallback should preserve individual feed items in public scans."""

import httpx
import pytest

from crawl4ai import DomainMapper, DomainMapperConfig
from crawl4ai.domain_mapper import FEED_PATHS, LXML

A = "https://example.test/link-page"
B = "https://example.test/guid-page"


def rss(items):
    return f'<rss version="2.0"><channel>{items}</channel></rss>'


@pytest.mark.skipif(not LXML, reason="Existing GUID fallback belongs to LXML")
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("feed", "expected"),
    [
        pytest.param(
            rss(
                f"<item><link>{A}</link></item>"
                f'<item><guid isPermaLink="true">{B}</guid></item>'
            ),
            [A, B],
            id="mixed-link-and-guid",
        ),
        pytest.param(
            rss(f"<item><link>{A}</link></item><item><guid>{B}</guid></item>"),
            [A, B],
            id="mixed-default-permalink",
        ),
        pytest.param(
            rss(f'<item><guid isPermaLink="true">{B}</guid></item>'),
            [B],
            id="guid-alone-control",
        ),
        pytest.param(
            rss(f"<item><guid>{B}</guid></item><item><link>{A}</link></item>"),
            [B, A],
            id="guid-before-link-order",
        ),
        pytest.param(
            rss(
                f"<item><link>{A}</link></item>"
                f"<item><link> \n </link><guid>{B}</guid></item>"
            ),
            [A, B],
            id="blank-link-fallback",
        ),
        pytest.param(
            '<rss xmlns="urn:example:rss" version="2.0"><channel>'
            f"<item><link>{A}</link></item><item><guid>{B}</guid></item>"
            "</channel></rss>",
            [A, B],
            id="namespaced-rss",
        ),
        pytest.param(
            rss(f'<item><link>{A}</link><guid isPermaLink="true">{B}</guid></item>'),
            [A],
            id="link-precedence-control",
        ),
        pytest.param(
            rss(
                f"<item><link>{A}</link></item>"
                f'<item><guid isPermaLink="false">{B}</guid></item>'
            ),
            [A],
            id="non-permalink-control",
        ),
        pytest.param(
            rss(
                f"<item><link>{A}</link></item>"
                '<item><guid isPermaLink="true">urn:example:article</guid></item>'
            ),
            [A],
            id="non-http-guid-control",
        ),
        pytest.param(
            f'<feed xmlns="http://www.w3.org/2005/Atom">'
            f'<entry><link href="{A}" rel="alternate"/></entry>'
            f'<entry><link href="{B}"/></entry></feed>',
            [A, B],
            id="atom-control",
        ),
    ],
)
async def test_public_feed_scan(tmp_path, feed, expected):
    requests = []

    def respond(request):
        requests.append((request.method, str(request.url)))
        assert request.url.host == "example.test"
        if request.method == "HEAD" and request.url.path == "/":
            return httpx.Response(200)
        assert request.method == "GET"
        assert request.url.path in FEED_PATHS
        if request.url.path == "/feed":
            return httpx.Response(
                200, text=feed, headers={"Content-Type": "application/xml"}
            )
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        async with DomainMapper(client=client, base_directory=tmp_path) as mapper:
            results = await mapper.scan(
                "example.test",
                DomainMapperConfig(
                    source="feed",
                    include_subdomains=False,
                    soft_404_detection=False,
                    extract_head=False,
                    verbose=False,
                ),
            )

    assert requests == [
        ("HEAD", "https://example.test/"),
        ("GET", "https://example.test/feed"),
    ]
    assert [result["url"] for result in results] == expected
    assert all(result["source"] == "feed" for result in results)
