"""
Company Website Scraper using Crawl4AI

This script crawls and scrapes company websites to extract information about:
- What the company does (products, services)
- How they produce it (manufacturing processes, technologies)
- Who it's for (target markets, industries)

Features:
- Deep crawling to explore relevant pages (Products, About, Services, etc.)
- Anti-scraping measures bypass (stealth mode, cookie handling)
- LLM-based intelligent extraction
- JSON output with markdown preservation
- Session management for complex sites
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter


# ===========================
# Data Models
# ===========================

class Product(BaseModel):
    """Product or Service information"""
    name: str = Field(..., description="Product or service name")
    description: str = Field(..., description="Detailed description of the product/service")
    category: Optional[str] = Field(None, description="Product category or type")
    target_market: Optional[str] = Field(None, description="Who this product/service is for")
    key_features: Optional[List[str]] = Field(None, description="Key features or capabilities")


class Industry(BaseModel):
    """Industry or market segment"""
    name: str = Field(..., description="Industry or market name")
    description: Optional[str] = Field(None, description="How the company serves this industry")


class CompanyInformation(BaseModel):
    """Comprehensive company information schema"""
    company_name: str = Field(..., description="Official company name")
    tagline: Optional[str] = Field(None, description="Company tagline or slogan")
    description: str = Field(..., description="What the company does - comprehensive description")

    # Products and Services
    products_services: List[Product] = Field(
        default_factory=list,
        description="List of products or services offered"
    )

    # Industries and Markets
    target_industries: List[Industry] = Field(
        default_factory=list,
        description="Industries or markets the company serves"
    )

    # Manufacturing/Production (if applicable)
    production_methods: Optional[List[str]] = Field(
        None,
        description="How products are manufactured or services are delivered"
    )

    technologies_used: Optional[List[str]] = Field(
        None,
        description="Key technologies, platforms, or methodologies used"
    )

    # Additional Information
    headquarters: Optional[str] = Field(None, description="Company headquarters location")
    year_founded: Optional[str] = Field(None, description="Year company was founded")
    company_size: Optional[str] = Field(None, description="Number of employees or company size")

    # Metadata
    url: str = Field(..., description="Company website URL")
    pages_analyzed: List[str] = Field(
        default_factory=list,
        description="URLs of pages analyzed"
    )


class ScraperResult(BaseModel):
    """Complete scraper result including metadata"""
    company_info: CompanyInformation
    markdown_content: Dict[str, str] = Field(
        default_factory=dict,
        description="Markdown content from each page analyzed"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    success: bool = True
    error_message: Optional[str] = None


# ===========================
# Company Website Scraper
# ===========================

class CompanyWebsiteScraper:
    """
    Advanced company website scraper using Crawl4AI
    """

    def __init__(
        self,
        llm_provider: str = "openai/gpt-4o",
        llm_api_key: Optional[str] = None,
        max_depth: int = 2,  # Reduced from 3 - less aggressive
        max_pages: int = 10,  # Reduced from 20 - avoid rate limits
        output_dir: str = "./scraped_companies",
        use_stealth: bool = True,
        headless: bool = True,
        verbose: bool = True
    ):
        """
        Initialize the company website scraper

        Args:
            llm_provider: LLM provider (e.g., "openai/gpt-4o", "anthropic/claude-3-opus")
            llm_api_key: API key for LLM provider (defaults to env variable)
            max_depth: Maximum depth for deep crawling
            max_pages: Maximum number of pages to crawl
            output_dir: Directory to save results
            use_stealth: Enable stealth mode to bypass bot detection
            headless: Run browser in headless mode
            verbose: Enable verbose logging
        """
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key or os.getenv('OPENAI_API_KEY')
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.use_stealth = use_stealth
        self.headless = headless
        self.verbose = verbose

        # Relevant keywords for company information pages (HIGH VALUE)
        self.relevant_keywords = [
            "about", "company", "mission", "vision",
            "products", "services", "solutions", "offerings",
            "industries", "markets", "sectors", "customers",
            "technology", "platform", "manufacturing", "process",
            "what we do", "our work", "portfolio", "capabilities"
        ]

        # URL patterns to prioritize (HIGH VALUE PAGES)
        self.url_patterns = [
            "*about*", "*company*",
            "*products*", "*services*", "*solutions*", "*offerings*",
            "*industries*", "*markets*", "*sectors*",
            "*technology*", "*platform*", "*manufacturing*",
            "*portfolio*", "*capabilities*"
        ]

        # HONEYPOT/LOW-VALUE URL patterns to AVOID
        # These are common traps that catch scrapers and provide little value
        self.blocked_patterns = [
            # Individual people (honeypot!)
            "*/leadership/*", "*/team/*", "*/executives/*",
            "*/management/*", "*/board/*", "*/people/*",
            "*/employee/*", "*/staff/*", "*/bio/*",

            # Blog/news (low value, often traps)
            "*/blog/*", "*/news/*", "*/press/*", "*/media/*",
            "*/article/*", "*/post/*", "*/story/*",

            # Careers/jobs (not relevant)
            "*/careers/*", "*/jobs/*", "*/hiring/*",
            "*/positions/*", "*/openings/*", "*/apply/*",

            # Events (low value)
            "*/events/*", "*/webinar/*", "*/conference/*",

            # Legal/policies (not relevant)
            "*/privacy*", "*/terms*", "*/legal*",
            "*/cookie*", "*/disclaimer*",

            # Support/help (not relevant for company info)
            "*/support/*", "*/help/*", "*/faq/*",
            "*/contact/*", "*/login/*", "*/signup/*",

            # Case studies of individual clients (often honeypots)
            "*/case-study/*", "*/customer/*", "*/client/*",

            # Resources/downloads (low value)
            "*/download/*", "*/resources/*", "*/whitepaper/*",
            "*/ebook/*", "*/pdf/*"
        ]

    def _create_browser_config(self) -> BrowserConfig:
        """Create browser configuration with anti-scraping measures"""
        return BrowserConfig(
            browser_type="chromium",
            headless=self.headless,
            enable_stealth=self.use_stealth,
            viewport_width=1920,
            viewport_height=1080,
            user_agent_mode="random",  # Rotate user agents
            extra_args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security"
            ],
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            verbose=self.verbose
        )

    def _create_deep_crawl_strategy(self) -> BestFirstCrawlingStrategy:
        """Create deep crawling strategy for intelligent page discovery"""
        # Create filter chain with both inclusion and exclusion filters
        filters = []

        # 1. BLOCK honeypot and low-value pages (reverse=True means block these patterns)
        if self.blocked_patterns:
            filters.append(
                URLPatternFilter(
                    patterns=self.blocked_patterns,
                    reverse=True  # This means: reject URLs matching these patterns
                )
            )

        # 2. ALLOW only high-value pages (if specified)
        if self.url_patterns:
            filters.append(
                URLPatternFilter(patterns=self.url_patterns)
            )

        url_filter = FilterChain(filters)

        # Keyword scorer to prioritize relevant pages
        keyword_scorer = KeywordRelevanceScorer(
            keywords=self.relevant_keywords,
            weight=0.8
        )

        return BestFirstCrawlingStrategy(
            max_depth=self.max_depth,
            max_pages=self.max_pages,
            include_external=False,  # Stay within the company domain
            filter_chain=url_filter,
            url_scorer=keyword_scorer
        )

    def _create_extraction_strategy(self) -> LLMExtractionStrategy:
        """Create LLM extraction strategy for intelligent data extraction"""
        llm_config = LLMConfig(
            provider=self.llm_provider,
            api_token=self.llm_api_key,
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=4000
        )

        extraction_instruction = """
        Analyze this webpage and extract comprehensive company information.

        Focus on:
        1. What the company does - products, services, solutions
        2. How they do it - manufacturing processes, technologies, methodologies
        3. Who it's for - target markets, industries, customer segments

        For manufacturers: Extract what they produce, production methods, and target industries.
        For software companies: Extract software products, technologies used, and target users.
        For service companies: Extract services offered, delivery methods, and target clients.

        Be thorough and extract all relevant details. If information is not available, omit those fields.
        """

        return LLMExtractionStrategy(
            llm_config=llm_config,
            schema=CompanyInformation.model_json_schema(),
            extraction_type="schema",
            instruction=extraction_instruction,
            input_format="fit_markdown"  # Use cleaned markdown for better LLM processing
        )

    async def scrape_company(
        self,
        url: str,
        session_id: Optional[str] = None
    ) -> ScraperResult:
        """
        Scrape a company website and extract comprehensive information

        Args:
            url: Company website URL
            session_id: Optional session ID for maintaining state across requests

        Returns:
            ScraperResult containing company information and metadata
        """
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"Starting to scrape: {url}")
            print(f"{'='*80}\n")

        browser_config = self._create_browser_config()

        # For session management
        if session_id is None:
            session_id = f"company_scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        all_results = []
        markdown_content = {}

        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                # Configure the crawling run
                config = CrawlerRunConfig(
                    # Deep crawling strategy
                    deep_crawl_strategy=self._create_deep_crawl_strategy(),

                    # Extraction strategy
                    extraction_strategy=self._create_extraction_strategy(),

                    # Page handling - LESS STRICT to avoid timeouts
                    wait_until="domcontentloaded",  # Don't wait for networkidle (too strict)
                    page_timeout=30000,  # 30 second timeout (reduced from 60s)
                    delay_before_return_html=3.0,  # Wait 3s for JS to load (increased)

                    # User simulation to appear more human
                    scan_full_page=True,  # Scroll through the page
                    scroll_delay=0.5,  # Slower scrolling (more human-like)
                    simulate_user=True,
                    override_navigator=True,

                    # Handle dynamic content
                    remove_overlay_elements=True,  # Remove popups/modals
                    magic=True,  # Auto-handle common overlays

                    # Session management
                    session_id=session_id,

                    # Caching
                    cache_mode=CacheMode.BYPASS,  # Always get fresh data

                    # Logging
                    verbose=self.verbose,

                    # Streaming results as they arrive
                    stream=True
                )

                if self.verbose:
                    print("Starting deep crawl...\n")

                # Crawl the website (streaming results)
                async for result in await crawler.arun(url=url, config=config):
                    if result.success:
                        depth = result.metadata.get('depth', 0)
                        if self.verbose:
                            print(f"  [Depth {depth}] Scraped: {result.url}")

                        # Store markdown content
                        markdown_content[result.url] = result.markdown.fit_markdown

                        # Store extracted data
                        if result.extracted_content:
                            try:
                                extracted_data = json.loads(result.extracted_content)
                                all_results.append({
                                    'url': result.url,
                                    'data': extracted_data,
                                    'depth': depth
                                })
                            except json.JSONDecodeError as e:
                                if self.verbose:
                                    print(f"    Warning: Failed to parse JSON from {result.url}: {e}")
                    else:
                        if self.verbose:
                            print(f"  Failed: {result.url} - {result.error_message}")

                # Clean up session
                await crawler.crawler_strategy.kill_session(session_id)

            # Merge all extracted data intelligently
            if self.verbose:
                print(f"\n{'='*80}")
                print(f"Scraped {len(all_results)} pages successfully")
                print(f"{'='*80}\n")
                print("Merging extracted data...")

            company_info = self._merge_extracted_data(all_results, url)

            return ScraperResult(
                company_info=company_info,
                markdown_content=markdown_content,
                success=True
            )

        except Exception as e:
            error_msg = f"Error scraping {url}: {str(e)}"
            if self.verbose:
                print(f"\nERROR: {error_msg}\n")

            return ScraperResult(
                company_info=CompanyInformation(
                    company_name="Unknown",
                    description="Failed to extract",
                    url=url
                ),
                success=False,
                error_message=error_msg
            )

    def _merge_extracted_data(
        self,
        results: List[Dict[str, Any]],
        url: str
    ) -> CompanyInformation:
        """
        Intelligently merge data extracted from multiple pages

        Args:
            results: List of extraction results from different pages
            url: Original URL

        Returns:
            Merged CompanyInformation
        """
        if not results:
            return CompanyInformation(
                company_name="Unknown",
                description="No data extracted",
                url=url
            )

        # Helper function to normalize extracted data
        def normalize_data(data: Any) -> Dict[str, Any]:
            """Convert various data formats to a consistent dictionary"""
            if isinstance(data, dict):
                return data
            elif isinstance(data, list) and len(data) > 0:
                # If it's a list, take the first item
                return normalize_data(data[0])
            elif isinstance(data, str):
                # If it's a string, try to parse it as JSON
                try:
                    parsed = json.loads(data)
                    return normalize_data(parsed)
                except:
                    return {}
            else:
                return {}

        # Start with the first result (usually homepage)
        first_data = normalize_data(results[0]['data'])
        if not first_data:
            return CompanyInformation(
                company_name="Unknown",
                description="Failed to parse extracted data",
                url=url
            )

        merged = first_data.copy()
        merged['pages_analyzed'] = [results[0]['url']]
        merged['url'] = url

        # Merge additional results
        for result in results[1:]:
            data = normalize_data(result['data'])
            if not data:
                continue

            merged['pages_analyzed'].append(result['url'])

            # Merge lists (products, industries, etc.)
            for key in ['products_services', 'target_industries', 'production_methods', 'technologies_used']:
                if key in data and data[key]:
                    if key not in merged or not merged[key]:
                        merged[key] = []

                    # Add unique items
                    if isinstance(data[key], list):
                        for item in data[key]:
                            # Handle both dict and string items
                            if isinstance(item, dict):
                                # Check if this dict is already in the list
                                if item not in merged[key]:
                                    merged[key].append(item)
                            else:
                                if item not in merged[key]:
                                    merged[key].append(item)

            # Update if more detailed
            if 'description' in data and data.get('description'):
                current_desc = merged.get('description', '')
                if isinstance(current_desc, str) and isinstance(data['description'], str):
                    if len(data['description']) > len(current_desc):
                        merged['description'] = data['description']

            # Fill in missing fields
            for key in ['company_name', 'tagline', 'headquarters', 'year_founded', 'company_size']:
                if key in data and data.get(key) and not merged.get(key):
                    merged[key] = data[key]

        # Ensure required fields are present
        if 'company_name' not in merged or not merged['company_name']:
            merged['company_name'] = "Unknown"
        if 'description' not in merged or not merged['description']:
            merged['description'] = "No description available"

        try:
            return CompanyInformation(**merged)
        except Exception as e:
            # If validation fails, return a minimal valid object
            if self.verbose:
                print(f"Warning: Failed to create CompanyInformation: {e}")
                print(f"Merged data keys: {merged.keys()}")
            return CompanyInformation(
                company_name=merged.get('company_name', 'Unknown'),
                description=merged.get('description', 'Failed to merge data'),
                url=url,
                pages_analyzed=merged.get('pages_analyzed', [url])
            )

    def save_results(
        self,
        result: ScraperResult,
        company_name: Optional[str] = None
    ) -> Path:
        """
        Save scraping results to JSON file

        Args:
            result: ScraperResult to save
            company_name: Optional company name for filename (uses extracted name if not provided)

        Returns:
            Path to saved JSON file
        """
        if company_name is None:
            company_name = result.company_info.company_name

        # Sanitize filename
        safe_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_'))
        safe_name = safe_name.strip().replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create filename
        filename = f"{safe_name}_{timestamp}.json"
        filepath = self.output_dir / filename

        # Save to JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)

        if self.verbose:
            print(f"\nResults saved to: {filepath}")

        return filepath

    def save_markdown_summary(
        self,
        result: ScraperResult,
        company_name: Optional[str] = None
    ) -> Path:
        """
        Save markdown content summary for LLM processing

        Args:
            result: ScraperResult containing markdown content
            company_name: Optional company name for filename

        Returns:
            Path to saved markdown file
        """
        if company_name is None:
            company_name = result.company_info.company_name

        # Sanitize filename
        safe_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_'))
        safe_name = safe_name.strip().replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create filename
        filename = f"{safe_name}_{timestamp}_content.md"
        filepath = self.output_dir / filename

        # Build markdown document
        md_content = f"# {result.company_info.company_name}\n\n"
        md_content += f"**URL:** {result.company_info.url}\n\n"
        md_content += f"**Scraped:** {result.timestamp}\n\n"
        md_content += "---\n\n"

        for page_url, content in result.markdown_content.items():
            md_content += f"## Page: {page_url}\n\n"
            md_content += content
            md_content += "\n\n---\n\n"

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)

        if self.verbose:
            print(f"Markdown summary saved to: {filepath}")

        return filepath


# ===========================
# CLI Interface
# ===========================

async def main():
    """Main CLI interface for the scraper"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape company websites to extract business information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape a single company website
  python company_website_scraper.py https://example.com

  # Scrape with custom settings
  python company_website_scraper.py https://example.com \\
    --max-depth 4 \\
    --max-pages 30 \\
    --llm-provider "anthropic/claude-3-opus"

  # Scrape multiple companies
  python company_website_scraper.py https://company1.com https://company2.com
        """
    )

    parser.add_argument(
        'urls',
        nargs='+',
        help='Company website URL(s) to scrape'
    )
    parser.add_argument(
        '--llm-provider',
        default='openai/gpt-4o',
        help='LLM provider (default: openai/gpt-4o)'
    )
    parser.add_argument(
        '--llm-api-key',
        help='LLM API key (defaults to OPENAI_API_KEY env variable)'
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        default=3,
        help='Maximum crawling depth (default: 3)'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=20,
        help='Maximum pages to crawl (default: 20)'
    )
    parser.add_argument(
        '--output-dir',
        default='./scraped_companies',
        help='Output directory (default: ./scraped_companies)'
    )
    parser.add_argument(
        '--no-stealth',
        action='store_true',
        help='Disable stealth mode'
    )
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Run browser in visible mode'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Disable verbose output'
    )
    parser.add_argument(
        '--save-markdown',
        action='store_true',
        help='Save markdown content for LLM processing'
    )

    args = parser.parse_args()

    # Create scraper instance
    scraper = CompanyWebsiteScraper(
        llm_provider=args.llm_provider,
        llm_api_key=args.llm_api_key,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        output_dir=args.output_dir,
        use_stealth=not args.no_stealth,
        headless=not args.no_headless,
        verbose=not args.quiet
    )

    # Scrape each URL
    for url in args.urls:
        result = await scraper.scrape_company(url)

        if result.success:
            # Save JSON results
            json_path = scraper.save_results(result)

            # Optionally save markdown
            if args.save_markdown:
                md_path = scraper.save_markdown_summary(result)

            # Print summary
            print(f"\n{'='*80}")
            print(f"SCRAPING SUMMARY - {result.company_info.company_name}")
            print(f"{'='*80}")
            print(f"Company: {result.company_info.company_name}")
            print(f"URL: {result.company_info.url}")
            print(f"Products/Services: {len(result.company_info.products_services)}")
            print(f"Industries: {len(result.company_info.target_industries)}")
            print(f"Pages Analyzed: {len(result.company_info.pages_analyzed)}")
            print(f"Results saved to: {json_path}")
            print(f"{'='*80}\n")
        else:
            print(f"\nFailed to scrape {url}: {result.error_message}\n")


if __name__ == "__main__":
    asyncio.run(main())
