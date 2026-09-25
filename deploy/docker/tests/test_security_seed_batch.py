"""
#2288: one refused seed must not take a whole /crawl batch down.

`_normalize_and_validate_seeds` used to raise on the first seed the destination
check turned away, so a single internal address -- or a single name that does
not resolve, e.g. a dead domain in a stale sitemap -- failed the whole request
with a 400 and no results at all. The caller could not tell WHICH seed it was,
so its only recovery was to split the batch and retry.

A refused seed is now reported as one failed result among the batch, shaped like
the robots.txt refusal `AsyncWebCrawler.arun()` already returns. The opaque
message is carried through verbatim, so this does not become a resolution
oracle: an internal address and an NXDOMAIN still produce the same "URL
blocked", and the caller already knows the hostname it sent.

A request with nothing crawlable left is still a 400 -- there is no batch to
report per-URL failures in, and that keeps a single blocked URL a 400 for the
/md, /llm and /crawl/stream callers.

Behavioral tests run fully offline: `seeds_dns` models a resolver that fails
for specific hosts, and the crawler pool is mocked, so no browser is launched.
"""

import asyncio
import ipaddress
import json
import socket

import pytest
from fastapi import HTTPException

import api
from api import (
    _append_refused_results,
    _normalize_and_validate_seeds,
    _prepend_refused_results,
    _refused_seed_result,
    _require_crawlable_seeds,
    _SeedBatch,
)
from egress_broker import EgressBlocked

pytestmark = pytest.mark.posture

BLOCKED_DETAIL = "URL blocked (SSRF protection): URL blocked"
DEAD_HOST = "https://no-such-host-12345.example/"
GOOD_HOST = "https://example.com/"
INTERNAL = "http://169.254.169.254/latest/meta-data/"


# ─────────────────────────── fixtures ───────────────────────────

class _SeedsDns:
    """Offline resolver for the seed-batch tests.

    Modelled on the real thing in the three ways these tests depend on:

    * a literal IP resolves to itself, so a literal internal address is
      refused by the real `is_global` rule rather than by the fixture
      (conftest's `offline_dns` answers every host with one public IP, which
      would quietly allow `http://169.254.169.254/`);
    * a host in `dead` fails to resolve, modelling the NXDOMAIN of a stale
      sitemap entry;
    * a host in `answers` resolves to the given IP, so a hostname can be made
      internal;
    * anything else resolves to one public address, so no test here can reach
      the network by accident.
    """

    PUBLIC = "93.184.216.34"

    def __init__(self):
        self.dead = set()
        self.answers = {}

    def add_dead(self, *hosts):
        self.dead.update(hosts)

    def answer(self, host, ip):
        self.answers[host] = ip

    def getaddrinfo(self, host, port, *args, **kwargs):
        if host in self.dead:
            raise socket.gaierror(-2, "Name or service not known")
        try:
            # A literal address (v4 or v6) resolves to itself, which is what
            # lets the real is_global rule reject http://[::1]/ and friends.
            literal = ipaddress.ip_address(host)
        except ValueError:
            literal = None
        if literal is not None:
            ip, family = str(literal), (
                socket.AF_INET6 if literal.version == 6 else socket.AF_INET
            )
        else:
            ip, family = self.answers.get(host, self.PUBLIC), socket.AF_INET
        return [(family, socket.SOCK_STREAM, 6, "", (ip, port or 0))]


@pytest.fixture
def seeds_dns(monkeypatch):
    resolver = _SeedsDns()
    monkeypatch.setattr(socket, "getaddrinfo", resolver.getaddrinfo)
    return resolver


@pytest.fixture
def refuse_dns(seeds_dns):
    """A resolver under which the classic internal targets are refused."""
    seeds_dns.answer("internal.example", "169.254.169.254")
    seeds_dns.answer("ten.example", "10.0.0.1")
    seeds_dns.answer("lan.example", "192.168.0.1")
    return seeds_dns


