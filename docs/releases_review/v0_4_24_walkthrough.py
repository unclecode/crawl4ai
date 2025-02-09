"""
Crawl4AI v0.4.24 Feature Walkthrough
===================================

This script demonstrates the new features introduced in Crawl4AI v0.4.24.
Each section includes detailed examples and explanations of the new capabilities.
"""

import asyncio
import os
import json
import re
from typing import List
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMExtractionStrategy,
    JsonCssExtractionStrategy,
)
from crawl4ai.content_filter_strategy import RelevantContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from bs4 import BeautifulSoup

# Sample HTML for demonstrations
SAMPLE_HTML = """
<div class="article-list">
    <article class="post" data-category="tech" data-author="john">
        <h2 class="title"><a href="/post-1">First Post</a></h2>
        <div class="meta">
            <a href="/author/john" class="author">John Doe</a>
            <span class="date">2023-12-31</span>
        </div>
        <div class="content">
            <p>First post content...</p>
            <a href="/read-more-1" class="read-more">Read More</a>
        </div>
    </article>
    <article class="post" data-category="science" data-author="jane">
        <h2 class="title"><a href="/post-2">Second Post</a></h2>
        <div class="meta">
            <a href="/author/jane" class="author">Jane Smith</a>
            <span class="date">2023-12-30</span>
        </div>
        <div class="content">
            <p>Second post content...</p>
            <a href="/read-more-2" class="read-more">Read More</a>
        </div>
    </article>
</div>
"""


async def demo_ssl_features():
    """
    Enhanced SSL & Security Features Demo
    -----------------------------------

    This example demonstrates the new SSL certificate handling and security features:
    1. Custom certificate paths
    2. SSL verification options
    3. HTTPS error handling
    4. Certificate validation configurations

    These features are particularly useful when:
    - Working with self-signed certificates
    - Dealing with corporate proxies
    - Handling mixed content websites
    - Managing different SSL security levels
    """
    print("\n1. Enhanced SSL & Security Demo")
    print("--------------------------------")

    browser_config = BrowserConfig()

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        fetch_ssl_certificate=True,  # Enable SSL certificate fetching
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com", config=run_config)
        print(f"SSL Crawl Success: {result.success}")
        result.ssl_certificate.to_json(
            os.path.join(os.getcwd(), "ssl_certificate.json")
        )
        if not result.success:
            print(f"SSL Error: {result.error_message}")


async def demo_content_filtering():
    """
    Smart Content Filtering Demo
    ----------------------

    Demonstrates advanced content filtering capabilities:
    1. Custom filter to identify and extract specific content
    2. Integration with markdown generation
    3. Flexible pruning rules
    """
    print("\n2. Smart Content Filtering Demo")
    print("--------------------------------")

    # Create a custom content filter
    class CustomNewsFilter(RelevantContentFilter):
        def __init__(self):
            super().__init__()
            # Add news-specific patterns
            self.negative_patterns = re.compile(
                r"nav|footer|header|sidebar|ads|comment|share|related|recommended|popular|trending",
                re.I,
            )
            self.min_word_count = 30  # Higher threshold for news content

        def filter_content(
            self, html: str, min_word_threshold: int = None
        ) -> List[str]:
            """
            Implements news-specific content filtering logic.

            Args:
                html (str): HTML content to be filtered
                min_word_threshold (int, optional): Minimum word count threshold

            Returns:
                List[str]: List of filtered HTML content blocks
            """
            if not html or not isinstance(html, str):
                return []

            soup = BeautifulSoup(html, "lxml")
            if not soup.body:
                soup = BeautifulSoup(f"<body>{html}</body>", "lxml")

            body = soup.find("body")

            # Extract chunks with metadata
            chunks = self.extract_text_chunks(
                body, min_word_threshold or self.min_word_count
            )

            # Filter chunks based on news-specific criteria
            filtered_chunks = []
            for _, text, tag_type, element in chunks:
                # Skip if element has negative class/id
                if self.is_excluded(element):
                    continue

                # Headers are important in news articles
                if tag_type == "header":
                    filtered_chunks.append(self.clean_element(element))
                    continue

                # For content, check word count and link density
                text = element.get_text(strip=True)
                if len(text.split()) >= (min_word_threshold or self.min_word_count):
                    # Calculate link density
                    links_text = " ".join(
                        a.get_text(strip=True) for a in element.find_all("a")
                    )
                    link_density = len(links_text) / len(text) if text else 1

                    # Accept if link density is reasonable
                    if link_density < 0.5:
                        filtered_chunks.append(self.clean_element(element))

            return filtered_chunks

    # Create markdown generator with custom filter
    markdown_gen = DefaultMarkdownGenerator(content_filter=CustomNewsFilter())

    run_config = CrawlerRunConfig(
        markdown_generator=markdown_gen, cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com", config=run_config
        )
        print("Filtered Content Sample:")
        print(result.markdown[:500])  # Show first 500 chars


