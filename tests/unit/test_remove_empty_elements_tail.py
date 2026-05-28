"""Regression tests for https://github.com/unclecode/crawl4ai/issues/1938

remove_empty_elements_fast() must preserve the .tail text of removed elements.

In lxml, when an element is removed via parent.remove(el), any trailing text
stored in el.tail is silently discarded.  The fix rescues that text by
appending it to the previous sibling's tail (or the parent's text).
"""

from lxml import html as lhtml


def _get_remove_empty_elements_fast():
    """Extract remove_empty_elements_fast without importing the full crawl4ai package."""
    import sys
    import types

    # Stub the crawl4ai package and its transitive sub-modules so we can load
    # content_scraping_strategy.py without needing playwright, OpenSSL, etc.
    stubs = [
        "crawl4ai",
        "crawl4ai.async_logger",
        "crawl4ai.config",
        "crawl4ai.models",
        "crawl4ai.utils",
        "crawl4ai.content_filter_strategy",
        "crawl4ai.extraction_strategy",
        "crawl4ai.le",
        "crawl4ai.le.legacy",
        "crawl4ai.le.legacy.model_loader",
    ]
    for mod_name in stubs:
        if mod_name not in sys.modules:
            m = types.ModuleType(mod_name)
            if "." in mod_name:
                m.__path__ = []  # type: ignore[attr-defined]
            sys.modules[mod_name] = m

    # -- crawl4ai.config symbols --
    config_mod = sys.modules["crawl4ai.config"]
    config_mod.MIN_WORD_THRESHOLD = 5  # type: ignore[attr-defined]
    config_mod.IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD = 5  # type: ignore[attr-defined]
    config_mod.IMAGE_SCORE_THRESHOLD = 0.5  # type: ignore[attr-defined]
    config_mod.ONLY_TEXT_ELIGIBLE_TAGS = set()  # type: ignore[attr-defined]
    config_mod.IMPORTANT_ATTRS = []  # type: ignore[attr-defined]
    config_mod.SOCIAL_MEDIA_DOMAINS = set()  # type: ignore[attr-defined]

    # -- crawl4ai.utils symbols --
    utils_mod = sys.modules["crawl4ai.utils"]
    for attr in [
        "extract_metadata",
        "normalize_url",
        "is_external_url",
        "get_base_domain",
        "extract_metadata_using_lxml",
        "extract_page_context",
        "calculate_link_intrinsic_score",
    ]:
        setattr(utils_mod, attr, lambda *a, **kw: None)  # type: ignore[attr-defined]

    # -- crawl4ai.models symbols --
    models_mod = sys.modules["crawl4ai.models"]
    for attr in ["ScrapingResult", "MediaItem", "Link", "Media", "Links"]:
        setattr(models_mod, attr, object)  # type: ignore[attr-defined]

    import importlib.util
    import pathlib

    # Remove any stale cached module from a previous test run.
    sys.modules.pop("crawl4ai.content_scraping_strategy", None)

    path = pathlib.Path(__file__).parent.parent.parent / "crawl4ai" / "content_scraping_strategy.py"
    spec = importlib.util.spec_from_file_location("crawl4ai.content_scraping_strategy", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "crawl4ai"
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    assert hasattr(mod, "LXMLWebScrapingStrategy"), (
        "LXMLWebScrapingStrategy not found — check stubs above"
    )
    return mod.LXMLWebScrapingStrategy.remove_empty_elements_fast


_fn = _get_remove_empty_elements_fast()


def _call(root, word_count_threshold=1):
    """Invoke the unbound method with a placeholder self=None."""
    _fn(None, root, word_count_threshold=word_count_threshold)


def _parse(html_fragment: str) -> lhtml.HtmlElement:
    """Parse an HTML fragment and return the root element."""
    return lhtml.fragment_fromstring(html_fragment)


def test_tail_after_removed_element_is_preserved():
    """Text following a removed empty element must not be dropped.

    HTML:  <div><span></span>trailing text</div>
    The <span> has no text content — it will be removed.
    "trailing text" lives in span.tail and must survive.
    """
    root = _parse("<div><span></span>trailing text</div>")
    _call(root)
    result = lhtml.tostring(root, encoding="unicode")
    assert "trailing text" in result, (
        f"remove_empty_elements_fast() dropped the tail text. HTML: {result!r}"
    )


def test_tail_appended_to_previous_sibling():
    """When a non-first empty element is removed, its tail joins the previous sibling."""
    # <div><b>kept</b><span></span> and this text</div>
    root = _parse("<div><b>kept</b><span></span> and this text</div>")
    _call(root)
    result = lhtml.tostring(root, encoding="unicode")
    assert "and this text" in result, (
        f"Tail text after removed element was dropped. HTML: {result!r}"
    )
    assert "<span>" not in result, "Empty <span> should have been removed"


def test_tail_merged_into_parent_text_when_first_child():
    """When the first child is removed, its tail merges into the parent's text."""
    # <div><span></span>after first child</div>  (no previous sibling)
    root = _parse("<div><span></span>after first child</div>")
    _call(root)
    result = lhtml.tostring(root, encoding="unicode")
    assert "after first child" in result, (
        f"Tail of first child was dropped after removal. HTML: {result!r}"
    )