def _crawled(url, success=True, error=None):
    """A real CrawlResult, so model_dump()/serialization is exercised for real."""
    from crawl4ai.models import CrawlResult

    return CrawlResult(
        url=url,
        html="<html><body>hi</body></html>" if success else "",
        success=success,
        status_code=200 if success else 500,
        error_message=error,
    )


@pytest.fixture
def pooled_crawler(monkeypatch):
    """Mock the pooled crawler so /crawl needs no browser.

    Returns (patch, calls) where `calls` records the urls/config each arun*
    received, which is how the tests check the refused seed was never handed to
    the crawler at all.
    """
    import crawler_pool

    calls = {"arun": [], "arun_many": []}

    class Pooled:
        active_requests = 0
        # _dispose_crawler branches on this; a non-PDF strategy takes the
        # release_crawler path, which is mocked.
        crawler_strategy = None

        async def arun(self, url, config=None, dispatcher=None):
            calls["arun"].append(url)
            return _crawled(url)

        async def arun_many(self, urls=None, config=None, dispatcher=None, **kw):
            urls = list(urls or [])
            calls["arun_many"].append(urls)
            return [_crawled(u) for u in urls]

    crawler = Pooled()

    async def get_crawler(*a, **kw):
        return crawler

    async def release_crawler(*a, **kw):
        return None

    monkeypatch.setattr(crawler_pool, "get_crawler", get_crawler)
    monkeypatch.setattr(crawler_pool, "release_crawler", release_crawler)
    return crawler, calls


def _auth():
    from auth import create_access_token

    return {"Authorization": f"Bearer {create_access_token({'sub': 'u@x.com'})}"}


def _stock_crawl_config():
    """The `config` dict handle_crawl_request reads, as config.yml supplies it."""
    return {
        "crawler": {
            "memory_threshold_percent": 90,
            "rate_limiter": {"enabled": False, "base_delay": [0.1, 0.3]},
            "base_config": {},
        },
        "limits": {"wall_clock_s": 0},
    }


# ───────────────── seed partitioning (unit) ─────────────────

class TestSeedPartitioning:
    def test_one_refused_seed_does_not_reject_the_batch(self, refuse_dns):
        """The reported bug: an internal seed must not raise for its neighbours."""
        batch = _normalize_and_validate_seeds([GOOD_HOST, INTERNAL])

        assert batch.crawlable == [GOOD_HOST]
        assert batch.refused == [(INTERNAL, BLOCKED_DETAIL)]

    def test_unresolvable_seed_is_refused_not_fatal(self, seeds_dns):
        """A dead domain from a stale sitemap is a per-URL failure, not a 400."""
        seeds_dns.add_dead("no-such-host-12345.example")
        batch = _normalize_and_validate_seeds([GOOD_HOST, DEAD_HOST])

        assert batch.crawlable == [GOOD_HOST]
        assert batch.refused == [(DEAD_HOST, BLOCKED_DETAIL)]

    def test_refusal_message_is_identical_for_internal_and_nxdomain(
        self, refuse_dns, seeds_dns
    ):
        """The no-oracle property: one message, so a refusal says nothing about
        why the host was refused beyond what the caller already knows."""
        seeds_dns.add_dead("no-such-host-12345.example")
        internal = _normalize_and_validate_seeds([INTERNAL])
        dead = _normalize_and_validate_seeds([DEAD_HOST])

        assert internal.refused[0][1] == dead.refused[0][1] == BLOCKED_DETAIL
        assert "169.254" not in internal.refused[0][1]
        assert "no-such-host" not in dead.refused[0][1]

    def test_every_refused_seed_is_collected_not_just_the_first(self, refuse_dns):
        """Validation must not stop at the first refusal."""
        batch = _normalize_and_validate_seeds(
            [GOOD_HOST, "http://10.0.0.1/", "http://192.168.0.1/", GOOD_HOST + "b"]
        )

        assert batch.crawlable == [GOOD_HOST, GOOD_HOST + "b"]
        assert [url for url, _ in batch.refused] == [
            "http://10.0.0.1/",
            "http://192.168.0.1/",
        ]

    def test_nothing_refused_is_a_passthrough(self, seeds_dns):
        """Unchanged behaviour for a clean batch: same seeds, no refusals."""
        batch = _normalize_and_validate_seeds([GOOD_HOST, "https://iana.org/"])

        assert batch.refused == []
        assert batch.crawlable == [GOOD_HOST, "https://iana.org/"]

    def test_bare_host_is_normalized_before_it_is_validated(self, refuse_dns):
        """The https:// prefix is applied first, so 'localhost' is refused as
        https://localhost and never reached the checker scheme-less."""
        batch = _normalize_and_validate_seeds(["internal.example"])

        assert batch.crawlable == []
        assert batch.refused == [("https://internal.example", BLOCKED_DETAIL)]

    def test_raw_urls_stay_crawlable(self, seeds_dns):
        """raw: is inline HTML with no network fetch, so it is never refused."""
        batch = _normalize_and_validate_seeds(["raw:<p>hello</p>", "raw://<p>hi</p>"])

        assert batch.crawlable == ["raw:<p>hello</p>", "raw://<p>hi</p>"]
        assert batch.refused == []

    def test_refused_url_echoes_the_normalized_form(self, refuse_dns):
        """The refused record carries the normalized URL, because that is the
        string the caller has to recognise in the response."""
        batch = _normalize_and_validate_seeds(["internal.example"])

        assert batch.refused[0][0] == "https://internal.example"


