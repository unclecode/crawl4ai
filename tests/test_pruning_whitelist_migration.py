import pytest

from crawl4ai.content_filter_strategy import (
    PruningContentFilter,
    PruningContentFilterLXML,
)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@pytest.mark.parametrize(
    "filter_class", [PruningContentFilter, PruningContentFilterLXML]
)
@pytest.mark.parametrize(
    "preservation",
    [{"preserve_classes": ["credit"]}, {"preserve_tags": ["cite"]}],
)
def test_pruning_migration_preserves_attribution(filter_class, preservation):
    html = """
    <main>
      <p>This paragraph describes how to process and preserve crawl results.</p>
      <cite class="byline credit"><span>Ada</span></cite>
      <div class="credit-card">Unrelated</div>
      <nav class="credit"><cite>Navigation</cite></nav>
    </main>
    """
    options = {"min_word_threshold": 4}
    ordinary = DefaultMarkdownGenerator(content_filter=filter_class(**options))
    preserved = DefaultMarkdownGenerator(
        content_filter=filter_class(**options, **preservation)
    )

    assert "Ada" not in ordinary.generate_markdown(html).fit_markdown
    result = preserved.generate_markdown(html)
    assert "Ada" in result.fit_markdown
    assert "<span>Ada</span>" in result.fit_html
    assert "Unrelated" not in result.fit_markdown
    assert "Navigation" not in result.fit_markdown


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@pytest.mark.parametrize(
    "filter_class", [PruningContentFilter, PruningContentFilterLXML]
)
def test_pruning_migration_preserves_body_children(filter_class):
    html = '<body class="fit-content"><p>Short credit.</p><nav>Menu</nav></body>'
    content_filter = filter_class(
        min_word_threshold=10, preserve_classes=["fit-content"]
    )
    assert content_filter.filter_content(html) == ["<p>Short credit.</p>"]


def test_default_lxml_pruning_still_drops_low_scoring_content():
    html = (
        "<main><p>This paragraph has enough words to survive content pruning.</p>"
        "<cite>Credit</cite></main>"
    )
    content_filter = PruningContentFilterLXML(min_word_threshold=5)
    result = DefaultMarkdownGenerator(content_filter=content_filter).generate_markdown(
        html
    )
    assert "enough words" in result.fit_markdown
    assert "Credit" not in result.fit_markdown
