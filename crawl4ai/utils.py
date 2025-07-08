import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup, Comment, element, Tag, NavigableString
import json
import html
import lxml
import re
import os
import subprocess
import platform
from .prompts import PROMPT_EXTRACT_BLOCKS
from array import array
from .html2text import html2text, CustomHTML2Text
# from .config import *
from .config import MIN_WORD_THRESHOLD, IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD, IMAGE_SCORE_THRESHOLD, DEFAULT_PROVIDER, PROVIDER_MODELS
import httpx
from socket import gaierror
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from urllib.parse import urljoin
import requests
from requests.exceptions import InvalidSchema
import xxhash
import textwrap
import cProfile
import pstats
from functools import wraps
import asyncio
from lxml import etree, html as lhtml
import sqlite3
import hashlib

from urllib.robotparser import RobotFileParser
import aiohttp
from functools import lru_cache

from packaging import version
from . import __version__
from typing import Sequence

from itertools import chain
from collections import deque
from typing import  Generator, Iterable

import numpy as np

from urllib.parse import (
    urljoin, urlparse, urlunparse,
    parse_qsl, urlencode, quote, unquote
)


# Monkey patch to fix wildcard handling in urllib.robotparser
from urllib.robotparser import RuleLine
import re

original_applies_to = RuleLine.applies_to

def patched_applies_to(self, filename):
   # Handle wildcards in paths
   if '*' in self.path or '%2A' in self.path or self.path in ("*", "%2A"):
       pattern = self.path.replace('%2A', '*')
       pattern = re.escape(pattern).replace('\\*', '.*')
       pattern = '^' + pattern
       if pattern.endswith('\\$'):
           pattern = pattern[:-2] + '$'
       try:
           return bool(re.match(pattern, filename))
       except re.error:
           return original_applies_to(self, filename)
   return original_applies_to(self, filename)

RuleLine.applies_to = patched_applies_to
# Monkey patch ends

def chunk_documents(
    documents: Iterable[str],
    chunk_token_threshold: int,
    overlap: int,
    word_token_rate: float = 0.75,
    tokenizer: Optional[Callable[[str], List[str]]] = None,
) -> Generator[str, None, None]:
    """
    Efficiently chunks documents into token-limited sections with overlap between chunks.

    Args:
        documents: Iterable of document strings
        chunk_token_threshold: Maximum tokens per chunk
        overlap: Number of tokens to overlap between chunks
        word_token_rate: Token estimate per word when not using a tokenizer
        tokenizer: Function that splits text into tokens (if available)

    Yields:
        Text chunks as strings
    """
    token_queue = deque()
    contribution_queue = deque()
    current_token_count = 0.0

    for doc in documents:
        # Tokenize document
        if tokenizer:
            tokens = tokenizer(doc)
            contributions = [1.0] * len(tokens)
        else:
            tokens = doc.split()
            contributions = [word_token_rate] * len(tokens)

        # Add to processing queues
        token_queue.extend(tokens)
        contribution_queue.extend(contributions)
        current_token_count += sum(contributions)

        # Process full chunks
        while current_token_count >= chunk_token_threshold:
            # Find chunk split point
            chunk_tokens = []
            chunk_contrib = []
            chunk_total = 0.0
            
            # Build chunk up to threshold
            while contribution_queue:
                next_contrib = contribution_queue[0]
                if chunk_total + next_contrib > chunk_token_threshold:
                    break
                
                chunk_total += next_contrib
                chunk_contrib.append(contribution_queue.popleft())
                chunk_tokens.append(token_queue.popleft())

            # Handle edge case where first token exceeds threshold
            if not chunk_contrib:  # Single token exceeds threshold
                chunk_contrib.append(contribution_queue.popleft())
                chunk_tokens.append(token_queue.popleft())

            # Calculate overlap
            overlap_total = 0.0
            overlap_idx = 0
            for contrib in reversed(chunk_contrib):
                if overlap_total + contrib > overlap:
                    break
                overlap_total += contrib
                overlap_idx += 1

            # Prepend overlap to queues
            if overlap_idx > 0:
                overlap_tokens = chunk_tokens[-overlap_idx:]
                overlap_contrib = chunk_contrib[-overlap_idx:]
                
                token_queue.extendleft(reversed(overlap_tokens))
                contribution_queue.extendleft(reversed(overlap_contrib))
                current_token_count += overlap_total

            # Update current token count and yield chunk
            current_token_count -= sum(chunk_contrib)
            yield " ".join(chunk_tokens[:len(chunk_tokens)-overlap_idx] if overlap_idx else chunk_tokens)

    # Yield remaining tokens
    if token_queue:
        yield " ".join(token_queue)

def merge_chunks(
    docs: Sequence[str], 
    target_size: int,
    overlap: int = 0,
    word_token_ratio: float = 1.0,
    splitter: Callable = None
) -> List[str]:
    """
    Merges a sequence of documents into chunks based on a target token count, with optional overlap.
    
    Each document is split into tokens using the provided splitter function (defaults to str.split). Tokens are distributed into chunks aiming for the specified target size, with optional overlapping tokens between consecutive chunks. Returns a list of non-empty merged chunks as strings.
    
    Args:
        docs: Sequence of input document strings to be merged.
        target_size: Target number of tokens per chunk.
        overlap: Number of tokens to overlap between consecutive chunks.
        word_token_ratio: Multiplier to estimate token count from word count.
        splitter: Callable used to split each document into tokens.
    
    Returns:
        List of merged document chunks as strings, each not exceeding the target token size.
    """
    # Pre-tokenize all docs and store token counts
    splitter = splitter or str.split
    token_counts = array('I')
    all_tokens: List[List[str]] = []
    total_tokens = 0
    
    for doc in docs:
        tokens = splitter(doc)
        count = int(len(tokens) * word_token_ratio)
        if count:  # Skip empty docs
            token_counts.append(count)
            all_tokens.append(tokens)
            total_tokens += count
    
    if not total_tokens:
        return []

    # Pre-allocate chunks
    num_chunks = max(1, (total_tokens + target_size - 1) // target_size)
    chunks: List[List[str]] = [[] for _ in range(num_chunks)]
    
    curr_chunk = 0
    curr_size = 0
    
    # Distribute tokens
    for tokens in chain.from_iterable(all_tokens):
        if curr_size >= target_size and curr_chunk < num_chunks - 1:
            if overlap > 0:
                overlap_tokens = chunks[curr_chunk][-overlap:]
                curr_chunk += 1
                chunks[curr_chunk].extend(overlap_tokens)
                curr_size = len(overlap_tokens)
            else:
                curr_chunk += 1
                curr_size = 0
                
        chunks[curr_chunk].append(tokens)
        curr_size += 1

    # Return only non-empty chunks
    return [' '.join(chunk) for chunk in chunks if chunk]


class VersionManager:
    def __init__(self):
        self.home_dir = Path.home() / ".crawl4ai"
        self.version_file = self.home_dir / "version.txt"

    def get_installed_version(self):
        """Get the version recorded in home directory"""
        if not self.version_file.exists():
            return None
        try:
            return version.parse(self.version_file.read_text().strip())
        except Exception as _ex:
            return None

    def update_version(self):
        """Update the version file to current library version"""
        self.version_file.write_text(__version__.__version__)

    def needs_update(self):
        """Check if database needs update based on version"""
        installed = self.get_installed_version()
        current = version.parse(__version__.__version__)
        return installed is None or installed < current


class RobotsParser:
    # Default 7 days cache TTL
    CACHE_TTL = 7 * 24 * 60 * 60

    def __init__(self, cache_dir=None, cache_ttl=None):
        self.cache_dir = cache_dir or os.path.join(get_home_folder(), ".crawl4ai", "robots")
        self.cache_ttl = cache_ttl or self.CACHE_TTL
        os.makedirs(self.cache_dir, exist_ok=True)
        self.db_path = os.path.join(self.cache_dir, "robots_cache.db")
        self._init_db()

    def _init_db(self):
        # Use WAL mode for better concurrency and performance
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS robots_cache (
                    domain TEXT PRIMARY KEY,
                    rules TEXT NOT NULL,
                    fetch_time INTEGER NOT NULL,
                    hash TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_domain ON robots_cache(domain)")

    def _get_cached_rules(self, domain: str) -> tuple[str, bool]:
        """Get cached rules. Returns (rules, is_fresh)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT rules, fetch_time, hash FROM robots_cache WHERE domain = ?", 
                (domain,)
            )
            result = cursor.fetchone()
            
            if not result:
                return None, False
                
            rules, fetch_time, _ = result
            # Check if cache is still fresh based on TTL
            return rules, (time.time() - fetch_time) < self.cache_ttl

    def _cache_rules(self, domain: str, content: str):
        """Cache robots.txt content with hash for change detection"""
        hash_val = hashlib.md5(content.encode()).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            # Check if content actually changed
            cursor = conn.execute(
                "SELECT hash FROM robots_cache WHERE domain = ?", 
                (domain,)
            )
            result = cursor.fetchone()
            
            # Only update if hash changed or no previous entry
            if not result or result[0] != hash_val:
                conn.execute(
                    """INSERT OR REPLACE INTO robots_cache 
                       (domain, rules, fetch_time, hash) 
                       VALUES (?, ?, ?, ?)""",
                    (domain, content, int(time.time()), hash_val)
                )

    async def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """
        Check if URL can be fetched according to robots.txt rules.
        
        Args:
            url: The URL to check
            user_agent: User agent string to check against (default: "*")
            
        Returns:
            bool: True if allowed, False if disallowed by robots.txt
        """
        # Handle empty/invalid URLs
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            if not domain:
                return True
        except Exception as _ex:
            return True

        # Fast path - check cache first
        rules, is_fresh = self._get_cached_rules(domain)
        
        # If rules not found or stale, fetch new ones
        if not is_fresh:
            try:
                # Ensure we use the same scheme as the input URL
                scheme = parsed.scheme or 'http'
                robots_url = f"{scheme}://{domain}/robots.txt"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(robots_url, timeout=2, ssl=False) as response:
                        if response.status == 200:
                            rules = await response.text()
                            self._cache_rules(domain, rules)
                        else:
                            return True
            except Exception as _ex:
                # On any error (timeout, connection failed, etc), allow access
                return True

        if not rules:
            return True

        # Create parser for this check
        parser = RobotFileParser() 
        parser.parse(rules.splitlines())
        
        # If parser can't read rules, allow access
        if not parser.mtime():
            return True
            
        return parser.can_fetch(user_agent, url)

    def clear_cache(self):
        """Clear all cached robots.txt entries"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM robots_cache")

    def clear_expired(self):
        """Remove only expired entries from cache"""
        with sqlite3.connect(self.db_path) as conn:
            expire_time = int(time.time()) - self.cache_ttl
            conn.execute("DELETE FROM robots_cache WHERE fetch_time < ?", (expire_time,))
      

class InvalidCSSSelectorError(Exception):
    pass


SPLITS = bytearray([
    # Control chars (0-31) + space (32)
    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
    # Special chars (33-47): ! " # $ % & ' ( ) * + , - . /
    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
    # Numbers (48-57): Treat as non-splits
    0,0,0,0,0,0,0,0,0,0,
    # More special chars (58-64): : ; < = > ? @
    1,1,1,1,1,1,1,
    # Uppercase (65-90): Keep
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    # More special chars (91-96): [ \ ] ^ _ `
    1,1,1,1,1,1,
    # Lowercase (97-122): Keep
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    # Special chars (123-126): { | } ~
    1,1,1,1,
    # Extended ASCII
    *([1] * 128)
])

# Additional split chars for HTML/code
HTML_CODE_CHARS = {
    # HTML specific
    '•', '►', '▼', '©', '®', '™', '→', '⇒', '≈', '≤', '≥',
    # Programming symbols  
    '+=', '-=', '*=', '/=', '=>', '<=>', '!=', '==', '===',
    '++', '--', '<<', '>>', '&&', '||', '??', '?:', '?.', 
    # Common Unicode
    '…', '"', '"', ''', ''', '«', '»', '—', '–',
    # Additional splits
    '+', '=', '~', '@', '#', '$', '%', '^', '&', '*',
    '(', ')', '{', '}', '[', ']', '|', '\\', '/', '`',
    '<', '>', ',', '.', '?', '!', ':', ';', '-', '_'
}

def advanced_split(text: str) -> list[str]:
    result = []
    word = array('u')
    
    i = 0
    text_len = len(text)
    
    while i < text_len:
        char = text[i]
        o = ord(char)
        
        # Fast path for ASCII
        if o < 256 and SPLITS[o]:
            if word:
                result.append(word.tounicode())
                word = array('u')
        # Check for multi-char symbols
        elif i < text_len - 1:
            two_chars = char + text[i + 1]
            if two_chars in HTML_CODE_CHARS:
                if word:
                    result.append(word.tounicode())
                    word = array('u')
                i += 1  # Skip next char since we used it
            else:
                word.append(char)
        else:
            word.append(char)
        i += 1
            
    if word:
        result.append(word.tounicode())
        
    return result

def create_box_message(
    message: str,
    type: str = "info",
    width: int = 120,
    add_newlines: bool = True,
    double_line: bool = False,
) -> str:
    """
    Create a styled message box with colored borders and formatted text.

    How it works:
    1. Determines box style and colors based on the message type (e.g., info, warning).
    2. Wraps text to fit within the specified width.
    3. Constructs a box using characters (single or double lines) with appropriate formatting.
    4. Adds optional newlines before and after the box.

    Args:
        message (str): The message to display inside the box.
        type (str): Type of the message (e.g., "info", "warning", "error", "success"). Defaults to "info".
        width (int): Width of the box. Defaults to 120.
        add_newlines (bool): Whether to add newlines before and after the box. Defaults to True.
        double_line (bool): Whether to use double lines for the box border. Defaults to False.

    Returns:
        str: A formatted string containing the styled message box.
    """

    # Define border and text colors for different types
    styles = {
        "warning": ("yellow", "bright_yellow", "⚠"),
        "info": ("blue", "bright_blue", "ℹ"),
        "debug": ("lightblack", "bright_black", "⋯"),
        "success": ("green", "bright_green", "✓"),
        "error": ("red", "bright_red", "×"),
    }

    border_color, text_color, prefix = styles.get(type.lower(), styles["info"])

    # Define box characters based on line style
    box_chars = {
        "single": ("─", "│", "┌", "┐", "└", "┘"),
        "double": ("═", "║", "╔", "╗", "╚", "╝"),
    }
    line_style = "double" if double_line else "single"
    h_line, v_line, tl, tr, bl, br = box_chars[line_style]

    # Process lines with lighter text color
    formatted_lines = []
    raw_lines = message.split("\n")

    if raw_lines:
        first_line = f"{prefix} {raw_lines[0].strip()}"
        wrapped_first = textwrap.fill(first_line, width=width - 4)
        formatted_lines.extend(wrapped_first.split("\n"))

        for line in raw_lines[1:]:
            if line.strip():
                wrapped = textwrap.fill(f"  {line.strip()}", width=width - 4)
                formatted_lines.extend(wrapped.split("\n"))
            else:
                formatted_lines.append("")

    # Create the box with colored borders and lighter text
    horizontal_line = h_line * (width - 1)
    box = [
        f"[{border_color}]{tl}{horizontal_line}{tr}[/{border_color}]",
        *[
            f"[{border_color}]{v_line}[{text_color}] {line:<{width-2}}[/{text_color}][{border_color}]{v_line}[/{border_color}]"
            for line in formatted_lines
        ],
        f"[{border_color}]{bl}{horizontal_line}{br}[/{border_color}]",
    ]

    result = "\n".join(box)
    if add_newlines:
        result = f"\n{result}\n"

    return result


def calculate_semaphore_count():
    """
    Calculate the optimal semaphore count based on system resources.

    How it works:
    1. Determines the number of CPU cores and total system memory.
    2. Sets a base count as half of the available CPU cores.
    3. Limits the count based on memory, assuming 2GB per semaphore instance.
    4. Returns the minimum value between CPU and memory-based limits.

    Returns:
        int: The calculated semaphore count.
    """

    cpu_count = os.cpu_count()
    memory_gb = get_system_memory() / (1024**3)  # Convert to GB
    base_count = max(1, cpu_count // 2)
    memory_based_cap = int(memory_gb / 2)  # Assume 2GB per instance
    return min(base_count, memory_based_cap)


def get_system_memory():
    """
    Get the total system memory in bytes.

    How it works:
    1. Detects the operating system.
    2. Reads memory information from system-specific commands or files.
    3. Converts the memory to bytes for uniformity.

    Returns:
        int: The total system memory in bytes.

    Raises:
        OSError: If the operating system is unsupported.
    """

    system = platform.system()
    if system == "Linux":
        with open("/proc/meminfo", "r") as mem:
            for line in mem:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) * 1024  # Convert KB to bytes
    elif system == "Darwin":  # macOS
        import subprocess

        output = subprocess.check_output(["sysctl", "-n", "hw.memsize"]).decode("utf-8")
        return int(output.strip())
    elif system == "Windows":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        c_ulonglong = ctypes.c_ulonglong

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", c_ulonglong),
                ("ullAvailPhys", c_ulonglong),
                ("ullTotalPageFile", c_ulonglong),
                ("ullAvailPageFile", c_ulonglong),
                ("ullTotalVirtual", c_ulonglong),
                ("ullAvailVirtual", c_ulonglong),
                ("ullAvailExtendedVirtual", c_ulonglong),
            ]

        memoryStatus = MEMORYSTATUSEX()
        memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus))
        return memoryStatus.ullTotalPhys
    else:
        raise OSError("Unsupported operating system")


