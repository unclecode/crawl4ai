import unittest

from crawl4ai.html2text import CustomHTML2Text, HTML2Text


class TestNumericCharacterReferences(unittest.TestCase):
    def convert(self, converter, source, unicode_snob=True):
        parser = converter()
        parser.unicode_snob = unicode_snob
        return parser.handle(f"<p>{source}</p>").strip()

    def test_legacy_control_references_use_html_replacements(self):
        for converter in (HTML2Text, CustomHTML2Text):
            for source, expected in (
                ("&#128;20", "€20"),
                ("&#x80;20", "€20"),
                ("&#X80;20", "€20"),
                ("&#147;quoted&#148;", "“quoted”"),
                ("&#x91;quoted&#x92;", "‘quoted’"),
                ("&#133;", "…"),
                ("&#153;", "™"),
            ):
                with self.subTest(converter=converter.__name__, source=source):
                    self.assertEqual(self.convert(converter, source), expected)

    def test_invalid_references_become_encodable_replacement_characters(self):
        for converter in (HTML2Text, CustomHTML2Text):
            for reference in ("0", "xD800", "xDFFF", "1114112", "xFFFFFFFF"):
                with self.subTest(converter=converter.__name__, reference=reference):
                    result = self.convert(converter, f"before &#{reference}; after")
                    self.assertEqual(result, "before � after")
                    result.encode("utf-8")

    def test_replaced_references_keep_ascii_approximation_option(self):
        for converter in (HTML2Text, CustomHTML2Text):
            with self.subTest(converter=converter.__name__):
                self.assertEqual(
                    self.convert(converter, "&#147;quote&#148; &#151;", False),
                    '"quote" --',
                )

    def test_valid_references_and_existing_ascii_approximations(self):
        for converter in (HTML2Text, CustomHTML2Text):
            with self.subTest(converter=converter.__name__):
                self.assertEqual(
                    self.convert(converter, "&#65; &#x20AC; &#x1F642; &#x4E2D;"),
                    "A € 🙂 中",
                )
                self.assertEqual(self.convert(converter, "&#169;", False), "(C)")

    def test_unmapped_controls_and_noncharacters_are_preserved(self):
        for converter in (HTML2Text, CustomHTML2Text):
            for reference, expected in (
                ("x01", "\x01"),
                ("x81", "\x81"),
                ("xFDD0", "\ufdd0"),
                ("x10FFFF", "\U0010ffff"),
            ):
                with self.subTest(converter=converter.__name__, reference=reference):
                    self.assertEqual(
                        self.convert(converter, f"before &#{reference}; after"),
                        f"before {expected} after",
                    )


if __name__ == "__main__":
    unittest.main()
