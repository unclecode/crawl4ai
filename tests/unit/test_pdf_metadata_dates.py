from datetime import datetime, timedelta, timezone

import pytest

pypdf = pytest.importorskip("pypdf")

from crawl4ai.processors.pdf import PDFContentScrapingStrategy


@pytest.mark.parametrize(
    ("metadata", "created", "modified"),
    [
        (
            {
                "/CreationDate": "D:20240403112233+05'30'",
                "/ModDate": "D:20240506123456Z",
            },
            datetime(
                2024, 4, 3, 11, 22, 33, tzinfo=timezone(timedelta(hours=5, minutes=30))
            ),
            datetime(2024, 5, 6, 12, 34, 56, tzinfo=timezone.utc),
        ),
        ({"/CreationDate": "D:202404"}, datetime(2024, 4, 1), None),
        (
            {"/CreationDate": "invalid", "/ModDate": "D:20240506123456-03'30'"},
            None,
            datetime(
                2024, 5, 6, 12, 34, 56, tzinfo=timezone(-timedelta(hours=3, minutes=30))
            ),
        ),
        ({"/CreationDate": "D:20240403112233"}, datetime(2024, 4, 3, 11, 22, 33), None),
        ({}, None, None),
    ],
)
def test_pdf_scraping_preserves_metadata_dates(tmp_path, metadata, created, modified):
    path = tmp_path / "dates.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_metadata(metadata)
    writer.write(path)

    result = PDFContentScrapingStrategy(extract_images=False).scrap(str(path), "")

    assert result.success
    for field, expected in (("created", created), ("modified", modified)):
        actual = result.metadata[field]
        assert actual == expected
        if expected is not None:
            assert actual.utcoffset() == expected.utcoffset()
