from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any
from colorama import Fore, Style, init
import os
from datetime import datetime
from urllib.parse import unquote


class LogLevel(Enum):
    DEFAULT = 0
    DEBUG = 1
    INFO = 2
    SUCCESS = 3
    WARNING = 4
    ERROR = 5
    CRITICAL = 6
    ALERT = 7
    NOTICE = 8
    EXCEPTION = 9
    FATAL = 10
    



class AsyncLoggerBase(ABC):
    @abstractmethod
    def debug(self, message: str, tag: str = "DEBUG", **kwargs):
        pass

    @abstractmethod
    def info(self, message: str, tag: str = "INFO", **kwargs):
        pass

    @abstractmethod
    def success(self, message: str, tag: str = "SUCCESS", **kwargs):
        pass

    @abstractmethod
    def warning(self, message: str, tag: str = "WARNING", **kwargs):
        pass

    @abstractmethod
    def error(self, message: str, tag: str = "ERROR", **kwargs):
        pass

    @abstractmethod
    def url_status(self, url: str, success: bool, timing: float, tag: str = "FETCH", url_length: int = 100):
        pass

    @abstractmethod
    def error_status(self, url: str, error: str, tag: str = "ERROR", url_length: int = 100):
        pass

class AsyncLogger(AsyncLoggerBase):
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
        "SUCCESS": "✔",
        "CRITICAL": "‼",
        "ALERT": "⚡",
        "NOTICE": "ℹ",
        "EXCEPTION": "❗",
        "FATAL": "☠",
        "DEFAULT": "•",
    }

    DEFAULT_COLORS = {
        LogLevel.DEBUG: Fore.LIGHTBLACK_EX,
        LogLevel.INFO: Fore.CYAN,
        LogLevel.SUCCESS: Fore.GREEN,
        LogLevel.WARNING: Fore.YELLOW,
        LogLevel.ERROR: Fore.RED,
        LogLevel.CRITICAL: Fore.RED + Style.BRIGHT,
        LogLevel.ALERT: Fore.RED + Style.BRIGHT,
        LogLevel.NOTICE: Fore.BLUE,
        LogLevel.EXCEPTION: Fore.RED + Style.BRIGHT,
        LogLevel.FATAL: Fore.RED + Style.BRIGHT,
        LogLevel.DEFAULT: Fore.WHITE,
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
    
    def _shorten(self, text, length, placeholder="..."):
        """Truncate text in the middle if longer than length, or pad if shorter."""
        if len(text) <= length:
            return text.ljust(length)  # Pad with spaces to reach desired length
        half = (length - len(placeholder)) // 2
        shortened = text[:half] + placeholder + text[-half:]
        return shortened.ljust(length)  # Also pad shortened text to consistent length

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
                color_map = {
                    "green": Fore.GREEN,
                    "red": Fore.RED,
                    "yellow": Fore.YELLOW,
                    "blue": Fore.BLUE,
                    "cyan": Fore.CYAN,
                    "magenta": Fore.MAGENTA,
                    "white": Fore.WHITE,
                    "black": Fore.BLACK,
                    "reset": Style.RESET_ALL,
                }
                if colors:
                    for key, color in colors.items():
                        # Find the formatted value in the message and wrap it with color
                        if color in color_map:
                            color = color_map[color]
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
        
    def critical(self, message: str, tag: str = "CRITICAL", **kwargs):
        """Log a critical message."""
        self._log(LogLevel.ERROR, message, tag, **kwargs)
    def exception(self, message: str, tag: str = "EXCEPTION", **kwargs):
        """Log an exception message."""
        self._log(LogLevel.ERROR, message, tag, **kwargs)
    def fatal(self, message: str, tag: str = "FATAL", **kwargs):
        """Log a fatal message."""
        self._log(LogLevel.ERROR, message, tag, **kwargs)
    def alert(self, message: str, tag: str = "ALERT", **kwargs):
        """Log an alert message."""
        self._log(LogLevel.ERROR, message, tag, **kwargs)
    def notice(self, message: str, tag: str = "NOTICE", **kwargs):
        """Log a notice message."""
        self._log(LogLevel.INFO, message, tag, **kwargs)

    def error(self, message: str, tag: str = "ERROR", **kwargs):
        """Log an error message."""
        self._log(LogLevel.ERROR, message, tag, **kwargs)

    def url_status(
        self,
        url: str,
        success: bool,
        timing: float,
        tag: str = "FETCH",
        url_length: int = 100,
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
        decoded_url = unquote(url)
        readable_url = self._shorten(decoded_url, url_length)
        self._log(
            level=LogLevel.SUCCESS if success else LogLevel.ERROR,
            message="{url} | {status} | ⏱: {timing:.2f}s",
            tag=tag,
            params={
                "url": readable_url,
                "status": "✓" if success else "✗",
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
        decoded_url = unquote(url)
        readable_url = self._shorten(decoded_url, url_length)
        self._log(
            level=LogLevel.ERROR,
            message="{url} | Error: {error}",
            tag=tag,
            params={"url": readable_url, "error": error},
        )

class AsyncFileLogger(AsyncLoggerBase):
    """
    File-only asynchronous logger that writes logs to a specified file.
    """

    def __init__(self, log_file: str):
        """
        Initialize the file logger.

        Args:
            log_file: File path for logging
        """
        self.log_file = log_file
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)

    def _write_to_file(self, level: str, message: str, tag: str):
        """Write a message to the log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{level}] [{tag}] {message}\n")

    def debug(self, message: str, tag: str = "DEBUG", **kwargs):
        """Log a debug message to file."""
        self._write_to_file("DEBUG", message, tag)

    def info(self, message: str, tag: str = "INFO", **kwargs):
        """Log an info message to file."""
        self._write_to_file("INFO", message, tag)

    def success(self, message: str, tag: str = "SUCCESS", **kwargs):
        """Log a success message to file."""
        self._write_to_file("SUCCESS", message, tag)

    def warning(self, message: str, tag: str = "WARNING", **kwargs):
        """Log a warning message to file."""
        self._write_to_file("WARNING", message, tag)

    def error(self, message: str, tag: str = "ERROR", **kwargs):
        """Log an error message to file."""
        self._write_to_file("ERROR", message, tag)

    def url_status(self, url: str, success: bool, timing: float, tag: str = "FETCH", url_length: int = 100):
        """Log URL fetch status to file."""
        status = "SUCCESS" if success else "FAILED"
        message = f"{url[:url_length]}... | Status: {status} | Time: {timing:.2f}s"
        self._write_to_file("URL_STATUS", message, tag)

    def error_status(self, url: str, error: str, tag: str = "ERROR", url_length: int = 100):
        """Log error status to file."""
        message = f"{url[:url_length]}... | Error: {error}"
        self._write_to_file("ERROR", message, tag)
