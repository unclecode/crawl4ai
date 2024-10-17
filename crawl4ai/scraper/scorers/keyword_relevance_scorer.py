from .url_scorer import URLScorer
from typing import List

class KeywordRelevanceScorer(URLScorer):
    def __init__(self,keywords: List[str]):
        self.keyworkds = keywords
    def score(self, url: str) -> float:
        #TODO: This is a stub. Will implement this later.
        return 1