"""Tests for issue #1691: background-images are skipped.

The bug: The crawler only extracted <img> tags, missing CSS background-image
properties and data-* image attributes common on Elementor/page-builder sites.
"""

import pytest
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy


BACKGROUND_IMAGE_HTML = """
<html>
<body>
    <div class="hero" style="background-image: url('https://example.com/hero.jpg');">
        <h1>Welcome to our site with many interesting words here</h1>
    </div>
    <div class="section" style="background: url(https://example.com/section-bg.png) no-repeat center;">
        <p>Section content with enough words to pass threshold filter easily.</p>
    </div>
    <img src="https://example.com/regular.jpg" alt="Regular image" width="200" height="200">
</body>
</html>
"""

DATA_ATTR_HTML = """
<html>
<body>
    <div class="elementor-widget" data-dce-background-image-url="https://example.com/elementor-bg.jpg">
        <p>Elementor widget content with enough words to pass threshold filter.</p>
    </div>
    <div class="lazy-bg" data-bg="https://example.com/lazy-bg.webp">
        <p>Lazy background with enough words to pass threshold filter easily here.</p>
    </div>
    <div class="card" data-background-src="https://example.com/card-bg.png">
        <p>Card content with enough words to pass threshold filter easily here too.</p>
    </div>
    <img src="https://example.com/normal.jpg" alt="Normal" width="200" height="200">
</body>
</html>
"""

MIXED_HTML = """
<html>
<body>
    <div style="background-image: url('https://example.com/bg1.jpg');">
        <p>Background div with enough words to pass threshold filter checks.</p>
    </div>
    <div data-bg-image="https://example.com/bg2.png">
        <p>Data attr div with enough words to pass threshold filter checks here.</p>
    </div>
    <img src="https://example.com/img1.jpg" alt="Image one" width="200" height="200">
    <img src="https://example.com/img2.webp" alt="Image two" width="200" height="200">
</body>
</html>
"""

NO_BG_HTML = """
<html>
<body>
    <div style="color: red; font-size: 14px;">
        <p>No background image here, just styling with words enough for threshold.</p>
    </div>
    <img src="https://example.com/only-img.jpg" alt="Only image" width="200" height="200">
</body>
</html>
"""


@pytest.fixture
def scraper():
    return LXMLWebScrapingStrategy()


class TestBackgroundImageExtraction:
    def test_css_background_image_url(self, scraper):
        """background-image: url(...) should be extracted."""
        result = scraper._scrap(url="http://test.com", html=BACKGROUND_IMAGE_HTML)
        image_srcs = [img["src"] for img in result["media"]["images"]]
        assert "https://example.com/hero.jpg" in image_srcs

    def test_css_background_shorthand(self, scraper):
        """background: url(...) shorthand should be extracted."""
        result = scraper._scrap(url="http://test.com", html=BACKGROUND_IMAGE_HTML)
        image_srcs = [img["src"] for img in result["media"]["images"]]
        assert "https://example.com/section-bg.png" in image_srcs

    def test_regular_img_still_works(self, scraper):
        """Regular <img> tags should still be extracted."""
        result = scraper._scrap(url="http://test.com", html=BACKGROUND_IMAGE_HTML)
        image_srcs = [img["src"] for img in result["media"]["images"]]
        assert "https://example.com/regular.jpg" in image_srcs

    def test_no_duplicate_bg_images(self, scraper):
        """Same URL shouldn't appear multiple times."""
        html = """
        <html><body>
            <div style="background-image: url('https://example.com/dup.jpg');">
                <p>First div content with enough words for threshold checks.</p>
            </div>
            <div style="background-image: url('https://example.com/dup.jpg');">
                <p>Second div content with enough words for threshold checks.</p>
            </div>
        </body></html>
        """
        result = scraper._scrap(url="http://test.com", html=html)
        image_srcs = [img["src"] for img in result["media"]["images"]]
        assert image_srcs.count("https://example.com/dup.jpg") == 1


class TestDataAttributeImages:
    def test_data_dce_background_attribute(self, scraper):
        """Elementor data-dce-background-image-url should be extracted."""
        result = scraper._scrap(url="http://test.com", html=DATA_ATTR_HTML)
        image_srcs = [img["src"] for img in result["media"]["images"]]
        assert "https://example.com/elementor-bg.jpg" in image_srcs

    def test_data_bg_attribute(self, scraper):
        """data-bg with image extension should be extracted."""
        result = scraper._scrap(url="http://test.com", html=DATA_ATTR_HTML)
        image_srcs = [img["src"] for img in result["media"]["images"]]
        assert "https://example.com/lazy-bg.webp" in image_srcs

    def test_data_background_src(self, scraper):
        """data-background-src with image extension should be extracted."""
        result = scraper._scrap(url="http://test.com", html=DATA_ATTR_HTML)
        image_srcs = [img["src"] for img in result["media"]["images"]]
        assert "https://example.com/card-bg.png" in image_srcs

    def test_img_data_attrs_not_duplicated(self, scraper):
        """data-* on <img> tags should not create duplicates (already handled by process_image)."""
        html = """
        <html><body>
            <img src="https://example.com/photo.jpg" data-src="https://example.com/photo-hd.jpg"
                 alt="Photo" width="200" height="200">
        </body></html>
        """
        result = scraper._scrap(url="http://test.com", html=html)
        images = result["media"]["images"]
        srcs = [img["src"] for img in images]
        # data-src on img is handled by process_image, not the bg extractor
        assert "https://example.com/photo.jpg" in srcs


class TestMixedContent:
    def test_all_image_types_extracted(self, scraper):
        """Mix of <img>, background-image, and data-* should all be found."""
        result = scraper._scrap(url="http://test.com", html=MIXED_HTML)
        image_srcs = [img["src"] for img in result["media"]["images"]]
        assert "https://example.com/bg1.jpg" in image_srcs
        assert "https://example.com/img1.jpg" in image_srcs

    def test_no_bg_images_no_false_positives(self, scraper):
        """Elements with non-background styles should not produce false positives."""
        result = scraper._scrap(url="http://test.com", html=NO_BG_HTML)
        image_srcs = [img["src"] for img in result["media"]["images"]]
        assert "https://example.com/only-img.jpg" in image_srcs
        # Only the regular img, no false bg images
        bg_images = [s for s in image_srcs if s != "https://example.com/only-img.jpg"]
        assert len(bg_images) == 0

    def test_data_attr_without_image_extension_ignored(self, scraper):
        """data-* attrs without image extensions should not be extracted."""
        html = """
        <html><body>
            <div data-config="some-random-value" data-id="12345">
                <p>Content with enough words for word count threshold filter.</p>
            </div>
        </body></html>
        """
        result = scraper._scrap(url="http://test.com", html=html)
        images = result["media"]["images"]
        assert len(images) == 0
