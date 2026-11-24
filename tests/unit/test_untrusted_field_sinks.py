"""Allowlisted untrusted fields that reached code, model-load or regex sinks.

Three 0.9.5 reports, one gate (crawl4ai/async_configs.py): a field the
untrusted gate let through by name still carried code (wait_for "js:..."), a
HuggingFace repo id (CosineStrategy.model_name), or a regex that backtracks
for hours with the GIL held (RegexExtractionStrategy.custom,
RegexChunking.patterns, schema fields of type "regex").

No browser, no network, no model download: everything here is the gate.
"""
import pytest

from crawl4ai.async_configs import CrawlerRunConfig, Provenance, UntrustedConfigError


def _load(params, provenance=Provenance.UNTRUSTED):
    return CrawlerRunConfig.load(
        {"type": "CrawlerRunConfig", "params": params}, provenance=provenance
    )


# ── wait_for ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "value",
    [
        "js:() => { fetch('http://x/'); return true; }",
        "() => { fetch('http://x/'); return true; }",
        "function () { return true; }",
    ],
)
def test_untrusted_wait_for_javascript_refused(value):
    with pytest.raises(UntrustedConfigError):
        _load({"wait_for": value})


def test_untrusted_bare_wait_for_is_pinned_to_css():
    """A bare value used to fall back to JS when it was not a valid selector."""
    assert _load({"wait_for": "fetch('http://x/'); return true;"}).wait_for == (
        "css:fetch('http://x/'); return true;"
    )
    assert _load({"wait_for": "#main"}).wait_for == "css:#main"
    assert _load({"wait_for": "css:#main"}).wait_for == "css:#main"


def test_trusted_wait_for_unchanged():
    value = "js:() => true"
    assert _load({"wait_for": value}, Provenance.TRUSTED).wait_for == value


# ── CosineStrategy.model_name ──────────────────────────────────────────


def test_untrusted_cosine_model_name_refused():
    with pytest.raises(UntrustedConfigError):
        _load({"extraction_strategy": {
            "type": "CosineStrategy",
            "params": {"model_name": "attacker-org/evil-model"},
        }})


# ── caller-supplied regex ──────────────────────────────────────────────


def test_untrusted_regex_strategy_custom_refused():
    with pytest.raises(UntrustedConfigError):
        _load({"extraction_strategy": {
            "type": "RegexExtractionStrategy",
            "params": {"custom": {"evil": "(a+)+$"}},
        }})


def test_untrusted_regex_strategy_builtins_still_allowed():
    cfg = _load({"extraction_strategy": {
        "type": "RegexExtractionStrategy", "params": {"pattern": 1},
    }})
    assert type(cfg.extraction_strategy).__name__ == "RegexExtractionStrategy"


def test_untrusted_regex_chunking_patterns_refused():
    with pytest.raises(UntrustedConfigError):
        _load({"chunking_strategy": {
            "type": "RegexChunking", "params": {"patterns": ["(a+)+$"]},
        }})


def _schema(field):
    return {"name": "x", "baseSelector": "p", "fields": [field]}


REGEX_FIELD = {"name": "f", "selector": "span", "type": "regex", "pattern": "(a+)+$"}


@pytest.mark.parametrize(
    "schema",
    [
        _schema(REGEX_FIELD),
        # nested inside another field
        _schema({"name": "n", "selector": "div", "type": "nested", "fields": [REGEX_FIELD]}),
        # behind the {"type": "dict", "value": ...} envelope
        {"type": "dict", "value": _schema(REGEX_FIELD)},
    ],
)
@pytest.mark.parametrize(
    "strategy",
    ["JsonCssExtractionStrategy", "JsonXPathExtractionStrategy", "JsonLxmlExtractionStrategy"],
)
def test_untrusted_schema_regex_field_refused(strategy, schema):
    with pytest.raises(UntrustedConfigError):
        _load({"extraction_strategy": {"type": strategy, "params": {"schema": schema}}})


def test_untrusted_schema_without_regex_still_allowed():
    cfg = _load({"extraction_strategy": {
        "type": "JsonCssExtractionStrategy",
        "params": {"schema": _schema({"name": "t", "selector": "h1", "type": "text"})},
    }})
    assert type(cfg.extraction_strategy).__name__ == "JsonCssExtractionStrategy"


def test_trusted_regex_unchanged():
    cfg = _load({"chunking_strategy": {
        "type": "RegexChunking", "params": {"patterns": [r"\n"]},
    }}, Provenance.TRUSTED)
    assert cfg.chunking_strategy.patterns == [r"\n"]


# ── list-form "type" pipeline (report 2026-10, bypass of GHSA-j843) ─────


SCHEMA_STRATEGIES = ["JsonCssExtractionStrategy", "JsonXPathExtractionStrategy", "JsonLxmlExtractionStrategy"]


def _list_regex(steps):
    return {"name": "f", "selector": "span", "type": steps, "pattern": "(a+)+$"}


