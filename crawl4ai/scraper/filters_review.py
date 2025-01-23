# from .url_filter import URLFilter, FilterChain
# from .content_type_filter import ContentTypeFilter
# from .url_pattern_filter import URLPatternFilter

from abc import ABC, abstractmethod
from typing import List, Pattern, Set, Union, FrozenSet
import re, time
from urllib.parse import urlparse
from array import array
import logging
from functools import lru_cache
import fnmatch
from dataclasses import dataclass
from typing import ClassVar
import weakref
import mimetypes


@dataclass
class FilterStats:
    # PERF: Using dataclass creates overhead with __init__ and property access
    # PERF: Could use __slots__ to reduce memory footprint
    # PERF: Consider using array.array('I') for atomic increments
    total_urls: int = 0
    rejected_urls: int = 0
    passed_urls: int = 0


class URLFilter(ABC):
    # PERF: Logger creation is expensive, consider lazy initialization
    # PERF: stats object creation adds overhead for each filter instance
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.stats = FilterStats()
        self.logger = logging.getLogger(f"urlfilter.{self.name}")

    @abstractmethod
    def apply(self, url: str) -> bool:
        pass

    def _update_stats(self, passed: bool):
        # PERF: Already optimized but could use bitwise operations
        # PERF: Consider removing stats entirely in production/fast mode
        self.stats.total_urls += 1
        self.stats.passed_urls += passed
        self.stats.rejected_urls += not passed


class FilterChain:
    # PERF: List traversal for each URL is expensive
    # PERF: Could use array.array instead of list for filters
    # PERF: Consider adding fast path for single filter case
    def __init__(self, filters: List[URLFilter] = None):
        self.filters = filters or []
        self.stats = FilterStats()
        self.logger = logging.getLogger("urlfilter.chain")

    def apply(self, url: str) -> bool:
        # PERF: Logging on every rejection is expensive
        # PERF: Could reorder filters by rejection rate
        # PERF: Consider batch processing mode
        self.stats.total_urls += 1

        for filter_ in self.filters:
            if not filter_.apply(url):
                self.stats.rejected_urls += 1
                self.logger.debug(f"URL {url} rejected by {filter_.name}")
                return False

        self.stats.passed_urls += 1
        return True


class URLPatternFilter(URLFilter):
    # PERF: Converting glob to regex is expensive
    # PERF: Multiple regex compilation is slow
    # PERF: List of patterns causes multiple regex evaluations
    def __init__(
        self,
        patterns: Union[str, Pattern, List[Union[str, Pattern]]],
        use_glob: bool = True,
    ):
        super().__init__()
        self.patterns = [patterns] if isinstance(patterns, (str, Pattern)) else patterns
        self.use_glob = use_glob
        self._compiled_patterns = []

        # PERF: This could be consolidated into a single regex with OR conditions
        # PERF: glob_to_regex creates complex patterns, could be simplified
        for pattern in self.patterns:
            if isinstance(pattern, str) and use_glob:
                self._compiled_patterns.append(self._glob_to_regex(pattern))
            else:
                self._compiled_patterns.append(
                    re.compile(pattern) if isinstance(pattern, str) else pattern
                )

    def _glob_to_regex(self, pattern: str) -> Pattern:
        # PERF: fnmatch.translate creates overly complex patterns
        # PERF: Could cache common translations
        return re.compile(fnmatch.translate(pattern))

    def apply(self, url: str) -> bool:
        # PERF: any() with generator is slower than direct loop with early return
        # PERF: searching entire string is slower than anchored match
        matches = any(pattern.search(url) for pattern in self._compiled_patterns)
        self._update_stats(matches)
        return matches


