#!/usr/bin/env python3
"""
Regression test for the PDF-image arbitrary-write via untrusted config body
(reported by sec-reex).

Root cause: PDFContentScrapingStrategy is an UNTRUSTED_ALLOWED_TYPE but had no
field allowlist, so _filter_untrusted_fields fell open and kept its
filesystem-write knobs (image_save_dir / save_images_locally). A request body
the API loads as UNTRUSTED could then steer the PDF image writer to an
attacker-chosen directory.

These tests hit the real deserialization path (from_serializable_dict /
CrawlerRunConfig.load with provenance=UNTRUSTED), not a copy.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from crawl4ai.async_configs import (
    CrawlerRunConfig,
    Provenance,
    UntrustedConfigError,
    from_serializable_dict,
)


def _pdf_strategy(params: dict) -> dict:
    return {"type": "PDFContentScrapingStrategy", "params": params}


class TestPdfImageWriteGate(unittest.TestCase):
    def test_untrusted_image_save_dir_is_rejected(self):
        """image_save_dir on an untrusted body must raise (loud 400), not pass."""
        body = _pdf_strategy({"save_images_locally": True, "image_save_dir": "/home/appuser/.ssh"})
        with self.assertRaises(UntrustedConfigError):
            from_serializable_dict(body, provenance=Provenance.UNTRUSTED)

    def test_untrusted_save_images_locally_is_rejected(self):
        """The boolean that turns the write on is forbidden on untrusted bodies too."""
        body = _pdf_strategy({"save_images_locally": True})
        with self.assertRaises(UntrustedConfigError):
            from_serializable_dict(body, provenance=Provenance.UNTRUSTED)

    def test_untrusted_rejected_when_nested_in_crawlerrunconfig(self):
        """The real server path: PDF strategy nested under CrawlerRunConfig.scraping_strategy."""
        body = {
            "type": "CrawlerRunConfig",
            "params": {
                "scraping_strategy": _pdf_strategy(
                    {"save_images_locally": True, "image_save_dir": "/tmp/c4_oob"}
                )
            },
        }
        with self.assertRaises(UntrustedConfigError):
            CrawlerRunConfig.load(body, provenance=Provenance.UNTRUSTED)

    def test_untrusted_extract_images_still_allowed(self):
        """Negative control: extract_images returns bytes base64-inline, no disk
        write, so it must NOT be blocked (feature preserved over the API)."""
        body = _pdf_strategy({"extract_images": True})
        obj = from_serializable_dict(body, provenance=Provenance.UNTRUSTED)
        self.assertEqual(type(obj).__name__, "PDFContentScrapingStrategy")

    def test_trusted_path_unchanged(self):
        """No regression: the in-process SDK (TRUSTED) may still set image_save_dir."""
        body = _pdf_strategy({"save_images_locally": True, "image_save_dir": "/tmp/mine"})
        obj = from_serializable_dict(body, provenance=Provenance.TRUSTED)
        self.assertEqual(type(obj).__name__, "PDFContentScrapingStrategy")

    def test_global_backstop_covers_future_types(self):
        """The global forbidden set catches a write-arg regardless of per-type map.
        LXMLWebScrapingStrategy has no path arg today, but a smuggled downloads_path
        must still be rejected by the fail-closed backstop."""
        body = {"type": "LXMLWebScrapingStrategy", "params": {"downloads_path": "/etc"}}
        with self.assertRaises(UntrustedConfigError):
            from_serializable_dict(body, provenance=Provenance.UNTRUSTED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
