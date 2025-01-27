from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from urllib.parse import urlparse, unquote
import re
from collections import defaultdict
import math
import logging
from functools import lru_cache
from array import array
from functools import lru_cache
import ctypes
import platform
PLATFORM = platform.system()

# Pre-computed scores for common year differences
_SCORE_LOOKUP = [1.0, 0.5, 0.3333333333333333, 0.25]

# Pre-computed scores for common year differences
_FRESHNESS_SCORES = [
   1.0,    # Current year
   0.9,    # Last year
   0.8,    # 2 years ago
   0.7,    # 3 years ago
   0.6,    # 4 years ago
   0.5,    # 5 years ago
]

# Pre-computed normalization factors for powers of 2
_POW2_NORM = [1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625]


@dataclass
class ScoringStats:
    # PERF: Dataclass introduces overhead with property access and __init__
    # PERF: Float operations and comparisons are expensive for high-frequency updates
    # PERF: Property calculation on every access is inefficient
    # PERF: Storing min/max adds memory overhead and comparison costs
    # PERF: Using inf/-inf creates unnecessary float objects
    urls_scored: int = 0
    total_score: float = 0.0
    min_score: float = float("inf")  # Expensive object creation
    max_score: float = float("-inf")
    
    def update(self, score: float):
        """Update scoring statistics"""
        self.urls_scored += 1
        self.total_score += score
        self.min_score = min(self.min_score, score)
        self.max_score = max(self.max_score, score)

    @property
    def average_score(self) -> float:
        """Calculate average score"""
        return self.total_score / self.urls_scored if self.urls_scored > 0 else 0.0

class FastScoringStats:
    __slots__ = ('_urls_scored', '_total_score', '_min_score', '_max_score')
    
    def __init__(self):
        self._urls_scored = 0
        self._total_score = 0.0
        self._min_score = None  # Lazy initialization
        self._max_score = None
    
    def update(self, score: float) -> None:
        """Optimized update with minimal operations"""
        self._urls_scored += 1
        self._total_score += score
        
        # Lazy min/max tracking - only if actually accessed
        if self._min_score is not None:
            if score < self._min_score:
                self._min_score = score
        if self._max_score is not None:
            if score > self._max_score:
                self._max_score = score
                
    def get_average(self) -> float:
        """Direct calculation instead of property"""
        return self._total_score / self._urls_scored if self._urls_scored else 0.0
    
    def get_min(self) -> float:
        """Lazy min calculation"""
        if self._min_score is None:
            self._min_score = self._total_score / self._urls_scored if self._urls_scored else 0.0
        return self._min_score
        
    def get_max(self) -> float:
        """Lazy max calculation"""
        if self._max_score is None:
            self._max_score = self._total_score / self._urls_scored if self._urls_scored else 0.0
        return self._max_score

class URLScorer(ABC):
    # PERF: Property access overhead for weight
    # PERF: Unnecessary name attribute
    # PERF: Stats object creation overhead
    # PERF: Logger creation for each instance
    # PERF: Abstract method overhead

    def __init__(self, weight: float = 1.0, name: str = None):
        self.weight = weight
        self.name = name or self.__class__.__name__
        self.stats = ScoringStats()
        self.logger = logging.getLogger(f"urlscorer.{self.name}")

    @abstractmethod
    def _calculate_score(self, url: str) -> float:
        pass

    def score(self, url: str) -> float:
        raw_score = self._calculate_score(url)
        weighted_score = raw_score * self.weight
        self.stats.update(weighted_score)
        return weighted_score

# Optimized base class
class FastURLScorer(ABC):
    __slots__ = ('_weight', '_stats')
    
    def __init__(self, weight: float = 1.0):
        # Store weight directly as float32 for memory efficiency
        self._weight = ctypes.c_float(weight).value
        self._stats = ScoringStats()
    
    @abstractmethod
    def _calculate_score(self, url: str) -> float:
        """Calculate raw score for URL."""
        pass
    
    def score(self, url: str) -> float:
        """Calculate weighted score with minimal overhead."""
        score = self._calculate_score(url) * self._weight
        self._stats.update(score)
        return score
    
    @property
    def stats(self):
        """Access to scoring statistics."""
        return self._stats
    
    @property
    def weight(self):
        return self._weight

class CompositeScorer(URLScorer):
    # PERF: Unnecessary list iteration for each score
    # PERF: Creates new list for scores
    # PERF: Division on every normalization
    # PERF: No parallelization for independent scorers
    # PERF: No short circuit for zero scores
    # PERF: No weighting optimization
    # PERF: No caching of combined scores
    # PERF: List allocation for scores storag
    """Combines multiple scorers with weights"""

    def __init__(self, scorers: List[URLScorer], normalize: bool = True):
        super().__init__(name="CompositeScorer")
        self.scorers = scorers
        self.normalize = normalize

    def _calculate_score(self, url: str) -> float:
        scores = [scorer.score(url) for scorer in self.scorers]
        total_score = sum(scores)

        if self.normalize and scores:
            total_score /= len(scores)

        return total_score

