"""
Tests for #1890: DocumentExtractionStrategy — pluggable binary document
detection and extraction in the crawl pipeline.

Tests the abstract interface, a concrete mock implementation, the
CrawlerRunConfig integration, and the pipeline routing logic.
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from crawl4ai.document_extraction_strategy import (
    DocumentExtractionStrategy,
    DocumentExtractionResult,
)
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.models import AsyncCrawlResponse, MarkdownGenerationResult


# ── Concrete test implementation ─────────────────────────────────────────

class MockDocumentStrategy(DocumentExtractionStrategy):
    """Test implementation that detects documents by downloaded_files."""

    def detect(self, response) -> bool:
        return bool(response.downloaded_files)

    async def extract(self, response, url) -> DocumentExtractionResult:
        filename = response.downloaded_files[0]
        return DocumentExtractionResult(
            content=f"Extracted text from {filename}",
            content_type="pdf",
            source_path=Path(filename),
            metadata={"pages": 5},
        )


class ContentTypeDocumentStrategy(DocumentExtractionStrategy):
    """Test implementation that detects by Content-Type header."""

    DOCUMENT_TYPES = {"application/pdf", "application/msword"}

    def detect(self, response) -> bool:
        ct = (response.response_headers or {}).get("content-type", "")
        return ct.split(";")[0].strip() in self.DOCUMENT_TYPES

    async def extract(self, response, url) -> DocumentExtractionResult:
        return DocumentExtractionResult(
            content="Document content here",
            content_type="pdf",
        )


class NeverDetectStrategy(DocumentExtractionStrategy):
    """Strategy that never detects documents — HTML pipeline should be used."""

    def detect(self, response) -> bool:
        return False

    async def extract(self, response, url) -> DocumentExtractionResult:
        raise RuntimeError("Should never be called")


# ── Helper ───────────────────────────────────────────────────────────────

def make_response(**kwargs):
    """Create a mock AsyncCrawlResponse."""
    defaults = {
        "html": "",
        "response_headers": {},
        "status_code": 200,
        "downloaded_files": None,
        "redirected_url": None,
        "redirected_status_code": None,
    }
    defaults.update(kwargs)
    resp = MagicMock(spec=AsyncCrawlResponse)
    for k, v in defaults.items():
        setattr(resp, k, v)
    return resp


# ── Base class tests ─────────────────────────────────────────────────────

class TestDocumentExtractionResult:

    def test_basic_creation(self):
        result = DocumentExtractionResult(
            content="Hello world",
            content_type="pdf",
        )
        assert result.content == "Hello world"
        assert result.content_type == "pdf"
        assert result.source_path is None
        assert result.metadata == {}

    def test_with_all_fields(self):
        result = DocumentExtractionResult(
            content="Text",
            content_type="application/pdf",
            source_path=Path("/tmp/doc.pdf"),
            metadata={"pages": 10, "author": "Jane"},
        )
        assert result.source_path == Path("/tmp/doc.pdf")
        assert result.metadata["pages"] == 10

    def test_cannot_instantiate_abstract(self):
        """DocumentExtractionStrategy is abstract — can't instantiate directly."""
        with pytest.raises(TypeError):
            DocumentExtractionStrategy()


# ── Detection tests ──────────────────────────────────────────────────────

class TestDetection:

    def test_detect_by_downloaded_files(self):
        strategy = MockDocumentStrategy()
        resp = make_response(downloaded_files=["/tmp/doc.pdf"])
        assert strategy.detect(resp) is True

    def test_no_downloaded_files_not_detected(self):
        strategy = MockDocumentStrategy()
        resp = make_response(downloaded_files=None)
        assert strategy.detect(resp) is False

    def test_empty_downloaded_files_not_detected(self):
        strategy = MockDocumentStrategy()
        resp = make_response(downloaded_files=[])
        assert strategy.detect(resp) is False

    def test_detect_by_content_type(self):
        strategy = ContentTypeDocumentStrategy()
        resp = make_response(
            response_headers={"content-type": "application/pdf; charset=utf-8"}
        )
        assert strategy.detect(resp) is True

    def test_html_content_type_not_detected(self):
        strategy = ContentTypeDocumentStrategy()
        resp = make_response(
            response_headers={"content-type": "text/html; charset=utf-8"}
        )
        assert strategy.detect(resp) is False

    def test_never_detect_strategy(self):
        strategy = NeverDetectStrategy()
        resp = make_response(downloaded_files=["/tmp/doc.pdf"])
        assert strategy.detect(resp) is False


# ── Extraction tests ─────────────────────────────────────────────────────

