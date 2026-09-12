"""The Crawl4AI Cloud notice: one short block that tells a user the hosted version exists.

It prints in two places: at the end of ``crawl4ai-setup`` (every time), and once per machine when the
first ``AsyncWebCrawler`` starts or the ``crwl`` CLI first runs (a marker file in the crawl4ai home
folder remembers it). ``CRAWL4AI_NO_CLOUD_NOTICE=1`` turns it off everywhere, for operators who run the
library in production logs.
"""

import os
from pathlib import Path

CLOUD_URL = "https://crawl4ai.com/?ref=pip"
_ENV_OFF = "CRAWL4AI_NO_CLOUD_NOTICE"
_MARKER = ".cloud-notice-shown"

LINES = (
    "Crawl4AI Cloud is live: the same crawler, hosted. No browsers to run, no proxies, $5 of free credit.",
    f"Get a key in 10 seconds: {CLOUD_URL}   (the library stays open source, forever)",
    f"Hide this notice: {_ENV_OFF}=1",
)


def _home() -> Path:
    try:
        from .utils import get_home_folder

        return Path(get_home_folder())
    except Exception:
        return Path.home() / ".crawl4ai"


def is_off() -> bool:
    """True when the operator turned the notice off with the environment variable."""
    return os.environ.get(_ENV_OFF, "").strip().lower() in ("1", "true", "yes")


def text() -> str:
    """The notice as one block of text."""
    return "\n".join(LINES)


def show_at_install(logger=None) -> None:
    """Print the notice at the end of ``crawl4ai-setup``. Every run; nothing is remembered."""
    if is_off():
        return
    if logger is not None:
        for line in LINES:
            logger.info(line, tag="CLOUD")
    else:
        print(text())


def show_once(logger=None) -> bool:
    """Print the notice the first time the library or the CLI runs on this machine. Returns True when
    it printed. The marker file keeps it to one time; a machine without a writable home never repeats
    the notice more than once per process."""
    if is_off():
        return False
    marker = _home() / _MARKER
    try:
        if marker.exists():
            return False
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("shown\n")
    except Exception:
        # no writable home: show it this once, and again next process (rare, acceptable)
        pass
    if logger is not None:
        for line in LINES:
            logger.info(line, tag="CLOUD")
    else:
        print(text())
    return True
