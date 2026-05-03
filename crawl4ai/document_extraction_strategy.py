"""
Document Extraction Strategy — abstract base for detecting and extracting
text from binary documents (PDF, DOCX, XLSX, etc.) during the crawl pipeline.

When configured on CrawlerRunConfig, the strategy is checked after browser
navigation but before HTML content scraping. If it detects a document, it
extracts text directly — skipping the HTML pipeline entirely.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import AsyncCrawlResponse


@dataclass
class DocumentExtractionResult:
    """Result of extracting text from a binary document."""

    content: str
    """Extracted text content (plain text or markdown)."""

    content_type: str
    """MIME type or file extension (e.g., 'application/pdf', 'pdf')."""

    source_path: Optional[Path] = None
    """Local file path if the document was downloaded."""

    metadata: dict = field(default_factory=dict)
    """Optional metadata (title, author, page count, etc.)."""


class DocumentExtractionStrategy(ABC):
    """
    Abstract strategy for detecting and extracting text from binary documents.

    Subclass this and implement ``detect()`` and ``extract()`` using your
    preferred extraction backend (Kreuzberg, PyMuPDF, Docling, etc.).

    Example::

        class KreuzbergDocumentStrategy(DocumentExtractionStrategy):
            DOCUMENT_TYPES = {"application/pdf", "application/msword", ...}

            def detect(self, response):
                if response.downloaded_files:
                    return True
                ct = (response.response_headers or {}).get("content-type", "")
                return ct.split(";")[0].strip() in self.DOCUMENT_TYPES

            async def extract(self, response, url):
                from kreuzberg import extract_file
                path = Path(response.downloaded_files[0])
                result = await extract_file(str(path))
                return DocumentExtractionResult(
                    content=result.content,
                    content_type=path.suffix.lstrip("."),
                    source_path=path,
                )
    """

    @abstractmethod
    def detect(self, response: "AsyncCrawlResponse") -> bool:
        """Return True if the response represents a binary document.

        Implementations can check:
        - ``response.downloaded_files`` — browser triggered a download
        - ``response.response_headers`` — Content-Type header
        - ``response.status_code`` — failed navigation
        - URL extension heuristics
        """
        ...

    @abstractmethod
    async def extract(
        self, response: "AsyncCrawlResponse", url: str
    ) -> DocumentExtractionResult:
        """Extract text content from the document.

        Args:
            response: The crawl response (may contain downloaded file paths).
            url: The original URL that was crawled.

        Returns:
            DocumentExtractionResult with extracted text.
        """
        ...