class ContentTypeFilter(URLFilter):
    # PERF: mimetypes guessing is extremely slow
    # PERF: URL parsing on every check is expensive
    # PERF: No caching of results for similar extensions
    def __init__(
        self, allowed_types: Union[str, List[str]], check_extension: bool = True
    ):
        super().__init__()
        self.allowed_types = (
            [allowed_types] if isinstance(allowed_types, str) else allowed_types
        )
        self.check_extension = check_extension
        self._normalize_types()

    def _normalize_types(self):
        """Normalize content type strings"""
        self.allowed_types = [t.lower() for t in self.allowed_types]

    def _check_extension(self, url: str) -> bool:
        # PERF: urlparse is called on every check
        # PERF: multiple string splits are expensive
        # PERF: mimetypes.guess_type is very slow
        ext = (
            urlparse(url).path.split(".")[-1].lower()
            if "." in urlparse(url).path
            else ""
        )
        if not ext:
            return True

        # PERF: guess_type is main bottleneck
        guessed_type = mimetypes.guess_type(url)[0]
        return any(
            allowed in (guessed_type or "").lower() for allowed in self.allowed_types
        )

    def apply(self, url: str) -> bool:
        """Check if URL's content type is allowed"""
        result = True
        if self.check_extension:
            result = self._check_extension(url)
        self._update_stats(result)
        return result


class DomainFilter(URLFilter):
    # PERF: Set lookups are fast but string normalizations on init are not
    # PERF: Creating two sets doubles memory usage
    def __init__(
        self,
        allowed_domains: Union[str, List[str]] = None,
        blocked_domains: Union[str, List[str]] = None,
    ):
        super().__init__()
        # PERF: Normalizing domains on every init is wasteful
        # PERF: Could use frozenset for immutable lists
        self.allowed_domains = (
            set(self._normalize_domains(allowed_domains)) if allowed_domains else None
        )
        self.blocked_domains = (
            set(self._normalize_domains(blocked_domains)) if blocked_domains else set()
        )

    def _normalize_domains(self, domains: Union[str, List[str]]) -> List[str]:
        # PERF: strip() and lower() create new strings for each domain
        # PERF: List comprehension creates intermediate list
        if isinstance(domains, str):
            domains = [domains]
        return [d.lower().strip() for d in domains]

    def _extract_domain(self, url: str) -> str:
        # PERF: urlparse is called for every URL check
        # PERF: lower() creates new string every time
        # PERF: Could cache recent results
        return urlparse(url).netloc.lower()

    def apply(self, url: str) -> bool:
        # PERF: Two separate set lookups in worst case
        # PERF: Domain extraction happens before knowing if we have any filters
        domain = self._extract_domain(url)

        if domain in self.blocked_domains:
            self._update_stats(False)
            return False

        if self.allowed_domains is not None and domain not in self.allowed_domains:
            self._update_stats(False)
            return False

        self._update_stats(True)
        return True


# Example usage:
def create_common_filter_chain() -> FilterChain:
    """Create a commonly used filter chain"""
    return FilterChain(
        [
            URLPatternFilter(
                [
                    "*.html",
                    "*.htm",  # HTML files
                    "*/article/*",
                    "*/blog/*",  # Common content paths
                ]
            ),
            ContentTypeFilter(["text/html", "application/xhtml+xml"]),
            DomainFilter(blocked_domains=["ads.*", "analytics.*"]),
        ]
    )


####################################################################################
# Uncledoe: Optimized Version
####################################################################################


# Use __slots__ and array for maximum memory/speed efficiency
class FastFilterStats:
    __slots__ = ("_counters",)

    def __init__(self):
        # Use array of unsigned ints for atomic operations
        self._counters = array("I", [0, 0, 0])  # total, passed, rejected

    @property
    def total_urls(self):
        return self._counters[0]

    @property
    def passed_urls(self):
        return self._counters[1]

    @property
    def rejected_urls(self):
        return self._counters[2]


