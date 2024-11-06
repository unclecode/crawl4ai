from .url_filter import URLFilter
from re import Pattern

class URLPatternFilter(URLFilter):
    def __init__(self, pattern: Pattern):
        self.pattern = pattern
    def apply(self, url: str) -> bool:
        #TODO: This is a stub. Will implement this later.
        return True