@pytest.mark.parametrize(
    "steps",
    [["regex"], ["text", "regex"], ["attribute", "regex"], ["html", "regex"],
     ["regex", "text"], ["regex", "regex"]],
)
@pytest.mark.parametrize(
    "place",
    ["fields", "nested", "list", "nested_list", "baseFields", "dict_envelope"],
)
@pytest.mark.parametrize("strategy", SCHEMA_STRATEGIES)
def test_untrusted_list_type_with_regex_refused(strategy, place, steps):
    field = _list_regex(steps)
    if place == "fields":
        schema = _schema(field)
    elif place == "baseFields":
        schema = {"name": "x", "baseSelector": "p", "baseFields": [field], "fields": []}
    elif place == "dict_envelope":
        schema = {"type": "dict", "value": _schema(field)}
    else:
        schema = _schema({"name": "n", "selector": "div", "type": place, "fields": [field]})
    with pytest.raises(UntrustedConfigError):
        _load({"extraction_strategy": {"type": strategy, "params": {"schema": schema}}})


@pytest.mark.parametrize("steps", [["text"], ["attribute", "text"], ["html"], []])
def test_untrusted_benign_list_type_still_allowed(steps):
    field = {"name": "regex", "selector": "span", "type": steps, "attribute": "title"}
    cfg = _load({"extraction_strategy": {
        "type": "JsonCssExtractionStrategy", "params": {"schema": _schema(field)},
    }})
    assert type(cfg.extraction_strategy).__name__ == "JsonCssExtractionStrategy"


def test_trusted_list_type_regex_still_runs():
    cfg = _load({"extraction_strategy": {
        "type": "JsonCssExtractionStrategy",
        "params": {"schema": _schema({"name": "n", "selector": "span",
                                      "type": ["text", "regex"], "pattern": r"(\d+)"})},
    }}, Provenance.TRUSTED)
    assert cfg.extraction_strategy.extract("raw:", "<p><span>id 42</span></p>") == [{"n": "42"}]


def test_no_untrusted_schema_reaches_re_search(monkeypatch):
    """Gate and sink agree: every field shape the untrusted gate accepts is
    run, and none of them may call the extractor's re.search."""
    import itertools
    import crawl4ai.extraction_strategy as es

    real_search = es.re.search
    ran = []

    def tripwire(pattern, *a, **k):
        # Recorded, not raised: the extractor catches per-field errors.
        if pattern == "(a+)+$":
            ran.append(pattern)
            return None
        return real_search(pattern, *a, **k)  # the library's own fixed patterns

    monkeypatch.setattr(es.re, "search", tripwire)
    words = ["text", "attribute", "html", "regex", "nested", "list", "Regex", None]
    shapes = [w for w in words] + [list(p) for n in (1, 2, 3) for p in itertools.product(words[:4], repeat=n)]
    accepted = 0
    for strategy, steps in itertools.product(SCHEMA_STRATEGIES, shapes):
        sel = "//span" if strategy == "JsonXPathExtractionStrategy" else "span"
        base = "//p" if strategy == "JsonXPathExtractionStrategy" else "p"
        field = {"name": "f", "selector": sel, "type": steps, "pattern": "(a+)+$", "attribute": "title"}
        schema = {"name": "x", "baseSelector": base, "fields": [field]}
        try:
            cfg = _load({"extraction_strategy": {"type": strategy, "params": {"schema": schema}}})
        except UntrustedConfigError:
            continue
        accepted += 1
        try:
            cfg.extraction_strategy.extract("raw:", '<p><span title="t">aaaa!</span></p>')
        except Exception:
            pass  # a malformed step may fail in other ways; only the regex matters
        assert not ran, (strategy, steps)
    assert accepted > 50  # the sweep really exercised accepted shapes


# ── DefaultMarkdownGenerator options ──────────────────────────────────
# Every key reaches html2text's update_params, which setattr()s it. Internal
# state such as the blockquote depth turns a tiny page into gigabytes.


def _md(options, provenance=Provenance.UNTRUSTED):
    return _load({"markdown_generator": {
        "type": "DefaultMarkdownGenerator", "params": {"options": options},
    }}, provenance)


@pytest.mark.parametrize(
    "options",
    [
        {"blockquote": 1_000_000_000},       # internal counter: the report
        {"outtextlist": []},                 # internal state
        {"handle": None},                    # a method
        {"ul_item_mark": "x" * 1_000_000},   # string repeated per list item
        {"ignore_links": "yes"},             # wrong type for a real option
        {"body_width": 10**12},              # out of range
        {"body_width": True},
        "not a dict",
    ],
)
def test_untrusted_markdown_options_rejected(options):
    with pytest.raises(UntrustedConfigError):
        _md(options)


@pytest.mark.parametrize(
    "options",
    [
        {"ignore_links": True},
        {"ignore_images": True, "escape_html": False, "body_width": 80},
        {"skip_internal_links": True, "citations": True, "body_width": None},
        {},
    ],
)
def test_untrusted_markdown_options_allowed(options):
    cfg = _md(options)
    assert cfg.markdown_generator.options == options


def test_trusted_markdown_options_untouched():
    cfg = _md({"blockquote": 3}, Provenance.TRUSTED)
    assert cfg.markdown_generator.options == {"blockquote": 3}


def test_untrusted_markdown_output_stays_small():
    cfg = _md({"ignore_links": True, "body_width": 0})
    html = "".join(f"<p>{c}</p>" for c in "abcdefghijklmnopqrst")
    md = cfg.markdown_generator.generate_markdown(input_html=html, base_url="https://x")
    assert len(md.raw_markdown) < 1000