class FastCompositeScorer(FastURLScorer):
    __slots__ = ('_scorers', '_normalize', '_weights_array', '_score_array')
    
    def __init__(self, scorers: List[URLScorer], normalize: bool = True):
        """Initialize composite scorer combining multiple scoring strategies.
        
        Optimized for:
        - Fast parallel scoring
        - Memory efficient score aggregation
        - Quick short-circuit conditions
        - Pre-allocated arrays
        
        Args:
            scorers: List of scoring strategies to combine
            normalize: Whether to normalize final score by scorer count
        """
        super().__init__(weight=1.0)
        self._scorers = scorers
        self._normalize = normalize
        
        # Pre-allocate arrays for scores and weights
        self._weights_array = array('f', [s.weight for s in scorers])
        self._score_array = array('f', [0.0] * len(scorers))

    @lru_cache(maxsize=10000)
    def _calculate_score(self, url: str) -> float:
        """Calculate combined score from all scoring strategies.
        
        Uses:
        1. Pre-allocated arrays for scores
        2. Short-circuit on zero scores
        3. Optimized normalization
        4. Vectorized operations where possible
        
        Args:
            url: URL to score
            
        Returns:
            Combined and optionally normalized score
        """
        total_score = 0.0
        scores = self._score_array
        
        # Get scores from all scorers
        for i, scorer in enumerate(self._scorers):
            # Use public score() method which applies weight
            scores[i] = scorer.score(url)
            total_score += scores[i]
            
        # Normalize if requested
        if self._normalize and self._scorers:
            count = len(self._scorers)
            return total_score / count
            
        return total_score

    def score(self, url: str) -> float:
        """Public scoring interface with stats tracking.
        
        Args:
            url: URL to score
            
        Returns:
            Final combined score
        """
        score = self._calculate_score(url)
        self.stats.update(score)
        return score

class KeywordRelevanceScorer(URLScorer):   
    # PERF: Regex compilation and pattern matching is expensive 
    # PERF: List comprehension with pattern search has high overhead
    # PERF: URL decoding on every calculation
    # PERF: Division operation for normalization is costly
    # PERF: Case insensitive regex adds overhead
    # PERF: No pattern caching or reuse
    # PERF: Using inheritance adds method lookup overhead
   
    """Score URLs based on keyword relevance.

    keyword_scorer = KeywordRelevanceScorer(
        keywords=["python", "programming"],
        weight=1.0,
        case_sensitive=False
    )

    - Score based on keyword matches
    - Case sensitivity options
    - Weighted scoring
    """

    def __init__(
        self, keywords: List[str], weight: float = 1.0, case_sensitive: bool = False
    ):
        super().__init__(weight=weight)
        self.keywords = keywords
        self.case_sensitive = case_sensitive
        self._compile_keywords()

    def _compile_keywords(self):
        """Prepare keywords for matching"""
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self.patterns = [re.compile(re.escape(k), flags) for k in self.keywords]

    def _calculate_score(self, url: str) -> float:
        """Calculate score based on keyword matches"""
        decoded_url = unquote(url)
        total_matches = sum(
            1 for pattern in self.patterns if pattern.search(decoded_url)
        )
        # Normalize score between 0 and 1
        return total_matches / len(self.patterns) if self.patterns else 0.0

class FastKeywordRelevanceScorer(FastURLScorer):
    __slots__ = ('_weight', '_stats', '_keywords', '_case_sensitive')
    
    def __init__(self, keywords: List[str], weight: float = 1.0, case_sensitive: bool = False):
        super().__init__(weight=weight)
        self._case_sensitive = case_sensitive
        # Pre-process keywords once
        self._keywords = [k if case_sensitive else k.lower() for k in keywords]
    
    @lru_cache(maxsize=10000)
    def _url_bytes(self, url: str) -> bytes:
        """Cache decoded URL bytes"""
        return url.encode('utf-8') if self._case_sensitive else url.lower().encode('utf-8')
    
    
    def _calculate_score(self, url: str) -> float:
        """Fast string matching without regex or byte conversion"""
        if not self._case_sensitive:
            url = url.lower()
            
        matches = sum(1 for k in self._keywords if k in url)
        
        # Fast return paths
        if not matches:
            return 0.0
        if matches == len(self._keywords):
            return 1.0
            
        return matches / len(self._keywords)