class FastURLFilter(ABC):
    """Optimized base filter class"""

    __slots__ = ("name", "stats", "_logger_ref")

    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.stats = FastFilterStats()
        # Lazy logger initialization using weakref
        self._logger_ref = None

    @property
    def logger(self):
        if self._logger_ref is None or self._logger_ref() is None:
            logger = logging.getLogger(f"urlfilter.{self.name}")
            self._logger_ref = weakref.ref(logger)
        return self._logger_ref()

    @abstractmethod
    def apply(self, url: str) -> bool:
        pass

    def _update_stats(self, passed: bool):
        # Use direct array index for speed
        self.stats._counters[0] += 1  # total
        self.stats._counters[1] += passed  # passed
        self.stats._counters[2] += not passed  # rejected


class FastFilterChain:
    """Optimized filter chain"""

    __slots__ = ("filters", "stats", "_logger_ref")

    def __init__(self, filters: List[FastURLFilter] = None):
        self.filters = tuple(filters or [])  # Immutable tuple for speed
        self.stats = FastFilterStats()
        self._logger_ref = None

    @property
    def logger(self):
        if self._logger_ref is None or self._logger_ref() is None:
            logger = logging.getLogger("urlfilter.chain")
            self._logger_ref = weakref.ref(logger)
        return self._logger_ref()

    def add_filter(self, filter_: FastURLFilter) -> "FastFilterChain":
        """Add a filter to the chain"""
        self.filters.append(filter_)
        return self  # Enable method chaining

    def apply(self, url: str) -> bool:
        """Optimized apply with minimal operations"""
        self.stats._counters[0] += 1  # total

        # Direct tuple iteration is faster than list
        for f in self.filters:
            if not f.apply(url):
                self.stats._counters[2] += 1  # rejected
                return False

        self.stats._counters[1] += 1  # passed
        return True

class FastURLPatternFilter(FastURLFilter):
    """Pattern filter balancing speed and completeness"""
    __slots__ = ('_simple_suffixes', '_simple_prefixes', '_domain_patterns', '_path_patterns')
    
    PATTERN_TYPES = {
        'SUFFIX': 1,    # *.html
        'PREFIX': 2,    # /foo/*
        'DOMAIN': 3,    # *.example.com
        'PATH': 4 ,      # Everything else
        'REGEX': 5 
    }
    
    def __init__(self, patterns: Union[str, Pattern, List[Union[str, Pattern]]], use_glob: bool = True):
        super().__init__()
        patterns = [patterns] if isinstance(patterns, (str, Pattern)) else patterns
        
        self._simple_suffixes = set()
        self._simple_prefixes = set()
        self._domain_patterns = []
        self._path_patterns = []
        
        for pattern in patterns:
            pattern_type = self._categorize_pattern(pattern)
            self._add_pattern(pattern, pattern_type)
    
    def _categorize_pattern(self, pattern: str) -> int:
        """Categorize pattern for specialized handling"""
        if not isinstance(pattern, str):
            return self.PATTERN_TYPES['PATH']
            
        # Check if it's a regex pattern
        if pattern.startswith('^') or pattern.endswith('$') or '\\d' in pattern:
            return self.PATTERN_TYPES['REGEX']
        
        if pattern.count('*') == 1:
            if pattern.startswith('*.'):
                return self.PATTERN_TYPES['SUFFIX']
            if pattern.endswith('/*'):
                return self.PATTERN_TYPES['PREFIX']
                
        if '://' in pattern and pattern.startswith('*.'):
            return self.PATTERN_TYPES['DOMAIN']
            
        return self.PATTERN_TYPES['PATH']
    
    def _add_pattern(self, pattern: str, pattern_type: int):
        """Add pattern to appropriate matcher"""
        if pattern_type == self.PATTERN_TYPES['REGEX']:
            # For regex patterns, compile directly without glob translation
            if isinstance(pattern, str) and (pattern.startswith('^') or pattern.endswith('$') or '\\d' in pattern):
                self._path_patterns.append(re.compile(pattern))
                return
        elif pattern_type == self.PATTERN_TYPES['SUFFIX']:
            self._simple_suffixes.add(pattern[2:])
        elif pattern_type == self.PATTERN_TYPES['PREFIX']:
            self._simple_prefixes.add(pattern[:-2])
        elif pattern_type == self.PATTERN_TYPES['DOMAIN']:
            self._domain_patterns.append(
                re.compile(pattern.replace('*.', r'[^/]+\.'))
            )
        else:
            if isinstance(pattern, str):
                # Handle complex glob patterns
                if '**' in pattern:
                    pattern = pattern.replace('**', '.*')
                if '{' in pattern:
                    # Convert {a,b} to (a|b)
                    pattern = re.sub(r'\{([^}]+)\}', 
                                   lambda m: f'({"|".join(m.group(1).split(","))})',
                                   pattern)
                pattern = fnmatch.translate(pattern)
            self._path_patterns.append(
                pattern if isinstance(pattern, Pattern) else re.compile(pattern)
            )

    @lru_cache(maxsize=10000)
    def apply(self, url: str) -> bool:
        """Hierarchical pattern matching"""
        # Quick suffix check (*.html)
        if self._simple_suffixes:
            path = url.split('?')[0]
            if path.split('/')[-1].split('.')[-1] in self._simple_suffixes:
                self._update_stats(True)
                return True
                
        # Domain check
        if self._domain_patterns:
            for pattern in self._domain_patterns:
                if pattern.match(url):
                    self._update_stats(True)
                    return True
        
        # Prefix check (/foo/*)
        if self._simple_prefixes:
            path = url.split('?')[0]
            if any(path.startswith(p) for p in self._simple_prefixes):
                self._update_stats(True)
                return True
                
        # Complex patterns
        if self._path_patterns:
            if any(p.search(url) for p in self._path_patterns):
                self._update_stats(True)
                return True
        
        self._update_stats(False)
        return False