def get_home_folder():
    """
    Get or create the home folder for Crawl4AI configuration and cache.

    How it works:
    1. Uses environment variables or defaults to the user's home directory.
    2. Creates `.crawl4ai` and its subdirectories (`cache`, `models`) if they don't exist.
    3. Returns the path to the home folder.

    Returns:
        str: The path to the Crawl4AI home folder.
    """

    home_folder = os.path.join(
        os.getenv(
            "CRAWL4_AI_BASE_DIRECTORY",
            os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home()),
        ),
        ".crawl4ai",
    )
    os.makedirs(home_folder, exist_ok=True)
    os.makedirs(f"{home_folder}/cache", exist_ok=True)
    os.makedirs(f"{home_folder}/models", exist_ok=True)
    return home_folder

async def get_chromium_path(browser_type) -> str:
    """Returns the browser executable path using playwright's browser management.
    
    Uses playwright's built-in browser management to get the correct browser executable
    path regardless of platform. This ensures we're using the same browser version
    that playwright is tested with.
    
    Returns:
        str: Path to browser executable
    Raises:
        RuntimeError: If browser executable cannot be found
    """        
    browser_types = {
        "chromium": "chromium",
        "firefox": "firefox",
        "webkit": "webkit"
    }
    
    browser_type = browser_types.get(browser_type)
    if not browser_type:
        raise RuntimeError(f"Unsupported browser type: {browser_type}")

    # Check if a path has already been saved for this browser type
    home_folder = get_home_folder()
    path_file = os.path.join(home_folder, f"{browser_type.lower()}.path")
    if os.path.exists(path_file):
        with open(path_file, "r") as f:
            return f.read()

    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browsers = {
            'chromium': p.chromium,
            'firefox': p.firefox, 
            'webkit': p.webkit
        }
        
        if browser_type.lower() not in browsers:
            raise ValueError(
                f"Invalid browser type. Must be one of: {', '.join(browsers.keys())}"
            )
            
        # Save the path int the crawl4ai home folder
        home_folder = get_home_folder()
        browser_path = browsers[browser_type.lower()].executable_path
        if not browser_path:
            raise RuntimeError(f"Browser executable not found for type: {browser_type}")
        # Save the path in a text file with browser type name
        with open(os.path.join(home_folder, f"{browser_type.lower()}.path"), "w") as f:
            f.write(browser_path)
        
        return browser_path

def beautify_html(escaped_html):
    """
    Beautifies an escaped HTML string.

    Parameters:
    escaped_html (str): A string containing escaped HTML.

    Returns:
    str: A beautifully formatted HTML string.
    """
    # Unescape the HTML string
    unescaped_html = html.unescape(escaped_html)

    # Use BeautifulSoup to parse and prettify the HTML
    soup = BeautifulSoup(unescaped_html, "html.parser")
    pretty_html = soup.prettify()

    return pretty_html


def split_and_parse_json_objects(json_string):
    """
    Splits a JSON string which is a list of objects and tries to parse each object.

    Parameters:
    json_string (str): A string representation of a list of JSON objects, e.g., '[{...}, {...}, ...]'.

    Returns:
    tuple: A tuple containing two lists:
        - First list contains all successfully parsed JSON objects.
        - Second list contains the string representations of all segments that couldn't be parsed.
    """
    # Trim the leading '[' and trailing ']'
    if json_string.startswith("[") and json_string.endswith("]"):
        json_string = json_string[1:-1].strip()

    # Split the string into segments that look like individual JSON objects
    segments = []
    depth = 0
    start_index = 0

    for i, char in enumerate(json_string):
        if char == "{":
            if depth == 0:
                start_index = i
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                segments.append(json_string[start_index : i + 1])

    # Try parsing each segment
    parsed_objects = []
    unparsed_segments = []

    for segment in segments:
        try:
            obj = json.loads(segment)
            parsed_objects.append(obj)
        except json.JSONDecodeError:
            unparsed_segments.append(segment)

    return parsed_objects, unparsed_segments


def sanitize_html(html):
    """
    Sanitize an HTML string by escaping quotes.

    How it works:
    1. Replaces all unwanted and special characters with an empty string.
    2. Escapes double and single quotes for safe usage.

    Args:
        html (str): The HTML string to sanitize.

    Returns:
        str: The sanitized HTML string.
    """

    # Replace all unwanted and special characters with an empty string
    sanitized_html = html
    # sanitized_html = re.sub(r'[^\w\s.,;:!?=\[\]{}()<>\/\\\-"]', '', html)

    # Escape all double and single quotes
    sanitized_html = sanitized_html.replace('"', '\\"').replace("'", "\\'")

    return sanitized_html


def sanitize_input_encode(text: str) -> str:
    """Sanitize input to handle potential encoding issues."""
    try:
        try:
            if not text:
                return ""
            # Attempt to encode and decode as UTF-8 to handle potential encoding issues
            return text.encode("utf-8", errors="ignore").decode("utf-8")
        except UnicodeEncodeError as e:
            print(
                f"Warning: Encoding issue detected. Some characters may be lost. Error: {e}"
            )
            # Fall back to ASCII if UTF-8 fails
            return text.encode("ascii", errors="ignore").decode("ascii")
    except Exception as e:
        raise ValueError(f"Error sanitizing input: {str(e)}") from e


def escape_json_string(s):
    """
    Escapes characters in a string to be JSON safe.

    Parameters:
    s (str): The input string to be escaped.

    Returns:
    str: The escaped string, safe for JSON encoding.
    """
    # Replace problematic backslash first
    s = s.replace("\\", "\\\\")

    # Replace the double quote
    s = s.replace('"', '\\"')

    # Escape control characters
    s = s.replace("\b", "\\b")
    s = s.replace("\f", "\\f")
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    s = s.replace("\t", "\\t")

    # Additional problematic characters
    # Unicode control characters
    s = re.sub(r"[\x00-\x1f\x7f-\x9f]", lambda x: "\\u{:04x}".format(ord(x.group())), s)

    return s


