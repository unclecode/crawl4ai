"""
Behavioral tests for 0.9.x legacy-compatibility handling:

  * root redirect   - "/" is public and redirects to /playground instead of
                      dying in the auth gate with a bare 401; /monitor and the
                      data routes stay gated.
  * output_path     - /screenshot and /pdf still accept the 0.8.x output_path
                      field but return a warning saying no file was written,
                      instead of silently dropping it.
  * legacy hooks    - hooks.code (removed 0.8.x inline Python) is captured,
                      never executed, and reported as status "ignored" with a
                      warning when hooks are enabled; any hooks payload is
                      still refused (403) while hooks are disabled.
  * compose file    - the PID cap lives under deploy.resources.limits (not
                      pids_limit), which Compose v5 rejects alongside a
                      limits block.

These exercise the running app via TestClient (no browser / Redis needed);
crawl internals are stubbed where a handler would otherwise need a browser.
"""

import base64
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from auth import create_access_token  # noqa: E402


def _bearer() -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': 'user@x.com'}, scope='data')}"}


# ───────────────────────── root redirect ─────────────────────────


class TestRootRedirect:
    def test_root_is_public_and_redirects_to_playground(self, stock_client):
        r = stock_client.get("/", follow_redirects=False)
        assert r.status_code in (302, 307), (
            f"GET / returned {r.status_code}; expected a redirect. The auth "
            f"gate must allow the exact path '/' so the redirect route runs."
        )
        assert r.headers["location"] == "/playground"

    def test_monitor_and_data_routes_stay_gated(self, stock_client):
        assert stock_client.get("/monitor").status_code == 401
        assert stock_client.get("/monitor/health").status_code == 401
        assert stock_client.post("/crawl", json={"urls": ["https://x"]}).status_code == 401


# ───────────────────────── output_path warning ─────────────────────────


@pytest.fixture
def stub_crawler(server_module, monkeypatch):
    """Stub the crawler pool + artifact store so /screenshot and /pdf run
    without a browser. Returns the fake artifact dict for assertions."""
    art = {"artifact_id": "a1", "url": "/artifacts/a1", "mime": "x", "size": 1}
    png_b64 = base64.b64encode(b"fake-png").decode()

    fake_result = SimpleNamespace(success=True, screenshot=png_b64, pdf=b"fake-pdf")

    class _FakeCrawler:
        async def arun(self, url, config):
            return [fake_result]

    async def fake_get_crawler(cfg):
        return _FakeCrawler()

    async def fake_release_crawler(crawler):
        pass

    monkeypatch.setattr(server_module, "get_crawler", fake_get_crawler)
    monkeypatch.setattr(server_module, "release_crawler", fake_release_crawler)
    monkeypatch.setattr(server_module, "_store_artifact", lambda kind, data: dict(art))
    return art


class TestOutputPathWarning:
    @pytest.mark.parametrize("endpoint,payload_key", [("/screenshot", "screenshot"), ("/pdf", "pdf")])
    def test_output_path_accepted_with_warning(self, stock_client, stub_crawler, endpoint, payload_key):
        r = stock_client.post(
            endpoint,
            json={"url": "https://example.com", "output_path": "/tmp/x.bin"},
            headers=_bearer(),
        )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "warning" in body, "output_path must not be silently dropped"
        assert "no file was written" in body["warning"]
        assert body["artifact_id"] == stub_crawler["artifact_id"]

    @pytest.mark.parametrize("endpoint", ["/screenshot", "/pdf"])
    def test_no_warning_without_output_path(self, stock_client, stub_crawler, endpoint):
        r = stock_client.post(endpoint, json={"url": "https://example.com"}, headers=_bearer())
        assert r.status_code == 200
        assert "warning" not in r.json()


# ───────────────────────── legacy hooks.code ─────────────────────────

LEGACY_HOOKS = {"code": {"before_goto": "async def hook(p, c, u, **kw): return p"}}
DECLARATIVE_HOOKS = {"hooks": [{"action": "scroll_to_bottom", "params": {"max_steps": 2}}]}


