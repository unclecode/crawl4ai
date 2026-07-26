import io
import json
from unittest.mock import patch

import crwl_remote


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_remote_entrypoint_sends_token_and_configs(capsys):
    response = FakeResponse(json.dumps({
        "success": True,
        "results": [{
            "url": "https://example.com",
            "markdown": {"raw_markdown": "# From Docker"},
        }],
    }).encode())

    with patch("crwl_remote.urlopen", return_value=response) as urlopen:
        code = crwl_remote._run_remote(
            [
                "crawl",
                "https://example.com",
                "--api-url", "http://backend:11235",
                "--api-token", "secret",
                "--browser", "headless=true",
                "--crawler", "scan_full_page=true",
                "--output", "markdown",
            ],
            "http://backend:11235",
            "secret",
        )

    assert code == 0
    assert capsys.readouterr().out.strip() == "# From Docker"
    request = urlopen.call_args.args[0]
    assert request.full_url == "http://backend:11235/crawl"
    assert request.headers["Authorization"] == "Bearer secret"
    payload = json.loads(request.data)
    assert payload["urls"] == ["https://example.com"]
    assert payload["browser_config"] == {"headless": True}
    assert payload["crawler_config"] == {
        "scan_full_page": True,
        "cache_mode": "bypass",
    }


def test_saved_credentials_enable_remote_mode_from_any_directory(tmp_path, monkeypatch):
    config_path = tmp_path / ".crawl4ai" / "remote.json"
    monkeypatch.setattr(crwl_remote, "CONFIG_PATH", config_path)
    assert crwl_remote._configure([
        "--api-url", "http://backend:11235",
        "--api-token", "saved-token",
    ]) == 0

    monkeypatch.chdir(tmp_path)
    assert crwl_remote._api_setting([], "--api-url", "CRAWL4AI_API_URL") == "http://backend:11235"
    assert crwl_remote._api_setting([], "--api-token", "CRAWL4AI_API_TOKEN") == "saved-token"
    assert config_path.stat().st_mode & 0o777 == 0o600


def test_environment_overrides_saved_credentials(tmp_path, monkeypatch):
    config_path = tmp_path / "remote.json"
    config_path.write_text(json.dumps({
        "api_url": "http://saved",
        "api_token": "saved-token",
    }), encoding="utf-8")
    monkeypatch.setattr(crwl_remote, "CONFIG_PATH", config_path)
    monkeypatch.setenv("CRAWL4AI_API_URL", "http://environment")
    monkeypatch.setenv("CRAWL4AI_API_TOKEN", "environment-token")

    assert crwl_remote._api_setting([], "--api-url", "CRAWL4AI_API_URL") == "http://environment"
    assert crwl_remote._api_setting([], "--api-token", "CRAWL4AI_API_TOKEN") == "environment-token"


def test_remote_failure_returns_nonzero(capsys):
    response = FakeResponse(json.dumps({
        "success": False,
        "msg": "not authorized",
    }).encode())

    with patch("crwl_remote.urlopen", return_value=response):
        code = crwl_remote._run_remote(
            ["https://example.com"],
            "http://backend:11235",
            None,
        )

    assert code == 1
    assert "not authorized" in capsys.readouterr().err


def test_deep_crawl_options_are_serialized_for_remote_api():
    parsed = crwl_remote._remote_args([
        "https://example.com/docs",
        "--deep-crawl", "bfs",
        "--max-pages", "7",
    ])

    assert parsed["crawler_config"]["deep_crawl_strategy"] == {
        "type": "BFSDeepCrawlStrategy",
        "params": {"max_depth": 3, "max_pages": 7},
    }
