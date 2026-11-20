"""Media descriptions stay bounded when the closest text is a page-wide wrapper.

`find_closest_parent_with_useful_text` returns the text of the closest ancestor
that has text. On real pages that ancestor is often a wrapper around the whole
page (whitespace between tags counts as text), so every <img>, and every srcset
variant of it, used to carry a full copy of the page's text: memory and time
grew as images x page size. A page with a few thousand images and 100 KB of
text produced over a gigabyte of `media.images[].desc`.
"""

from lxml import html as lhtml

from crawl4ai.config import IMAGE_DESCRIPTION_MAX_LENGTH
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

IMG = (
    "<img src='/img/{i}.jpg' alt='photo {i}' width='400' height='400'"
    " srcset='/img/{i}@2x.jpg 2x, /img/{i}@3x.jpg 3x'>"
)
PARAGRAPH = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20


def _scrape(html: str, **kwargs):
    return LXMLWebScrapingStrategy().scrap("https://example.com/", html, **kwargs)


def test_a_short_caption_is_unchanged():
    html = f"<html><body><p>Our office in Stockholm {IMG.format(i=1)}</p></body></html>"

    images = _scrape(html).media.images

    assert images
    assert all(img.desc == "Our office in Stockholm" for img in images)


def test_a_page_wide_wrapper_does_not_copy_the_page_into_every_image():
    html = (
        "<html><body><div>\n"
        + "".join(f"<p>{PARAGRAPH}</p>\n{IMG.format(i=i)}\n" for i in range(300))
        + "</div></body></html>"
    )

    images = _scrape(html).media.images

    # 300 images x 3 srcset variants, each previously holding ~340 KB of text.
    assert len(images) >= 300
    assert all(
        0 < len(img.desc or "") <= IMAGE_DESCRIPTION_MAX_LENGTH for img in images
    )
    assert images[0].desc.startswith("Lorem ipsum dolor sit amet")


def test_video_and_audio_descriptions_are_bounded_too():
    doc = lhtml.fromstring(
        f"<html><body><div>\n<p>{PARAGRAPH * 10}</p>"
        "<video src='/v.mp4'></video><audio src='/a.mp3'></audio></div></body></html>"
    )
    scraper = LXMLWebScrapingStrategy()

    for element in doc.xpath("//video | //audio"):
        description = scraper.find_closest_parent_with_useful_text(element)
        assert 0 < len(description) <= IMAGE_DESCRIPTION_MAX_LENGTH


def test_the_limit_can_be_set_per_call():
    html = f"<html><body><div>\n<p>{PARAGRAPH}</p>{IMG.format(i=1)}</div></body></html>"

    images = _scrape(html, image_description_max_length=40).media.images

    assert images
    assert all(len(img.desc or "") <= 40 for img in images)
