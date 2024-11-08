from .url_filter import URLFilter
from re import Pattern
from typing import List, Union
import re
import fnmatch


class URLPatternFilter(URLFilter):
    """Filter URLs based on glob patterns or regex"""
    
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

# class URLPatternFilter(URLFilter):
#     def __init__(self, pattern: Pattern):
#         self.pattern = pattern
#     def apply(self, url: str) -> bool:
#         #TODO: This is a stub. Will implement this later.
#         return True