"""Regression test for https://github.com/unclecode/crawl4ai/issues/1909

NlpSentenceChunking.chunk() must preserve sentence order and not deduplicate.
"""

import sys
import types
from unittest.mock import patch


def _import_chunking_module():
    """Import chunking_strategy without triggering the heavy crawl4ai.__init__.

    crawl4ai/__init__.py pulls in async_webcrawler which requires OpenSSL and
    playwright at import time.  We bypass that by creating a minimal stub for
    the crawl4ai package and its transitive dependencies.
    """
    # Stub the crawl4ai package itself
    pkg = types.ModuleType("crawl4ai")
    pkg.__path__ = []  # type: ignore[attr-defined]
    sys.modules.setdefault("crawl4ai", pkg)

    # Stub crawl4ai.model_loader (imported at top level of chunking_strategy)
    loader_mod = types.ModuleType("crawl4ai.model_loader")
    loader_mod.load_nltk_punkt = lambda: None  # type: ignore[attr-defined]
    sys.modules.setdefault("crawl4ai.model_loader", loader_mod)

    # Stub crawl4ai.le.legacy.model_loader (imported inside NlpSentenceChunking.__init__)
    le_pkg = types.ModuleType("crawl4ai.le")
    le_pkg.__path__ = []  # type: ignore[attr-defined]
    sys.modules.setdefault("crawl4ai.le", le_pkg)

    legacy_pkg = types.ModuleType("crawl4ai.le.legacy")
    legacy_pkg.__path__ = []  # type: ignore[attr-defined]
    sys.modules.setdefault("crawl4ai.le.legacy", legacy_pkg)

    le_loader_mod = types.ModuleType("crawl4ai.le.legacy.model_loader")
    le_loader_mod.load_nltk_punkt = lambda: None  # type: ignore[attr-defined]
    sys.modules.setdefault("crawl4ai.le.legacy.model_loader", le_loader_mod)

    import importlib
    import importlib.util
    import os

    spec = importlib.util.spec_from_file_location(
        "crawl4ai.chunking_strategy",
        os.path.join(os.path.dirname(__file__), "../../crawl4ai/chunking_strategy.py"),
        submodule_search_locations=[],
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "crawl4ai"  # needed for relative imports
    sys.modules["crawl4ai.chunking_strategy"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_mod = _import_chunking_module()
NlpSentenceChunking = _mod.NlpSentenceChunking  # type: ignore[attr-defined]


def _make_chunker():
    """Instantiate NlpSentenceChunking without calling __init__ (avoids NLTK check)."""
    return NlpSentenceChunking.__new__(NlpSentenceChunking)


def test_nlp_sentence_chunking_preserves_order():
    """chunk() must return sentences in document order, not arbitrary set order."""
    sentences = ["Alice likes cats.", "Bob likes dogs.", "Carol likes fish."]
    text = " ".join(sentences)
    chunker = _make_chunker()

    with patch("nltk.tokenize.sent_tokenize", return_value=sentences):
        result = chunker.chunk(text)

    assert result == sentences, (
        f"chunk() returned sentences in wrong order: {result}. "
        "Using list(set(...)) destroys sentence order; fix: return sens directly."
    )


def test_nlp_sentence_chunking_keeps_duplicates():
    """chunk() must not silently deduplicate repeated sentences."""
    sentences = ["This is a test.", "This is a test.", "Another sentence."]
    text = " ".join(sentences)
    chunker = _make_chunker()

    with patch("nltk.tokenize.sent_tokenize", return_value=sentences):
        result = chunker.chunk(text)

    assert result.count("This is a test.") == 2, (
        "chunk() silently dropped a duplicate sentence. "
        "list(set(...)) removes duplicates; fix: return sens directly."
    )