async def demo_json_extraction():
    """
    Improved JSON Extraction Demo
    ---------------------------

    Demonstrates the enhanced JSON extraction capabilities:
    1. Base element attributes extraction
    2. Complex nested structures
    3. Multiple extraction patterns

    Key features shown:
    - Extracting attributes from base elements (href, data-* attributes)
    - Processing repeated patterns
    - Handling optional fields
    """
    print("\n3. Improved JSON Extraction Demo")
    print("--------------------------------")

    # Define the extraction schema with base element attributes
    json_strategy = JsonCssExtractionStrategy(
        schema={
            "name": "Blog Posts",
            "baseSelector": "div.article-list",
            "baseFields": [
                {"name": "list_id", "type": "attribute", "attribute": "data-list-id"},
                {"name": "category", "type": "attribute", "attribute": "data-category"},
            ],
            "fields": [
                {
                    "name": "posts",
                    "selector": "article.post",
                    "type": "nested_list",
                    "baseFields": [
                        {
                            "name": "post_id",
                            "type": "attribute",
                            "attribute": "data-post-id",
                        },
                        {
                            "name": "author_id",
                            "type": "attribute",
                            "attribute": "data-author",
                        },
                    ],
                    "fields": [
                        {
                            "name": "title",
                            "selector": "h2.title a",
                            "type": "text",
                            "baseFields": [
                                {
                                    "name": "url",
                                    "type": "attribute",
                                    "attribute": "href",
                                }
                            ],
                        },
                        {
                            "name": "author",
                            "selector": "div.meta a.author",
                            "type": "text",
                            "baseFields": [
                                {
                                    "name": "profile_url",
                                    "type": "attribute",
                                    "attribute": "href",
                                }
                            ],
                        },
                        {"name": "date", "selector": "span.date", "type": "text"},
                        {
                            "name": "read_more",
                            "selector": "a.read-more",
                            "type": "nested",
                            "fields": [
                                {"name": "text", "type": "text"},
                                {
                                    "name": "url",
                                    "type": "attribute",
                                    "attribute": "href",
                                },
                            ],
                        },
                    ],
                }
            ],
        }
    )

    # Demonstrate extraction from raw HTML
    run_config = CrawlerRunConfig(
        extraction_strategy=json_strategy, cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="raw:" + SAMPLE_HTML,  # Use raw: prefix for raw HTML
            config=run_config,
        )
        print("Extracted Content:")
        print(result.extracted_content)


