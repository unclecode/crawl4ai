"""The Crawl4AI Cloud notice: short lines that tell a user the hosted version exists.

It prints in four places:

- at the end of ``crawl4ai-setup``, every time (``show_at_install``);
- once per minor release per machine, when the first ``AsyncWebCrawler`` starts or the ``crwl`` CLI runs
  (``show_once``; a marker file in the crawl4ai home folder holds the last minor version shown);
- when a crawl is blocked by anti-bot protection, at most once a day (``show_blocked``);
- when ``crawl4ai-setup`` could not install the browser (``show_setup_failed``).

Each link carries its own ``ref`` so the cloud can tell which moment brought a user.
``CRAWL4AI_NO_CLOUD_NOTICE=1`` turns every line off, for operators who run the library in production logs.
"""

import os
import time
from pathlib import Path

CLOUD_URL = "https://crawl4ai.com/?ref=pip"
BLOCKED_URL = "https://crawl4ai.com/?ref=blocked"
SETUP_URL = "https://crawl4ai.com/?ref=setup"
_ENV_OFF = "CRAWL4AI_NO_CLOUD_NOTICE"
_MARKER = ".cloud-notice-shown"
_BLOCKED_MARKER = ".cloud-notice-blocked"

LINES = (
    "Crawl4AI Cloud is live: the same crawler, hosted. $5 free every month, no card. Try it now with no signup.",
    f"Get a key in 10 seconds: {CLOUD_URL}   (the library stays open source, forever)",
    f"Hide this notice: {_ENV_OFF}=1",
)

BLOCKED_LINES = (
    f"Blocked? Crawl4AI Cloud gets through the hard sites, $5 free every month: {BLOCKED_URL}",
    f"Hide this notice: {_ENV_OFF}=1",
)

SETUP_LINES = (
    f"Browser setup failed? Skip it: the same crawler, hosted, nothing to install, $5 free every month: {SETUP_URL}",
)


def _home() -> Path:
    try:
        from .utils import get_home_folder

        return Path(get_home_folder())
    except Exception:
        return Path.home() / ".crawl4ai"


def _minor_version() -> str:
    """This release's minor version, "0.9" for 0.9.3: the notice returns once per minor release."""
    try:
        from .__version__ import __version__

        return ".".join(__version__.split(".")[:2])
    except Exception:
        return ""


def is_off() -> bool:
    """True when the operator turned the notice off with the environment variable."""
    return os.environ.get(_ENV_OFF, "").strip().lower() in ("1", "true", "yes")


def text() -> str:
    """The notice as one block of text."""
    return "\n".join(LINES)


def _print(lines, logger=None) -> None:
    if logger is not None:
        for line in lines:
            logger.info(line, tag="CLOUD")
    else:
        print("\n".join(lines))


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
    """Print the notice at the end of ``crawl4ai-setup``. Every run; nothing is remembered."""
    if is_off():
        return
    _print(LINES, logger)


def show_once(logger=None) -> bool:
    """Print the notice the first time the library or the CLI runs on this machine after a new minor
    release. Returns True when it printed."""
    if is_off() or not _claim(_MARKER, _minor_version() or "shown"):
        return False
    _print(LINES, logger)
    return True


def show_blocked(logger=None) -> bool:
    """Print the blocked line when a crawl hit anti-bot protection: the moment the cloud helps most.
    At most once a day per machine. Returns True when it printed."""
    if is_off() or not _claim(_BLOCKED_MARKER, time.strftime("%Y-%m-%d", time.gmtime())):
        return False
    _print(BLOCKED_LINES, logger)
    return True


def show_setup_failed(logger=None) -> None:
    """Print the setup line when ``crawl4ai-setup`` could not install the browser."""
    if is_off():
        return
    _print(SETUP_LINES, logger)
