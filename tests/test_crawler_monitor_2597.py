"""Regression tests for issue #2597: CrawlerMonitor memory %, peak time, and time formatting."""

import psutil
import pytest

from crawl4ai.components.crawler_monitor import CrawlerMonitor
from crawl4ai.models import CrawlStatus


@pytest.fixture
def monitor():
    m = CrawlerMonitor(urls_total=1, enable_ui=False)
    m.start()
    m.add_task("task-1", "https://example.com")
    yield m
    m.stop()


def test_peak_memory_percent_uses_matching_units(monitor):
    # memory_usage is reported in MiB, so 10% of system RAM should read as ~10%
    total_mib = psutil.virtual_memory().total / (1024 * 1024)
    monitor.update_task("task-1", status=CrawlStatus.IN_PROGRESS, memory_usage=total_mib * 0.10)

    assert monitor.get_summary()["peak_memory_percent"] == pytest.approx(10.0, rel=1e-6)


def test_peak_memory_time_is_elapsed_runtime(monitor):
    monitor.update_task("task-1", status=CrawlStatus.IN_PROGRESS, memory_usage=100.0)

    peak_time = monitor.get_summary()["peak_memory_time"]
    assert 0 <= peak_time < 5  # seconds since start(), not a Unix timestamp


@pytest.mark.parametrize(
    "seconds, expected",
    [
        (59, "0:59"),
        (3599, "59:59"),
        (3600, "1:00:00"),
        (86400, "24:00:00"),
        (90061, "25:01:01"),
        (-5, "0:00"),
    ],
)
def test_format_time_keeps_hours_past_one_day(seconds, expected):
    monitor = CrawlerMonitor(enable_ui=False)
    assert monitor._format_time(seconds) == expected