# ───────────────── all-refused stays a 400 ─────────────────

class TestRequireCrawlableSeeds:
    def test_all_refused_raises_the_same_400(self, refuse_dns):
        batch = _normalize_and_validate_seeds([INTERNAL, "http://10.0.0.1/"])

        with pytest.raises(HTTPException) as raised:
            _require_crawlable_seeds(batch)

        assert raised.value.status_code == 400
        assert raised.value.detail == BLOCKED_DETAIL

    def test_partially_refused_does_not_raise(self, refuse_dns):
        _require_crawlable_seeds(_normalize_and_validate_seeds([GOOD_HOST, INTERNAL]))

    def test_clean_batch_does_not_raise(self, seeds_dns):
        _require_crawlable_seeds(_normalize_and_validate_seeds([GOOD_HOST]))

    def test_empty_batch_does_not_raise(self):
        """No seeds is a request-shape error handled by the route, not a refusal."""
        _require_crawlable_seeds(_SeedBatch([], []))


# ───────────────── the failed result's shape ─────────────────

class TestRefusedResultShape:
    def test_matches_the_robots_txt_refusal(self):
        """Same contract as the robots.txt refusal in async_webcrawler.arun():
        success False, 403, the reason in error_message."""
        result = _refused_seed_result(INTERNAL, BLOCKED_DETAIL)

        assert result.url == INTERNAL
        assert result.success is False
        assert result.status_code == 403
        assert result.error_message == BLOCKED_DETAIL
        assert result.response_headers == {"X-Egress-Status": "Blocked by egress policy"}

    def test_serializes_with_the_same_keys_as_a_crawled_result(self):
        """A refused seed is a CrawlResult, not a hand-rolled dict, so a client
        reading result['links'] / result['media'] does not hit a KeyError."""
        dumped = _refused_seed_result(INTERNAL, BLOCKED_DETAIL).model_dump()
        crawled = _crawled(GOOD_HOST).model_dump()

        assert set(dumped) == set(crawled)
        assert dumped["links"] == {} and dumped["media"] == {}

    def test_is_json_serializable_for_the_response(self):
        payload = _refused_seed_result(INTERNAL, BLOCKED_DETAIL).model_dump()
        assert json.loads(json.dumps(payload, default=str))["url"] == INTERNAL

    def test_survives_the_docker_clients_reconstruction(self):
        """Crawl4aiDockerClient.crawl does `CrawlResult(**r)` on every result, so
        a refused seed has to reconstruct into a CrawlResult like any other."""
        from crawl4ai.models import CrawlResult

        dumped = _refused_seed_result(INTERNAL, BLOCKED_DETAIL).model_dump()
        rebuilt = CrawlResult(**dumped)

        assert rebuilt.success is False
        assert rebuilt.status_code == 403
        assert rebuilt.error_message == BLOCKED_DETAIL