class PathDepthScorer(URLScorer):
    # PERF: URL parsing on every call is expensive
    # PERF: Split and list comprehension creates temporary lists
    # PERF: abs() call adds function overhead
    # PERF: Division and addition in score calculation are expensive for high frequency
    # PERF: Path parts filtering creates extra list
    # PERF: Inherits URLScorer adding method lookup overhead
    # PERF: No caching of parsed URLs or calculated depths    
    """Score URLs based on their path depth.

    path_scorer = PathDepthScorer(
        optimal_depth=3,  # Preferred URL depth
        weight=0.7
    )

    - Score based on URL path depth
    - Configurable optimal depth
    - Diminishing returns for deeper paths
    """

    def __init__(self, optimal_depth: int = 3, weight: float = 1.0):
        super().__init__(weight=weight)
        self.optimal_depth = optimal_depth

    def _calculate_score(self, url: str) -> float:
        """Calculate score based on path depth"""
        path = urlparse(url).path
        depth = len([x for x in path.split("/") if x])

        # Score decreases as we move away from optimal depth
        distance_from_optimal = abs(depth - self.optimal_depth)
        return 1.0 / (1.0 + distance_from_optimal)

class FastPathDepthScorer(FastURLScorer):
    __slots__ = ('_weight', '_stats', '_optimal_depth')  # Remove _url_cache
    
    def __init__(self, optimal_depth: int = 3, weight: float = 1.0):
        super().__init__(weight=weight)
        self._optimal_depth = optimal_depth

    @staticmethod
    @lru_cache(maxsize=10000)
    def _quick_depth(path: str) -> int:
        """Ultra fast path depth calculation.
        
        Examples:
            - "http://example.com" -> 0  # No path segments
            - "http://example.com/" -> 0  # Empty path
            - "http://example.com/a" -> 1
            - "http://example.com/a/b" -> 2
        """
        if not path or path == '/':
            return 0
            
        if '/' not in path:
            return 0
            
        depth = 0
        last_was_slash = True
        
        for c in path:
            if c == '/':
                if not last_was_slash:
                    depth += 1
                last_was_slash = True
            else:
                last_was_slash = False
                
        if not last_was_slash:
            depth += 1
            
        return depth

    @lru_cache(maxsize=10000)  # Cache the whole calculation
    def _calculate_score(self, url: str) -> float:
        pos = url.find('/', url.find('://') + 3)
        if pos == -1:
            depth = 0
        else:
            depth = self._quick_depth(url[pos:])
            
        # Use lookup table for common distances
        distance = depth - self._optimal_depth
        distance = distance if distance >= 0 else -distance  # Faster than abs()
        
        if distance < 4:
            return _SCORE_LOOKUP[distance]
            
        return 1.0 / (1.0 + distance)                                             

class ContentTypeScorer(URLScorer):
    # PERF: Regex compilation on every initialization
    # PERF: Dict lookup and regex search for every URL
    # PERF: Pattern iteration adds loop overhead
    # PERF: No pattern priority or short-circuit
    # PERF: Dict storage has lookup overhead
    # PERF: Missing extension fast path check
    # PERF: Unnecessary regex for simple extensions    
    """Score URLs based on content type preferences.

    content_scorer = ContentTypeScorer({
        r'\.html$': 1.0,
        r'\.pdf$': 0.8,
        r'\.xml$': 0.6
    })

    - Score based on file types
    - Configurable type weights
    - Pattern matching support
    """

    def __init__(self, type_weights: Dict[str, float], weight: float = 1.0):
        super().__init__(weight=weight)
        self.type_weights = type_weights
        self._compile_patterns()

    def _compile_patterns(self):
        """Prepare content type patterns"""
        self.patterns = {
            re.compile(pattern): weight for pattern, weight in self.type_weights.items()
        }

    def _calculate_score(self, url: str) -> float:
        """Calculate score based on content type matching"""
        for pattern, weight in self.patterns.items():
            if pattern.search(url):
                return weight
        return 0.0

