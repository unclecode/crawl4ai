# from .url_filter import URLFilter, FilterChain
# from .content_type_filter import ContentTypeFilter
# from .url_pattern_filter import URLPatternFilter

from abc import ABC, abstractmethod
from typing import List, Pattern, Set, Union
import re
from urllib.parse import urlparse
import mimetypes
import logging
from dataclasses import dataclass
import fnmatch

@dataclass
class FilterStats:
    """Statistics for filter applications"""
    total_urls: int = 0
    rejected_urls: int = 0
    passed_urls: int = 0

class URLFilter(ABC):
    """Base class for URL filters"""
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.stats = FilterStats()
        self.logger = logging.getLogger(f"urlfilter.{self.name}")

    @abstractmethod
    def apply(self, url: str) -> bool:
        """Apply the filter to a URL"""
        pass

    def _update_stats(self, passed: bool):
        """Update filter statistics"""
        self.stats.total_urls += 1
        if passed:
            self.stats.passed_urls += 1
        else:
            self.stats.rejected_urls += 1

class FilterChain:
    """Chain of URL filters."""
    
    def __init__(self, filters: List[URLFilter] = None):
        self.filters = filters or []
        self.stats = FilterStats()
        self.logger = logging.getLogger("urlfilter.chain")

    def add_filter(self, filter_: URLFilter) -> 'FilterChain':
        """Add a filter to the chain"""
        self.filters.append(filter_)
        return self  # Enable method chaining

    def apply(self, url: str) -> bool:
        """Apply all filters in the chain"""
        self.stats.total_urls += 1
        
        for filter_ in self.filters:
            if not filter_.apply(url):
                self.stats.rejected_urls += 1
                self.logger.debug(f"URL {url} rejected by {filter_.name}")
                return False
        
        self.stats.passed_urls += 1
        return True

class URLPatternFilter(URLFilter):
    """Filter URLs based on glob patterns or regex.
    
    pattern_filter = URLPatternFilter([
        "*.example.com/*",  # Glob pattern
        "*/article/*",      # Path pattern
        re.compile(r"blog-\d+") # Regex pattern
    ])

    - Supports glob patterns and regex
    - Multiple patterns per filter
    - Pattern pre-compilation for performance    
    """
    
    def __init__(self, patterns: Union[str, Pattern, List[Union[str, Pattern]]], 
                 use_glob: bool = True):
        super().__init__()
        self.patterns = [patterns] if isinstance(patterns, (str, Pattern)) else patterns
        self.use_glob = use_glob
        self._compiled_patterns = []
        
        for pattern in self.patterns:
            if isinstance(pattern, str) and use_glob:
                self._compiled_patterns.append(self._glob_to_regex(pattern))
            else:
                self._compiled_patterns.append(re.compile(pattern) if isinstance(pattern, str) else pattern)

    def _glob_to_regex(self, pattern: str) -> Pattern:
        """Convert glob pattern to regex"""
        return re.compile(fnmatch.translate(pattern))

    def apply(self, url: str) -> bool:
        """Check if URL matches any of the patterns"""
        matches = any(pattern.search(url) for pattern in self._compiled_patterns)
        self._update_stats(matches)
        return matches

class ContentTypeFilter(URLFilter):
    """Filter URLs based on expected content type.
    
    content_filter = ContentTypeFilter([
        "text/html",
        "application/pdf"
    ], check_extension=True)

    - Filter by MIME types
    - Extension checking
    - Support for multiple content types
    """
    
    def __init__(self, allowed_types: Union[str, List[str]], 
                 check_extension: bool = True):
        super().__init__()
        self.allowed_types = [allowed_types] if isinstance(allowed_types, str) else allowed_types
        self.check_extension = check_extension
        self._normalize_types()

    def _normalize_types(self):
        """Normalize content type strings"""
        self.allowed_types = [t.lower() for t in self.allowed_types]

    def _check_extension(self, url: str) -> bool:
        """Check URL's file extension"""
        ext = urlparse(url).path.split('.')[-1].lower() if '.' in urlparse(url).path else ''
        if not ext:
            return True  # No extension, might be dynamic content
            
        guessed_type = mimetypes.guess_type(url)[0]
        return any(allowed in (guessed_type or '').lower() for allowed in self.allowed_types)

    def apply(self, url: str) -> bool:
        """Check if URL's content type is allowed"""
        result = True
        if self.check_extension:
            result = self._check_extension(url)
        self._update_stats(result)
        return result

class DomainFilter(URLFilter):
    """Filter URLs based on allowed/blocked domains.
    
    domain_filter = DomainFilter(
        allowed_domains=["example.com", "blog.example.com"],
        blocked_domains=["ads.example.com"]
    )

    - Allow/block specific domains
    - Subdomain support
    - Efficient domain matching
    """
    
    def __init__(self, allowed_domains: Union[str, List[str]] = None, 
                 blocked_domains: Union[str, List[str]] = None):
        super().__init__()
        self.allowed_domains = set(self._normalize_domains(allowed_domains)) if allowed_domains else None
        self.blocked_domains = set(self._normalize_domains(blocked_domains)) if blocked_domains else set()

    def _normalize_domains(self, domains: Union[str, List[str]]) -> List[str]:
        """Normalize domain strings"""
        if isinstance(domains, str):
            domains = [domains]
        return [d.lower().strip() for d in domains]

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        return urlparse(url).netloc.lower()

    def apply(self, url: str) -> bool:
        """Check if URL's domain is allowed"""
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
    return FilterChain([
        URLPatternFilter([
            "*.html", "*.htm",  # HTML files
            "*/article/*", "*/blog/*"  # Common content paths
        ]),
        ContentTypeFilter([
            "text/html",
            "application/xhtml+xml"
        ]),
        DomainFilter(
            blocked_domains=["ads.*", "analytics.*"]
        )
    ])