"""Unit tests for chunking_strategy.py."""
import sys
import types
from unittest.mock import patch, MagicMock
from crawl4ai.chunking_strategy import TopicSegmentationChunking


class TestTopicSegmentationExtractKeywords:

    def test_extract_keywords_does_not_raise(self):
        # extract_keywords previously called the non-existent `nl.toknize`
        # instead of `nl.tokenize`, raising AttributeError on every call.
        # __init__ is bypassed since it builds a real TextTilingTokenizer,
        # which needs NLTK data unrelated to this bug.
        #
        # nltk's real `corpus`/`tokenize` modules are lazy-loaded and touch
        # disk data on first attribute access even under mock.patch, so a
        # bare stand-in module is swapped into sys.modules instead.
        fake_nltk = types.ModuleType("nltk")
        fake_nltk.tokenize = MagicMock()
        fake_nltk.tokenize.word_tokenize.return_value = ["fast", "car", "fast", "car", "road"]
        fake_nltk.corpus = MagicMock()
        fake_nltk.corpus.stopwords.words.return_value = ["the", "a"]

        chunker = TopicSegmentationChunking.__new__(TopicSegmentationChunking)
        chunker.num_keywords = 2

        with patch.dict(sys.modules, {"nltk": fake_nltk}):
            keywords = chunker.extract_keywords("Fast car, fast car, on the road.")

        assert keywords == ["fast", "car"]