async def demo_input_formats():
    """
    Input Format Handling Demo
    ----------------------

    Demonstrates how LLM extraction can work with different input formats:
    1. Markdown (default) - Good for simple text extraction
    2. HTML - Better when you need structure and attributes

    This example shows how HTML input can be beneficial when:
    - You need to understand the DOM structure
    - You want to extract both visible text and HTML attributes
    - The content has complex layouts like tables or forms
    """
    print("\n4. Input Format Handling Demo")
    print("---------------------------")

    # Create a dummy HTML with rich structure
    dummy_html = """
    <div class="job-posting" data-post-id="12345">
        <header class="job-header">
            <h1 class="job-title">Senior AI/ML Engineer</h1>
            <div class="job-meta">
                <span class="department">AI Research Division</span>
                <span class="location" data-remote="hybrid">San Francisco (Hybrid)</span>
            </div>
            <div class="salary-info" data-currency="USD">
                <span class="range">$150,000 - $220,000</span>
                <span class="period">per year</span>
            </div>
        </header>
        
        <section class="requirements">
            <div class="technical-skills">
                <h3>Technical Requirements</h3>
                <ul class="required-skills">
                    <li class="skill required" data-priority="must-have">
                        5+ years experience in Machine Learning
                    </li>
                    <li class="skill required" data-priority="must-have">
                        Proficiency in Python and PyTorch/TensorFlow
                    </li>
                    <li class="skill preferred" data-priority="nice-to-have">
                        Experience with distributed training systems
                    </li>
                </ul>
            </div>
            
            <div class="soft-skills">
                <h3>Professional Skills</h3>
                <ul class="required-skills">
                    <li class="skill required" data-priority="must-have">
                        Strong problem-solving abilities
                    </li>
                    <li class="skill preferred" data-priority="nice-to-have">
                        Experience leading technical teams
                    </li>
                </ul>
            </div>
        </section>
        
        <section class="timeline">
            <time class="deadline" datetime="2024-02-28">
                Application Deadline: February 28, 2024
            </time>
        </section>
        
        <footer class="contact-section">
            <div class="hiring-manager">
                <h4>Hiring Manager</h4>
                <div class="contact-info">
                    <span class="name">Dr. Sarah Chen</span>
                    <span class="title">Director of AI Research</span>
                    <span class="email">ai.hiring@example.com</span>
                </div>
            </div>
            <div class="team-info">
                <p>Join our team of 50+ researchers working on cutting-edge AI applications</p>
            </div>
        </footer>
    </div>
    """

    # Use raw:// prefix to pass HTML content directly
    url = f"raw://{dummy_html}"

    from pydantic import BaseModel, Field
    from typing import List, Optional

    # Define our schema using Pydantic
    class JobRequirement(BaseModel):
        category: str = Field(
            description="Category of the requirement (e.g., Technical, Soft Skills)"
        )
        items: List[str] = Field(
            description="List of specific requirements in this category"
        )
        priority: str = Field(
            description="Priority level (Required/Preferred) based on the HTML class or context"
        )

    class JobPosting(BaseModel):
        title: str = Field(description="Job title")
        department: str = Field(description="Department or team")
        location: str = Field(description="Job location, including remote options")
        salary_range: Optional[str] = Field(description="Salary range if specified")
        requirements: List[JobRequirement] = Field(
            description="Categorized job requirements"
        )
        application_deadline: Optional[str] = Field(
            description="Application deadline if specified"
        )
        contact_info: Optional[dict] = Field(
            description="Contact information from footer or contact section"
        )

    # First try with markdown (default)
    markdown_strategy = LLMExtractionStrategy(
        provider="openai/gpt-4o",
        api_token=os.getenv("OPENAI_API_KEY"),
        schema=JobPosting.model_json_schema(),
        extraction_type="schema",
        instruction="""
        Extract job posting details into structured data. Focus on the visible text content 
        and organize requirements into categories.
        """,
        input_format="markdown",  # default
    )

    # Then with HTML for better structure understanding
    html_strategy = LLMExtractionStrategy(
        provider="openai/gpt-4",
        api_token=os.getenv("OPENAI_API_KEY"),
        schema=JobPosting.model_json_schema(),
        extraction_type="schema",
        instruction="""
        Extract job posting details, using HTML structure to:
        1. Identify requirement priorities from CSS classes (e.g., 'required' vs 'preferred')
        2. Extract contact info from the page footer or dedicated contact section
        3. Parse salary information from specially formatted elements
        4. Determine application deadline from timestamp or date elements
        
        Use HTML attributes and classes to enhance extraction accuracy.
        """,
        input_format="html",  # explicitly use HTML
    )

    async with AsyncWebCrawler() as crawler:
        # Try with markdown first
        markdown_config = CrawlerRunConfig(extraction_strategy=markdown_strategy)
        markdown_result = await crawler.arun(url=url, config=markdown_config)
        print("\nMarkdown-based Extraction Result:")
        items = json.loads(markdown_result.extracted_content)
        print(json.dumps(items, indent=2))

        # Then with HTML for better structure understanding
        html_config = CrawlerRunConfig(extraction_strategy=html_strategy)
        html_result = await crawler.arun(url=url, config=html_config)
        print("\nHTML-based Extraction Result:")
        items = json.loads(html_result.extracted_content)
        print(json.dumps(items, indent=2))


# Main execution
async def main():
    print("Crawl4AI v0.4.24 Feature Walkthrough")
    print("====================================")

    # Run all demos
    await demo_ssl_features()
    await demo_content_filtering()
    await demo_json_extraction()
    # await demo_input_formats()


if __name__ == "__main__":
    asyncio.run(main())
