"""Content scraper implementation using lxml and BeautifulSoup."""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from lxml import html as lxml_html
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentScraper:
    """Scrapes content from HTML using lxml and BeautifulSoup."""

    def scrape(
        self,
        html: str,
        extract_links: bool = False,
        extract_images: bool = False,
        extract_media: bool = False,
        extract_metadata: bool = False,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Scrape content from HTML.

        Args:
            html: HTML content to scrape
            extract_links: Extract all links
            extract_images: Extract all images
            extract_media: Extract media elements
            extract_metadata: Extract page metadata
            base_url: Base URL for resolving relative URLs

        Returns:
            Dictionary with extracted content
        """
        result: Dict[str, Any] = {}

        # Parse with lxml for performance
        tree = lxml_html.fromstring(html)

        # Extract plain text
        result["text"] = self._extract_text(tree)

        # Extract links
        if extract_links:
            result["links"] = self._extract_links(tree, base_url)

        # Extract images
        if extract_images:
            result["images"] = self._extract_images(tree, base_url)

        # Extract media
        if extract_media:
            result["media"] = self._extract_media(tree, base_url)

        # Extract metadata
        if extract_metadata:
            result["metadata"] = self._extract_metadata(tree)

        return result

    def _extract_text(self, tree) -> str:
        """Extract plain text from HTML tree.

        Args:
            tree: lxml HTML tree

        Returns:
            Extracted text
        """
        # Remove script and style elements
        for element in tree.xpath(".//script | .//style"):
            element.getparent().remove(element)

        # Get text content
        text = tree.text_content()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        return text

    def _extract_links(self, tree, base_url: Optional[str] = None) -> List[str]:
        """Extract all links from HTML tree.

        Args:
            tree: lxml HTML tree
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute URLs
        """
        links = []

        for element in tree.xpath(".//a[@href]"):
            href = element.get("href")
            if href:
                # Resolve relative URLs
                if base_url:
                    href = urljoin(base_url, href)
                links.append(href)

        return list(set(links))  # Remove duplicates

    def _extract_images(
        self, tree, base_url: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Extract all images from HTML tree.

        Args:
            tree: lxml HTML tree
            base_url: Base URL for resolving relative URLs

        Returns:
            List of image dictionaries with src, alt, etc.
        """
        images = []

        for element in tree.xpath(".//img[@src]"):
            src = element.get("src")
            if src:
                # Resolve relative URLs
                if base_url:
                    src = urljoin(base_url, src)

                images.append(
                    {
                        "src": src,
                        "alt": element.get("alt", ""),
                        "title": element.get("title", ""),
                    }
                )

        return images

    def _extract_media(
        self, tree, base_url: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Extract media elements (video, audio) from HTML tree.

        Args:
            tree: lxml HTML tree
            base_url: Base URL for resolving relative URLs

        Returns:
            List of media dictionaries
        """
        media = []

        # Extract videos
        for element in tree.xpath(".//video"):
            src = element.get("src") or (element.xpath(".//source/@src") or [None])[0]
            if src:
                if base_url:
                    src = urljoin(base_url, src)
                media.append(
                    {
                        "type": "video",
                        "src": src,
                        "poster": element.get("poster", ""),
                    }
                )

        # Extract audio
        for element in tree.xpath(".//audio"):
            src = element.get("src") or (element.xpath(".//source/@src") or [None])[0]
            if src:
                if base_url:
                    src = urljoin(base_url, src)
                media.append(
                    {
                        "type": "audio",
                        "src": src,
                    }
                )

        return media

    def _extract_metadata(self, tree) -> Dict[str, Any]:
        """Extract page metadata from HTML tree.

        Args:
            tree: lxml HTML tree

        Returns:
            Dictionary with metadata
        """
        metadata = {}

        # Extract title
        title = tree.xpath(".//title/text()")
        if title:
            metadata["title"] = title[0].strip()

        # Extract meta tags
        for element in tree.xpath(".//meta"):
            name = element.get("name") or element.get("property")
            content = element.get("content")
            if name and content:
                metadata[name] = content

        return metadata