class FastContentTypeFilter(FastURLFilter):
    """Optimized content type filter using fast lookups"""

    __slots__ = ("allowed_types", "_ext_map", "_check_extension")

    # Fast extension to mime type mapping
    _MIME_MAP = {
        # Text Formats
        "txt": "text/plain",
        "html": "text/html",
        "htm": "text/html",
        "xhtml": "application/xhtml+xml",
        "css": "text/css",
        "csv": "text/csv",
        "ics": "text/calendar",
        "js": "application/javascript",
        # Images
        "bmp": "image/bmp",
        "gif": "image/gif",
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "png": "image/png",
        "svg": "image/svg+xml",
        "tiff": "image/tiff",
        "ico": "image/x-icon",
        "webp": "image/webp",
        # Audio
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "m4a": "audio/mp4",
        "aac": "audio/aac",
        # Video
        "mp4": "video/mp4",
        "mpeg": "video/mpeg",
        "webm": "video/webm",
        "avi": "video/x-msvideo",
        "mov": "video/quicktime",
        "flv": "video/x-flv",
        "wmv": "video/x-ms-wmv",
        "mkv": "video/x-matroska",
        # Applications
        "json": "application/json",
        "xml": "application/xml",
        "pdf": "application/pdf",
        "zip": "application/zip",
        "gz": "application/gzip",
        "tar": "application/x-tar",
        "rar": "application/vnd.rar",
        "7z": "application/x-7z-compressed",
        "exe": "application/vnd.microsoft.portable-executable",
        "msi": "application/x-msdownload",
        # Fonts
        "woff": "font/woff",
        "woff2": "font/woff2",
        "ttf": "font/ttf",
        "otf": "font/otf",
        # Microsoft Office
        "doc": "application/msword",
        "dot": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        # OpenDocument Formats
        "odt": "application/vnd.oasis.opendocument.text",
        "ods": "application/vnd.oasis.opendocument.spreadsheet",
        "odp": "application/vnd.oasis.opendocument.presentation",
        # Archives
        "tar.gz": "application/gzip",
        "tgz": "application/gzip",
        "bz2": "application/x-bzip2",
        # Others
        "rtf": "application/rtf",
        "apk": "application/vnd.android.package-archive",
        "epub": "application/epub+zip",
        "jar": "application/java-archive",
        "swf": "application/x-shockwave-flash",
        "midi": "audio/midi",
        "mid": "audio/midi",
        "ps": "application/postscript",
        "ai": "application/postscript",
        "eps": "application/postscript",
        # Custom or less common
        "bin": "application/octet-stream",
        "dmg": "application/x-apple-diskimage",
        "iso": "application/x-iso9660-image",
        "deb": "application/x-debian-package",
        "rpm": "application/x-rpm",
        "sqlite": "application/vnd.sqlite3",
        # Placeholder
        "unknown": "application/octet-stream",  # Fallback for unknown file types
    }

    @staticmethod
    @lru_cache(maxsize=1000)
    def _extract_extension(path: str) -> str:
        """Fast extension extraction with caching"""
        if "." not in path:
            return ""
        return path.rpartition(".")[-1].lower()

    def __init__(
        self, allowed_types: Union[str, List[str]], check_extension: bool = True
    ):
        super().__init__()
        # Normalize and store as frozenset for fast lookup
        self.allowed_types = frozenset(
            t.lower()
            for t in (
                allowed_types if isinstance(allowed_types, list) else [allowed_types]
            )
        )
        self._check_extension = check_extension

        # Pre-compute extension map for allowed types
        self._ext_map = frozenset(
            ext
            for ext, mime in self._MIME_MAP.items()
            if any(allowed in mime for allowed in self.allowed_types)
        )

    @lru_cache(maxsize=1000)
    def _check_url_cached(self, url: str) -> bool:
        """Cached URL checking"""
        if not self._check_extension:
            return True

        path = url.split("?")[0]  # Fast path split
        ext = self._extract_extension(path)
        if not ext:
            return True

        return ext in self._ext_map

    def apply(self, url: str) -> bool:
        """Fast extension check with caching"""
        result = self._check_url_cached(url)
        self._update_stats(result)
        return result


