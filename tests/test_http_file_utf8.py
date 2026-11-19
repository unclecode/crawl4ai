"""Local-file crawling must decode UTF-8 across byte-read boundaries."""

import pytest

from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("character", "boundary_offset"),
    [
        ("é", -1),
        ("é", 0),
        ("é", 1),
        ("€", -2),
        ("€", -1),
        ("€", 0),
        ("€", 1),
        ("😀", -3),
        ("😀", -2),
        ("😀", -1),
        ("😀", 0),
        ("😀", 1),
    ],
)
async def test_default_chunk_boundary_preserves_utf8(
    tmp_path, character, boundary_offset
):
    strategy = AsyncHTTPCrawlerStrategy()
    prefix = "<p>" + "a" * (strategy.DEFAULT_CHUNK_SIZE + boundary_offset - 3)
    html = prefix + character + "</p>"
    path = tmp_path / "boundary.html"
    path.write_bytes(html.encode("utf-8"))

    response = await strategy.crawl(path.as_uri())

    assert response.html[len(prefix) :] == character + "</p>"
    assert response.html == html
    assert response.status_code == 200
    assert response.response_headers == {}


@pytest.mark.asyncio
@pytest.mark.parametrize("character", ["é", "€", "😀"])
async def test_one_byte_chunks_preserve_utf8(tmp_path, character):
    html = f"<p>{character}</p>"
    path = tmp_path / "one-byte.html"
    path.write_bytes(html.encode("utf-8"))

    response = await AsyncHTTPCrawlerStrategy(chunk_size=1).crawl(path.as_uri())

    assert response.html == html


@pytest.mark.asyncio
@pytest.mark.parametrize("chunk_size", [65536, 1])
@pytest.mark.parametrize(
    ("content", "expected"),
    [
        pytest.param(b"<p>ASCII</p>", "<p>ASCII</p>", id="ascii"),
        pytest.param(b"", "", id="empty"),
        pytest.param("<p>é€😀</p>".encode("utf-8"), "<p>é€😀</p>", id="small-utf8"),
        pytest.param(b"<p>\xff</p>", "<p>\ufffd</p>", id="invalid-byte"),
        pytest.param(b"<p>\xe2(</p>", "<p>\ufffd(</p>", id="invalid-continuation"),
        pytest.param(b"<p>\xc3", "<p>\ufffd", id="truncated-two-byte-eof"),
        pytest.param(b"<p>\xe2\x82", "<p>\ufffd", id="truncated-three-byte-eof"),
        pytest.param(b"<p>\xf0\x9f\x98", "<p>\ufffd", id="truncated-four-byte-eof"),
    ],
)
async def test_file_decoding_controls(tmp_path, chunk_size, content, expected):
    path = tmp_path / "control.html"
    path.write_bytes(content)

    response = await AsyncHTTPCrawlerStrategy(chunk_size=chunk_size).crawl(
        path.as_uri()
    )

    assert response.html == expected
    assert response.status_code == 200
    assert response.response_headers == {}


@pytest.mark.asyncio
async def test_missing_local_file_keeps_file_not_found_error(tmp_path):
    path = tmp_path / "missing.html"

    with pytest.raises(FileNotFoundError) as error:
        await AsyncHTTPCrawlerStrategy().crawl(path.as_uri())

    assert str(error.value) == f"Local file not found: {path}"
