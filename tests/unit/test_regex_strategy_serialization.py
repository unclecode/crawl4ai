"""RegexExtractionStrategy survives CrawlerRunConfig.dump()/load().

to_serializable_dict() rebuilds an object from attributes named after its
constructor arguments. RegexExtractionStrategy did not keep `pattern` or
`custom`, so dump() sent it as {"params": {}} and the loaded copy (on the
Docker server, or anywhere else) had no patterns and extracted nothing.
"""

import json

import pytest

from crawl4ai import CrawlerRunConfig, RegexExtractionStrategy
from crawl4ai.async_configs import Provenance, UntrustedConfigError

TEXT = "Contact sales@example.com or see https://example.com/pricing (SKU-1234)"


def _roundtrip(strategy, provenance=Provenance.TRUSTED):
    # json round-trip: what Crawl4aiDockerClient puts on the wire.
    wire = json.loads(json.dumps(CrawlerRunConfig(extraction_strategy=strategy).dump()))
    return CrawlerRunConfig.load(wire, provenance=provenance).extraction_strategy


def _values(strategy):
    return sorted((m["label"], m["value"]) for m in strategy.extract("u", TEXT))


@pytest.mark.parametrize("provenance", [Provenance.TRUSTED, Provenance.UNTRUSTED])
def test_builtin_patterns_survive_dump_load(provenance):
    strategy = RegexExtractionStrategy(
        pattern=RegexExtractionStrategy.Email | RegexExtractionStrategy.Url
    )
    loaded = _roundtrip(strategy, provenance)

    assert _values(loaded) == _values(strategy)
    assert {label for label, _ in _values(loaded)} == {"email", "url"}


@pytest.mark.parametrize(
    "custom", [{"sku": r"SKU-\d+"}, [("sku", r"SKU-\d+")]], ids=["dict", "pairs"]
)
def test_custom_patterns_survive_dump_load(custom):
    strategy = RegexExtractionStrategy(custom=custom)
    loaded = _roundtrip(strategy)

    assert _values(loaded) == [("sku", "SKU-1234")]


def test_custom_patterns_from_iterator_are_kept():
    strategy = RegexExtractionStrategy(custom=iter([("sku", r"SKU-\d+")]))

    assert _values(strategy) == [("sku", "SKU-1234")]
    assert _values(_roundtrip(strategy)) == [("sku", "SKU-1234")]


def test_untrusted_body_still_refuses_custom_patterns():
    # dump() now carries `custom`, so the server's ReDoS gate refuses it
    # loudly instead of silently running with no patterns.
    with pytest.raises(UntrustedConfigError):
        _roundtrip(
            RegexExtractionStrategy(custom={"sku": r"SKU-\d+"}), Provenance.UNTRUSTED
        )


def test_default_strategy_still_dumps_no_params():
    dumped = CrawlerRunConfig(extraction_strategy=RegexExtractionStrategy()).dump()

    assert dumped["params"]["extraction_strategy"]["params"] == {}