class FastDomainFilter(FastURLFilter):
    """Optimized domain filter with fast lookups and caching"""

    __slots__ = ("_allowed_domains", "_blocked_domains", "_domain_cache")

    # Regex for fast domain extraction
    _DOMAIN_REGEX = re.compile(r"://([^/]+)")

    def __init__(
        self,
        allowed_domains: Union[str, List[str]] = None,
        blocked_domains: Union[str, List[str]] = None,
    ):
        super().__init__()

        # Convert inputs to frozensets for immutable, fast lookups
        self._allowed_domains = (
            frozenset(self._normalize_domains(allowed_domains))
            if allowed_domains
            else None
        )
        self._blocked_domains = (
            frozenset(self._normalize_domains(blocked_domains))
            if blocked_domains
            else frozenset()
        )

    @staticmethod
    def _normalize_domains(domains: Union[str, List[str]]) -> Set[str]:
        """Fast domain normalization"""
        if isinstance(domains, str):
            return {domains.lower()}
        return {d.lower() for d in domains}

    @staticmethod
    @lru_cache(maxsize=10000)
    def _extract_domain(url: str) -> str:
        """Ultra-fast domain extraction with regex and caching"""
        match = FastDomainFilter._DOMAIN_REGEX.search(url)
        return match.group(1).lower() if match else ""

    def apply(self, url: str) -> bool:
        """Optimized domain checking with early returns"""
        # Skip processing if no filters
        if not self._blocked_domains and self._allowed_domains is None:
            self._update_stats(True)
            return True

        domain = self._extract_domain(url)

        # Early return for blocked domains
        if domain in self._blocked_domains:
            self._update_stats(False)
            return False

        # If no allowed domains specified, accept all non-blocked
        if self._allowed_domains is None:
            self._update_stats(True)
            return True

        # Final allowed domains check
        result = domain in self._allowed_domains
        self._update_stats(result)
        return result


