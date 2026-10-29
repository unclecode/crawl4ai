"""PDF images extracted by PDFContentScrapingStrategy keep their location.

The PDF processor reports a saved image as ``{"path": ...}`` and an inline one
as ``{"data": ...}``. ``ScrapingResult.media.images`` holds ``MediaItem``
objects, which have no ``path`` field, so a saved image used to come back with
an empty ``src`` and no way to find the file.
"""

import os

import pytest

pytest.importorskip("pypdf")
Image = pytest.importorskip("PIL.Image")

from crawl4ai.processors.pdf import PDFContentScrapingStrategy


@pytest.fixture
def image_pdf(tmp_path):
    path = tmp_path / "image.pdf"
    Image.new("RGB", (40, 30), "red").save(path)
    return str(path)


def test_saved_pdf_image_path_lands_in_src(image_pdf, tmp_path):
    image_dir = tmp_path / "images"
    strategy = PDFContentScrapingStrategy(
        extract_images=True, save_images_locally=True, image_save_dir=str(image_dir)
    )

    result = strategy.scrap(image_pdf, "")

    assert len(result.media.images) == 1
    image = result.media.images[0]
    assert image.src
    assert os.path.dirname(image.src) == str(image_dir)
    assert os.path.isfile(image.src)
    assert image.data == ""
    assert image.width == 40


def test_inline_pdf_image_keeps_base64_data(image_pdf):
    strategy = PDFContentScrapingStrategy(extract_images=True, save_images_locally=False)

    result = strategy.scrap(image_pdf, "")

    assert len(result.media.images) == 1
    image = result.media.images[0]
    assert image.src == ""
    assert image.data
    assert image.format == "jpeg"
