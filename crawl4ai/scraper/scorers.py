# from .url_scorer import URLScorer
# from .keyword_relevance_scorer import KeywordRelevanceScorer

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from urllib.parse import urlparse, unquote
import re
from collections import defaultdict
import math
import logging

@dataclass
class ScoringStats:
    """Statistics for URL scoring"""
    urls_scored: int = 0
    total_score: float = 0.0
    min_score: float = float('inf')
    max_score: float = float('-inf')
    
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

class URLScorer(ABC):
    """Base class for URL scoring strategies"""
    
    def __init__(self, weight: float = 1.0, name: str = None):
        self.weight = weight
        self.name = name or self.__class__.__name__
        self.stats = ScoringStats()
        self.logger = logging.getLogger(f"urlscorer.{self.name}")

    @abstractmethod
    def _calculate_score(self, url: str) -> float:
        """Calculate the raw score for a URL"""
        pass

    def score(self, url: str) -> float:
        """Calculate the weighted score for a URL"""
        raw_score = self._calculate_score(url)
        weighted_score = raw_score * self.weight
        self.stats.update(weighted_score)
        return weighted_score

class CompositeScorer(URLScorer):
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

class KeywordRelevanceScorer(URLScorer):
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
    
    def __init__(self, keywords: List[str], weight: float = 1.0,
                 case_sensitive: bool = False):
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
            1 for pattern in self.patterns
            if pattern.search(decoded_url)
        )
        # Normalize score between 0 and 1
        return total_matches / len(self.patterns) if self.patterns else 0.0

class PathDepthScorer(URLScorer):
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
        depth = len([x for x in path.split('/') if x])
        
        # Score decreases as we move away from optimal depth
        distance_from_optimal = abs(depth - self.optimal_depth)
        return 1.0 / (1.0 + distance_from_optimal)

class ContentTypeScorer(URLScorer):
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
            re.compile(pattern): weight
            for pattern, weight in self.type_weights.items()
        }

    def _calculate_score(self, url: str) -> float:
        """Calculate score based on content type matching"""
        for pattern, weight in self.patterns.items():
            if pattern.search(url):
                return weight
        return 0.0

class FreshnessScorer(URLScorer):
    """Score URLs based on freshness indicators.
    
    freshness_scorer = FreshnessScorer(weight=0.9)

    Score based on date indicators in URLs
    Multiple date format support
    Recency weighting"""
    
    def __init__(self, weight: float = 1.0):
        super().__init__(weight=weight)
        self.date_patterns = [
            r'/(\d{4})/(\d{2})/(\d{2})/',  # yyyy/mm/dd
            r'(\d{4})[-_](\d{2})[-_](\d{2})',  # yyyy-mm-dd
            r'/(\d{4})/',  # year only
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

class DomainAuthorityScorer(URLScorer):
    """Score URLs based on domain authority.

    authority_scorer = DomainAuthorityScorer({
        "python.org": 1.0,
        "github.com": 0.9,
        "medium.com": 0.7
    })

    Score based on domain importance
    Configurable domain weights
    Default weight for unknown domains"""
    
    def __init__(self, domain_weights: Dict[str, float], 
                 default_weight: float = 0.5, weight: float = 1.0):
        super().__init__(weight=weight)
        self.domain_weights = domain_weights
        self.default_weight = default_weight

    def _calculate_score(self, url: str) -> float:
        """Calculate score based on domain authority"""
        domain = urlparse(url).netloc.lower()
        return self.domain_weights.get(domain, self.default_weight)

def create_balanced_scorer() -> CompositeScorer:
    """Create a balanced composite scorer"""
    return CompositeScorer([
        KeywordRelevanceScorer(
            keywords=["article", "blog", "news", "research"],
            weight=1.0
        ),
        PathDepthScorer(
            optimal_depth=3,
            weight=0.7
        ),
        ContentTypeScorer(
            type_weights={
                r'\.html?$': 1.0,
                r'\.pdf$': 0.8,
                r'\.xml$': 0.6
            },
            weight=0.8
        ),
        FreshnessScorer(
            weight=0.9
        )
    ])

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