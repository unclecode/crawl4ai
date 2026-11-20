import io
from types import SimpleNamespace

import pytest
from rich.console import Console

import crawl4ai.components.crawler_monitor as monitor_mod
from crawl4ai.components.crawler_monitor import CrawlerMonitor
from crawl4ai.models import CrawlStatus


def _render(renderable) -> str:
    console = Console(width=140, file=io.StringIO(), record=True)
    console.print(renderable)
    return console.export_text()


def test_peak_and_live_memory_percent_use_matching_units(monkeypatch):
    total_bytes = 16 * 1024 * 1024 * 1024  # 16 GiB = 16384 MiB
    rss_bytes = int(1638.4 * 1024 * 1024)  # 10.0% of 16 GiB

    monkeypatch.setattr(
        monitor_mod.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(total=total_bytes),
    )
    monkeypatch.setattr(
        monitor_mod.psutil,
        "Process",
        lambda: SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=rss_bytes)),
    )

    monitor = CrawlerMonitor(urls_total=2, enable_ui=True)
    monitor.start_time = 100.0
    monitor.add_task("t1", "https://example.com/1")
    monitor.update_task("t1", status=CrawlStatus.IN_PROGRESS, memory_usage=819.2)

    summary = monitor.get_summary()
    assert summary["peak_memory_percent"] == pytest.approx(5.0, rel=1e-3)

    monitor.terminal_ui.monitor = monitor
    panel_text = _render(monitor.terminal_ui._create_status_panel())
    assert "Memory: 10.0%" in panel_text
    assert "Peak Mem: 5.0%" in panel_text


def test_peak_memory_time_records_elapsed_seconds(monkeypatch):
    monkeypatch.setattr(
        monitor_mod.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(total=1000 * 1024 * 1024),
    )
    now = [1_700_000_000.0]
    monkeypatch.setattr(monitor_mod.time, "time", lambda: now[0])

    monitor = CrawlerMonitor(urls_total=1, enable_ui=False)
    monitor.start()
    try:
        monitor.add_task("t1", "https://example.com")
        now[0] += 75.0
        monitor.update_task("t1", memory_usage=250.0)
        summary = monitor.get_summary()
        assert summary["peak_memory_time"] == pytest.approx(75.0)

        ui = monitor_mod.TerminalUI()
        ui.monitor = monitor
        panel_text = _render(ui._create_status_panel())
        assert "Peak Mem: 25.0% at 1:15" in panel_text
    finally:
        monitor.stop()


def test_format_time_preserves_durations_over_24_hours():
    monitor = CrawlerMonitor(enable_ui=False)
    assert monitor._format_time(86400) == "24:00:00"
    assert monitor._format_time(90061) == "25:01:01"
    assert monitor._format_time(-5) == "0:00"


def test_runtime_freezes_after_stop(monkeypatch):
    now = [500.0]
    monkeypatch.setattr(monitor_mod.time, "time", lambda: now[0])

    monitor = CrawlerMonitor(urls_total=1, enable_ui=False)
    monitor.start()
    now[0] = 542.0
    monitor.stop()

    now[0] = 900.0
    assert monitor.get_summary()["runtime"] == pytest.approx(42.0)


def test_task_details_panel_sorts_before_slicing_display_count():
    monitor = CrawlerMonitor(urls_total=25, enable_ui=True)
    monitor.terminal_ui.monitor = monitor

    for i in range(20):
        tid = f"done-{i:02d}"
        monitor.add_task(tid, f"https://example.com/done/{i}")
        monitor.update_task(
            tid,
            status=CrawlStatus.COMPLETED,
            start_time=10.0,
            end_time=20.0 + i,
        )

    for i in range(3):
        tid = f"wait-{i:02d}"
        monitor.add_task(tid, f"https://example.com/queued/{i}")

    for i in range(2):
        tid = f"live-{i:02d}"
        monitor.add_task(tid, f"https://example.com/active/{i}")
        monitor.update_task(tid, status=CrawlStatus.IN_PROGRESS, start_time=50.0)

    panel_text = _render(monitor.terminal_ui._create_task_details_panel())
    assert "live-00" in panel_text
    assert "live-01" in panel_text
    assert "wait-00" in panel_text
    assert "wait-02" in panel_text