def replace_inline_tags(soup, tags, only_text=False):
    """
    Replace inline HTML tags with Markdown-style equivalents.

    How it works:
    1. Maps specific tags (e.g., <b>, <i>) to Markdown syntax.
    2. Finds and replaces all occurrences of these tags in the provided BeautifulSoup object.
    3. Optionally replaces tags with their text content only.

    Args:
        soup (BeautifulSoup): Parsed HTML content.
        tags (List[str]): List of tags to replace.
        only_text (bool): Whether to replace tags with plain text. Defaults to False.

    Returns:
        BeautifulSoup: Updated BeautifulSoup object with replaced tags.
    """

    tag_replacements = {
        "b": lambda tag: f"**{tag.text}**",
        "i": lambda tag: f"*{tag.text}*",
        "u": lambda tag: f"__{tag.text}__",
        "span": lambda tag: f"{tag.text}",
        "del": lambda tag: f"~~{tag.text}~~",
        "ins": lambda tag: f"++{tag.text}++",
        "sub": lambda tag: f"~{tag.text}~",
        "sup": lambda tag: f"^^{tag.text}^^",
        "strong": lambda tag: f"**{tag.text}**",
        "em": lambda tag: f"*{tag.text}*",
        "code": lambda tag: f"`{tag.text}`",
        "kbd": lambda tag: f"`{tag.text}`",
        "var": lambda tag: f"_{tag.text}_",
        "s": lambda tag: f"~~{tag.text}~~",
        "q": lambda tag: f'"{tag.text}"',
        "abbr": lambda tag: f"{tag.text} ({tag.get('title', '')})",
        "cite": lambda tag: f"_{tag.text}_",
        "dfn": lambda tag: f"_{tag.text}_",
        "time": lambda tag: f"{tag.text}",
        "small": lambda tag: f"<small>{tag.text}</small>",
        "mark": lambda tag: f"=={tag.text}==",
    }

    replacement_data = [
        (tag, tag_replacements.get(tag, lambda t: t.text)) for tag in tags
    ]

    for tag_name, replacement_func in replacement_data:
        for tag in soup.find_all(tag_name):
            replacement_text = tag.text if only_text else replacement_func(tag)
            tag.replace_with(replacement_text)

    return soup

    # for tag_name in tags:
    #     for tag in soup.find_all(tag_name):
    #         if not only_text:
    #             replacement_text = tag_replacements.get(tag_name, lambda t: t.text)(tag)
    #             tag.replace_with(replacement_text)
    #         else:
    #             tag.replace_with(tag.text)

    # return soup


def get_content_of_website(
    url, html, word_count_threshold=MIN_WORD_THRESHOLD, css_selector=None, **kwargs
):
    """
    Extract structured content, media, and links from website HTML.

    How it works:
    1. Parses the HTML content using BeautifulSoup.
    2. Extracts internal/external links and media (images, videos, audios).
    3. Cleans the content by removing unwanted tags and attributes.
    4. Converts cleaned HTML to Markdown.
    5. Collects metadata and returns the extracted information.

    Args:
        url (str): The website URL.
        html (str): The HTML content of the website.
        word_count_threshold (int): Minimum word count for content inclusion. Defaults to MIN_WORD_THRESHOLD.
        css_selector (Optional[str]): CSS selector to extract specific content. Defaults to None.

    Returns:
        Dict[str, Any]: Extracted content including Markdown, cleaned HTML, media, links, and metadata.
    """

    try:
        if not html:
            return None
        # Parse HTML content with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Get the content within the <body> tag
        body = soup.body

        # If css_selector is provided, extract content based on the selector
        if css_selector:
            selected_elements = body.select(css_selector)
            if not selected_elements:
                raise InvalidCSSSelectorError(
                    f"Invalid CSS selector , No elements found for CSS selector: {css_selector}"
                )
            div_tag = soup.new_tag("div")
            for el in selected_elements:
                div_tag.append(el)
            body = div_tag

        links = {"internal": [], "external": []}

        # Extract all internal and external links
        for a in body.find_all("a", href=True):
            href = a["href"]
            url_base = url.split("/")[2]
            if href.startswith("http") and url_base not in href:
                links["external"].append({"href": href, "text": a.get_text()})
            else:
                links["internal"].append({"href": href, "text": a.get_text()})

        # Remove script, style, and other tags that don't carry useful content from body
        for tag in body.find_all(["script", "style", "link", "meta", "noscript"]):
            tag.decompose()

        # Remove all attributes from remaining tags in body, except for img tags
        for tag in body.find_all():
            if tag.name != "img":
                tag.attrs = {}

        # Extract all img tgas int0 [{src: '', alt: ''}]
        media = {"images": [], "videos": [], "audios": []}
        for img in body.find_all("img"):
            media["images"].append(
                {"src": img.get("src"), "alt": img.get("alt"), "type": "image"}
            )

        # Extract all video tags into [{src: '', alt: ''}]
        for video in body.find_all("video"):
            media["videos"].append(
                {"src": video.get("src"), "alt": video.get("alt"), "type": "video"}
            )

        # Extract all audio tags into [{src: '', alt: ''}]
        for audio in body.find_all("audio"):
            media["audios"].append(
                {"src": audio.get("src"), "alt": audio.get("alt"), "type": "audio"}
            )

        # Replace images with their alt text or remove them if no alt text is available
        for img in body.find_all("img"):
            alt_text = img.get("alt")
            if alt_text:
                img.replace_with(soup.new_string(alt_text))
            else:
                img.decompose()

        # Create a function that replace content of all"pre" tag with its inner text
        def replace_pre_tags_with_text(node):
            for child in node.find_all("pre"):
                # set child inner html to its text
                child.string = child.get_text()
            return node

        # Replace all "pre" tags with their inner text
        body = replace_pre_tags_with_text(body)

        # Replace inline tags with their text content
        body = replace_inline_tags(
            body,
            [
                "b",
                "i",
                "u",
                "span",
                "del",
                "ins",
                "sub",
                "sup",
                "strong",
                "em",
                "code",
                "kbd",
                "var",
                "s",
                "q",
                "abbr",
                "cite",
                "dfn",
                "time",
                "small",
                "mark",
            ],
            only_text=kwargs.get("only_text", False),
        )

        # Recursively remove empty elements, their parent elements, and elements with word count below threshold
        def remove_empty_and_low_word_count_elements(node, word_count_threshold):
            for child in node.contents:
                if isinstance(child, element.Tag):
                    remove_empty_and_low_word_count_elements(
                        child, word_count_threshold
                    )
                    word_count = len(child.get_text(strip=True).split())
                    if (
                        len(child.contents) == 0 and not child.get_text(strip=True)
                    ) or word_count < word_count_threshold:
                        child.decompose()
            return node

        body = remove_empty_and_low_word_count_elements(body, word_count_threshold)

        def remove_small_text_tags(
            body: Tag, word_count_threshold: int = MIN_WORD_THRESHOLD
        ):
            # We'll use a list to collect all tags that don't meet the word count requirement
            tags_to_remove = []

            # Traverse all tags in the body
            for tag in body.find_all(True):  # True here means all tags
                # Check if the tag contains text and if it's not just whitespace
                if tag.string and tag.string.strip():
                    # Split the text by spaces and count the words
                    word_count = len(tag.string.strip().split())
                    # If the word count is less than the threshold, mark the tag for removal
                    if word_count < word_count_threshold:
                        tags_to_remove.append(tag)

            # Remove all marked tags from the tree
            for tag in tags_to_remove:
                tag.decompose()  # or tag.extract() to remove and get the element

            return body

        # Remove small text tags
        body = remove_small_text_tags(body, word_count_threshold)

        def is_empty_or_whitespace(tag: Tag):
            if isinstance(tag, NavigableString):
                return not tag.strip()
            # Check if the tag itself is empty or all its children are empty/whitespace
            if not tag.contents:
                return True
            return all(is_empty_or_whitespace(child) for child in tag.contents)

        def remove_empty_tags(body: Tag):
            # Continue processing until no more changes are made
            changes = True
            while changes:
                changes = False
                # Collect all tags that are empty or contain only whitespace
                empty_tags = [
                    tag for tag in body.find_all(True) if is_empty_or_whitespace(tag)
                ]
                for tag in empty_tags:
                    # If a tag is empty, decompose it
                    tag.decompose()
                    changes = True  # Mark that a change was made

            return body

        # Remove empty tags
        body = remove_empty_tags(body)

        # Flatten nested elements with only one child of the same type
        def flatten_nested_elements(node):
            for child in node.contents:
                if isinstance(child, element.Tag):
                    flatten_nested_elements(child)
                    if (
                        len(child.contents) == 1
                        and child.contents[0].name == child.name
                    ):
                        # print('Flattening:', child.name)
                        child_content = child.contents[0]
                        child.replace_with(child_content)

            return node

        body = flatten_nested_elements(body)

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Remove consecutive empty newlines and replace multiple spaces with a single space
        cleaned_html = str(body).replace("\n\n", "\n").replace("  ", " ")

        # Sanitize the cleaned HTML content
        cleaned_html = sanitize_html(cleaned_html)
        # sanitized_html = escape_json_string(cleaned_html)

        # Convert cleaned HTML to Markdown
        h = html2text.HTML2Text()
        h = CustomHTML2Text()
        h.ignore_links = True
        markdown = h.handle(cleaned_html)
        markdown = markdown.replace("    ```", "```")

        try:
            meta = extract_metadata(html, soup)
        except Exception as e:
            print("Error extracting metadata:", str(e))
            meta = {}

        # Return the Markdown content
        return {
            "markdown": markdown,
            "cleaned_html": cleaned_html,
            "success": True,
            "media": media,
            "links": links,
            "metadata": meta,
        }

    except Exception as e:
        print("Error processing HTML content:", str(e))
        raise InvalidCSSSelectorError(f"Invalid CSS selector: {css_selector}") from e