class FastContentTypeScorer(FastURLScorer):
    __slots__ = ('_weight', '_exact_types', '_regex_types')

    def __init__(self, type_weights: Dict[str, float], weight: float = 1.0):
        """Initialize scorer with type weights map.
        
        Args:
            type_weights: Dict mapping file extensions/patterns to scores (e.g. {'.html$': 1.0})
            weight: Overall weight multiplier for this scorer
        """
        super().__init__(weight=weight)
        self._exact_types = {}  # Fast lookup for simple extensions
        self._regex_types = []  # Fallback for complex patterns
        
        # Split into exact vs regex matchers for performance
        for pattern, score in type_weights.items():
            if pattern.startswith('.') and pattern.endswith('$'):
                ext = pattern[1:-1]
                self._exact_types[ext] = score
            else:
                self._regex_types.append((re.compile(pattern), score))
                
        # Sort complex patterns by score for early exit
        self._regex_types.sort(key=lambda x: -x[1])

    @staticmethod
    @lru_cache(maxsize=10000)
    def _quick_extension(url: str) -> str:
        """Extract file extension ultra-fast without regex/splits.
        
        Handles:
        - Basic extensions: "example.html" -> "html"
        - Query strings: "page.php?id=1" -> "php" 
        - Fragments: "doc.pdf#page=1" -> "pdf"
        - Path params: "file.jpg;width=100" -> "jpg"
        
        Args:
            url: URL to extract extension from
            
        Returns:
            Extension without dot, or empty string if none found
        """
        pos = url.rfind('.')
        if pos == -1:
            return ''
        
        # Find first non-alphanumeric char after extension
        end = len(url)
        for i in range(pos + 1, len(url)):
            c = url[i]
            # Stop at query string, fragment, path param or any non-alphanumeric
            if c in '?#;' or not c.isalnum():
                end = i
                break
                
        return url[pos + 1:end].lower()

    @lru_cache(maxsize=10000)
    def _calculate_score(self, url: str) -> float:
        """Calculate content type score for URL.
        
        Uses staged approach:
        1. Try exact extension match (fast path)
        2. Fall back to regex patterns if needed
        
        Args:
            url: URL to score
            
        Returns:
            Score between 0.0 and 1.0 * weight
        """
        # Fast path: direct extension lookup
        ext = self._quick_extension(url)
        if ext:
            score = self._exact_types.get(ext, None)
            if score is not None:
                return score
                
        # Slow path: regex patterns
        for pattern, score in self._regex_types:
            if pattern.search(url):
                return score

        return 0.0

class FreshnessScorer(URLScorer):
    # PERF: Multiple regex compilations for each pattern
    # PERF: Tries all patterns sequentially 
    # PERF: Regex pattern matching is expensive
    # PERF: Int conversion and arithmetic for every match
    # PERF: Repeated constant value (2024) hardcoded
    # PERF: No URL caching
    # PERF: Complex patterns with redundant groups
    # PERF: Unnecessary list of patterns when could combine
    """Score URLs based on freshness indicators.

    freshness_scorer = FreshnessScorer(weight=0.9)

    Score based on date indicators in URLs
    Multiple date format support
    Recency weighting"""

    def __init__(self, weight: float = 1.0):
        super().__init__(weight=weight)
        self.date_patterns = [
            r"/(\d{4})/(\d{2})/(\d{2})/",  # yyyy/mm/dd
            r"(\d{4})[-_](\d{2})[-_](\d{2})",  # yyyy-mm-dd
            r"/(\d{4})/",  # year only
        ]
        self._compile_patterns()

    def _compile_patterns(self):
        """Prepare date patterns"""
        self.compiled_patterns = [re.compile(p) for p in self.date_patterns]

    def _calculate_score(self, url: str) -> float:
        """Calculate score based on date indicators"""
        for pattern in self.compiled_patterns:
            if match := pattern.search(url):
                year = int(match.group(1))
                # Score higher for more recent years
                return 1.0 - (2024 - year) * 0.1
        return 0.5  # Default score for URLs without dates

class FastFreshnessScorer(FastURLScorer):
    __slots__ = ('_weight', '_date_pattern', '_current_year')

    def __init__(self, weight: float = 1.0, current_year: int = 2024):
        """Initialize freshness scorer.
        
        Extracts and scores dates from URLs using format:
        - YYYY/MM/DD 
        - YYYY-MM-DD
        - YYYY_MM_DD
        - YYYY (year only)
        
        Args:
            weight: Score multiplier
            current_year: Year to calculate freshness against (default 2024)
        """
        super().__init__(weight=weight)
        self._current_year = current_year
        
        # Combined pattern for all date formats
        # Uses non-capturing groups (?:) and alternation
        self._date_pattern = re.compile(
            r'(?:/'  # Path separator
            r'|[-_])'  # or date separators
            r'((?:19|20)\d{2})'  # Year group (1900-2099)
            r'(?:'  # Optional month/day group
            r'(?:/|[-_])'  # Date separator  
            r'(?:\d{2})'  # Month
            r'(?:'  # Optional day
            r'(?:/|[-_])'  # Date separator
            r'(?:\d{2})'  # Day
            r')?'  # Day is optional
            r')?'  # Month/day group is optional
        )

    @lru_cache(maxsize=10000)
    def _extract_year(self, url: str) -> Optional[int]:
        """Extract the most recent year from URL.
        
        Args:
            url: URL to extract year from
            
        Returns:
            Year as int or None if no valid year found
        """
        matches = self._date_pattern.finditer(url)
        latest_year = None
        
        # Find most recent year
        for match in matches:
            year = int(match.group(1))
            if (year <= self._current_year and  # Sanity check
                (latest_year is None or year > latest_year)):
                latest_year = year
                
        return latest_year

    @lru_cache(maxsize=10000) 
    def _calculate_score(self, url: str) -> float:
        """Calculate freshness score based on URL date.
        
        More recent years score higher. Uses pre-computed scoring
        table for common year differences.
        
        Args:
            url: URL to score
            
        Returns:
            Score between 0.0 and 1.0 * weight
        """
        year = self._extract_year(url)
        if year is None:
            return 0.5  # Default score
            
        # Use lookup table for common year differences
        year_diff = self._current_year - year
        if year_diff < len(_FRESHNESS_SCORES):
            return _FRESHNESS_SCORES[year_diff]
            
        # Fallback calculation for older content
        return max(0.1, 1.0 - year_diff * 0.1)

