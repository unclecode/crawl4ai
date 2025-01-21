from enum import Enum
from typing import Optional, Dict, Any
from colorama import Fore, Style, init
import os
from datetime import datetime


class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    SUCCESS = 3
    WARNING = 4
    ERROR = 5


class AsyncLogger:
    """
    Asynchronous logger with support for colored console output and file logging.
    Supports templated messages with colored components.
    """

    DEFAULT_ICONS = {
        "INIT": "→",
        "READY": "✓",
        "FETCH": "↓",
        "SCRAPE": "◆",
        "EXTRACT": "■",
        "COMPLETE": "●",
        "ERROR": "×",
        "DEBUG": "⋯",
        "INFO": "ℹ",
        "WARNING": "⚠",
    }

    DEFAULT_COLORS = {
        LogLevel.DEBUG: Fore.LIGHTBLACK_EX,
        LogLevel.INFO: Fore.CYAN,
        LogLevel.SUCCESS: Fore.GREEN,
        LogLevel.WARNING: Fore.YELLOW,
        LogLevel.ERROR: Fore.RED,
    }

    def __init__(
        self,
        log_file: Optional[str] = None,
        log_level: LogLevel = LogLevel.DEBUG,
        tag_width: int = 10,
        icons: Optional[Dict[str, str]] = None,
        colors: Optional[Dict[LogLevel, str]] = None,
        verbose: bool = True,
    ):
        """
        Initialize the logger.

        Args:
            log_file: Optional file path for logging
            log_level: Minimum log level to display
            tag_width: Width for tag formatting
            icons: Custom icons for different tags
            colors: Custom colors for different log levels
            verbose: Whether to output to console
        """
        init()  # Initialize colorama
        self.log_file = log_file
        self.log_level = log_level
        self.tag_width = tag_width
        self.icons = icons or self.DEFAULT_ICONS
        self.colors = colors or self.DEFAULT_COLORS
        self.verbose = verbose

        # Create log file directory if needed
        if log_file:
            os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)

    def _format_tag(self, tag: str) -> str:
        """Format a tag with consistent width."""
        return f"[{tag}]".ljust(self.tag_width, ".")

    def _get_icon(self, tag: str) -> str:
        """Get the icon for a tag, defaulting to info icon if not found."""
        return self.icons.get(tag, self.icons["INFO"])

    def _write_to_file(self, message: str):
        """Write a message to the log file if configured."""
        if self.log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with open(self.log_file, "a", encoding="utf-8") as f:
                # Strip ANSI color codes for file output
                clean_message = message.replace(Fore.RESET, "").replace(
                    Style.RESET_ALL, ""
                )
                for color in vars(Fore).values():
                    if isinstance(color, str):
                        clean_message = clean_message.replace(color, "")
                f.write(f"[{timestamp}] {clean_message}\n")

    def _log(
        self,
        level: LogLevel,
        message: str,
        tag: str,
        params: Optional[Dict[str, Any]] = None,
        colors: Optional[Dict[str, str]] = None,
        base_color: Optional[str] = None,
        **kwargs,
    ):
        """
        Core logging method that handles message formatting and output.

        Args:
            level: Log level for this message
            message: Message template string
            tag: Tag for the message
            params: Parameters to format into the message
            colors: Color overrides for specific parameters
            base_color: Base color for the entire message
        """
        if level.value < self.log_level.value:
            return

        # Format the message with parameters if provided
        if params:
            try:
                # First format the message with raw parameters
                formatted_message = message.format(**params)

                # Then apply colors if specified
                if colors:
                    for key, color in colors.items():
                        # Find the formatted value in the message and wrap it with color
                        if key in params:
                            value_str = str(params[key])
                            formatted_message = formatted_message.replace(
                                value_str, f"{color}{value_str}{Style.RESET_ALL}"
                            )

            except KeyError as e:
                formatted_message = (
                    f"LOGGING ERROR: Missing parameter {e} in message template"
                )
                level = LogLevel.ERROR
        else:
            formatted_message = message

        # Construct the full log line
        color = base_color or self.colors[level]
        log_line = f"{color}{self._format_tag(tag)} {self._get_icon(tag)} {formatted_message}{Style.RESET_ALL}"

        # Output to console if verbose
        if self.verbose or kwargs.get("force_verbose", False):
            print(log_line)

        # Write to file if configured
        self._write_to_file(log_line)

    def debug(self, message: str, tag: str = "DEBUG", **kwargs):
        """Log a debug message."""
        self._log(LogLevel.DEBUG, message, tag, **kwargs)

    def info(self, message: str, tag: str = "INFO", **kwargs):
        """Log an info message."""
        self._log(LogLevel.INFO, message, tag, **kwargs)

    def success(self, message: str, tag: str = "SUCCESS", **kwargs):
        """Log a success message."""
        self._log(LogLevel.SUCCESS, message, tag, **kwargs)

    def warning(self, message: str, tag: str = "WARNING", **kwargs):
        """Log a warning message."""
        self._log(LogLevel.WARNING, message, tag, **kwargs)

    def error(self, message: str, tag: str = "ERROR", **kwargs):
        """Log an error message."""
        self._log(LogLevel.ERROR, message, tag, **kwargs)

    def url_status(
        self,
        url: str,
        success: bool,
        timing: float,
        tag: str = "FETCH",
        url_length: int = 50,
    ):
        """
        Convenience method for logging URL fetch status.

        Args:
            url: The URL being processed
            success: Whether the operation was successful
            timing: Time taken for the operation
            tag: Tag for the message
            url_length: Maximum length for URL in log
        """
        self._log(
            level=LogLevel.SUCCESS if success else LogLevel.ERROR,
            message="{url:.{url_length}}... | Status: {status} | Time: {timing:.2f}s",
            tag=tag,
            params={
                "url": url,
                "url_length": url_length,
                "status": success,
                "timing": timing,
            },
            colors={
                "status": Fore.GREEN if success else Fore.RED,
                "timing": Fore.YELLOW,
            },
        )

    def error_status(
        self, url: str, error: str, tag: str = "ERROR", url_length: int = 50
    ):
        """
        Convenience method for logging error status.

        Args:
            url: The URL being processed
            error: Error message
            tag: Tag for the message
            url_length: Maximum length for URL in log
        """
        self._log(
            level=LogLevel.ERROR,
            message="{url:.{url_length}}... | Error: {error}",
            tag=tag,
            params={"url": url, "url_length": url_length, "error": error},
        )
