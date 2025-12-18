# // File: tests/deep_crawling/test_filters.py
import pytest
from urllib.parse import urlparse
from crawl4ai import ContentTypeFilter, URLFilter 

# Minimal URLFilter base class stub if not already importable directly for tests
# In a real scenario, this would be imported from the library
if not hasattr(URLFilter, '_update_stats'): # Check if it's a basic stub
    class URLFilter: # Basic stub for testing if needed
        def __init__(self, name=None): self.name = name
        def apply(self, url: str) -> bool: raise NotImplementedError
        def _update_stats(self, passed: bool): pass # Mock implementation

# Assume ContentTypeFilter is structured as discussed. If its definition is not fully
# available for direct import in the test environment, a more elaborate stub or direct
# instantiation of the real class (if possible) would be needed.
# For this example, we assume ContentTypeFilter can be imported and used.

class TestContentTypeFilter:
    @pytest.mark.parametrize(
        "url, allowed_types, expected",
        [
            # Existing tests (examples)
            ("http://example.com/page.html", ["text/html"], True),
            ("http://example.com/page.json", ["application/json"], True),
            ("http://example.com/image.png", ["text/html"], False),
            ("http://example.com/document.pdf", ["application/pdf"], True),
            ("http://example.com/page", ["text/html"], True), # No extension, allowed
            ("http://example.com/page", ["text/html"], False), # No extension, disallowed
            ("http://example.com/page.unknown", ["text/html"], False), # Unknown extension
            
            # Tests for PHP extensions
            ("http://example.com/index.php", ["application/x-httpd-php"], True),
            ("http://example.com/script.php3", ["application/x-httpd-php"], True),
            ("http://example.com/legacy.php4", ["application/x-httpd-php"], True),
            ("http://example.com/main.php5", ["application/x-httpd-php"], True),
            ("http://example.com/api.php7", ["application/x-httpd-php"], True),
            ("http://example.com/index.phtml", ["application/x-httpd-php"], True),
            ("http://example.com/source.phps", ["application/x-httpd-php-source"], True),

            # Test rejection of PHP extensions
            ("http://example.com/index.php", ["text/html"], False),
            ("http://example.com/script.php3", ["text/plain"], False),
            ("http://example.com/source.phps", ["application/x-httpd-php"], False), # Mismatch MIME
            ("http://example.com/source.php", ["application/x-httpd-php-source"], False), # Mismatch MIME for .php

            # Test case-insensitivity of extensions in URL
            ("http://example.com/PAGE.HTML", ["text/html"], True),
            ("http://example.com/INDEX.PHP", ["application/x-httpd-php"], True),
            ("http://example.com/SOURCE.PHPS", ["application/x-httpd-php-source"], True),

            # Test case-insensitivity of allowed_types
            ("http://example.com/index.php", ["APPLICATION/X-HTTPD-PHP"], True),
        ],
    )
    def test_apply(self, url, allowed_types, expected):
        content_filter = ContentTypeFilter(
            allowed_types=allowed_types
        )
        assert content_filter.apply(url) == expected

    @pytest.mark.parametrize(
        "url, expected_extension",
        [
            ("http://example.com/file.html", "html"),
            ("http://example.com/file.tar.gz", "gz"),
            ("http://example.com/path/", ""),
            ("http://example.com/nodot", ""),
            ("http://example.com/.config", "config"), # hidden file with extension
            ("http://example.com/path/to/archive.BIG.zip", "zip"), # Case test
        ]
    )
    def test_extract_extension(self, url, expected_extension):
        # Test the static method directly
        assert ContentTypeFilter._extract_extension(url) == expected_extension
