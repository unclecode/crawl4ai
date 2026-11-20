"""SEOFilter keeps its keywords and weights through to_serializable_dict().

SEOFilter compiled its keywords into a regex and kept only the pattern, so
serialization dropped `keywords` and `weights` and a loaded filter scored
pages without them.
"""

import json

from crawl4ai.async_configs import from_serializable_dict, to_serializable_dict
from crawl4ai.deep_crawling.filters import SEOFilter


def round_trip(obj):
    return from_serializable_dict(json.loads(json.dumps(to_serializable_dict(obj))))


def test_keywords_and_weights_survive_a_round_trip():
    original = SEOFilter(
        threshold=0.5, keywords=["python", "c++"], weights={"title_kw": 1.0}
    )

    back = round_trip(original)

    assert back.threshold == 0.5
    assert back.keywords == ["python", "c++"]
    assert back.weights == {"title_kw": 1.0}
    assert back._kw_patterns.pattern == original._kw_patterns.pattern


def test_default_filter_serializes_without_keywords_or_weights():
    serialized = to_serializable_dict(SEOFilter())

    assert serialized == {"type": "SEOFilter", "params": {}}
    back = round_trip(SEOFilter())
    assert back.keywords is None
    assert back._weights == SEOFilter.DEFAULT_WEIGHTS
