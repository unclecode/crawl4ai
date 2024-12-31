"""
Crawl4AI v0.4.24 Feature Walkthrough
===================================

This script demonstrates the new features introduced in Crawl4AI v0.4.24.
Each section includes detailed examples and explanations of the new capabilities.
"""

import asyncio
import os
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMExtractionStrategy
)
from crawl4ai.content_filter_strategy import PruningContentFilter

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

    browser_config = BrowserConfig(
        ignore_https_errors=True,
        verbose=True
    )

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        fetch_ssl_certificate=True  # Enable SSL certificate fetching
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config
        )
        print(f"SSL Crawl Success: {result.success}")
        if not result.success:
            print(f"SSL Error: {result.error_message}")

async def demo_content_filtering():
    """
    Smart Content Filtering Demo
    --------------------------
    
    Demonstrates the new content filtering system with:
    1. Regular expression pattern matching
    2. Length-based filtering
    3. Custom filtering rules
    4. Content chunking strategies
    
    This is particularly useful for:
    - Removing advertisements and boilerplate content
    - Extracting meaningful paragraphs
    - Filtering out irrelevant sections
    - Processing content in manageable chunks
    """
    print("\n2. Smart Content Filtering Demo")
    print("--------------------------------")

    content_filter = PruningContentFilter(
        min_word_threshold=50,
        threshold_type='dynamic',
        threshold=0.5
    )

    run_config = CrawlerRunConfig(
        content_filter=content_filter,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",
            config=run_config
        )
        print("Filtered Content Sample:")
        print(result.markdown[:500] + "...\n")

async def demo_json_extraction():
    """
    Advanced JSON Extraction Demo
    ---------------------------
    
    Demonstrates the enhanced JSON extraction capabilities:
    1. Using different input formats (markdown, html)
    2. Base element attributes extraction
    3. Complex nested structures
    4. Multiple extraction patterns
    
    Key features shown:
    - Extracting from different input formats (markdown vs html)
    - Extracting attributes from base elements (href, data-* attributes)
    - Processing repeated patterns
    - Handling optional fields
    - Computing derived values
    """
    print("\n3. Improved JSON Extraction Demo")
    print("--------------------------------")

    # Define the extraction schema with base element attributes
    json_strategy = JsonCssExtractionStrategy(
        schema={
            "name": "Blog Posts",
            "baseSelector": "div.article-list",
            "fields": [
                {
                    "name": "posts",
                    "selector": "article.post",
                    "type": "nested_list",
                    "baseFields": [
                        {"name": "category", "type": "attribute", "attribute": "data-category"},
                        {"name": "author_id", "type": "attribute", "attribute": "data-author"}
                    ],
                    "fields": [
                        {
                            "name": "title",
                            "selector": "h2.title a",
                            "type": "text",
                            "baseFields": [
                                {"name": "url", "type": "attribute", "attribute": "href"}
                            ]
                        },
                        {
                            "name": "author",
                            "selector": "div.meta a.author",
                            "type": "text",
                            "baseFields": [
                                {"name": "profile_url", "type": "attribute", "attribute": "href"}
                            ]
                        },
                        {
                            "name": "date",
                            "selector": "span.date",
                            "type": "text"
                        },
                        {
                            "name": "read_more",
                            "selector": "a.read-more",
                            "type": "nested",
                            "fields": [
                                {"name": "text", "type": "text"},
                                {"name": "url", "type": "attribute", "attribute": "href"}
                            ]
                        }
                    ]
                }
            ]
        }
    )

    # Demonstrate extraction from raw HTML
    run_config = CrawlerRunConfig(
        extraction_strategy=json_strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="raw:" + SAMPLE_HTML,  # Use raw: prefix for raw HTML
            config=run_config
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
        category: str = Field(description="Category of the requirement (e.g., Technical, Soft Skills)")
        items: List[str] = Field(description="List of specific requirements in this category")
        priority: str = Field(description="Priority level (Required/Preferred) based on the HTML class or context")

    class JobPosting(BaseModel):
        title: str = Field(description="Job title")
        department: str = Field(description="Department or team")
        location: str = Field(description="Job location, including remote options")
        salary_range: Optional[str] = Field(description="Salary range if specified")
        requirements: List[JobRequirement] = Field(description="Categorized job requirements")
        application_deadline: Optional[str] = Field(description="Application deadline if specified")
        contact_info: Optional[dict] = Field(description="Contact information from footer or contact section")

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
        input_format="markdown"  # default
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
        input_format="html"  # explicitly use HTML
    )

    async with AsyncWebCrawler() as crawler:
        # Try with markdown first
        markdown_config = CrawlerRunConfig(
            extraction_strategy=markdown_strategy
        )
        markdown_result = await crawler.arun(
            url=url,
            config=markdown_config
        )
        print("\nMarkdown-based Extraction Result:")
        items = json.loads(markdown_result.extracted_content)
        print(json.dumps(items, indent=2))

        # Then with HTML for better structure understanding
        html_config = CrawlerRunConfig(
            extraction_strategy=html_strategy
        )
        html_result = await crawler.arun(
            url=url,
            config=html_config
        )
        print("\nHTML-based Extraction Result:")
        items = json.loads(html_result.extracted_content)
        print(json.dumps(items, indent=2))

# Main execution
async def main():
    print("Crawl4AI v0.4.24 Feature Walkthrough")
    print("====================================")

    # Run all demos
    # await demo_ssl_features()
    # await demo_content_filtering()
    # await demo_json_extraction()
    await demo_input_formats()

if __name__ == "__main__":
    asyncio.run(main())