class DomainAuthorityScorer(URLScorer):
    # PERF: URL parsing on every score calculation
    # PERF: Repeated domain extraction
    # PERF: Case conversion on every lookup
    # PERF: Dict lookup without caching
    # PERF: Processes full URL when only needs domain
    # PERF: No fast path for common domains
    # PERF: Netloc includes port which requires extra processing
    """Score URLs based on domain authority.

    authority_scorer = DomainAuthorityScorer({
        "python.org": 1.0,
        "github.com": 0.9,
        "medium.com": 0.7
    })

    Score based on domain importance
    Configurable domain weights
    Default weight for unknown domains"""

    def __init__(
        self,
        domain_weights: Dict[str, float],
        default_weight: float = 0.5,
        weight: float = 1.0,
    ):
        super().__init__(weight=weight)
        self.domain_weights = domain_weights
        self.default_weight = default_weight

    def _calculate_score(self, url: str) -> float:
        """Calculate score based on domain authority"""
        domain = urlparse(url).netloc.lower()
        return self.domain_weights.get(domain, self.default_weight)

class FastDomainAuthorityScorer(FastURLScorer):
    __slots__ = ('_weight', '_domain_weights', '_default_weight', '_top_domains')
    
    def __init__(
        self,
        domain_weights: Dict[str, float],
        default_weight: float = 0.5,
        weight: float = 1.0,
    ):
        """Initialize domain authority scorer.
        
        Args:
            domain_weights: Dict mapping domains to authority scores
            default_weight: Score for unknown domains
            weight: Overall scorer weight multiplier
            
        Example:
            {
                'python.org': 1.0,
                'github.com': 0.9,
                'medium.com': 0.7
            }
        """
        super().__init__(weight=weight)
        
        # Pre-process domains for faster lookup
        self._domain_weights = {
            domain.lower(): score 
            for domain, score in domain_weights.items()
        }
        self._default_weight = default_weight
        
        # Cache top domains for fast path
        self._top_domains = {
            domain: score
            for domain, score in sorted(
                domain_weights.items(), 
                key=lambda x: -x[1]
            )[:5]  # Keep top 5 highest scoring domains
        }

    @staticmethod
    @lru_cache(maxsize=10000)
    def _extract_domain(url: str) -> str:
        """Extract domain from URL ultra-fast.
        
        Handles:
        - Basic domains: "example.com"
        - Subdomains: "sub.example.com" 
        - Ports: "example.com:8080"
        - IPv4: "192.168.1.1"
        
        Args:
            url: Full URL to extract domain from
            
        Returns:
            Lowercase domain without port
        """
        # Find domain start
        start = url.find('://') 
        if start == -1:
            start = 0
        else:
            start += 3
            
        # Find domain end
        end = url.find('/', start)
        if end == -1:
            end = url.find('?', start)
            if end == -1:
                end = url.find('#', start)
                if end == -1:
                    end = len(url)
                    
        # Extract domain and remove port
        domain = url[start:end]
        port_idx = domain.rfind(':')
        if port_idx != -1:
            domain = domain[:port_idx]
            
        return domain.lower()

    @lru_cache(maxsize=10000)
    def _calculate_score(self, url: str) -> float:
        """Calculate domain authority score.
        
        Uses staged approach:
        1. Check top domains (fastest)
        2. Check full domain weights
        3. Return default weight
        
        Args:
            url: URL to score
            
        Returns:
            Authority score between 0.0 and 1.0 * weight
        """
        domain = self._extract_domain(url)
        
        # Fast path: check top domains first
        score = self._top_domains.get(domain)
        if score is not None:
            return score
            
        # Regular path: check all domains
        return self._domain_weights.get(domain, self._default_weight)

