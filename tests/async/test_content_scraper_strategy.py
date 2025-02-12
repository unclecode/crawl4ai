import os
import sys
import time
import csv
from tabulate import tabulate
from dataclasses import dataclass
from typing import List

parent_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(parent_dir)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

from crawl4ai.content_scraping_strategy import WebScrapingStrategy
from crawl4ai.content_scraping_strategy import (
    WebScrapingStrategy as WebScrapingStrategyCurrent,
)
# from crawl4ai.content_scrapping_strategy_current import WebScrapingStrategy as WebScrapingStrategyCurrent


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
        self.new_scraper = WebScrapingStrategy()
        self.current_scraper = WebScrapingStrategyCurrent()
        with open(__location__ + "/sample_wikipedia.html", "r", encoding="utf-8") as f:
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

        all_results = []
        for name, kwargs in test_cases:
            try:
                new_result, current_result = self.run_test(name, **kwargs)
                all_results.append((name, new_result, current_result))
            except Exception as e:
                print(f"Error in {name}: {str(e)}")

        self.save_results_to_csv(all_results)
        self.print_comparison_table(all_results)

    def save_results_to_csv(self, all_results: List[tuple]):
        csv_file = os.path.join(__location__, "strategy_comparison_results.csv")
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Test Name",
                    "Strategy",
                    "Success",
                    "Images",
                    "Internal Links",
                    "External Links",
                    "Markdown Length",
                    "Execution Time",
                ]
            )

            for name, new_result, current_result in all_results:
                writer.writerow(
                    [
                        name,
                        "New",
                        new_result.success,
                        new_result.images,
                        new_result.internal_links,
                        new_result.external_links,
                        new_result.markdown_length,
                        f"{new_result.execution_time:.3f}",
                    ]
                )
                writer.writerow(
                    [
                        name,
                        "Current",
                        current_result.success,
                        current_result.images,
                        current_result.internal_links,
                        current_result.external_links,
                        current_result.markdown_length,
                        f"{current_result.execution_time:.3f}",
                    ]
                )

    def print_comparison_table(self, all_results: List[tuple]):
        table_data = []
        headers = [
            "Test Name",
            "Strategy",
            "Success",
            "Images",
            "Internal Links",
            "External Links",
            "Markdown Length",
            "Time (s)",
        ]

        for name, new_result, current_result in all_results:
            # Check for differences
            differences = []
            if new_result.images != current_result.images:
                differences.append("images")
            if new_result.internal_links != current_result.internal_links:
                differences.append("internal_links")
            if new_result.external_links != current_result.external_links:
                differences.append("external_links")
            if new_result.markdown_length != current_result.markdown_length:
                differences.append("markdown")

            # Add row for new strategy
            new_row = [
                name,
                "New",
                new_result.success,
                new_result.images,
                new_result.internal_links,
                new_result.external_links,
                new_result.markdown_length,
                f"{new_result.execution_time:.3f}",
            ]
            table_data.append(new_row)

            # Add row for current strategy
            current_row = [
                "",
                "Current",
                current_result.success,
                current_result.images,
                current_result.internal_links,
                current_result.external_links,
                current_result.markdown_length,
                f"{current_result.execution_time:.3f}",
            ]
            table_data.append(current_row)

            # Add difference summary if any
            if differences:
                table_data.append(
                    ["", "⚠️ Differences", ", ".join(differences), "", "", "", "", ""]
                )

            # Add empty row for better readability
            table_data.append([""] * len(headers))

        print("\nStrategy Comparison Results:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    tester = StrategyTester()
    tester.run_all_tests()
