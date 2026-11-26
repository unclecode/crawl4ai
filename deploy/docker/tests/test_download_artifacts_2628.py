"""Tests for #2628: Docker HTTP API exposes downloaded files via sandboxed artifact store."""

import importlib
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def isolated_artifacts(tmp_path, monkeypatch):
    monkeypatch.setenv("CRAWL4AI_ARTIFACT_DIR", str(tmp_path / "art"))
    monkeypatch.setenv("CRAWL4AI_MAX_ARTIFACT_BYTES", str(1024 * 1024))
    monkeypatch.setenv("CRAWL4AI_ARTIFACT_QUOTA_BYTES", str(4 * 1024 * 1024))
    monkeypatch.setenv("CRAWL4AI_ARTIFACT_TTL_SECONDS", "3600")
    import artifacts

    importlib.reload(artifacts)
    artifacts.init_store()
    yield artifacts
    importlib.reload(artifacts)


class TestArtifactStoreBinSupport:
    def test_bin_artifact_roundtrip_and_resolve(self, isolated_artifacts):
        payload = b"%PDF-1.4\ndownload-bytes"
        meta = isolated_artifacts.write_artifact("bin", payload)
        path, mime = isolated_artifacts.resolve_artifact(meta["artifact_id"])
        assert mime == "application/octet-stream"
        with open(path, "rb") as f:
            assert f.read() == payload


class TestCrawlApiDownloadArtifacts:
    @pytest.mark.asyncio
    async def test_handle_crawl_request_publishes_downloaded_artifacts_and_cleans_temp(
        self, isolated_artifacts, tmp_path, monkeypatch
    ):
        import api
        import crawler_pool
        from auth import create_access_token
        from fastapi.testclient import TestClient
        import server

        dl_file = tmp_path / "lm317.pdf"
        dl_bytes = b"%PDF-1.4\nLM317 datasheet"
        dl_file.write_bytes(dl_bytes)

        fake_result = SimpleNamespace(
            model_dump=lambda: {
                "url": "https://example.com/lm317.pdf",
                "html": "<html><head></head><body></body></html>",
                "fit_html": None,
                "success": True,
                "downloaded_files": [str(dl_file)],
                "pdf": None,
            }
        )
        fake_crawler = MagicMock()
        fake_crawler.arun = AsyncMock(return_value=[fake_result])
        fake_crawler.crawler_strategy = MagicMock()

        monkeypatch.setattr(api, "_normalize_and_validate_seeds", lambda urls: (urls, []))
        monkeypatch.setattr(crawler_pool, "get_crawler", AsyncMock(return_value=fake_crawler))
        monkeypatch.setattr(crawler_pool, "release_crawler", AsyncMock())
        monkeypatch.setattr("egress_broker.enforce_egress", lambda bc: None)

        cfg = {
            "crawler": {
                "memory_threshold_percent": 95.0,
                "rate_limiter": {"enabled": False, "base_delay": [0.1, 0.2]},
                "base_config": {},
                "timeouts": {"stream_init": 30, "batch_crawl": 300},
                "deep_crawl": {"max_depth": 3, "max_pages": 50},
            },
            "limits": {"wall_clock_s": 0},
        }

        resp = await api.handle_crawl_request(
            urls=["https://example.com/lm317.pdf"],
            browser_config={"accept_downloads": True},
            crawler_config={},
            config=cfg,
        )

        assert resp["success"] is True
        item = resp["results"][0]
        assert "downloaded_artifacts" in item
        assert len(item["downloaded_artifacts"]) == 1
        art = item["downloaded_artifacts"][0]
        assert art["filename"] == "lm317.pdf"
        assert art["size"] == len(dl_bytes)
        assert art["url"] == f"/artifacts/{art['artifact_id']}"
        # Raw container filesystem path must not be exposed to remote API callers
        assert item["downloaded_files"] == [art["url"]]
        assert not dl_file.exists()

        # Fetch bytes through GET /artifacts/{artifact_id}
        client = TestClient(server.app, raise_server_exceptions=False)
        token = create_access_token({"sub": "tester@example.com"})
        dl_resp = client.get(
            art["url"],
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dl_resp.status_code == 200
        assert dl_resp.content == dl_bytes
        assert dl_resp.headers.get("x-content-type-options") == "nosniff"
        assert "attachment" in dl_resp.headers.get("content-disposition", "")

        # Docker client deserializes downloaded_artifacts cleanly
        from crawl4ai.docker_client import Crawl4aiDockerClient

        parsed = Crawl4aiDockerClient._to_result(dict(item))
        assert parsed.downloaded_files == [art["url"]]
        assert parsed.downloaded_artifacts == [art]

    def test_store_downloaded_file_rejects_symlink_and_oversize(self, isolated_artifacts, tmp_path):
        secret = tmp_path / "secret.txt"
        secret.write_bytes(b"SECRET")
        link = tmp_path / "evil.pdf"
        link.symlink_to(secret)
        with pytest.raises(isolated_artifacts.ArtifactNotFound):
            isolated_artifacts.store_downloaded_file(str(link))

        big = tmp_path / "big.bin"
        big.write_bytes(b"x" * (1024 * 1024 + 1))
        with pytest.raises(isolated_artifacts.ArtifactTooLarge):
            isolated_artifacts.store_downloaded_file(str(big))

    def test_untrusted_crawl_still_rejects_caller_downloads_path(self, offline_dns):
        from auth import create_access_token
        from fastapi.testclient import TestClient
        import server

        client = TestClient(server.app, raise_server_exceptions=False)
        token = create_access_token({"sub": "tester@example.com"})
        resp = client.post(
            "/crawl",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "urls": ["https://example.com"],
                "browser_config": {"accept_downloads": True, "downloads_path": "/tmp/evil"},
            },
        )
        assert resp.status_code == 400
        assert "downloads_path" in resp.text

    @pytest.mark.asyncio
    async def test_stream_results_publishes_downloaded_artifacts(
        self, isolated_artifacts, tmp_path, monkeypatch
    ):
        import api
        import crawler_pool

        dl_file = tmp_path / "archive.zip"
        dl_bytes = b"PK\x03\x04testzip"
        dl_file.write_bytes(dl_bytes)

        fake_result = SimpleNamespace(
            model_dump=lambda: {
                "url": "https://example.com/archive.zip",
                "html": "",
                "fit_html": None,
                "success": True,
                "downloaded_files": [str(dl_file)],
                "pdf": None,
            }
        )

        async def _gen():
            yield fake_result

        fake_crawler = MagicMock()
        fake_crawler.crawler_strategy = MagicMock()
        monkeypatch.setattr(crawler_pool, "release_crawler", AsyncMock())

        chunks = []
        async for chunk in api.stream_results(fake_crawler, _gen()):
            chunks.append(json.loads(chunk.decode("utf-8")))

        item = chunks[0]
        assert len(item["downloaded_artifacts"]) == 1
        art = item["downloaded_artifacts"][0]
        assert art["filename"] == "archive.zip"
        assert item["downloaded_files"] == [art["url"]]
        path, _ = isolated_artifacts.resolve_artifact(art["artifact_id"])
        with open(path, "rb") as f:
            assert f.read() == dl_bytes