def create_balanced_scorer() -> CompositeScorer:
    """Create a balanced composite scorer"""
    return CompositeScorer(
        [
            KeywordRelevanceScorer(
                keywords=["article", "blog", "news", "research"], weight=1.0
            ),
            PathDepthScorer(optimal_depth=3, weight=0.7),
            ContentTypeScorer(
                type_weights={r"\.html?$": 1.0, r"\.pdf$": 0.8, r"\.xml$": 0.6},
                weight=0.8,
            ),
            FreshnessScorer(weight=0.9),
        ]
    )

def create_balanced_fast_freshness_scorer() -> CompositeScorer:
    """Create a balanced composite scorer with fast freshness scorer"""
    return FastCompositeScorer(
        [
            FastKeywordRelevanceScorer(
                keywords=["article", "blog", "news", "research"], weight=1.0
            ),
            FastPathDepthScorer(optimal_depth=3, weight=0.7),
            FastContentTypeScorer(
                type_weights={r"\.html?$": 1.0, r"\.pdf$": 0.8, r"\.xml$": 0.6},
                weight=0.8,
            ),
            FastFreshnessScorer(weight=0.9),
        ]
    )

# Example Usage:
"""
# Create a composite scorer
scorer = CompositeScorer([
    KeywordRelevanceScorer(["python", "programming"], weight=1.0),
    PathDepthScorer(optimal_depth=2, weight=0.7),
    FreshnessScorer(weight=0.8),
    DomainAuthorityScorer(
        domain_weights={
            "python.org": 1.0,
            "github.com": 0.9,
            "medium.com": 0.7
        },
        weight=0.9
    )
])

# Score a URL
score = scorer.score("https://python.org/article/2024/01/new-features")

# Access statistics
print(f"Average score: {scorer.stats.average_score}")
print(f"URLs scored: {scorer.stats.urls_scored}")
"""


