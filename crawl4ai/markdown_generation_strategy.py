from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from .models import MarkdownGenerationResult
from .utils import CustomHTML2Text
from .content_filter_strategy import RelevantContentFilter, BM25ContentFilter
import re
from urllib.parse import urljoin

# Pre-compile the regex pattern
LINK_PATTERN = re.compile(r'!?\[([^\]]+)\]\(([^)]+?)(?:\s+"([^"]*)")?\)')

class MarkdownGenerationStrategy(ABC):
    """Abstract base class for markdown generation strategies."""
    def __init__(self, content_filter: Optional[RelevantContentFilter] = None):
        self.content_filter = content_filter
    
    @abstractmethod
    def generate_markdown(self, 
                         cleaned_html: str, 
                         base_url: str = "",
                         html2text_options: Optional[Dict[str, Any]] = None,
                         content_filter: Optional[RelevantContentFilter] = None,
                         citations: bool = True,
                         **kwargs) -> MarkdownGenerationResult:
        """Generate markdown from cleaned HTML."""
        pass

class DefaultMarkdownGenerator(MarkdownGenerationStrategy):
    """Default implementation of markdown generation strategy."""
    def __init__(self, content_filter: Optional[RelevantContentFilter] = None):
        super().__init__(content_filter)
    
    def convert_links_to_citations(self, markdown: str, base_url: str = "") -> Tuple[str, str]:
        link_map = {}
        url_cache = {}  # Cache for URL joins
        parts = []
        last_end = 0
        counter = 1
        
        for match in LINK_PATTERN.finditer(markdown):
            parts.append(markdown[last_end:match.start()])
            text, url, title = match.groups()
            
            # Use cached URL if available, otherwise compute and cache
            if base_url and not url.startswith(('http://', 'https://', 'mailto:')):
                if url not in url_cache:
                    url_cache[url] = fast_urljoin(base_url, url)
                url = url_cache[url]
                
            if url not in link_map:
                desc = []
                if title: desc.append(title)
                if text and text != title: desc.append(text)
                link_map[url] = (counter, ": " + " - ".join(desc) if desc else "")
                counter += 1
                
            num = link_map[url][0]
            parts.append(f"{text}⟨{num}⟩" if not match.group(0).startswith('!') else f"![{text}⟨{num}⟩]")
            last_end = match.end()
        
        parts.append(markdown[last_end:])
        converted_text = ''.join(parts)
        
        # Pre-build reference strings
        references = ["\n\n## References\n\n"]
        references.extend(
            f"⟨{num}⟩ {url}{desc}\n" 
            for url, (num, desc) in sorted(link_map.items(), key=lambda x: x[1][0])
        )
        
        return converted_text, ''.join(references)

    def generate_markdown(self, 
                         cleaned_html: str, 
                         base_url: str = "",
                         html2text_options: Optional[Dict[str, Any]] = None,
                         content_filter: Optional[RelevantContentFilter] = None,
                         citations: bool = True,
                         **kwargs) -> MarkdownGenerationResult:
        """Generate markdown with citations from cleaned HTML."""
        # Initialize HTML2Text with options
        h = CustomHTML2Text()
        if html2text_options:
            h.update_params(**html2text_options)

        # Generate raw markdown
        raw_markdown = h.handle(cleaned_html)
        raw_markdown = raw_markdown.replace('    ```', '```')

        # Convert links to citations
        markdown_with_citations: str = ""
        references_markdown: str = ""
        if citations:
            markdown_with_citations, references_markdown = self.convert_links_to_citations(
                raw_markdown, base_url
            )

        # Generate fit markdown if content filter is provided
        fit_markdown: Optional[str] = ""
        filtered_html: Optional[str] = ""
        if content_filter or self.content_filter:
            content_filter = content_filter or self.content_filter
            filtered_html = content_filter.filter_content(cleaned_html)
            filtered_html = '\n'.join('<div>{}</div>'.format(s) for s in filtered_html)
            fit_markdown = h.handle(filtered_html)

        return MarkdownGenerationResult(
            raw_markdown=raw_markdown,
            markdown_with_citations=markdown_with_citations,
            references_markdown=references_markdown,
            fit_markdown=fit_markdown,
            fit_html=filtered_html,
        )

def fast_urljoin(base: str, url: str) -> str:
    """Fast URL joining for common cases."""
    if url.startswith(('http://', 'https://', 'mailto:', '//')):
        return url
    if url.startswith('/'):
        # Handle absolute paths
        if base.endswith('/'):
            return base[:-1] + url
        return base + url
    return urljoin(base, url)