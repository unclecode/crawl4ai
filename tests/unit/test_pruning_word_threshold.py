import pytest

from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.content_filter_strategy_lxml import PruningContentFilterLXML

HTML = "<p>one two</p>"
pytestmark = pytest.mark.filterwarnings(
    "ignore:PruningContentFilter .*deprecated:DeprecationWarning"
)


@pytest.mark.parametrize(
    "filter_class", [PruningContentFilter, PruningContentFilterLXML]
)
def test_per_call_threshold_can_disable_constructor_threshold(filter_class):
    content_filter = filter_class(min_word_threshold=3, threshold=0)
    assert content_filter.filter_content(HTML) == []
    assert content_filter.filter_content(HTML, min_word_threshold=0) == [HTML]
    assert content_filter.filter_content(HTML) == []


@pytest.mark.parametrize(
    "filter_class", [PruningContentFilter, PruningContentFilterLXML]
)
def test_per_call_threshold_can_enable_word_count(filter_class):
    content_filter = filter_class(threshold=0)
    assert content_filter.filter_content(HTML, min_word_threshold=2) == [HTML]
    assert content_filter.filter_content(HTML, min_word_threshold=3) == []
    assert content_filter.filter_content(HTML) == [HTML]