class TestAppendRefusedResults:
    def test_appends_one_failure_per_refused_seed(self):
        crawled = [_crawled(GOOD_HOST)]
        batch = _SeedBatch([GOOD_HOST], [(INTERNAL, BLOCKED_DETAIL)])

        out = _append_refused_results(crawled, batch)

        assert len(out) == 2
        assert out[0].url == GOOD_HOST
        assert out[1].url == INTERNAL
        assert out[1].success is False

    def test_does_not_mutate_the_crawlers_list(self):
        crawled = [_crawled(GOOD_HOST)]
        _append_refused_results(crawled, _SeedBatch([GOOD_HOST], [(INTERNAL, BLOCKED_DETAIL)]))

        assert len(crawled) == 1

    def test_no_refusals_returns_the_crawlers_list_untouched(self):
        """Documented fast path: with nothing refused the crawler's own list is
        handed back, so a clean batch is not copied."""
        crawled = [_crawled(GOOD_HOST)]

        out = _append_refused_results(crawled, _SeedBatch([GOOD_HOST], []))

        assert out is crawled


class TestPrependRefusedResults:
    @pytest.mark.asyncio
    async def test_refusals_are_yielded_then_the_crawled_results(self):
        async def gen():
            yield _crawled(GOOD_HOST)

        batch = _SeedBatch([GOOD_HOST], [(INTERNAL, BLOCKED_DETAIL)])
        out = [r async for r in _prepend_refused_results(gen(), batch)]

        assert [r.url for r in out] == [INTERNAL, GOOD_HOST]
        assert out[0].success is False


# ───────────────── behavioral: /crawl ─────────────────

