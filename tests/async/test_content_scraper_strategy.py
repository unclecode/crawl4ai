import csv
import sys
import time
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, List

import pytest
from _pytest.mark import ParameterSet
from tabulate import tabulate

from crawl4ai.content_scraping_strategy import (
    ContentScrapingStrategy,
    WebScrapingStrategy,
)
from crawl4ai.content_scraping_strategy import (
    WebScrapingStrategy as WebScrapingStrategyCurrent,
)
from crawl4ai.models import ScrapingResult


@dataclass
class Result:
    name: str
    strategy: str
    success: bool
    images: int
    internal_links: int
    external_links: int
    cleaned_html_length: int
    execution_time: float


@lru_cache
@pytest.fixture
def wiki_html() -> str:
    file_path: Path = Path(__file__).parent / "sample_wikipedia.html"
    with file_path.open("r", encoding="utf-8") as f:
        return f.read()


results: List[Result] = []


def print_comparison_table():
    """Print comparison table of results."""
    if not results:
        return

    table_data = []
    headers = [
        "Test Name",
        "Strategy",
        "Success",
        "Images",
        "Internal Links",
        "External Links",
        "Cleaned HTML Length",
        "Time (s)",
    ]

    all_results: List[tuple[str, Result, Result]] = []
    new_results = [result for result in results if result.strategy == "new"]
    current_results = [result for result in results if result.strategy == "current"]
    for new_result in new_results:
        for current_result in current_results:
            if new_result.name == current_result.name:
                all_results.append((new_result.name, new_result, current_result))

    for name, new_result, current_result in all_results:
        # Check for differences
        differences = []
        if new_result.images != current_result.images:
            differences.append("images")
        if new_result.internal_links != current_result.internal_links:
            differences.append("internal_links")
        if new_result.external_links != current_result.external_links:
            differences.append("external_links")
        if new_result.cleaned_html_length != current_result.cleaned_html_length:
            differences.append("cleaned_html")

        # Add row for new strategy
        new_row = [
            name,
            "New",
            new_result.success,
            new_result.images,
            new_result.internal_links,
            new_result.external_links,
            new_result.cleaned_html_length,
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
            current_result.cleaned_html_length,
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


def write_results_to_csv():
    """Write results to CSV and print comparison table."""
    if not results:
        return
    csv_file: Path = Path(__file__).parent / "output/strategy_comparison_results.csv"
    with csv_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Test Name",
                "Strategy",
                "Success",
                "Images",
                "Internal Links",
                "External Links",
                "Cleaned HTML Length",
                "Execution Time",
            ]
        )

        for result in results:
            writer.writerow(asdict(result))


def scrapper_params() -> List[ParameterSet]:
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
    params: List[ParameterSet] = []
    for strategy_name, strategy in [
        ("new", WebScrapingStrategy()),
        ("current", WebScrapingStrategyCurrent()),
    ]:
        for name, kwargs in test_cases:
            params.append(
                pytest.param(
                    name,
                    strategy_name,
                    strategy,
                    kwargs,
                    id=f"{name} - {strategy_name}",
                )
            )

    return params


@pytest.mark.parametrize("name,strategy_name,strategy,kwargs", scrapper_params())
def test_strategy(
    wiki_html: str,
    name: str,
    strategy_name: str,
    strategy: ContentScrapingStrategy,
    kwargs: dict[str, Any],
):
    start_time = time.time()
    result: ScrapingResult = strategy.scrap(
        url="https://en.wikipedia.org/wiki/Test", html=wiki_html, **kwargs
    )
    assert result.success
    execution_time = time.time() - start_time

    results.append(
        Result(
            name=name,
            strategy=strategy_name,
            success=result.success,
            images=len(result.media.images),
            internal_links=len(result.links.internal),
            external_links=len(result.links.external),
            cleaned_html_length=len(result.cleaned_html),
            execution_time=execution_time,
        )
    )


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
