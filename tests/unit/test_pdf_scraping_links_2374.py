"""Regression tests for unclecode/crawl4ai#2374.

`PDFContentScrapingStrategy.scrap()` used to build ``links = {"urls": [...]}``
with ``{"url", "page"}`` items and hand it to ``ScrapingResult``. ``Links`` only
has ``internal`` and ``external`` lists of ``Link`` items (keyed by ``href``),
so pydantic dropped the unknown ``urls`` key and every URI annotation the PDF
processor had extracted was lost, with ``success=True``.

The links now land in ``internal`` / ``external`` as ``Link`` items, classified
against the PDF's own domain the same way the HTML scraper does it.
"""

import pytest

pypdf = pytest.importorskip("pypdf")

from pypdf import PdfWriter
from pypdf.annotations import Link as LinkAnnotation

from crawl4ai.processors.pdf import PDFContentScrapingStrategy


def _write_pdf(path, pages):
    """Write a PDF with one blank page per entry; each entry lists its URIs."""
    writer = PdfWriter()
    for page_index, urls in enumerate(pages):
        writer.add_blank_page(width=612, height=792)
        for i, url in enumerate(urls):
            y = 20 + i * 30
            writer.add_annotation(
                page_index,
                LinkAnnotation(rect=(20, y, 200, y + 20), url=url),
            )
    writer.write(path)
    return path


def _hrefs(items):
    return [item.href for item in items]


def test_local_pdf_uri_links_survive_scraping(tmp_path):
    pdf = _write_pdf(tmp_path / "linked.pdf", [["https://example.org/reference"]])

    result = PDFContentScrapingStrategy(extract_images=False).scrap(str(pdf), "")

    assert result.success is True
    # A local file has no domain of its own, so every absolute link is external.
    assert _hrefs(result.links.external) == ["https://example.org/reference"]
    assert result.links.internal == []
    assert result.links.external[0].base_domain == "example.org"


def test_remote_pdf_links_split_into_internal_and_external(tmp_path, monkeypatch):
    pdf = _write_pdf(
        tmp_path / "remote.pdf",
        [
            ["https://docs.example.org/guide", "https://other.net/paper"],
            # The same target on a later page is reported once, like HTML links.
            ["https://docs.example.org/guide", "mailto:team@example.org"],
        ],
    )
    strategy = PDFContentScrapingStrategy(extract_images=False)
    # Skip the download: serve the local file for the remote URL.
    monkeypatch.setattr(strategy, "_get_pdf_path", lambda url: str(pdf))

    result = strategy.scrap("https://www.example.org/files/report.pdf", "")

    assert result.success is True
    assert _hrefs(result.links.internal) == ["https://docs.example.org/guide"]
    assert _hrefs(result.links.external) == [
        "https://other.net/paper",
        "mailto:team@example.org",
    ]
    assert result.links.internal[0].base_domain == "example.org"
    assert result.links.external[0].base_domain == "other.net"


def test_links_reach_the_model_dump_used_by_crawl_results(tmp_path):
    pdf = _write_pdf(tmp_path / "dump.pdf", [["https://example.org/a"]])

    dumped = (
        PDFContentScrapingStrategy(extract_images=False)
        .scrap(str(pdf), "")
        .links.model_dump()
    )

    assert [link["href"] for link in dumped["external"]] == ["https://example.org/a"]