class TestCrawlBatchBehavioral:
    def test_reported_repro_returns_200_with_one_failed_result(
        self, stock_client, seeds_dns, pooled_crawler
    ):
        """The issue's exact input, as a client."""
        seeds_dns.add_dead("no-such-host-12345.example")
        _crawler, calls = pooled_crawler

        r = stock_client.post(
            "/crawl", json={"urls": [GOOD_HOST, DEAD_HOST]}, headers=_auth()
        )

        assert r.status_code == 200, r.text[:300]
        body = r.json()
        assert body["success"] is True
        by_url = {res["url"]: res for res in body["results"]}
        assert set(by_url) == {GOOD_HOST, DEAD_HOST}
        assert by_url[GOOD_HOST]["success"] is True
        assert by_url[DEAD_HOST]["success"] is False
        assert by_url[DEAD_HOST]["error_message"] == BLOCKED_DETAIL

    def test_the_refused_seed_is_never_handed_to_the_crawler(
        self, stock_client, refuse_dns, pooled_crawler
    ):
        """The SSRF check is a gate, not a filter applied after the fetch: the
        refused URL must not appear in the crawler's work at all."""
        _crawler, calls = pooled_crawler

        r = stock_client.post(
            "/crawl",
            json={"urls": [GOOD_HOST, "http://10.0.0.1/", "https://iana.org/"]},
            headers=_auth(),
        )

        assert r.status_code == 200, r.text[:300]
        crawled = calls["arun_many"] + calls["arun"]
        assert crawled == [[GOOD_HOST, "https://iana.org/"]]
        assert "http://10.0.0.1/" not in crawled[0]

    def test_an_internal_address_still_fails_and_still_blocks_the_fetch(
        self, stock_client, refuse_dns, pooled_crawler
    ):
        """A refused seed in a batch is a failed result, not a silent success and
        not a fetch of the internal address."""
        _crawler, calls = pooled_crawler

        r = stock_client.post(
            "/crawl", json={"urls": [GOOD_HOST, INTERNAL]}, headers=_auth()
        )

        assert r.status_code == 200, r.text[:300]
        blocked = [res for res in r.json()["results"] if res["url"] == INTERNAL]
        assert len(blocked) == 1
        assert blocked[0]["success"] is False
        assert blocked[0]["error_message"] == BLOCKED_DETAIL
        # One crawlable seed left, so arun was used -- and the refused URL was
        # not the argument.
        assert calls["arun"] == [GOOD_HOST]
        assert calls["arun_many"] == []

    def test_single_refused_url_still_400(self, stock_client, refuse_dns, pooled_crawler):
        """The one-URL contract the other endpoints and clients rely on."""
        r = stock_client.post("/crawl", json={"urls": [INTERNAL]}, headers=_auth())

        assert r.status_code == 400, f"got {r.status_code}: {r.text[:200]}"
        assert BLOCKED_DETAIL in r.text

    def test_batch_where_every_seed_is_refused_still_400(
        self, stock_client, refuse_dns, pooled_crawler
    ):
        _crawler, calls = pooled_crawler

        r = stock_client.post(
            "/crawl",
            json={"urls": [INTERNAL, "http://10.0.0.1/"]},
            headers=_auth(),
        )

        assert r.status_code == 400, f"got {r.status_code}: {r.text[:200]}"
        assert calls["arun"] == [] and calls["arun_many"] == []

    def test_clean_batch_is_unaffected(self, stock_client, seeds_dns, pooled_crawler):
        r = stock_client.post(
            "/crawl", json={"urls": [GOOD_HOST, "https://iana.org/"]}, headers=_auth()
        )

        assert r.status_code == 200, r.text[:300]
        results = r.json()["results"]
        assert len(results) == 2
        assert all(res["success"] for res in results)

    def test_empty_url_list_is_still_an_empty_success(self, pooled_crawler):
        """CrawlJobPayload.urls has no min_length and /crawl/job has no emptiness
        guard, so an empty list reaches the handler. It must keep returning the
        empty success it always did, not IndexError on urls[0] into a 500."""
        _crawler, calls = pooled_crawler

        result = asyncio.run(
            api.handle_crawl_request(
                urls=[],
                browser_config={},
                crawler_config={},
                config=_stock_crawl_config(),
            )
        )

        assert result["success"] is True
        assert result["results"] == []
        assert calls["arun"] == []
        assert calls["arun_many"] == [[]]

    def test_per_url_crawler_configs_survive_a_refused_seed(
        self, stock_client, refuse_dns, monkeypatch
    ):
        """A caller that sent per-URL configs still means them when a seed is
        refused. The list reaches arun_many unfiltered, because the dispatcher
        pairs a config to a URL by url_matcher and not by position -- filtering
        it by the surviving seeds would drop the config that matches.
        """
        from crawl4ai.async_dispatcher import BaseDispatcher

        seen = {}

        class ConfigCrawler:
            active_requests = 0
            crawler_strategy = None

            async def arun_many(self, urls=None, config=None, dispatcher=None, **kw):
                seen["urls"] = list(urls or [])
                seen["config"] = config
                return [_crawled(u) for u in seen["urls"]]

        crawler = ConfigCrawler()

        async def get_crawler(*a, **kw):
            return crawler

        async def release_crawler(*a, **kw):
            return None

        import crawler_pool

        monkeypatch.setattr(crawler_pool, "get_crawler", get_crawler)
        monkeypatch.setattr(crawler_pool, "release_crawler", release_crawler)

        r = stock_client.post(
            "/crawl",
            json={
                "urls": [GOOD_HOST, INTERNAL, "https://iana.org/"],
                "crawler_configs": [
                    {"type": "CrawlerRunConfig",
                     "params": {"screenshot": True, "url_matcher": "*example.com*"}},
                    {"type": "CrawlerRunConfig",
                     "params": {"word_count_threshold": 5, "url_matcher": "*iana.org*"}},
                    # A catch-all, so one config is not needed per URL.
                    {"type": "CrawlerRunConfig", "params": {}},
                ],
            },
            headers=_auth(),
        )

        assert r.status_code == 200, r.text[:300]
        assert seen["urls"] == [GOOD_HOST, "https://iana.org/"]
        # Unfiltered: all three survive, including the ones that only matched a
        # refused seed's position would have shifted.
        assert len(seen["config"]) == 3
        # And the pairing the dispatcher will do still resolves per URL.
        assert BaseDispatcher.select_config(None, GOOD_HOST, seen["config"]).screenshot is True
        assert BaseDispatcher.select_config(
            None, "https://iana.org/", seen["config"]
        ).word_count_threshold == 5


