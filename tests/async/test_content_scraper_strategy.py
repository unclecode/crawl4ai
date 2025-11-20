import os
import sys
import time
from dataclasses import dataclass

from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

parent_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(parent_dir)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


# This test compares the same strategy with itself now since WebScrapingStrategy is deprecated


@dataclass
class TestResult:
    name: str
    success: bool
    images: int
    internal_links: int
    external_links: int
    markdown_length: int
    execution_time: float


class StrategyTester:
    def __init__(self):
        self.new_scraper = LXMLWebScrapingStrategy()
        self.current_scraper = LXMLWebScrapingStrategy()  # Same strategy now
        with open(__location__ + "/sample_wikipedia.html", encoding="utf-8") as f:
            self.WIKI_HTML = f.read()
        self.results = {"new": [], "current": []}

    def run_test(self, name: str, **kwargs) -> tuple[TestResult, TestResult]:
        results = []
        for scraper in [self.new_scraper, self.current_scraper]:
            start_time = time.time()
            result = scraper._get_content_of_website_optimized(
                url="https://en.wikipedia.org/wiki/Test", html=self.WIKI_HTML, **kwargs
            )
            execution_time = time.time() - start_time

            test_result = TestResult(
                name=name,
                success=result["success"],
                images=len(result["media"]["images"]),
                internal_links=len(result["links"]["internal"]),
                external_links=len(result["links"]["external"]),
                markdown_length=len(result["markdown"]),
                execution_time=execution_time,
            )
            results.append(test_result)

        return results[0], results[1]  # new, current

    def run_all_tests(self):
        test_cases = [
            ("Basic Extraction", {}),
            ("Exclude Tags", {"excluded_tags": ["table", "div.infobox", "div.navbox"]}),
            ("Word Threshold", {"word_count_threshold": 50}),
            ("CSS Selector", {"css_selector": "div.mw-parser-output > p"}),
            (
                "Link Exclusions",
                {
                    "exclude_external_links": True,
                    "exclude_social_media_links": True,
                    "exclude_domains": ["facebook.com", "twitter.com"],
                },
            ),
            (
                "Media Handling",
                {
                    "exclude_external_images": True,
                    "image_description_min_word_threshold": 20,
                },
            ),
            ("Text Only", {"only_text": True, "remove_forms": True}),
            ("HTML Cleaning", {"clean_html": True, "keep_data_attributes": True}),
            (
                "HTML2Text Options",
                {
                    "html2text": {
                        "skip_internal_links": True,
                        "single_line_break": True,
                        "mark_code": True,
                        "preserve_tags": ["pre", "code"],
                    }
                },
            ),
        ]

        for name, kwargs in test_cases:
            new_result, current_result = self.run_test(name, **kwargs)
            assert new_result == current_result, f"Mismatch in results for {name}"


def test_content_scraper_strategy():
    tester = StrategyTester()
    tester.run_all_tests()
