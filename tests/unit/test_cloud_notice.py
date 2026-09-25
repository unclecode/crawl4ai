"""The cloud notice: when it prints, and what it prints."""

import io

import pytest
from rich.console import Console

from crawl4ai import cloud_notice


@pytest.fixture
def home(tmp_path, monkeypatch):
    """The marker files go to a temporary home folder; the notice is on."""
    monkeypatch.setattr(cloud_notice, "_home", lambda: tmp_path)
    monkeypatch.delenv(cloud_notice._ENV_OFF, raising=False)
    return tmp_path


def _render(lines) -> str:
    """The banner as a terminal without colour would show it."""
    out = io.StringIO()
    console = Console(file=out, width=200, force_terminal=False, color_system=None)
    cloud_notice._print(lines, logger=type("L", (), {"console": console})())
    return out.getvalue()


def test_the_environment_variable_turns_every_banner_off(home, monkeypatch):
    monkeypatch.setenv(cloud_notice._ENV_OFF, "1")
    assert cloud_notice.show_once() is False
    assert cloud_notice.show_blocked() is False
    assert not (home / cloud_notice._MARKER).exists()


def test_daily_while_the_offer_runs_then_once_per_version(home, monkeypatch):
    printed = []
    monkeypatch.setattr(cloud_notice, "_print", lambda lines, logger=None: printed.append(lines))
    monkeypatch.setattr(cloud_notice, "_version", lambda: "0.9.4")

    monkeypatch.setattr(cloud_notice, "_today", lambda: "2026-10-01")
    assert cloud_notice.show_once() is True
    assert cloud_notice.show_once() is False, "the same day prints once"
    monkeypatch.setattr(cloud_notice, "_today", lambda: "2026-10-02")
    assert cloud_notice.show_once() is True, "the next day prints again"

    monkeypatch.setattr(cloud_notice, "_today", lambda: "2027-01-01")
    assert cloud_notice.show_once() is True, "the first run after the offer prints once per version"
    monkeypatch.setattr(cloud_notice, "_today", lambda: "2027-01-02")
    assert cloud_notice.show_once() is False, "the next day, same version: quiet"
    monkeypatch.setattr(cloud_notice, "_version", lambda: "0.9.5")
    assert cloud_notice.show_once() is True, "a new version, a patch included, prints again"
    assert len(printed) == 4


def test_the_blocked_banner_prints_once_a_day(home, monkeypatch):
    monkeypatch.setattr(cloud_notice, "_print", lambda lines, logger=None: None)
    monkeypatch.setattr(cloud_notice, "_today", lambda: "2026-10-01")
    assert cloud_notice.show_blocked() is True
    assert cloud_notice.show_blocked() is False
    monkeypatch.setattr(cloud_notice, "_today", lambda: "2026-10-02")
    assert cloud_notice.show_blocked() is True


def test_the_banner_is_ascii_with_the_link_and_the_off_switch():
    for lines in (cloud_notice.LINES, cloud_notice.BLOCKED_LINES, cloud_notice.SETUP_LINES):
        shown = _render(lines)
        assert shown.isascii(), "every console can print it"
        assert shown.startswith(cloud_notice._RULE) and shown.rstrip().endswith(cloud_notice._RULE)
        assert "https://crawl4ai.com/?ref=" in shown
    assert cloud_notice._ENV_OFF in _render(cloud_notice.LINES)
    assert cloud_notice.text() == _render(cloud_notice.LINES).rstrip("\n")