def run_scorer_performance_test():
    import time
    import random
    from itertools import cycle
    import sys

    # Generate varied test URLs
    base_urls = [
        # News/blog articles with dates
        "https://example.com/2024/01/article-123",
        "https://news.com/2023-12-31/breaking-news",
        "https://blog.site.com/2022_11_15/tech-update",
        
        # Different content types
        "https://docs.example.com/report.pdf",
        "https://site.com/page.html?q=test",
        "https://api.service.com/data.json",
        
        # Various domain authorities
        "https://python.org/downloads",
        "https://github.com/repo/code",
        "https://medium.com/@user/post",
        
        # Different path depths
        "https://site.com/category/subcategory/product/detail",
        "https://shop.com/items",
        "https://edu.org/courses/cs/intro/lecture1",
    ]

    # Create variations
    test_urls = []
    years = list(range(2020, 2025))
    domains = ["example.com", "python.org", "github.com", "medium.com"]
    extensions = ["html", "pdf", "php", "jsx"]
    
    for base in base_urls:
        test_urls.append(base)
        # Add year variations
        for year in years:
            test_urls.append(f"https://blog.com/{year}/post-{random.randint(1,999)}")
        # Add domain variations    
        for domain in domains:
            test_urls.append(f"https://{domain}/article-{random.randint(1,999)}")
        # Add extension variations    
        for ext in extensions:
            test_urls.append(f"https://site.com/doc-{random.randint(1,999)}.{ext}")

    # Multiply dataset
    test_urls = test_urls * 5000  # Creates ~300k URLs
    
    def benchmark(name: str, scorer, urls, warmup=True):
        if warmup:
            for url in urls[:100]:  # Warmup with subset
                scorer.score(url)

        start = time.perf_counter_ns()
        for url in urls:
            scorer.score(url)
        elapsed = (time.perf_counter_ns() - start) / 1_000_000  # Convert to ms
        
        print(
            f"{name:<35} {elapsed:>8.3f} ms  ({len(urls)/elapsed*1000:,.0f} URLs/sec)"
        )
        return elapsed

    print("\nBenchmarking original vs optimized scorers...")
    print("-" * 75)

    # Initialize test data
    domain_weights = {"python.org": 1.0, "github.com": 0.9, "medium.com": 0.7}
    type_weights = {".html$": 1.0, ".pdf$": 0.8, ".php$": 0.6}
    keywords = ["python", "article", "blog", "docs"]

    # Original implementations
    keyword_scorer = KeywordRelevanceScorer(keywords=keywords, weight=1.0)
    path_scorer = PathDepthScorer(optimal_depth=3, weight=0.7)
    content_scorer = ContentTypeScorer(type_weights=type_weights, weight=0.8)
    freshness_scorer = FreshnessScorer(weight=0.9)
    domain_scorer = DomainAuthorityScorer(domain_weights=domain_weights, weight=1.0)

    # Fast implementations
    fast_keyword_scorer = FastKeywordRelevanceScorer(keywords=keywords, weight=1.0)
    fast_path_scorer = FastPathDepthScorer(optimal_depth=3, weight=0.7)
    fast_content_scorer = FastContentTypeScorer(type_weights=type_weights, weight=0.8)
    fast_freshness_scorer = FastFreshnessScorer(weight=0.9)
    fast_domain_scorer = FastDomainAuthorityScorer(domain_weights=domain_weights, weight=1.0)

    # Test subset for individual scorers
    test_subset = test_urls[:1000]

    print("\nIndividual Scorer Performance (first 1000 URLs):")
    
    print("\nKeyword Relevance Scorers:")
    benchmark("Original Keyword Scorer", keyword_scorer, test_subset)
    benchmark("Optimized Keyword Scorer", fast_keyword_scorer, test_subset)

    print("\nPath Depth Scorers:")
    benchmark("Original Path Scorer", path_scorer, test_subset)
    benchmark("Optimized Path Scorer", fast_path_scorer, test_subset)

    print("\nContent Type Scorers:")
    benchmark("Original Content Scorer", content_scorer, test_subset)
    benchmark("Optimized Content Scorer", fast_content_scorer, test_subset)

    print("\nFreshness Scorers:")
    benchmark("Original Freshness Scorer", freshness_scorer, test_subset)
    benchmark("Optimized Freshness Scorer", fast_freshness_scorer, test_subset)

    print("\nDomain Authority Scorers:")
    benchmark("Original Domain Scorer", domain_scorer, test_subset)
    benchmark("Optimized Domain Scorer", fast_domain_scorer, test_subset)

    # Test composite scorers
    print("\nComposite Scorer Performance (all URLs):")
    
    original_composite = CompositeScorer([
        keyword_scorer, path_scorer, content_scorer, 
        freshness_scorer, domain_scorer
    ])
    
    fast_composite = FastCompositeScorer([
        fast_keyword_scorer, fast_path_scorer, fast_content_scorer,
        fast_freshness_scorer, fast_domain_scorer
    ])

    benchmark("Original Composite Scorer", original_composite, test_urls)
    benchmark("Optimized Composite Scorer", fast_composite, test_urls)

    # Memory usage
    print("\nMemory Usage per Scorer:")
    print(f"Original Keyword Scorer: {sys.getsizeof(keyword_scorer):,} bytes")
    print(f"Optimized Keyword Scorer: {sys.getsizeof(fast_keyword_scorer):,} bytes")
    print(f"Original Path Scorer: {sys.getsizeof(path_scorer):,} bytes")
    print(f"Optimized Path Scorer: {sys.getsizeof(fast_path_scorer):,} bytes")
    print(f"Original Content Scorer: {sys.getsizeof(content_scorer):,} bytes")
    print(f"Optimized Content Scorer: {sys.getsizeof(fast_content_scorer):,} bytes")
    print(f"Original Freshness Scorer: {sys.getsizeof(freshness_scorer):,} bytes")
    print(f"Optimized Freshness Scorer: {sys.getsizeof(fast_freshness_scorer):,} bytes")
    print(f"Original Domain Scorer: {sys.getsizeof(domain_scorer):,} bytes")
    print(f"Optimized Domain Scorer: {sys.getsizeof(fast_domain_scorer):,} bytes")
    print(f"Original Composite: {sys.getsizeof(original_composite):,} bytes")
    print(f"Optimized Composite: {sys.getsizeof(fast_composite):,} bytes")