# ───────────────── behavioral: /crawl/stream ─────────────────

def _stream_results(response):
    """Parse an NDJSON crawl stream into its result objects.

    The stream is a result object per line, then a trailing
    {"status": "completed"} marker.
    """
    results = []
    for line in response.iter_lines():
        if not line:
            continue
        obj = json.loads(line)
        if isinstance(obj, dict) and "url" in obj:
            results.append(obj)
    return results


class TestStreamBatchBehavioral:
    def test_refused_seed_is_streamed_as_a_failed_result(
        self, stock_client, refuse_dns, monkeypatch
    ):
        """The streaming path shares the seed check, so it must report the
        refusal the same way instead of 400-ing the whole stream."""
        import crawler_pool

        seen = {}

        class Pooled:
            active_requests = 0
            crawler_strategy = None

            async def arun_many(self, urls=None, config=None, dispatcher=None, **kw):
                urls = list(urls or [])
                seen["urls"] = urls

                async def gen():
                    for url in urls:
                        yield _crawled(url)

                return gen()

        crawler = Pooled()

        async def get_crawler(*a, **kw):
            return crawler

        async def release_crawler(*a, **kw):
            return None

        monkeypatch.setattr(crawler_pool, "get_crawler", get_crawler)
        monkeypatch.setattr(crawler_pool, "release_crawler", release_crawler)

        with stock_client.stream(
            "POST", "/crawl/stream", json={"urls": [INTERNAL, GOOD_HOST]},
            headers=_auth(),
        ) as r:
            assert r.status_code == 200, r.read().decode()[:300]
            results = _stream_results(r)

        by_url = {res["url"]: res for res in results}
        # The gate is a gate: the refused seed is never handed to the crawler,
        # so it is absent from the stream and present only as a failed result.
        assert seen["urls"] == [GOOD_HOST]
        assert INTERNAL in by_url, f"refusal missing from stream: {results}"
        assert by_url[INTERNAL]["success"] is False
        assert by_url[INTERNAL]["error_message"] == BLOCKED_DETAIL
        assert by_url[INTERNAL]["status_code"] == 403
        assert by_url[GOOD_HOST]["success"] is True

    def test_single_refused_url_still_400s_the_stream(
        self, stock_client, refuse_dns
    ):
        r = stock_client.post("/crawl/stream", json={"urls": [INTERNAL]}, headers=_auth())

        assert r.status_code == 400, f"got {r.status_code}: {r.text[:200]}"
        assert BLOCKED_DETAIL in r.text


# ───────────────── the guard itself still guards ─────────────────

class TestNoOracleRegression:
    def test_refused_detail_never_leaks_the_address_or_host(self, refuse_dns):
        """Belt and braces on the property the issue depends on: whatever the
        reason, the refused detail is the one opaque string."""
        for url in (
            INTERNAL,
            "http://10.0.0.1/",
            "http://192.168.1.1/",
            "http://localhost:8080/",
            "http://[::1]/",
            "http://host.docker.internal:3000/",
        ):
            batch = _normalize_and_validate_seeds([url])
            assert batch.refused, f"{url} was not refused"
            detail = batch.refused[0][1]
            assert detail == BLOCKED_DETAIL, f"{url} -> {detail}"

    def test_egress_blocked_still_raises_for_the_direct_call(self, refuse_dns):
        """The broker's own contract is untouched: resolve_and_pin still raises
        rather than returning a verdict, so no other caller can be softened."""
        from egress_broker import resolve_and_pin

        with pytest.raises(EgressBlocked):
            resolve_and_pin(INTERNAL)
