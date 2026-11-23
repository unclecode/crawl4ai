from unittest.mock import Mock, patch

from crawl4ai.content_scraping_strategy import fetch_image_file_size


def test_fetch_image_file_size_returns_content_length():
    image = {"src": "/image.png"}
    response = Mock(status_code=200, headers={"Content-Length": "1024"})

    with patch("crawl4ai.content_scraping_strategy.requests.head", return_value=response):
        assert fetch_image_file_size(image, "https://example.com/page") == "1024"
