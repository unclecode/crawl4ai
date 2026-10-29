import importlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from packaging.requirements import InvalidRequirement, Requirement

from crawl4ai.processors.pdf import PDFContentScrapingStrategy

ROOT = Path(__file__).resolve().parent.parent


def test_default_docker_dependencies_include_pypdf():
    lines = (ROOT / "deploy" / "docker" / "requirements.txt").read_text().splitlines()
    names = set()
    for line in lines:
        line = line.strip()
        if not line or line.startswith(("#", "-")):
            continue
        try:
            names.add(Requirement(line).name)
        except InvalidRequirement:
            continue

    assert "pypdf" in names


@pytest.mark.asyncio
async def test_stream_handler_preserves_requested_scraping_strategy(monkeypatch):
    docker_dir = ROOT / "deploy" / "docker"
    monkeypatch.syspath_prepend(str(docker_dir))

    api = importlib.import_module("api")
    egress_broker = importlib.import_module("egress_broker")
    governor = importlib.import_module("governor")

    crawler = MagicMock()
    crawler.arun_many = AsyncMock(return_value=MagicMock())
    crawler.start = AsyncMock()
    monkeypatch.setattr(api, "_normalize_and_validate_seeds", lambda urls: urls)
    monkeypatch.setattr(egress_broker, "enforce_egress", lambda _: None)
    monkeypatch.setattr(governor, "clamp_deep_crawl", lambda _: None)
    monkeypatch.setattr(api, "AsyncWebCrawler", MagicMock(return_value=crawler))

    crawler_config = {
        "type": "CrawlerRunConfig",
        "params": {
            "cache_mode": "bypass",
            "stream": False,
            "scraping_strategy": {
                "type": "PDFContentScrapingStrategy",
                "params": {"extract_images": False, "batch_size": 8},
            },
        },
    }
    config = {
        "crawler": {
            "memory_threshold_percent": 90,
            "rate_limiter": {"base_delay": [0.1, 0.3]},
        }
    }

    await api.handle_stream_crawl_request(
        urls=["https://example.com/document.pdf"],
        browser_config={"type": "BrowserConfig", "params": {}},
        crawler_config=crawler_config,
        config=config,
    )

    effective_config = crawler.arun_many.await_args.kwargs["config"]
    assert isinstance(effective_config.scraping_strategy, PDFContentScrapingStrategy)
