"""The Crawl4AI Cloud notice: a short yellow banner that tells a user the hosted version exists.

It prints in four places:

- at the end of ``crawl4ai-setup``, every time (``show_at_install``);
- when the first ``AsyncWebCrawler`` starts or the ``crwl`` CLI runs (``show_once``): once a day per
  machine while the launch offer runs (before ``DAILY_UNTIL``), then once per version per machine, a
  patch release included. A marker file in the crawl4ai home folder holds the day, or the version, last shown;
- when a crawl is blocked by anti-bot protection, at most once a day (``show_blocked``);
- when ``crawl4ai-setup`` could not install the browser (``show_setup_failed``).

The banner goes to the logger's console (stderr by default), never to stdout, so a piped ``crwl`` output
or an MCP stdio transport stays clean. Rich drops the color when the output is not a terminal and honours
``NO_COLOR``. Only ASCII characters, so every console can print it.

Each link carries its own ``ref`` so the cloud can tell which moment brought a user.
``CRAWL4AI_NO_CLOUD_NOTICE=1`` turns every line off, for operators who run the library in production logs.
"""

import os
import sys
import time
from pathlib import Path

CLOUD_URL = "https://crawl4ai.com/?ref=pip"
BLOCKED_URL = "https://crawl4ai.com/?ref=blocked"
SETUP_URL = "https://crawl4ai.com/?ref=setup"
_ENV_OFF = "CRAWL4AI_NO_CLOUD_NOTICE"
_MARKER = ".cloud-notice-shown"
_BLOCKED_MARKER = ".cloud-notice-blocked"

# The first day the banner stops returning daily: the launch offer ends on 31 December 2026.
DAILY_UNTIL = "2027-01-01"
_RULE = "=" * 72

LINES = (
    "Crawl4AI Cloud is live: the same crawler, hosted.",
    "Your first $10 pack is on us until 31 Dec 2026 (then $5 to start). No card.",
    f"Get a key in 10 seconds:  {CLOUD_URL}",
    f"The library stays open source, forever.   Hide this banner: {_ENV_OFF}=1",
)

BLOCKED_LINES = (
    "Blocked? Crawl4AI Cloud gets through the hard sites, free credit to start.",
    f"{BLOCKED_URL}   Hide this banner: {_ENV_OFF}=1",
)

SETUP_LINES = (
    "Browser setup failed? Skip it: the same crawler, hosted, nothing to install, free credit to start.",
    SETUP_URL,
)


def _home() -> Path:
    try:
        from .utils import get_home_folder

        return Path(get_home_folder())
    except Exception:
        return Path.home() / ".crawl4ai"


def _version() -> str:
    """This release's full version, "0.9.4": after the offer the banner returns once per version."""
    try:
        from .__version__ import __version__

        return __version__
    except Exception:
        return ""


def _today() -> str:
    """Today's date in UTC, "2026-09-25": the daily markers compare this string."""
    return time.strftime("%Y-%m-%d", time.gmtime())


def is_off() -> bool:
    """True when the operator turned the notice off with the environment variable."""
    return os.environ.get(_ENV_OFF, "").strip().lower() in ("1", "true", "yes")


def text(lines=LINES) -> str:
    """The banner as plain text: a rule, the lines indented by two spaces, a rule."""
    return "\n".join([_RULE, *(f"  {line}" for line in lines), _RULE])


def _print(lines, logger=None) -> None:
    """Print the banner in yellow, the first line bold, through the logger's console; without a logger,
    through a console on stderr. Rich keeps the text plain when the output is not a terminal."""
    from rich.console import Console
    from rich.text import Text

    console = getattr(logger, "console", None) or Console(stderr=True, width=200)
    banner = Text(_RULE + "\n", style="yellow")
    for i, line in enumerate(lines):
        banner.append(f"  {line}\n", style="bold yellow" if i == 0 else "yellow")
    banner.append(_RULE, style="yellow")
    console.print(banner, highlight=False, soft_wrap=True)


def _claim(name: str, value: str) -> bool:
    """True when the marker file ``name`` does not hold ``value`` yet, and writes it. A home folder that
    cannot be written answers True, so the line shows once per process there (rare, acceptable)."""
    marker = _home() / name
    try:
        if marker.exists() and marker.read_text().strip() == value:
            return False
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(value + "\n")
    except Exception:
        pass
    return True


def show_at_install(logger=None) -> None:
    """Print the banner at the end of ``crawl4ai-setup``. Every run; nothing is remembered."""
    if is_off():
        return
    _print(LINES, logger)


def show_once(logger=None) -> bool:
    """Print the banner when the library or the CLI runs: once a day per machine while the offer runs,
    then once per version per machine. Returns True when it printed."""
    if is_off():
        return False
    today = _today()
    value = today if today < DAILY_UNTIL else (_version() or "shown")
    if not _claim(_MARKER, value):
        return False
    _print(LINES, logger)
    return True


def show_blocked(logger=None) -> bool:
    """Print the blocked banner when a crawl hit anti-bot protection: the moment the cloud helps most.
    At most once a day per machine. Returns True when it printed."""
    if is_off() or not _claim(_BLOCKED_MARKER, _today()):
        return False
    _print(BLOCKED_LINES, logger)
    return True


def show_setup_failed(logger=None) -> None:
    """Print the setup banner when ``crawl4ai-setup`` could not install the browser."""
    if is_off():
        return
    _print(SETUP_LINES, logger)