def test_scorers():
    import time
    from itertools import chain

    test_cases = [
        # Keyword Scorer Tests
        {
            "scorer_type": "keyword",
            "config": {
                "keywords": ["python", "blog"],
                "weight": 1.0,
                "case_sensitive": False
            },
            "urls": {
                "https://example.com/python-blog": 1.0,
                "https://example.com/PYTHON-BLOG": 1.0,
                "https://example.com/python-only": 0.5,
                "https://example.com/other": 0.0
            }
        },
        
        # Path Depth Scorer Tests
        {
            "scorer_type": "path_depth",
            "config": {
                "optimal_depth": 2,
                "weight": 1.0
            },
            "urls": {
                "https://example.com/a/b": 1.0,
                "https://example.com/a": 0.5,
                "https://example.com/a/b/c": 0.5,
                "https://example.com": 0.33333333
            }
        },
        
        # Content Type Scorer Tests
        {
            "scorer_type": "content_type",
            "config": {
                "type_weights": {
                    ".html$": 1.0,
                    ".pdf$": 0.8,
                    ".jpg$": 0.6
                },
                "weight": 1.0
            },
            "urls": {
                "https://example.com/doc.html": 1.0,
                "https://example.com/doc.pdf": 0.8,
                "https://example.com/img.jpg": 0.6,
                "https://example.com/other.txt": 0.0
            }
        },
        
        # Freshness Scorer Tests
        {
            "scorer_type": "freshness",
            "config": {
                "weight": 1.0,  # Remove current_year since original doesn't support it
            },
            "urls": {
                "https://example.com/2024/01/post": 1.0,
                "https://example.com/2023/12/post": 0.9,
                "https://example.com/2022/post": 0.8,
                "https://example.com/no-date": 0.5
            }
        },
        
        # Domain Authority Scorer Tests
        {
            "scorer_type": "domain",
            "config": {
                "domain_weights": {
                    "python.org": 1.0,
                    "github.com": 0.8,
                    "medium.com": 0.6
                },
                "default_weight": 0.3,
                "weight": 1.0
            },
            "urls": {
                "https://python.org/about": 1.0,
                "https://github.com/repo": 0.8,
                "https://medium.com/post": 0.6,
                "https://unknown.com": 0.3
            }
        }
    ]

    def create_scorer(scorer_type, config):
        if scorer_type == "keyword":
            return (
                KeywordRelevanceScorer(**config),
                FastKeywordRelevanceScorer(**config)
            )
        elif scorer_type == "path_depth":
            return (
                PathDepthScorer(**config),
                FastPathDepthScorer(**config)
            )
        elif scorer_type == "content_type":
            return (
                ContentTypeScorer(**config),
                FastContentTypeScorer(**config)
            )
        elif scorer_type == "freshness":
            return (
        FreshnessScorer(**config),
        FastFreshnessScorer(**config, current_year=2024)
            )
        elif scorer_type == "domain":
            return (
                DomainAuthorityScorer(**config),
                FastDomainAuthorityScorer(**config)
            )

    def run_accuracy_test():
        print("\nAccuracy Tests:")
        print("-" * 50)
        
        all_passed = True
        for test_case in test_cases:
            print(f"\nTesting {test_case['scorer_type']} scorer:")
            original, fast = create_scorer(
                test_case['scorer_type'],
                test_case['config']
            )
            
            for url, expected in test_case['urls'].items():
                orig_score = round(original.score(url), 8)
                fast_score = round(fast.score(url), 8)
                expected = round(expected, 8)
                
                if abs(orig_score - expected) > 0.00001:
                    print(f"❌ Original Failed: URL '{url}'")
                    print(f"   Expected: {expected}, Got: {orig_score}")
                    all_passed = False
                else:
                    print(f"✅ Original Passed: URL '{url}'")
                    
                if abs(fast_score - expected) > 0.00001:
                    print(f"❌ Fast Failed: URL '{url}'")
                    print(f"   Expected: {expected}, Got: {fast_score}")
                    all_passed = False
                else:
                    print(f"✅ Fast Passed: URL '{url}'")
                    
        return all_passed

    def run_composite_test():
        print("\nTesting Composite Scorer:")
        print("-" * 50)
        
        # Create test data
        test_urls = {
            "https://python.org/blog/2024/01/new-release.html":0.86666667,
            "https://github.com/repo/old-code.pdf": 0.62,
            "https://unknown.com/random": 0.26
        }
        
        # Create composite scorers with all types
        original_scorers = []
        fast_scorers = []
        
        for test_case in test_cases:
            orig, fast = create_scorer(
                test_case['scorer_type'],
                test_case['config']
            )
            original_scorers.append(orig)
            fast_scorers.append(fast)
            
        original_composite = CompositeScorer(original_scorers, normalize=True)
        fast_composite = FastCompositeScorer(fast_scorers, normalize=True)
        
        all_passed = True
        for url, expected in test_urls.items():
            orig_score = round(original_composite.score(url), 8)
            fast_score = round(fast_composite.score(url), 8)
            
            if abs(orig_score - expected) > 0.00001:
                print(f"❌ Original Composite Failed: URL '{url}'")
                print(f"   Expected: {expected}, Got: {orig_score}")
                all_passed = False
            else:
                print(f"✅ Original Composite Passed: URL '{url}'")
                
            if abs(fast_score - expected) > 0.00001:
                print(f"❌ Fast Composite Failed: URL '{url}'")
                print(f"   Expected: {expected}, Got: {fast_score}")
                all_passed = False
            else:
                print(f"✅ Fast Composite Passed: URL '{url}'")
                
        return all_passed

    # Run tests
    print("Running Scorer Tests...")
    accuracy_passed = run_accuracy_test()
    composite_passed = run_composite_test()
    
    if accuracy_passed and composite_passed:
        print("\n✨ All tests passed!")
        # Note: Already have performance tests in run_scorer_performance_test()
    else:
        print("\n❌ Some tests failed!")

    

if __name__ == "__main__":
    run_scorer_performance_test()
    # test_scorers()