def get_content_of_website_optimized(
    url: str,
    html: str,
    word_count_threshold: int = MIN_WORD_THRESHOLD,
    css_selector: str = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Extracts and cleans content from website HTML, optimizing for useful media and contextual information.
    
    Parses the provided HTML to extract internal and external links, filters and scores images for usefulness, gathers contextual descriptions for media, removes unwanted or low-value elements, and converts the cleaned HTML to Markdown. Also extracts metadata and returns all structured content in a dictionary.
    
    Args:
        url: The URL of the website being processed.
        html: The raw HTML content to extract from.
        word_count_threshold: Minimum word count for elements to be retained.
        css_selector: Optional CSS selector to restrict extraction to specific elements.
    
    Returns:
        A dictionary containing Markdown content, cleaned HTML, extraction success status, media and link lists, and metadata.
    
    Raises:
        InvalidCSSSelectorError: If a provided CSS selector does not match any elements.
    """
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    body = soup.body

    image_description_min_word_threshold = kwargs.get(
        "image_description_min_word_threshold", IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD
    )

    for tag in kwargs.get("excluded_tags", []) or []:
        for el in body.select(tag):
            el.decompose()

    if css_selector:
        selected_elements = body.select(css_selector)
        if not selected_elements:
            raise InvalidCSSSelectorError(
                f"Invalid CSS selector, No elements found for CSS selector: {css_selector}"
            )
        body = soup.new_tag("div")
        for el in selected_elements:
            body.append(el)

    links = {"internal": [], "external": []}
    media = {"images": [], "videos": [], "audios": []}

    # Extract meaningful text for media files from closest parent
    def find_closest_parent_with_useful_text(tag):
        current_tag = tag
        while current_tag:
            current_tag = current_tag.parent
            # Get the text content from the parent tag
            if current_tag:
                text_content = current_tag.get_text(separator=" ", strip=True)
                # Check if the text content has at least word_count_threshold
                if len(text_content.split()) >= image_description_min_word_threshold:
                    return text_content
        return None

    def process_image(img, url, index, total_images):
        # Check if an image has valid display and inside undesired html elements
        """
        Processes an HTML image element to determine its relevance and extract metadata.
        
        Evaluates an image's visibility, context, and usefulness based on its attributes and parent elements. If the image passes validation and exceeds a usefulness score threshold, returns a dictionary with its source, alt text, contextual description, score, and type. Otherwise, returns None.
        
        Args:
            img: The BeautifulSoup image tag to process.
            url: The base URL of the page containing the image.
            index: The index of the image in the list of images on the page.
            total_images: The total number of images on the page.
        
        Returns:
            A dictionary with image metadata if the image is considered useful, or None otherwise.
        """
        def is_valid_image(img, parent, parent_classes):
            style = img.get("style", "")
            src = img.get("src", "")
            classes_to_check = ["button", "icon", "logo"]
            tags_to_check = ["button", "input"]
            return all(
                [
                    "display:none" not in style,
                    src,
                    not any(
                        s in var
                        for var in [src, img.get("alt", ""), *parent_classes]
                        for s in classes_to_check
                    ),
                    parent.name not in tags_to_check,
                ]
            )

        # Score an image for it's usefulness
        def score_image_for_usefulness(img, base_url, index, images_count):
            # Function to parse image height/width value and units
            """
            Scores an HTML image element for usefulness based on size, format, attributes, and position.
            
            The function evaluates an image's dimensions, file format, alt text, and its position among all images on the page to assign a usefulness score. Higher scores indicate images that are likely more relevant or informative for content extraction or summarization.
            
            Args:
                img: The HTML image element to score.
                base_url: The base URL used to resolve relative image sources.
                index: The position of the image in the list of images on the page (zero-based).
                images_count: The total number of images on the page.
            
            Returns:
                An integer usefulness score for the image.
            """
            def parse_dimension(dimension):
                if dimension:
                    match = re.match(r"(\d+)(\D*)", dimension)
                    if match:
                        number = int(match.group(1))
                        unit = (
                            match.group(2) or "px"
                        )  # Default unit is 'px' if not specified
                        return number, unit
                return None, None

            # Fetch image file metadata to extract size and extension
            def fetch_image_file_size(img, base_url):
                # If src is relative path construct full URL, if not it may be CDN URL
                """
                Fetches the file size of an image by sending a HEAD request to its URL.
                
                Args:
                    img: A BeautifulSoup tag representing the image element.
                    base_url: The base URL to resolve relative image sources.
                
                Returns:
                    The value of the "Content-Length" header as a string if available, otherwise None.
                """
                img_url = urljoin(base_url, img.get("src"))
                try:
                    response = requests.head(img_url)
                    if response.status_code == 200:
                        return response.headers.get("Content-Length", None)
                    else:
                        print(f"Failed to retrieve file size for {img_url}")
                        return None
                except InvalidSchema:
                    return None

            image_height = img.get("height")
            height_value, height_unit = parse_dimension(image_height)
            image_width = img.get("width")
            width_value, width_unit = parse_dimension(image_width)
            image_size = 0  # int(fetch_image_file_size(img,base_url) or 0)
            image_format = os.path.splitext(img.get("src", ""))[1].lower()
            # Remove . from format
            image_format = image_format.strip(".")
            score = 0
            if height_value:
                if height_unit == "px" and height_value > 150:
                    score += 1
                if height_unit in ["%", "vh", "vmin", "vmax"] and height_value > 30:
                    score += 1
            if width_value:
                if width_unit == "px" and width_value > 150:
                    score += 1
                if width_unit in ["%", "vh", "vmin", "vmax"] and width_value > 30:
                    score += 1
            if image_size > 10000:
                score += 1
            if img.get("alt") != "":
                score += 1
            if any(image_format == format for format in ["jpg", "png", "webp"]):
                score += 1
            if index / images_count < 0.5:
                score += 1
            return score

        if not is_valid_image(img, img.parent, img.parent.get("class", [])):
            return None
        score = score_image_for_usefulness(img, url, index, total_images)
        if score <= IMAGE_SCORE_THRESHOLD:
            return None
        return {
            "src": img.get("src", "").replace('\\"', '"').strip(),
            "alt": img.get("alt", ""),
            "desc": find_closest_parent_with_useful_text(img),
            "score": score,
            "type": "image",
        }

    def process_element(element: element.PageElement) -> bool:
        try:
            if isinstance(element, NavigableString):
                if isinstance(element, Comment):
                    element.extract()
                return False

            if element.name in ["script", "style", "link", "meta", "noscript"]:
                element.decompose()
                return False

            keep_element = False

            if element.name == "a" and element.get("href"):
                href = element["href"]
                url_base = url.split("/")[2]
                link_data = {"href": href, "text": element.get_text()}
                if href.startswith("http") and url_base not in href:
                    links["external"].append(link_data)
                else:
                    links["internal"].append(link_data)
                keep_element = True

            elif element.name == "img":
                return True  # Always keep image elements

            elif element.name in ["video", "audio"]:
                media[f"{element.name}s"].append(
                    {
                        "src": element.get("src"),
                        "alt": element.get("alt"),
                        "type": element.name,
                        "description": find_closest_parent_with_useful_text(element),
                    }
                )
                source_tags = element.find_all("source")
                for source_tag in source_tags:
                    media[f"{element.name}s"].append(
                        {
                            "src": source_tag.get("src"),
                            "alt": element.get("alt"),
                            "type": element.name,
                            "description": find_closest_parent_with_useful_text(
                                element
                            ),
                        }
                    )
                return True  # Always keep video and audio elements

            if element.name != "pre":
                if element.name in [
                    "b",
                    "i",
                    "u",
                    "span",
                    "del",
                    "ins",
                    "sub",
                    "sup",
                    "strong",
                    "em",
                    "code",
                    "kbd",
                    "var",
                    "s",
                    "q",
                    "abbr",
                    "cite",
                    "dfn",
                    "time",
                    "small",
                    "mark",
                ]:
                    if kwargs.get("only_text", False):
                        element.replace_with(element.get_text())
                    else:
                        element.unwrap()
                elif element.name != "img":
                    element.attrs = {}

            # Process children
            for child in list(element.children):
                if isinstance(child, NavigableString) and not isinstance(
                    child, Comment
                ):
                    if len(child.strip()) > 0:
                        keep_element = True
                else:
                    if process_element(child):
                        keep_element = True

            # Check word count
            if not keep_element:
                word_count = len(element.get_text(strip=True).split())
                keep_element = word_count >= word_count_threshold

            if not keep_element:
                element.decompose()

            return keep_element
        except Exception as e:
            print("Error processing element:", str(e))
            return False

    # process images by filtering and extracting contextual text from the page
    imgs = body.find_all("img")
    media["images"] = [
        result
        for result in (
            process_image(img, url, i, len(imgs)) for i, img in enumerate(imgs)
        )
        if result is not None
    ]

    process_element(body)

    def flatten_nested_elements(node):
        if isinstance(node, NavigableString):
            return node
        if (
            len(node.contents) == 1
            and isinstance(node.contents[0], element.Tag)
            and node.contents[0].name == node.name
        ):
            return flatten_nested_elements(node.contents[0])
        node.contents = [flatten_nested_elements(child) for child in node.contents]
        return node

    body = flatten_nested_elements(body)
    base64_pattern = re.compile(r'data:image/[^;]+;base64,([^"]+)')
    for img in imgs:
        try:
            src = img.get("src", "")
            if base64_pattern.match(src):
                img["src"] = base64_pattern.sub("", src)
        except Exception as _ex:
            pass

    cleaned_html = str(body).replace("\n\n", "\n").replace("  ", " ")
    cleaned_html = sanitize_html(cleaned_html)

    h = CustomHTML2Text()
    h.ignore_links = True
    markdown = h.handle(cleaned_html)
    markdown = markdown.replace("    ```", "```")

    try:
        meta = extract_metadata(html, soup)
    except Exception as e:
        print("Error extracting metadata:", str(e))
        meta = {}

    return {
        "markdown": markdown,
        "cleaned_html": cleaned_html,
        "success": True,
        "media": media,
        "links": links,
        "metadata": meta,
    }


def extract_metadata_using_lxml(html, doc=None):
    """
    Extract metadata from HTML using lxml for better performance.
    """
    metadata = {}

    if not html and doc is None:
        return {}

    if doc is None:
        try:
            doc = lxml.html.document_fromstring(html)
        except Exception:
            return {}

    # Use XPath to find head element
    head = doc.xpath("//head")
    if not head:
        return metadata

    head = head[0]

    # Title - using XPath
    title = head.xpath(".//title/text()")
    metadata["title"] = title[0].strip() if title else None

    # Meta description - using XPath with multiple attribute conditions
    description = head.xpath('.//meta[@name="description"]/@content')
    metadata["description"] = description[0].strip() if description else None

    # Meta keywords
    keywords = head.xpath('.//meta[@name="keywords"]/@content')
    metadata["keywords"] = keywords[0].strip() if keywords else None

    # Meta author
    author = head.xpath('.//meta[@name="author"]/@content')
    metadata["author"] = author[0].strip() if author else None

    # Open Graph metadata - using starts-with() for performance
    og_tags = head.xpath('.//meta[starts-with(@property, "og:")]')
    for tag in og_tags:
        property_name = tag.get("property", "").strip()
        content = tag.get("content", "").strip()
        if property_name and content:
            metadata[property_name] = content

    # Twitter Card metadata
    twitter_tags = head.xpath('.//meta[starts-with(@name, "twitter:")]')
    for tag in twitter_tags:
        property_name = tag.get("name", "").strip()
        content = tag.get("content", "").strip()
        if property_name and content:
            metadata[property_name] = content
   
   # Article metadata
    article_tags = head.xpath('.//meta[starts-with(@property, "article:")]')
    for tag in article_tags:
        property_name = tag.get("property", "").strip()
        content = tag.get("content", "").strip()
        if property_name and content:
            metadata[property_name] = content

    return metadata


def extract_metadata(html, soup=None):
    """
    Extract optimized content, media, and links from website HTML.

    How it works:
    1. Similar to `get_content_of_website`, but optimized for performance.
    2. Filters and scores images for usefulness.
    3. Extracts contextual descriptions for media files.
    4. Handles excluded tags and CSS selectors.
    5. Cleans HTML and converts it to Markdown.

    Args:
        url (str): The website URL.
        html (str): The HTML content of the website.
        word_count_threshold (int): Minimum word count for content inclusion. Defaults to MIN_WORD_THRESHOLD.
        css_selector (Optional[str]): CSS selector to extract specific content. Defaults to None.
        **kwargs: Additional options for customization.

    Returns:
        Dict[str, Any]: Extracted content including Markdown, cleaned HTML, media, links, and metadata.
    """

    metadata = {}

    if not html and not soup:
        return {}

    if not soup:
        soup = BeautifulSoup(html, "lxml")

    head = soup.head
    if not head:
        return metadata

    # Title
    title_tag = head.find("title")
    metadata["title"] = (
        title_tag.string.strip() if title_tag and title_tag.string else None
    )

    # Meta description
    description_tag = head.find("meta", attrs={"name": "description"})
    metadata["description"] = (
        description_tag.get("content", "").strip() if description_tag else None
    )

    # Meta keywords
    keywords_tag = head.find("meta", attrs={"name": "keywords"})
    metadata["keywords"] = (
        keywords_tag.get("content", "").strip() if keywords_tag else None
    )

    # Meta author
    author_tag = head.find("meta", attrs={"name": "author"})
    metadata["author"] = author_tag.get("content", "").strip() if author_tag else None

    # Open Graph metadata
    og_tags = head.find_all("meta", attrs={"property": re.compile(r"^og:")})
    for tag in og_tags:
        property_name = tag.get("property", "").strip()
        content = tag.get("content", "").strip()
        if property_name and content:
            metadata[property_name] = content

    # Twitter Card metadata
    twitter_tags = head.find_all("meta", attrs={"name": re.compile(r"^twitter:")})
    for tag in twitter_tags:
        property_name = tag.get("name", "").strip()
        content = tag.get("content", "").strip()
        if property_name and content:
            metadata[property_name] = content
    
    # Article metadata
    article_tags = head.find_all("meta", attrs={"property": re.compile(r"^article:")})
    for tag in article_tags:
        property_name = tag.get("property", "").strip()
        content = tag.get("content", "").strip()
        if property_name and content:
            metadata[property_name] = content
    
    return metadata


def extract_xml_tags(string):
    """
    Extracts XML tags from a string.

    Args:
        string (str): The input string containing XML tags.

    Returns:
        List[str]: A list of XML tags extracted from the input string.
    """
    tags = re.findall(r"<(\w+)>", string)
    return list(set(tags))


def extract_xml_data_legacy(tags, string):
    """
    Extract data for specified XML tags from a string.

    How it works:
    1. Searches the string for each tag using regex.
    2. Extracts the content within the tags.
    3. Returns a dictionary of tag-content pairs.

    Args:
        tags (List[str]): The list of XML tags to extract.
        string (str): The input string containing XML data.

    Returns:
        Dict[str, str]: A dictionary with tag names as keys and extracted content as values.
    """

    data = {}

    for tag in tags:
        pattern = f"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, string, re.DOTALL)
        if match:
            data[tag] = match.group(1).strip()
        else:
            data[tag] = ""

    return data

def extract_xml_data(tags, string):
    """
    Extract data for specified XML tags from a string, returning the longest content for each tag.

    How it works:
    1. Finds all occurrences of each tag in the string using regex.
    2. For each tag, selects the occurrence with the longest content.
    3. Returns a dictionary of tag-content pairs.

    Args:
        tags (List[str]): The list of XML tags to extract.
        string (str): The input string containing XML data.

    Returns:
        Dict[str, str]: A dictionary with tag names as keys and longest extracted content as values.
    """

    data = {}

    for tag in tags:
        pattern = f"<{tag}>(.*?)</{tag}>"
        matches = re.findall(pattern, string, re.DOTALL)
        
        if matches:
            # Find the longest content for this tag
            longest_content = max(matches, key=len).strip()
            data[tag] = longest_content
        else:
            data[tag] = ""

    return data


def perform_completion_with_backoff(
    provider,
    prompt_with_variables,
    api_token,
    json_response=False,
    base_url=None,
    **kwargs,
):
    """
    Perform an API completion request with exponential backoff.

    How it works:
    1. Sends a completion request to the API.
    2. Retries on rate-limit errors with exponential delays.
    3. Returns the API response or an error after all retries.

    Args:
        provider (str): The name of the API provider.
        prompt_with_variables (str): The input prompt for the completion request.
        api_token (str): The API token for authentication.
        json_response (bool): Whether to request a JSON response. Defaults to False.
        base_url (Optional[str]): The base URL for the API. Defaults to None.
        **kwargs: Additional arguments for the API request.

    Returns:
        dict: The API response or an error message after all retries.
    """

    from litellm import completion
    from litellm.exceptions import RateLimitError

    max_attempts = 3
    base_delay = 2  # Base delay in seconds, you can adjust this based on your needs

    extra_args = {"temperature": 0.01, "api_key": api_token, "base_url": base_url}
    if json_response:
        extra_args["response_format"] = {"type": "json_object"}

    if kwargs.get("extra_args"):
        extra_args.update(kwargs["extra_args"])

    for attempt in range(max_attempts):
        try:
            response = completion(
                model=provider,
                messages=[{"role": "user", "content": prompt_with_variables}],
                **extra_args,
            )
            return response  # Return the successful response
        except RateLimitError as e:
            print("Rate limit error:", str(e))

            # Check if we have exhausted our max attempts
            if attempt < max_attempts - 1:
                # Calculate the delay and wait
                delay = base_delay * (2**attempt)  # Exponential backoff formula
                print(f"Waiting for {delay} seconds before retrying...")
                time.sleep(delay)
            else:
                # Return an error response after exhausting all retries
                return [
                    {
                        "index": 0,
                        "tags": ["error"],
                        "content": ["Rate limit error. Please try again later."],
                    }
                ]
        except Exception as e:
            raise e  # Raise any other exceptions immediately
            # print("Error during completion request:", str(e))
            # error_message = e.message
            # return [
            #     {
            #         "index": 0,
            #         "tags": ["error"],
            #         "content": [
            #             f"Error during LLM completion request. {error_message}"
            #         ],
            #     }
            # ]


def extract_blocks(url, html, provider=DEFAULT_PROVIDER, api_token=None, base_url=None):
    """
    Extract content blocks from website HTML using an AI provider.

    How it works:
    1. Prepares a prompt by sanitizing and escaping HTML.
    2. Sends the prompt to an AI provider with optional retries.
    3. Parses the response to extract structured blocks or errors.

    Args:
        url (str): The website URL.
        html (str): The HTML content of the website.
        provider (str): The AI provider for content extraction. Defaults to DEFAULT_PROVIDER.
        api_token (Optional[str]): The API token for authentication. Defaults to None.
        base_url (Optional[str]): The base URL for the API. Defaults to None.

    Returns:
        List[dict]: A list of extracted content blocks.
    """

    # api_token = os.getenv('GROQ_API_KEY', None) if not api_token else api_token
    api_token = PROVIDER_MODELS.get(provider, None) if not api_token else api_token

    variable_values = {
        "URL": url,
        "HTML": escape_json_string(sanitize_html(html)),
    }

    prompt_with_variables = PROMPT_EXTRACT_BLOCKS
    for variable in variable_values:
        prompt_with_variables = prompt_with_variables.replace(
            "{" + variable + "}", variable_values[variable]
        )

    response = perform_completion_with_backoff(
        provider, prompt_with_variables, api_token, base_url=base_url
    )

    try:
        blocks = extract_xml_data(["blocks"], response.choices[0].message.content)[
            "blocks"
        ]
        blocks = json.loads(blocks)
        ## Add error: False to the blocks
        for block in blocks:
            block["error"] = False
    except Exception:
        parsed, unparsed = split_and_parse_json_objects(
            response.choices[0].message.content
        )
        blocks = parsed
        # Append all unparsed segments as onr error block and content is list of unparsed segments
        if unparsed:
            blocks.append(
                {"index": 0, "error": True, "tags": ["error"], "content": unparsed}
            )
    return blocks


def extract_blocks_batch(batch_data, provider="groq/llama3-70b-8192", api_token=None):
    """
    Extract content blocks from a batch of website HTMLs.

    How it works:
    1. Prepares prompts for each URL and HTML pair.
    2. Sends the prompts to the AI provider in a batch request.
    3. Parses the responses to extract structured blocks or errors.

    Args:
        batch_data (List[Tuple[str, str]]): A list of (URL, HTML) pairs.
        provider (str): The AI provider for content extraction. Defaults to "groq/llama3-70b-8192".
        api_token (Optional[str]): The API token for authentication. Defaults to None.

    Returns:
        List[dict]: A list of extracted content blocks from all batch items.
    """

    api_token = os.getenv("GROQ_API_KEY", None) if not api_token else api_token
    from litellm import batch_completion

    messages = []

    for url, _html in batch_data:
        variable_values = {
            "URL": url,
            "HTML": _html,
        }

        prompt_with_variables = PROMPT_EXTRACT_BLOCKS
        for variable in variable_values:
            prompt_with_variables = prompt_with_variables.replace(
                "{" + variable + "}", variable_values[variable]
            )

        messages.append([{"role": "user", "content": prompt_with_variables}])

    responses = batch_completion(model=provider, messages=messages, temperature=0.01)

    all_blocks = []
    for response in responses:
        try:
            blocks = extract_xml_data(["blocks"], response.choices[0].message.content)[
                "blocks"
            ]
            blocks = json.loads(blocks)

        except Exception:
            blocks = [
                {
                    "index": 0,
                    "tags": ["error"],
                    "content": [
                        "Error extracting blocks from the HTML content. Choose another provider/model or try again."
                    ],
                    "questions": [
                        "What went wrong during the block extraction process?"
                    ],
                }
            ]
        all_blocks.append(blocks)

    return sum(all_blocks, [])


def merge_chunks_based_on_token_threshold(chunks, token_threshold):
    """
    Merges small chunks into larger ones based on the total token threshold.

    :param chunks: List of text chunks to be merged based on token count.
    :param token_threshold: Max number of tokens for each merged chunk.
    :return: List of merged text chunks.
    """
    merged_sections = []
    current_chunk = []
    total_token_so_far = 0

    for chunk in chunks:
        chunk_token_count = (
            len(chunk.split()) * 1.3
        )  # Estimate token count with a factor
        if total_token_so_far + chunk_token_count < token_threshold:
            current_chunk.append(chunk)
            total_token_so_far += chunk_token_count
        else:
            if current_chunk:
                merged_sections.append("\n\n".join(current_chunk))
            current_chunk = [chunk]
            total_token_so_far = chunk_token_count

    # Add the last chunk if it exists
    if current_chunk:
        merged_sections.append("\n\n".join(current_chunk))

    return merged_sections


def process_sections(
    url: str, sections: list, provider: str, api_token: str, base_url=None
) -> list:
    """
    Process sections of HTML content sequentially or in parallel.

    How it works:
    1. Sequentially processes sections with delays for "groq/" providers.
    2. Uses ThreadPoolExecutor for parallel processing with other providers.
    3. Extracts content blocks for each section.

    Args:
        url (str): The website URL.
        sections (List[str]): The list of HTML sections to process.
        provider (str): The AI provider for content extraction.
        api_token (str): The API token for authentication.
        base_url (Optional[str]): The base URL for the API. Defaults to None.

    Returns:
        List[dict]: The list of extracted content blocks from all sections.
    """

    extracted_content = []
    if provider.startswith("groq/"):
        # Sequential processing with a delay
        for section in sections:
            extracted_content.extend(
                extract_blocks(url, section, provider, api_token, base_url=base_url)
            )
            time.sleep(0.5)  # 500 ms delay between each processing
    else:
        # Parallel processing using ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    extract_blocks, url, section, provider, api_token, base_url=base_url
                )
                for section in sections
            ]
            for future in as_completed(futures):
                extracted_content.extend(future.result())

    return extracted_content


def wrap_text(draw, text, font, max_width):
    """
    Wrap text to fit within a specified width for rendering.

    How it works:
    1. Splits the text into words.
    2. Constructs lines that fit within the maximum width using the provided font.
    3. Returns the wrapped text as a single string.

    Args:
        draw (ImageDraw.Draw): The drawing context for measuring text size.
        text (str): The text to wrap.
        font (ImageFont.FreeTypeFont): The font to use for measuring text size.
        max_width (int): The maximum width for each line.

    Returns:
        str: The wrapped text.
    """

    # Wrap the text to fit within the specified width
    lines = []
    words = text.split()
    while words:
        line = ""
        while (
            words and draw.textbbox((0, 0), line + words[0], font=font)[2] <= max_width
        ):
            line += words.pop(0) + " "
        lines.append(line)
    return "\n".join(lines)


def format_html(html_string):
    """
    Prettify an HTML string using BeautifulSoup.

    How it works:
    1. Parses the HTML string with BeautifulSoup.
    2. Formats the HTML with proper indentation.
    3. Returns the prettified HTML string.

    Args:
        html_string (str): The HTML string to format.

    Returns:
        str: The prettified HTML string.
    """

    soup = BeautifulSoup(html_string, "lxml.parser")
    return soup.prettify()


def fast_format_html(html_string):
    """
    A fast HTML formatter that uses string operations instead of parsing.

    Args:
        html_string (str): The HTML string to format

    Returns:
        str: The formatted HTML string
    """
    # Initialize variables
    indent = 0
    indent_str = "  "  # Two spaces for indentation
    formatted = []
    # in_content = False

    # Split by < and > to separate tags and content
    parts = html_string.replace(">", ">\n").replace("<", "\n<").split("\n")

    for part in parts:
        if not part.strip():
            continue

        # Handle closing tags
        if part.startswith("</"):
            indent -= 1
            formatted.append(indent_str * indent + part)

        # Handle self-closing tags
        elif part.startswith("<") and part.endswith("/>"):
            formatted.append(indent_str * indent + part)

        # Handle opening tags
        elif part.startswith("<"):
            formatted.append(indent_str * indent + part)
            indent += 1

        # Handle content between tags
        else:
            content = part.strip()
            if content:
                formatted.append(indent_str * indent + content)

    return "\n".join(formatted)


def normalize_url(href, base_url):
    """Normalize URLs to ensure consistent format"""
    from urllib.parse import urljoin, urlparse

    # Parse base URL to get components
    parsed_base = urlparse(base_url)
    if not parsed_base.scheme or not parsed_base.netloc:
        raise ValueError(f"Invalid base URL format: {base_url}")
    
    if  parsed_base.scheme.lower() not in ["http", "https"]:
        # Handle special protocols
        raise ValueError(f"Invalid base URL format: {base_url}")
    cleaned_href = href.strip()

    # Use urljoin to handle all cases
    return urljoin(base_url, cleaned_href)




def normalize_url(
    href: str,
    base_url: str,
    *,
    drop_query_tracking=True,
    sort_query=True,
    keep_fragment=False,
    extra_drop_params=None
):
    """
    Extended URL normalizer

    Parameters
    ----------
    href : str
        The raw link extracted from a page.
    base_url : str
        The page’s canonical URL (used to resolve relative links).
    drop_query_tracking : bool (default True)
        Remove common tracking query parameters.
    sort_query : bool (default True)
        Alphabetically sort query keys for deterministic output.
    keep_fragment : bool (default False)
        Preserve the hash fragment (#section) if you need in-page links.
    extra_drop_params : Iterable[str] | None
        Additional query keys to strip (case-insensitive).

    Returns
    -------
    str | None
        A clean, canonical URL or None if href is empty/None.
    """
    if not href:
        return None

    # Resolve relative paths first
    full_url = urljoin(base_url, href.strip())

    # Parse once, edit parts, then rebuild
    parsed = urlparse(full_url)

    # ── netloc ──
    netloc = parsed.netloc.lower()

    # ── path ──
    # Strip duplicate slashes and trailing “/” (except root)
    path = quote(unquote(parsed.path))
    if path.endswith('/') and path != '/':
        path = path.rstrip('/')

    # ── query ──
    query = parsed.query
    if query:
        # explode, mutate, then rebuild
        params = [(k.lower(), v) for k, v in parse_qsl(query, keep_blank_values=True)]

        if drop_query_tracking:
            default_tracking = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term',
                'utm_content', 'gclid', 'fbclid', 'ref', 'ref_src'
            }
            if extra_drop_params:
                default_tracking |= {p.lower() for p in extra_drop_params}
            params = [(k, v) for k, v in params if k not in default_tracking]

        if sort_query:
            params.sort(key=lambda kv: kv[0])

        query = urlencode(params, doseq=True) if params else ''

    # ── fragment ──
    fragment = parsed.fragment if keep_fragment else ''

    # Re-assemble
    normalized = urlunparse((
        parsed.scheme,
        netloc,
        path,
        parsed.params,
        query,
        fragment
    ))

    return normalized


def normalize_url_for_deep_crawl(href, base_url):
    """Normalize URLs to ensure consistent format"""
    from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, urlencode

    # Handle None or empty values
    if not href:
        return None

    # Use urljoin to handle relative URLs
    full_url = urljoin(base_url, href.strip())
    
    # Parse the URL for normalization
    parsed = urlparse(full_url)
    
    # Convert hostname to lowercase
    netloc = parsed.netloc.lower()
    
    # Remove fragment entirely
    fragment = ''
    
    # Normalize query parameters if needed
    query = parsed.query
    if query:
        # Parse query parameters
        params = parse_qs(query)
        
        # Remove tracking parameters (example - customize as needed)
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'fbclid']
        for param in tracking_params:
            if param in params:
                del params[param]
                
        # Rebuild query string, sorted for consistency
        query = urlencode(params, doseq=True) if params else ''
    
    # Build normalized URL
    normalized = urlunparse((
        parsed.scheme,
        netloc,
        parsed.path.rstrip('/'),  # Normalize trailing slash
        parsed.params,
        query,
        fragment
    ))
    
    return normalized

@lru_cache(maxsize=10000)
def efficient_normalize_url_for_deep_crawl(href, base_url):
    """Efficient URL normalization with proper parsing"""
    from urllib.parse import urljoin
    
    if not href:
        return None
    
    # Resolve relative URLs
    full_url = urljoin(base_url, href.strip())
    
    # Use proper URL parsing
    parsed = urlparse(full_url)
    
    # Only perform the most critical normalizations
    # 1. Lowercase hostname
    # 2. Remove fragment
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc.lower(),
        parsed.path.rstrip('/'),
        parsed.params,
        parsed.query,
        ''  # Remove fragment
    ))
    
    return normalized


def normalize_url_tmp(href, base_url):
    """Normalize URLs to ensure consistent format"""
    # Extract protocol and domain from base URL
    try:
        base_parts = base_url.split("/")
        protocol = base_parts[0]
        domain = base_parts[2]
    except IndexError:
        raise ValueError(f"Invalid base URL format: {base_url}")

    # Handle special protocols
    special_protocols = {"mailto:", "tel:", "ftp:", "file:", "data:", "javascript:"}
    if any(href.lower().startswith(proto) for proto in special_protocols):
        return href.strip()

    # Handle anchor links
    if href.startswith("#"):
        return f"{base_url}{href}"

    # Handle protocol-relative URLs
    if href.startswith("//"):
        return f"{protocol}{href}"

    # Handle root-relative URLs
    if href.startswith("/"):
        return f"{protocol}//{domain}{href}"

    # Handle relative URLs
    if not href.startswith(("http://", "https://")):
        # Remove leading './' if present
        href = href.lstrip("./")
        return f"{protocol}//{domain}/{href}"

    return href.strip()


def get_base_domain(url: str) -> str:
    """
    Extract the base domain from a given URL, handling common edge cases.

    How it works:
    1. Parses the URL to extract the domain.
    2. Removes the port number and 'www' prefix.
    3. Handles special domains (e.g., 'co.uk') to extract the correct base.

    Args:
        url (str): The URL to extract the base domain from.

    Returns:
        str: The extracted base domain or an empty string if parsing fails.
    """
    try:
        # Get domain from URL
        domain = urlparse(url).netloc.lower()
        if not domain:
            return ""

        # Remove port if present
        domain = domain.split(":")[0]

        # Remove www
        domain = re.sub(r"^www\.", "", domain)

        # Extract last two parts of domain (handles co.uk etc)
        parts = domain.split(".")
        if len(parts) > 2 and parts[-2] in {
            "co",
            "com",
            "org",
            "gov",
            "edu",
            "net",
            "mil",
            "int",
            "ac",
            "ad",
            "ae",
            "af",
            "ag",
        }:
            return ".".join(parts[-3:])

        return ".".join(parts[-2:])
    except Exception:
        return ""


def is_external_url(url: str, base_domain: str) -> bool:
    """
    Extract the base domain from a given URL, handling common edge cases.

    How it works:
    1. Parses the URL to extract the domain.
    2. Removes the port number and 'www' prefix.
    3. Handles special domains (e.g., 'co.uk') to extract the correct base.

    Args:
        url (str): The URL to extract the base domain from.

    Returns:
        str: The extracted base domain or an empty string if parsing fails.
    """
    special = {"mailto:", "tel:", "ftp:", "file:", "data:", "javascript:"}
    if any(url.lower().startswith(p) for p in special):
        return True

    try:
        parsed = urlparse(url)
        if not parsed.netloc:  # Relative URL
            return False

        # Strip 'www.' from both domains for comparison
        url_domain = parsed.netloc.lower().replace("www.", "")
        base = base_domain.lower().replace("www.", "")

        # Check if URL domain ends with base domain
        return not url_domain.endswith(base)
    except Exception:
        return False


def clean_tokens(tokens: list[str]) -> list[str]:
    """
    Clean a list of tokens by removing noise, stop words, and short tokens.

    How it works:
    1. Defines a set of noise words and stop words.
    2. Filters tokens based on length and exclusion criteria.
    3. Excludes tokens starting with certain symbols (e.g., "↑", "▲").

    Args:
        tokens (list[str]): The list of tokens to clean.

    Returns:
        list[str]: The cleaned list of tokens.
    """

    # Set of tokens to remove
    noise = {
        "ccp",
        "up",
        "↑",
        "▲",
        "⬆️",
        "a",
        "an",
        "at",
        "by",
        "in",
        "of",
        "on",
        "to",
        "the",
    }

    STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "that",
        "the",
        "to",
        "was",
        "were",
        "will",
        "with",
        # Pronouns
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
        "my",
        "your",
        "his",
        "her",
        "its",
        "our",
        "their",
        "mine",
        "yours",
        "hers",
        "ours",
        "theirs",
        "myself",
        "yourself",
        "himself",
        "herself",
        "itself",
        "ourselves",
        "themselves",
        # Common verbs
        "am",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "doing",
        # Prepositions
        "about",
        "above",
        "across",
        "after",
        "against",
        "along",
        "among",
        "around",
        "at",
        "before",
        "behind",
        "below",
        "beneath",
        "beside",
        "between",
        "beyond",
        "by",
        "down",
        "during",
        "except",
        "for",
        "from",
        "in",
        "inside",
        "into",
        "near",
        "of",
        "off",
        "on",
        "out",
        "outside",
        "over",
        "past",
        "through",
        "to",
        "toward",
        "under",
        "underneath",
        "until",
        "up",
        "upon",
        "with",
        "within",
        # Conjunctions
        "and",
        "but",
        "or",
        "nor",
        "for",
        "yet",
        "so",
        "although",
        "because",
        "since",
        "unless",
        # Articles
        "a",
        "an",
        "the",
        # Other common words
        "this",
        "that",
        "these",
        "those",
        "what",
        "which",
        "who",
        "whom",
        "whose",
        "when",
        "where",
        "why",
        "how",
        "all",
        "any",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "can",
        "cannot",
        "can't",
        "could",
        "couldn't",
        "may",
        "might",
        "must",
        "mustn't",
        "shall",
        "should",
        "shouldn't",
        "will",
        "won't",
        "would",
        "wouldn't",
        "not",
        "n't",
        "no",
        "nor",
        "none",
    }

    # Single comprehension, more efficient than multiple passes
    return [
        token
        for token in tokens
        if len(token) > 2
        and token not in noise
        and token not in STOP_WORDS
        and not token.startswith("↑")
        and not token.startswith("▲")
        and not token.startswith("⬆")
    ]


def profile_and_time(func):
    """
    Decorator to profile a function's execution time and performance.

    How it works:
    1. Records the start time before executing the function.
    2. Profiles the function's execution using `cProfile`.
    3. Prints the elapsed time and profiling statistics.

    Args:
        func (Callable): The function to decorate.

    Returns:
        Callable: The decorated function with profiling and timing enabled.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Start timer
        start_time = time.perf_counter()

        # Setup profiler
        profiler = cProfile.Profile()
        profiler.enable()

        # Run function
        result = func(self, *args, **kwargs)

        # Stop profiler
        profiler.disable()

        # Calculate elapsed time
        elapsed_time = time.perf_counter() - start_time

        # Print timing
        print(f"[PROFILER] Scraping completed in {elapsed_time:.2f} seconds")

        # Print profiling stats
        stats = pstats.Stats(profiler)
        stats.sort_stats("cumulative")  # Sort by cumulative time
        stats.print_stats(20)  # Print top 20 time-consuming functions

        return result

    return wrapper


def generate_content_hash(content: str) -> str:
    """Generate a unique hash for content"""
    return xxhash.xxh64(content.encode()).hexdigest()
    # return hashlib.sha256(content.encode()).hexdigest()


def ensure_content_dirs(base_path: str) -> Dict[str, str]:
    """Create content directories if they don't exist"""
    dirs = {
        "html": "html_content",
        "cleaned": "cleaned_html",
        "markdown": "markdown_content",
        "extracted": "extracted_content",
        "screenshots": "screenshots",
        "screenshot": "screenshots",
    }

    content_paths = {}
    for key, dirname in dirs.items():
        path = os.path.join(base_path, dirname)
        os.makedirs(path, exist_ok=True)
        content_paths[key] = path

    return content_paths


def configure_windows_event_loop():
    """
    Configure the Windows event loop to use ProactorEventLoop.
    This resolves the NotImplementedError that occurs on Windows when using asyncio subprocesses.

    This function should only be called on Windows systems and before any async operations.
    On non-Windows systems, this function does nothing.

    Example:
        ```python
        from crawl4ai.async_configs import configure_windows_event_loop

        # Call this before any async operations if you're on Windows
        configure_windows_event_loop()
        ```
    """
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def get_error_context(exc_info, context_lines: int = 5):
    """
    Extract error context with more reliable line number tracking.

    Args:
        exc_info: The exception info from sys.exc_info()
        context_lines: Number of lines to show before and after the error

    Returns:
        dict: Error context information
    """
    import traceback
    import linecache
    import os

    # Get the full traceback
    tb = traceback.extract_tb(exc_info[2])

    # Get the last frame (where the error occurred)
    last_frame = tb[-1]
    filename = last_frame.filename
    line_no = last_frame.lineno
    func_name = last_frame.name

    # Get the source code context using linecache
    # This is more reliable than inspect.getsourcelines
    context_start = max(1, line_no - context_lines)
    context_end = line_no + context_lines + 1

    # Build the context lines with line numbers
    context_lines = []
    for i in range(context_start, context_end):
        line = linecache.getline(filename, i)
        if line:
            # Remove any trailing whitespace/newlines and add the pointer for error line
            line = line.rstrip()
            pointer = "→" if i == line_no else " "
            context_lines.append(f"{i:4d} {pointer} {line}")

    # Join the lines with newlines
    code_context = "\n".join(context_lines)

    # Get relative path for cleaner output
    try:
        rel_path = os.path.relpath(filename)
    except ValueError:
        # Fallback if relpath fails (can happen on Windows with different drives)
        rel_path = filename

    return {
        "filename": rel_path,
        "line_no": line_no,
        "function": func_name,
        "code_context": code_context,
    }

def truncate(value, threshold):
    if len(value) > threshold:
        return value[:threshold] + '...'  # Add ellipsis to indicate truncation
    return value

def optimize_html(html_str, threshold=200):
    root = lxml.html.fromstring(html_str)
    
    for _element in root.iter():
        # Process attributes
        for attr in list(_element.attrib):
            _element.attrib[attr] = truncate(_element.attrib[attr], threshold)
        
        # Process text content
        if _element.text and len(_element.text) > threshold:
            _element.text = truncate(_element.text, threshold)
            
        # Process tail text
        if _element.tail and len(_element.tail) > threshold:
            _element.tail = truncate(_element.tail, threshold)
    
    return lxml.html.tostring(root, encoding='unicode', pretty_print=False)

class HeadPeekr:
    @staticmethod
    async def fetch_head_section(url, timeout=0.3):
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; CrawlBot/1.0)",
            "Accept": "text/html",
            "Connection": "close"  # Force close after response
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                
                # Handle redirects explicitly by using the final URL
                if response.url != url:
                    url = str(response.url)
                    response = await client.get(url, headers=headers)
                
                content = b""
                async for chunk in response.aiter_bytes():
                    content += chunk
                    if b"</head>" in content:
                        break  # Stop after detecting </head>
                return content.split(b"</head>")[0] + b"</head>"
        except (httpx.HTTPError, gaierror) :
            return None

    @staticmethod
    async def peek_html(url, timeout=0.3):
        head_section = await HeadPeekr.fetch_head_section(url, timeout=timeout)
        if head_section:
            return head_section.decode("utf-8", errors="ignore")
        return None

    @staticmethod
    def extract_meta_tags(head_content: str):
        meta_tags = {}
        
        # Find all meta tags
        meta_pattern = r'<meta[^>]+>'
        for meta_tag in re.finditer(meta_pattern, head_content):
            tag = meta_tag.group(0)
            
            # Extract name/property and content
            name_match = re.search(r'name=["\'](.*?)["\']', tag)
            property_match = re.search(r'property=["\'](.*?)["\']', tag)
            content_match = re.search(r'content=["\'](.*?)["\']', tag)
            
            if content_match and (name_match or property_match):
                key = name_match.group(1) if name_match else property_match.group(1)
                meta_tags[key] = content_match.group(1)
                
        return meta_tags

    def get_title(head_content: str):
        title_match = re.search(r'<title>(.*?)</title>', head_content, re.IGNORECASE | re.DOTALL)
        return title_match.group(1) if title_match else None

def preprocess_html_for_schema(html_content, text_threshold=100, attr_value_threshold=200, max_size=100000):
    """
    Preprocess HTML to reduce size while preserving structure for schema generation.
    
    Args:
        html_content (str): Raw HTML content
        text_threshold (int): Maximum length for text nodes before truncation
        attr_value_threshold (int): Maximum length for attribute values before truncation
        max_size (int): Target maximum size for output HTML
        
    Returns:
        str: Preprocessed HTML content
    """
    try:
        # Parse HTML with error recovery
        parser = etree.HTMLParser(remove_comments=True, remove_blank_text=True)
        tree = lhtml.fromstring(html_content, parser=parser)
        
        # 1. Remove HEAD section (keep only BODY)
        head_elements = tree.xpath('//head')
        for head in head_elements:
            if head.getparent() is not None:
                head.getparent().remove(head)
        
        # 2. Define tags to remove completely
        tags_to_remove = [
            'script', 'style', 'noscript', 'iframe', 'canvas', 'svg',
            'video', 'audio', 'source', 'track', 'map', 'area'
        ]
        
        # Remove unwanted elements
        for tag in tags_to_remove:
            elements = tree.xpath(f'//{tag}')
            for element in elements:
                if element.getparent() is not None:
                    element.getparent().remove(element)
        
        # 3. Process remaining elements to clean attributes and truncate text
        for element in tree.iter():
            # Skip if we're at the root level
            if element.getparent() is None:
                continue
                
            # Clean non-essential attributes but preserve structural ones
            # attribs_to_keep = {'id', 'class', 'name', 'href', 'src', 'type', 'value', 'data-'}

            # This is more aggressive than the previous version
            attribs_to_keep = {'id', 'class', 'name', 'type', 'value'}

            # attributes_hates_truncate = ['id', 'class', "data-"]

            # This means, I don't care, if an attribute is too long, truncate it, go and find a better css selector to build a schema
            attributes_hates_truncate = []
            
            # Process each attribute
            for attrib in list(element.attrib.keys()):
                # Keep if it's essential or starts with data-
                if not (attrib in attribs_to_keep or attrib.startswith('data-')):
                    element.attrib.pop(attrib)
                # Truncate long attribute values except for selectors
                elif attrib not in attributes_hates_truncate and len(element.attrib[attrib]) > attr_value_threshold:
                    element.attrib[attrib] = element.attrib[attrib][:attr_value_threshold] + '...'
            
            # Truncate text content if it's too long
            if element.text and len(element.text.strip()) > text_threshold:
                element.text = element.text.strip()[:text_threshold] + '...'
                
            # Also truncate tail text if present
            if element.tail and len(element.tail.strip()) > text_threshold:
                element.tail = element.tail.strip()[:text_threshold] + '...'

        # 4. Detect duplicates and drop them in a single pass
        seen: dict[tuple, None] = {}
        for el in list(tree.xpath('//*[@class]')):          # snapshot once, XPath is fast
            parent = el.getparent()
            if parent is None:
                continue

            cls = el.get('class')
            if not cls:
                continue

            # ── build signature ───────────────────────────────────────────
            h = xxhash.xxh64()                              # stream, no big join()
            for txt in el.itertext():
                h.update(txt)
            sig = (el.tag, cls, h.intdigest())             # tuple cheaper & hashable

            # ── first seen? keep – else drop ─────────────
            if sig in seen and parent is not None:
                parent.remove(el)                           # duplicate
            else:
                seen[sig] = None
        
        # # 4. Find repeated patterns and keep only a few examples
        # # This is a simplistic approach - more sophisticated pattern detection could be implemented
        # pattern_elements = {}
        # for element in tree.xpath('//*[contains(@class, "")]'):
        #     parent = element.getparent()
        #     if parent is None:
        #         continue
                
        #     # Create a signature based on tag and classes
        #     classes = element.get('class', '')
        #     if not classes:
        #         continue
        #     innert_text = ''.join(element.xpath('.//text()'))
        #     innert_text_hash = xxhash.xxh64(innert_text.encode()).hexdigest()
        #     signature = f"{element.tag}.{classes}.{innert_text_hash}"
            
        #     if signature in pattern_elements:
        #         pattern_elements[signature].append(element)
        #     else:
        #         pattern_elements[signature] = [element]
        
        # # Keep only first examples of each repeating pattern
        # for signature, elements in pattern_elements.items():
        #     if len(elements) > 1:
        #         # Keep the first element and remove the rest
        #         for element in elements[1:]:
        #             if element.getparent() is not None:
        #                 element.getparent().remove(element)


        # # Keep only 3 examples of each repeating pattern
        # for signature, elements in pattern_elements.items():
        #     if len(elements) > 3:
        #         # Keep the first 2 and last elements
        #         for element in elements[2:-1]:
        #             if element.getparent() is not None:
        #                 element.getparent().remove(element)
        
        # 5. Convert back to string
        result = etree.tostring(tree, encoding='unicode', method='html')
        
        # If still over the size limit, apply more aggressive truncation
        if len(result) > max_size:
            return result[:max_size] + "..."
            
        return result
    
    except Exception as e:
        # Fallback for parsing errors
        return html_content[:max_size] if len(html_content) > max_size else html_content    

def start_colab_display_server():
    """
    Start virtual display server in Google Colab.
    Raises error if not running in Colab environment.
    """
    # Check if running in Google Colab
    try:
        import google.colab
        from google.colab import output
        from IPython.display import IFrame, display
    except ImportError:
        raise RuntimeError("This function must be run in Google Colab environment.")
    
    import os, time, subprocess
    
    os.environ["DISPLAY"] = ":99"
    
    # Xvfb
    xvfb = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1280x720x24"])
    time.sleep(2)
    
    # minimal window manager
    fluxbox = subprocess.Popen(["fluxbox"])
    
    # VNC → X
    x11vnc = subprocess.Popen(["x11vnc",
                              "-display", ":99",
                              "-nopw", "-forever", "-shared",
                              "-rfbport", "5900", "-quiet"])
    
    # websockify → VNC
    novnc = subprocess.Popen(["/opt/novnc/utils/websockify/run",
                              "6080", "localhost:5900",
                              "--web", "/opt/novnc"])
    
    time.sleep(2)  # give ports a moment
    
    # Colab proxy url
    url = output.eval_js("google.colab.kernel.proxyPort(6080)")
    display(IFrame(f"{url}/vnc.html?autoconnect=true&resize=scale", width=1024, height=768))



def setup_colab_environment():
    """
    Alternative setup using IPython magic commands
    """
    from IPython import get_ipython
    ipython = get_ipython()
    
    print("🚀 Setting up Crawl4AI environment in Google Colab...")
    
    # Run the bash commands
    ipython.run_cell_magic('bash', '', '''
set -e

echo "📦 Installing system dependencies..."
apt-get update -y
apt-get install -y xvfb x11vnc fluxbox websockify git

echo "📥 Setting up virtual display..."
git clone https://github.com/novnc/noVNC         /opt/novnc
git clone https://github.com/novnc/websockify    /opt/novnc/utils/websockify

pip install -q nest_asyncio google-colab
echo "✅ Setup complete!"
''')


# Link Quality Scoring Functions
def extract_page_context(page_title: str, headlines_text: str, meta_description: str, base_url: str) -> dict:
    """
    Extract page context for link scoring - called ONCE per page for performance.
    Parser-agnostic function that takes pre-extracted data.
    
    Args:
        page_title: Title of the page
        headlines_text: Combined text from h1, h2, h3 elements
        meta_description: Meta description content
        base_url: Base URL of the page
        
    Returns:
        Dictionary containing page context data for fast link scoring
    """
    context = {
        'terms': set(),
        'headlines': headlines_text or '',
        'meta_description': meta_description or '',
        'domain': '',
        'is_docs_site': False
    }
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        context['domain'] = parsed.netloc.lower()
        
        # Check if this is a documentation/reference site
        context['is_docs_site'] = any(indicator in context['domain'] 
                                    for indicator in ['docs.', 'api.', 'developer.', 'reference.'])
        
        # Create term set for fast intersection (performance optimization)
        all_text = ((page_title or '') + ' ' + context['headlines'] + ' ' + context['meta_description']).lower()
        # Simple tokenization - fast and sufficient for scoring
        context['terms'] = set(word.strip('.,!?;:"()[]{}') 
                             for word in all_text.split() 
                             if len(word.strip('.,!?;:"()[]{}')) > 2)
                             
    except Exception:
        # Fail gracefully - return empty context
        pass
    
    return context


def calculate_link_intrinsic_score(
    link_text: str, 
    url: str, 
    title_attr: str, 
    class_attr: str, 
    rel_attr: str, 
    page_context: dict
) -> float:
    """
    Ultra-fast link quality scoring using only provided data (no DOM access needed).
    Parser-agnostic function.
    
    Args:
        link_text: Text content of the link
        url: Link URL
        title_attr: Title attribute of the link
        class_attr: Class attribute of the link
        rel_attr: Rel attribute of the link
        page_context: Pre-computed page context from extract_page_context()
        
    Returns:
        Quality score (0.0 - 10.0), higher is better
    """
    score = 0.0
    
    try:
        # 1. ATTRIBUTE QUALITY (string analysis - very fast)
        if title_attr and len(title_attr.strip()) > 3:
            score += 1.0
            
        class_str = (class_attr or '').lower()
        # Navigation/important classes boost score
        if any(nav_class in class_str for nav_class in ['nav', 'menu', 'primary', 'main', 'important']):
            score += 1.5
        # Marketing/ad classes reduce score  
        if any(bad_class in class_str for bad_class in ['ad', 'sponsor', 'track', 'promo', 'banner']):
            score -= 1.0
            
        rel_str = (rel_attr or '').lower()
        # Semantic rel values
        if any(good_rel in rel_str for good_rel in ['canonical', 'next', 'prev', 'chapter']):
            score += 1.0
        if any(bad_rel in rel_str for bad_rel in ['nofollow', 'sponsored', 'ugc']):
            score -= 0.5
            
        # 2. URL STRUCTURE QUALITY (string operations - very fast)
        url_lower = url.lower()
        
        # High-value path patterns
        if any(good_path in url_lower for good_path in ['/docs/', '/api/', '/guide/', '/tutorial/', '/reference/', '/manual/']):
            score += 2.0
        elif any(medium_path in url_lower for medium_path in ['/blog/', '/article/', '/post/', '/news/']):
            score += 1.0
            
        # Penalize certain patterns
        if any(bad_path in url_lower for bad_path in ['/admin/', '/login/', '/cart/', '/checkout/', '/track/', '/click/']):
            score -= 1.5
            
        # URL depth (shallow URLs often more important)
        url_depth = url.count('/') - 2  # Subtract protocol and domain
        if url_depth <= 2:
            score += 1.0
        elif url_depth > 5:
            score -= 0.5
            
        # HTTPS bonus
        if url.startswith('https://'):
            score += 0.5
            
        # 3. TEXT QUALITY (string analysis - very fast)
        if link_text:
            text_clean = link_text.strip()
            if len(text_clean) > 3:
                score += 1.0
                
            # Multi-word links are usually more descriptive
            word_count = len(text_clean.split())
            if word_count >= 2:
                score += 0.5
            if word_count >= 4:
                score += 0.5
                
            # Avoid generic link text
            generic_texts = ['click here', 'read more', 'more info', 'link', 'here']
            if text_clean.lower() in generic_texts:
                score -= 1.0
                
        # 4. CONTEXTUAL RELEVANCE (pre-computed page terms - very fast)
        if page_context.get('terms') and link_text:
            link_words = set(word.strip('.,!?;:"()[]{}').lower() 
                           for word in link_text.split() 
                           if len(word.strip('.,!?;:"()[]{}')) > 2)
            
            if link_words:
                # Calculate word overlap ratio
                overlap = len(link_words & page_context['terms'])
                if overlap > 0:
                    relevance_ratio = overlap / min(len(link_words), 10)  # Cap to avoid over-weighting
                    score += relevance_ratio * 2.0  # Up to 2 points for relevance
                    
        # 5. DOMAIN CONTEXT BONUSES (very fast string checks)
        if page_context.get('is_docs_site', False):
            # Documentation sites: prioritize internal navigation
            if link_text and any(doc_keyword in link_text.lower() 
                               for doc_keyword in ['api', 'reference', 'guide', 'tutorial', 'example']):
                score += 1.0
                
    except Exception:
        # Fail gracefully - return minimal score
        score = 0.5
        
    # Ensure score is within reasonable bounds
    return max(0.0, min(score, 10.0))


def calculate_total_score(
    intrinsic_score: Optional[float] = None,
    contextual_score: Optional[float] = None,
    score_links_enabled: bool = False,
    query_provided: bool = False
) -> float:
    """
    Calculate combined total score from intrinsic and contextual scores with smart fallbacks.
    
    Args:
        intrinsic_score: Quality score based on URL structure, text, and context (0-10)
        contextual_score: BM25 relevance score based on query and head content (0-1 typically)
        score_links_enabled: Whether link scoring is enabled
        query_provided: Whether a query was provided for contextual scoring
        
    Returns:
        Combined total score (0-10 scale)
        
    Scoring Logic:
        - No scoring: return 5.0 (neutral score)
        - Only intrinsic: return normalized intrinsic score
        - Only contextual: return contextual score scaled to 10
        - Both: weighted combination (70% intrinsic, 30% contextual scaled)
    """
    # Case 1: No scoring enabled at all
    if not score_links_enabled:
        return 5.0  # Neutral score - all links treated equally
    
    # Normalize scores to handle None values
    intrinsic = intrinsic_score if intrinsic_score is not None else 0.0
    contextual = contextual_score if contextual_score is not None else 0.0
    
    # Case 2: Only intrinsic scoring (no query provided or no head extraction)
    if not query_provided or contextual_score is None:
        # Use intrinsic score directly (already 0-10 scale)
        return max(0.0, min(intrinsic, 10.0))
    
    # Case 3: Both intrinsic and contextual scores available
    # Scale contextual score (typically 0-1) to 0-10 range
    contextual_scaled = min(contextual * 10.0, 10.0)
    
    # Weighted combination: 70% intrinsic (structure/content quality) + 30% contextual (query relevance)
    # This gives more weight to link quality while still considering relevance
    total = (intrinsic * 0.7) + (contextual_scaled * 0.3)
    
    return max(0.0, min(total, 10.0))


# Embedding utilities
async def get_text_embeddings(
    texts: List[str], 
    llm_config: Optional[Dict] = None,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    batch_size: int = 32
) -> np.ndarray:
    """
    Compute embeddings for a list of texts using specified model.
    
    Args:
        texts: List of texts to embed
        llm_config: Optional LLM configuration for API-based embeddings
        model_name: Model name (used when llm_config is None)
        batch_size: Batch size for processing
        
    Returns:
        numpy array of embeddings
    """
    import numpy as np
    
    if not texts:
        return np.array([])
    
    # If LLMConfig provided, use litellm for embeddings
    if llm_config is not None:
        from litellm import aembedding
        
        # Get embedding model from config or use default
        embedding_model = llm_config.get('provider', 'text-embedding-3-small')
        api_base = llm_config.get('base_url', llm_config.get('api_base'))
        
        # Prepare kwargs
        kwargs = {
            'model': embedding_model,
            'input': texts,
            'api_key': llm_config.get('api_token', llm_config.get('api_key'))
        }
        
        if api_base:
            kwargs['api_base'] = api_base
            
        # Handle OpenAI-compatible endpoints
        if api_base and 'openai/' not in embedding_model:
            kwargs['model'] = f"openai/{embedding_model}"
        
        # Get embeddings
        response = await aembedding(**kwargs)
        
        # Extract embeddings from response
        embeddings = []
        for item in response.data:
            embeddings.append(item['embedding'])
            
        return np.array(embeddings)
    
    # Default: use sentence-transformers
    else:
        # Lazy load to avoid importing heavy libraries unless needed
        from sentence_transformers import SentenceTransformer
        
        # Cache the model in function attribute to avoid reloading
        if not hasattr(get_text_embeddings, '_models'):
            get_text_embeddings._models = {}
        
        if model_name not in get_text_embeddings._models:
            get_text_embeddings._models[model_name] = SentenceTransformer(model_name)
        
        encoder = get_text_embeddings._models[model_name]
        
        # Batch encode for efficiency
        embeddings = encoder.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        return embeddings


def get_text_embeddings_sync(
    texts: List[str],
    llm_config: Optional[Dict] = None,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    batch_size: int = 32
) -> np.ndarray:
    """Synchronous wrapper for get_text_embeddings"""
    import numpy as np
    return asyncio.run(get_text_embeddings(texts, llm_config, model_name, batch_size))


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    import numpy as np
    dot_product = np.dot(vec1, vec2)
    norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    return float(dot_product / norm_product) if norm_product != 0 else 0.0


def cosine_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine distance (1 - similarity) between two vectors"""
    return 1 - cosine_similarity(vec1, vec2)

