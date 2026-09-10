from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


def test_inline_css_background_images_are_preserved_for_markdown_and_media():
    image_url = "https://cdn.example.com/property/photo-34753.jpg"
    html = f"""
    <html>
      <body>
        <main>
          <h1>Property listing</h1>
          <div class="slick-slide" style="background: url('{image_url}') center / cover no-repeat"></div>
          <div class="slick-slide slick-cloned" style='background-image: url("{image_url}")'></div>
        </main>
      </body>
    </html>
    """

    result = LXMLWebScrapingStrategy()._scrap(
        url="https://example.com/listings/123",
        html=html,
    )

    assert result["success"] is True
    assert [image["src"] for image in result["media"]["images"]] == [image_url]
    assert result["cleaned_html"].count(f'src="{image_url}"') == 1

    markdown = DefaultMarkdownGenerator().generate_markdown(
        result["cleaned_html"],
        base_url="https://example.com/listings/123",
        citations=False,
    )
    assert image_url in markdown.raw_markdown


def test_css_background_images_respect_image_exclusions():
    image_url = "https://cdn.external.test/property.jpg"
    html = f'<div style="background-image: url({image_url})"></div>'
    strategy = LXMLWebScrapingStrategy()

    external_result = strategy._scrap(
        url="https://example.com/listings/123",
        html=html,
        exclude_external_images=True,
    )
    all_images_result = strategy._scrap(
        url="https://example.com/listings/123",
        html=html,
        exclude_all_images=True,
    )

    for result in (external_result, all_images_result):
        assert result["media"]["images"] == []
        assert image_url not in result["cleaned_html"]


def test_css_background_images_do_not_require_file_extensions():
    image_urls = [
        "https://cdn.example.com/media/34753",
        "https://cdn.example.com/media/34754",
    ]
    html = "".join(
        f'<div style="background: url({image_url}) center/cover no-repeat"></div>'
        for image_url in image_urls
    )

    result = LXMLWebScrapingStrategy()._scrap(
        url="https://example.com/listings/123",
        html=html,
    )

    assert [image["src"] for image in result["media"]["images"]] == image_urls


def test_css_background_images_skip_non_http_schemes():
    html = """
    <div style="background: url(data:image/png;base64,abc)"></div>
    <div style="background-image: url('blob:https://example.com/id')"></div>
    <div style="background: url(javascript:alert(1))"></div>
    """

    result = LXMLWebScrapingStrategy()._scrap(
        url="https://example.com/listings/123",
        html=html,
    )

    assert result["media"]["images"] == []
    assert "<img" not in result["cleaned_html"]


def test_css_background_images_resolve_relative_urls_for_markdown():
    result = LXMLWebScrapingStrategy()._scrap(
        url="https://example.com/listings/123",
        html='<div style="background-image: url(../images/house.jpg)"></div>',
    )

    assert [image["src"] for image in result["media"]["images"]] == [
        "../images/house.jpg"
    ]
    markdown = DefaultMarkdownGenerator().generate_markdown(
        result["cleaned_html"],
        base_url="https://example.com/listings/123",
        citations=False,
    )
    assert "https://example.com/images/house.jpg" in markdown.raw_markdown


def test_css_background_images_allow_semicolons_in_quoted_urls():
    image_url = "https://cdn.example.com/property.jpg?variant=hero;size=large"
    result = LXMLWebScrapingStrategy()._scrap(
        url="https://example.com/listings/123",
        html=f'<div style="background-image: url(\'{image_url}\')"></div>',
    )

    assert [image["src"] for image in result["media"]["images"]] == [image_url]


def test_css_background_images_deduplicate_repeated_urls_globally():
    image_url = "https://cdn.example.com/property.jpg"
    result = LXMLWebScrapingStrategy()._scrap(
        url="https://example.com/listings/123",
        html=(
            f'<section style="background: url({image_url})"></section>'
            f'<aside style="background-image: url({image_url})"></aside>'
        ),
    )

    assert [image["src"] for image in result["media"]["images"]] == [image_url]