def create_fast_filter_chain() -> FastFilterChain:
    """Create an optimized filter chain with filters ordered by rejection rate"""
    return FastFilterChain(
        [
            # Domain filter first (fastest rejection)
            FastDomainFilter(blocked_domains=["ads.*", "analytics.*"]),
            # Content filter second (medium speed)
            FastContentTypeFilter(["text/html", "application/xhtml+xml"]),
            # Pattern filter last (most expensive)
            FastURLPatternFilter(
                [
                    "*.html",
                    "*.htm",
                    "*/article/*",
                    "*/blog/*",
                ]
            ),
        ]
    )


def run_performance_test():
    import time
    import random
    from itertools import cycle

    # Generate test URLs
    base_urls = [
        "https://example.com/article/123",
        "https://blog.example.com/post/456",
        "https://ads.example.com/tracking",
        "https://example.com/about.html",
        "https://analytics.example.com/script.js",
        "https://example.com/products.php",
        "https://subdomain.example.com/blog/post-123",
        "https://example.com/path/file.pdf",
    ]

    # Create more varied test data
    test_urls = []
    for base in base_urls:
        # Add original
        test_urls.append(base)
        # Add variations
        parts = base.split("/")
        for i in range(10):
            parts[-1] = f"page_{i}.html"
            test_urls.append("/".join(parts))

    # Multiply to get enough test data
    test_urls = test_urls * 10000  # Creates ~800k URLs

    def benchmark(name: str, func, *args, warmup=True):
        if warmup:
            # Warmup run
            func(*args)

        # Actual timing
        start = time.perf_counter_ns()
        result = func(*args)
        elapsed = (time.perf_counter_ns() - start) / 1_000_000  # Convert to ms
        print(
            f"{name:<30} {elapsed:>8.3f} ms  ({len(test_urls)/elapsed*1000:,.0f} URLs/sec)"
        )
        return result

    print("\nBenchmarking original vs optimized implementations...")
    print("-" * 70)

    # Original implementation
    pattern_filter = URLPatternFilter(["*.html", "*/article/*"])
    content_filter = ContentTypeFilter(["text/html"])
    domain_filter = DomainFilter(blocked_domains=["ads.*", "analytics.*"])
    chain = FilterChain([pattern_filter, content_filter, domain_filter])

    # Optimized implementation
    fast_pattern_filter = FastURLPatternFilter(["*.html", "*/article/*"])
    fast_content_filter = FastContentTypeFilter(["text/html"])
    fast_domain_filter = FastDomainFilter(blocked_domains=["ads.*", "analytics.*"])
    fast_chain = FastFilterChain(
        [fast_domain_filter, fast_content_filter, fast_pattern_filter]
    )

    # Test individual filters
    print("\nSingle filter performance (first 1000 URLs):")
    test_subset = test_urls[:1000]

    print("\nPattern Filters:")
    benchmark(
        "Original Pattern Filter",
        lambda: [pattern_filter.apply(url) for url in test_subset],
    )
    benchmark(
        "Optimized Pattern Filter",
        lambda: [fast_pattern_filter.apply(url) for url in test_subset],
    )

    print("\nContent Filters:")
    benchmark(
        "Original Content Filter",
        lambda: [content_filter.apply(url) for url in test_subset],
    )
    benchmark(
        "Optimized Content Filter",
        lambda: [fast_content_filter.apply(url) for url in test_subset],
    )

    print("\nDomain Filters:")
    benchmark(
        "Original Domain Filter",
        lambda: [domain_filter.apply(url) for url in test_subset],
    )
    benchmark(
        "Optimized Domain Filter",
        lambda: [fast_domain_filter.apply(url) for url in test_subset],
    )

    print("\nFull Chain Performance (all URLs):")
    # Test chain
    benchmark("Original Chain", lambda: [chain.apply(url) for url in test_urls])
    benchmark("Optimized Chain", lambda: [fast_chain.apply(url) for url in test_urls])

    # Memory usage
    import sys

    print("\nMemory Usage per Filter:")
    print(f"Original Pattern Filter: {sys.getsizeof(pattern_filter):,} bytes")
    print(f"Optimized Pattern Filter: {sys.getsizeof(fast_pattern_filter):,} bytes")
    print(f"Original Content Filter: {sys.getsizeof(content_filter):,} bytes")
    print(f"Optimized Content Filter: {sys.getsizeof(fast_content_filter):,} bytes")
    print(f"Original Domain Filter: {sys.getsizeof(domain_filter):,} bytes")
    print(f"Optimized Domain Filter: {sys.getsizeof(fast_domain_filter):,} bytes")