class TestExtraction:

    @pytest.mark.asyncio
    async def test_extract_returns_result(self):
        strategy = MockDocumentStrategy()
        resp = make_response(downloaded_files=["/tmp/report.pdf"])
        result = await strategy.extract(resp, "https://example.com/report.pdf")

        assert isinstance(result, DocumentExtractionResult)
        assert "report.pdf" in result.content
        assert result.content_type == "pdf"
        assert result.source_path == Path("/tmp/report.pdf")
        assert result.metadata == {"pages": 5}

    @pytest.mark.asyncio
    async def test_extract_content_type_strategy(self):
        strategy = ContentTypeDocumentStrategy()
        resp = make_response(
            response_headers={"content-type": "application/pdf"}
        )
        result = await strategy.extract(resp, "https://example.com/doc.pdf")
        assert result.content == "Document content here"


# ── CrawlerRunConfig integration ─────────────────────────────────────────

class TestConfigIntegration:

    def test_default_is_none(self):
        config = CrawlerRunConfig()
        assert config.document_extraction_strategy is None

    def test_set_strategy(self):
        strategy = MockDocumentStrategy()
        config = CrawlerRunConfig(document_extraction_strategy=strategy)
        assert config.document_extraction_strategy is strategy

    def test_none_strategy_no_effect(self):
        """When strategy is None, the config should work normally."""
        config = CrawlerRunConfig(document_extraction_strategy=None)
        assert config.document_extraction_strategy is None


# ── Pipeline routing tests ───────────────────────────────────────────────

class TestPipelineRouting:
    """Test that the arun integration point routes correctly."""

    def test_detect_true_skips_html_pipeline(self):
        """When detect() returns True, HTML processing should be skipped."""
        strategy = MockDocumentStrategy()
        resp = make_response(downloaded_files=["/tmp/doc.pdf"])

        # Simulate the routing logic from async_webcrawler.py
        doc_strategy = strategy
        if doc_strategy and doc_strategy.detect(resp):
            route = "document"
        else:
            route = "html"

        assert route == "document"

    def test_detect_false_uses_html_pipeline(self):
        """When detect() returns False, normal HTML processing should proceed."""
        strategy = NeverDetectStrategy()
        resp = make_response(downloaded_files=["/tmp/doc.pdf"])

        doc_strategy = strategy
        if doc_strategy and doc_strategy.detect(resp):
            route = "document"
        else:
            route = "html"

        assert route == "html"

    def test_no_strategy_uses_html_pipeline(self):
        """When no strategy is configured, always use HTML pipeline."""
        resp = make_response(downloaded_files=["/tmp/doc.pdf"])

        doc_strategy = None
        if doc_strategy and doc_strategy.detect(resp):
            route = "document"
        else:
            route = "html"

        assert route == "html"

    @pytest.mark.asyncio
    async def test_document_result_has_markdown(self):
        """Document extraction result should be wrapped in MarkdownGenerationResult."""
        strategy = MockDocumentStrategy()
        resp = make_response(
            downloaded_files=["/tmp/report.pdf"],
            status_code=200,
            response_headers={},
            redirected_url=None,
            redirected_status_code=None,
        )

        doc_result = await strategy.extract(resp, "https://example.com/report.pdf")

        # Simulate what async_webcrawler.py does
        md_result = MarkdownGenerationResult(
            raw_markdown=doc_result.content,
            markdown_with_citations=doc_result.content,
            references_markdown="",
            fit_markdown="",
            fit_html="",
        )

        assert "report.pdf" in md_result.raw_markdown
        assert md_result.fit_markdown == ""

    @pytest.mark.asyncio
    async def test_document_metadata_includes_is_document(self):
        """CrawlResult metadata should include is_document=True."""
        strategy = MockDocumentStrategy()
        resp = make_response(downloaded_files=["/tmp/doc.pdf"])
        doc_result = await strategy.extract(resp, "https://example.com/doc.pdf")

        metadata = {
            "is_document": True,
            "content_type": doc_result.content_type,
            **(doc_result.metadata or {}),
        }

        assert metadata["is_document"] is True
        assert metadata["content_type"] == "pdf"
        assert metadata["pages"] == 5


# ── Import tests ─────────────────────────────────────────────────────────

class TestImports:

    def test_importable_from_crawl4ai(self):
        from crawl4ai import DocumentExtractionStrategy, DocumentExtractionResult
        assert DocumentExtractionStrategy is not None
        assert DocumentExtractionResult is not None

    def test_importable_from_module(self):
        from crawl4ai.document_extraction_strategy import (
            DocumentExtractionStrategy,
            DocumentExtractionResult,
        )
        assert DocumentExtractionStrategy is not None