class TestLegacyHookCode:
    def test_hook_config_captures_code_field(self):
        """The legacy field must be parsed (not dropped) so it can be reported."""
        from schemas import CrawlRequestWithHooks

        req = CrawlRequestWithHooks(urls=["https://x"], hooks=LEGACY_HOOKS)
        assert req.hooks.code == LEGACY_HOOKS["code"]
        assert req.hooks.hooks == []

    @pytest.mark.parametrize("hooks_payload", [LEGACY_HOOKS, DECLARATIVE_HOOKS])
    def test_any_hooks_payload_403_when_disabled(self, server_module, monkeypatch, stock_client, hooks_payload):
        monkeypatch.setattr(server_module, "HOOKS_ENABLED", False)
        r = stock_client.post(
            "/crawl",
            json={"urls": ["https://example.com"], "hooks": hooks_payload},
            headers=_bearer(),
        )
        assert r.status_code == 403

    def _stub_crawl(self, server_module, monkeypatch, results):
        async def fake_handle_crawl_request(**kwargs):
            return dict(results)

        monkeypatch.setattr(server_module, "handle_crawl_request", fake_handle_crawl_request)

    def test_legacy_code_warned_and_ignored_when_enabled(self, server_module, monkeypatch, stock_client):
        monkeypatch.setattr(server_module, "HOOKS_ENABLED", True)
        # Empty declarative specs -> api.py reports a vacuous success
        self._stub_crawl(
            server_module, monkeypatch,
            {"success": True, "results": [{"success": True}],
             "hooks": {"status": "success", "attached": []}},
        )
        r = stock_client.post(
            "/crawl",
            json={"urls": ["https://example.com"], "hooks": LEGACY_HOOKS},
            headers=_bearer(),
        )
        assert r.status_code == 200
        hooks = r.json()["hooks"]
        assert hooks["status"] == "ignored", "vacuous 'success' must be rewritten"
        assert hooks["attached"] == []
        assert "NOT executed" in hooks["warning"]

    def test_mixed_request_keeps_declarative_status_and_warns(self, server_module, monkeypatch, stock_client):
        monkeypatch.setattr(server_module, "HOOKS_ENABLED", True)
        self._stub_crawl(
            server_module, monkeypatch,
            {"success": True, "results": [{"success": True}],
             "hooks": {"status": "success", "attached": ["before_retrieve_html"]}},
        )
        r = stock_client.post(
            "/crawl",
            json={"urls": ["https://example.com"],
                  "hooks": {**DECLARATIVE_HOOKS, **LEGACY_HOOKS}},
            headers=_bearer(),
        )
        assert r.status_code == 200
        hooks = r.json()["hooks"]
        assert hooks["status"] == "success", "real declarative execution must not be relabeled"
        assert hooks["attached"] == ["before_retrieve_html"]
        assert "NOT executed" in hooks["warning"]

    def test_no_hooks_response_untouched(self, server_module, monkeypatch, stock_client):
        self._stub_crawl(
            server_module, monkeypatch,
            {"success": True, "results": [{"success": True}]},
        )
        r = stock_client.post("/crawl", json={"urls": ["https://example.com"]}, headers=_bearer())
        assert r.status_code == 200
        assert "hooks" not in r.json()


# ───────────────────────── compose file ─────────────────────────


class TestComposeFile:
    def test_pid_cap_lives_under_deploy_limits(self):
        """Compose v5 rejects pids_limit next to deploy.resources.limits
        ("can't set distinct values"); the cap must be expressed once, under
        deploy.resources.limits.pids."""
        import os

        override = os.environ.get("CRAWL4AI_COMPOSE_FILE")
        if override:
            compose_path = Path(override)
        else:
            here = Path(__file__).resolve()
            if len(here.parents) < 4:
                pytest.skip("not running from a repo checkout")
            compose_path = here.parents[3] / "docker-compose.yml"
        if not compose_path.exists():
            pytest.skip(f"docker-compose.yml not found at {compose_path}")
        doc = yaml.safe_load(compose_path.read_text())
        base = doc["x-base-config"]
        assert "pids_limit" not in base
        assert base["deploy"]["resources"]["limits"]["pids"] == 512