def test_pattern_filter():
    import time
    from itertools import chain

    # Test cases as list of tuples instead of dict for multiple patterns
    test_cases = [
        # Simple suffix patterns (*.html)
        ("*.html", {
            "https://example.com/page.html": True,
            "https://example.com/path/doc.html": True,
            "https://example.com/page.htm": False,
            "https://example.com/page.html?param=1": True,
        }),
        
        # Path prefix patterns (/foo/*)
        ("*/article/*", {
            "https://example.com/article/123": True,
            "https://example.com/blog/article/456": True,
            "https://example.com/articles/789": False,
            "https://example.com/article": False,
        }),
        
        # Complex patterns
        ("blog-*-[0-9]", {
            "https://example.com/blog-post-1": True,
            "https://example.com/blog-test-9": True,
            "https://example.com/blog-post": False,
            "https://example.com/blog-post-x": False,
        }),
        
        # Multiple patterns case
        (["*.pdf", "*/download/*"], {
            "https://example.com/doc.pdf": True,
            "https://example.com/download/file.txt": True,
            "https://example.com/path/download/doc": True,
            "https://example.com/uploads/file.txt": False,
        }),
        
        # Edge cases
        ("*", {
            "https://example.com": True,
            "": True,
            "http://test.com/path": True,
        }),
        
        # Complex regex
        (r"^https?://.*\.example\.com/\d+", {
            "https://sub.example.com/123": True,
            "http://test.example.com/456": True,
            "https://example.com/789": False,
            "https://sub.example.com/abc": False,
        })
    ]

    def run_accuracy_test():
        print("\nAccuracy Tests:")
        print("-" * 50)
        
        all_passed = True
        for patterns, test_urls in test_cases:
            filter_obj = FastURLPatternFilter(patterns)
            
            for url, expected in test_urls.items():
                result = filter_obj.apply(url)
                if result != expected:
                    print(f"❌ Failed: Pattern '{patterns}' with URL '{url}'")
                    print(f"   Expected: {expected}, Got: {result}")
                    all_passed = False
                else:
                    print(f"✅ Passed: Pattern '{patterns}' with URL '{url}'")
        
        return all_passed

    def run_speed_test():
        print("\nSpeed Tests:")
        print("-" * 50)
        
        # Create a large set of test URLs
        all_urls = list(chain.from_iterable(urls.keys() for _, urls in test_cases))
        test_urls = all_urls * 10000  # 100K+ URLs
        
        # Test both implementations
        original = URLPatternFilter(["*.html", "*/article/*", "blog-*"])
        optimized = FastURLPatternFilter(["*.html", "*/article/*", "blog-*"])
        
        def benchmark(name, filter_obj):
            start = time.perf_counter()
            for url in test_urls:
                filter_obj.apply(url)
            elapsed = time.perf_counter() - start
            urls_per_sec = len(test_urls) / elapsed
            print(f"{name:<20} {elapsed:.3f}s ({urls_per_sec:,.0f} URLs/sec)")
        
        benchmark("Original Filter:", original)
        benchmark("Optimized Filter:", optimized)

    # Run tests
    print("Running Pattern Filter Tests...")
    accuracy_passed = run_accuracy_test()
    
    if accuracy_passed:
        print("\n✨ All accuracy tests passed!")
        run_speed_test()
    else:
        print("\n❌ Some accuracy tests failed!")

if __name__ == "__main__":
    run_performance_test()
    # test_pattern_filter()
