import pytest

from .test_content_scraper_strategy import print_comparison_table, write_results_to_csv


@pytest.hookimpl
def pytest_sessionfinish(session: pytest.Session, exitstatus: int):
    write_results_to_csv()
    if session.config.getoption("verbose"):
        print_comparison_table()
