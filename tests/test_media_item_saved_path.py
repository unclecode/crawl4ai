"""A locally saved PDF image keeps its path in ``result.media.images`` (#2469).

``PDFContentScrapingStrategy`` reports a saved image as ``{"path": ...}`` and
builds ``MediaItem(**image)`` from that dict. ``MediaItem`` had no ``path``
field, so pydantic dropped it and callers saw ``src=""`` with no way to find
the file written under ``image_save_dir``.
"""

from crawl4ai.models import MediaItem


def test_media_item_keeps_saved_pdf_image_path():
    item = MediaItem(
        **{
            "format": "jpeg",
            "width": 40,
            "height": 30,
            "path": "/tmp/page_1_img_1.jpg",
        }
    )

    assert item.path == "/tmp/page_1_img_1.jpg"
    assert item.model_dump()["path"] == "/tmp/page_1_img_1.jpg"
