from pathlib import Path

import httpx
from click.testing import CliRunner

import crawl4ai.cloud.cli as cloud_cli


def _set_home(monkeypatch, tmp_path: Path, api_url: str = "https://api.crawl4ai.com"):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    cfg_dir = tmp_path / ".crawl4ai"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "global.yml").write_text(
        f"CLOUD_API_KEY: sk_test_1234567890abcd\nCLOUD_API_URL: {api_url}\n",
        encoding="utf-8",
    )


def test_delete_prefers_exact_name_over_earlier_id_prefix(monkeypatch, tmp_path):
    _set_home(monkeypatch, tmp_path)
    deleted_ids = []

    profiles = [
        {"id": "dev-91a00000-1111", "name": "staging"},
        {"id": "88f3b210-2222", "name": "dev"},
    ]

    monkeypatch.setattr(
        cloud_cli.httpx,
        "get",
        lambda url, **kw: httpx.Response(200, json={"profiles": profiles}),
    )

    def fake_delete(url, **kw):
        deleted_ids.append(url.rsplit("/", 1)[-1])
        return httpx.Response(200, json={"deleted": True})

    monkeypatch.setattr(cloud_cli.httpx, "delete", fake_delete)

    res = CliRunner().invoke(
        cloud_cli.cloud_cmd, ["profiles", "delete", "dev", "--yes"]
    )
    assert res.exit_code == 0, res.output
    assert deleted_ids == ["88f3b210-2222"]


def test_delete_rejects_ambiguous_id_prefix(monkeypatch, tmp_path):
    _set_home(monkeypatch, tmp_path)
    deleted_ids = []

    profiles = [
        {"id": "abc11111-0001", "name": "prod-eu"},
        {"id": "abc22222-0002", "name": "prod-us"},
    ]

    monkeypatch.setattr(
        cloud_cli.httpx,
        "get",
        lambda url, **kw: httpx.Response(200, json={"profiles": profiles}),
    )
    monkeypatch.setattr(
        cloud_cli.httpx,
        "delete",
        lambda url, **kw: deleted_ids.append(url) or httpx.Response(200, json={}),
    )

    res = CliRunner().invoke(
        cloud_cli.cloud_cmd, ["profiles", "delete", "abc", "--yes"]
    )
    assert res.exit_code == 1
    assert deleted_ids == []
    assert "prod-eu" in res.output and "prod-us" in res.output


def test_upload_handles_non_dict_or_plain_text_400_and_request_error(
    monkeypatch, tmp_path
):
    _set_home(monkeypatch, tmp_path)
    prof_dir = tmp_path / "sample_profile"
    prof_dir.mkdir()
    (prof_dir / "Cookies").write_text("cookie-data", encoding="utf-8")

    class _FakeProfiler:
        def get_profile_path(self, name):
            return str(prof_dir)

        def list_profiles(self):
            return [{"name": "sample_profile"}]

    monkeypatch.setattr(cloud_cli, "BrowserProfiler", _FakeProfiler)

    # 1. Plain-text 400 from reverse proxy
    monkeypatch.setattr(
        cloud_cli.httpx,
        "post",
        lambda url, **kw: httpx.Response(400, text="Bad Gateway Payload"),
    )
    res_text = CliRunner().invoke(
        cloud_cli.cloud_cmd, ["profiles", "upload", "sample_profile", "--no-shrink"]
    )
    assert res_text.exit_code == 1
    assert res_text.exception is None or isinstance(res_text.exception, SystemExit)
    assert "Bad Gateway Payload" in res_text.output

    # 2. JSON list 400
    monkeypatch.setattr(
        cloud_cli.httpx,
        "post",
        lambda url, **kw: httpx.Response(400, json=["archive corrupt"]),
    )
    res_list = CliRunner().invoke(
        cloud_cli.cloud_cmd, ["profiles", "upload", "sample_profile", "--no-shrink"]
    )
    assert res_list.exit_code == 1
    assert isinstance(res_list.exception, SystemExit)
    assert "archive corrupt" in res_list.output

    # 3. Network error during upload
    def boom(url, **kw):
        raise httpx.ConnectError("connection reset")

    monkeypatch.setattr(cloud_cli.httpx, "post", boom)
    res_net = CliRunner().invoke(
        cloud_cli.cloud_cmd, ["profiles", "upload", "sample_profile", "--no-shrink"]
    )
    assert res_net.exit_code == 1
    assert isinstance(res_net.exception, SystemExit)
    assert "Connection error" in res_net.output


def test_trailing_slash_on_api_url_does_not_produce_double_slash_paths(
    monkeypatch, tmp_path
):
    _set_home(monkeypatch, tmp_path, api_url="https://api.crawl4ai.com/")
    seen_urls = []

    def fake_get(url, **kw):
        seen_urls.append(url)
        return httpx.Response(200, json={"profiles": []})

    monkeypatch.setattr(cloud_cli.httpx, "get", fake_get)

    res_auth = CliRunner().invoke(
        cloud_cli.cloud_cmd,
        [
            "auth",
            "--api-key",
            "sk_test_1234567890abcd",
            "--api-url",
            "https://cloud.example.com/",
        ],
    )
    assert res_auth.exit_code == 0, res_auth.output

    res_list = CliRunner().invoke(cloud_cli.cloud_cmd, ["profiles", "list"])
    assert res_list.exit_code == 0, res_list.output

    assert seen_urls == [
        "https://cloud.example.com/v1/profiles",
        "https://cloud.example.com/v1/profiles",
    ]
