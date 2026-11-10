"""The URL normalizers must lowercase the host without rewriting userinfo.

A URL may carry `user:password@` in front of the host. Hostnames are
case-insensitive, credentials are not, so lowering the whole netloc rewrites
them: a crawl that follows such a link authenticates with a different password
than the one in the page.
"""

import unittest

from crawl4ai.utils import (
    efficient_normalize_url_for_deep_crawl,
    normalize_url,
    normalize_url_for_deep_crawl,
)

BASE = "https://example.com/dir/page"


class TestNormalizeUrlUserinfo(unittest.TestCase):
    def test_normalize_url_keeps_userinfo_casing(self):
        self.assertEqual(
            normalize_url("https://User:SecRet@Example.COM/path", BASE),
            "https://User:SecRet@example.com/path",
        )

    def test_normalize_url_still_lowercases_the_host(self):
        self.assertEqual(
            normalize_url("https://EXAMPLE.com/path", BASE),
            "https://example.com/path",
        )

    def test_normalize_url_keeps_userinfo_and_port(self):
        self.assertEqual(
            normalize_url("https://Token:AbC@Example.com:8443/x?a=1", BASE),
            "https://Token:AbC@example.com:8443/x?a=1",
        )

    def test_normalize_url_keeps_an_at_sign_in_the_password(self):
        # Percent-encoded, as it has to be for `urlparse` to keep it in the netloc.
        self.assertEqual(
            normalize_url("https://user:p%40ss@Example.com/x", BASE),
            "https://user:p%40ss@example.com/x",
        )

    def test_deep_crawl_normalizer_keeps_userinfo_casing(self):
        self.assertEqual(
            normalize_url_for_deep_crawl("https://User:SecRet@Example.COM/path", BASE),
            "https://User:SecRet@example.com/path",
        )

    def test_efficient_normalizer_keeps_userinfo_casing(self):
        self.assertEqual(
            efficient_normalize_url_for_deep_crawl(
                "https://User:SecRet@Example.COM/path", BASE
            ),
            "https://User:SecRet@example.com/path",
        )


if __name__ == "__main__":
    unittest.main()
