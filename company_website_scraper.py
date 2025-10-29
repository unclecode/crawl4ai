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
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Rich library for beautiful terminal output
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

# Load environment variables from .env file
load_dotenv()

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter

# Initialize rich console
console = Console()


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


class ScraperStats(BaseModel):
    """Statistics for a scraping session"""
    total_pages_attempted: int = 0
    total_pages_succeeded: int = 0
    total_pages_failed: int = 0
    llm_api_calls: int = 0
    estimated_cost: float = 0.0
    total_time_seconds: float = 0.0
    pages_per_minute: float = 0.0
    success_rate: float = 0.0


class QualityScore(BaseModel):
    """Data quality scoring"""
    completeness: float = 0.0  # 0-100: How many fields are filled
    confidence: float = 0.0    # 0-100: Overall confidence in extraction
    page_coverage: float = 0.0  # 0-100: % of expected pages found
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ScraperResult(BaseModel):
    """Complete scraper result including metadata"""
    company_info: CompanyInformation
    markdown_content: Dict[str, str] = Field(
        default_factory=dict,
        description="Markdown content from each page analyzed"
    )
    stats: ScraperStats = Field(default_factory=ScraperStats)
    quality_score: QualityScore = Field(default_factory=QualityScore)
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
            "what we do", "our work", "portfolio", "capabilities",
            "features", "integrations", "use case", "methodology"
        ]

        # URL patterns to prioritize (HIGH VALUE PAGES)
        self.url_patterns = [
            # Company overview
            "*about*", "*company*",

            # Core offerings - Products & Services
            "*products*", "*product/*", "*product-line/*",
            "*services*", "*service/*", "*professional-services*", "*consulting*",
            "*solutions*", "*solution/*", "*offerings*",

            # Platform & Technology
            "*platform*", "*suite*", "*software*", "*cloud*", "*saas*",
            "*app*", "*apps*",

            # Features & Capabilities
            "*features*", "*capabilities*", "*modules*",
            "*addon*", "*add-on*", "*extension*",

            # Use Cases & Applications
            "*use-case*", "*usecase*", "*by-need*",

            # How It Works (especially valuable for manufacturers!)
            "*how-it-works*", "*how-we-work*",
            "*methodology*", "*approach*", "*process*", "*framework*",

            # Markets & Industries
            "*industries*", "*industry/*", "*markets*", "*sectors*",
            "*segments*", "*vertical*",

            # Integrations & Technical
            "*integration*", "*integrations*", "*connector*",
            "*api*", "*developer*",

            # Competitive & Value
            "*compare*", "*vs/*", "*alternative*",
            "*outcome*", "*benefit*", "*result*",

            # Manufacturing specific
            "*manufacturing*", "*portfolio*"
        ]

        # HONEYPOT/LOW-VALUE URL patterns to AVOID
        # These are common traps that catch scrapers and provide little value
        self.blocked_patterns = [
            # Individual people (honeypot!)
            "*/leadership/*", "*/team/*", "*/executives/*",
            "*/management/*", "*/board/*", "*/people/*",
            "*/employee/*", "*/staff/*", "*/bio/*",

            # Lead generation forms (MAJOR HONEYPOTS!)
            "*/demo*", "*/trial*", "*/get-started*",
            "*/request-*", "*/talk-to-*", "*/book-*",
            "*/contact-sales*", "*/speak-*", "*/schedule-*",

            # Campaign landing pages (HONEYPOTS!)
            "*/lp/*", "*/campaign/*", "*/go/*", "*/promo/*",
            "*/pages/*",  # Often campaign-specific pages

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
            "*/customer-story/*", "*/success-story/*",
            "*/testimonial/*",

            # Partner pages (can be honeypots)
            "*/partner/*",  # Individual partner pages
            "*/find-a-partner*", "*/partner-directory*",
            "*/partner-locator*",

            # Community/forums (low value)
            "*/community*", "*/forum*", "*/discuss*",
            "*/slack*", "*/discord*",

            # Resources/downloads (gated content)
            "*/download/*", "*/resources/*", "*/whitepaper/*",
            "*/ebook/*", "*/pdf/*", "*/guide/*",
            "*/datasheet/*", "*/brochure/*"
        ]

        # LLM pricing per 1M tokens (approximate as of Jan 2025)
        self.llm_pricing = {
            "openai/gpt-4o": {"input": 2.50, "output": 10.00},
            "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "openai/gpt-4": {"input": 30.00, "output": 60.00},
            "anthropic/claude-3-opus": {"input": 15.00, "output": 75.00},
            "anthropic/claude-3-sonnet": {"input": 3.00, "output": 15.00},
            "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
        }

        # Error tracking
        self.error_counts = {
            "timeout": 0,
            "rate_limit": 0,
            "bot_detection": 0,
            "network": 0,
            "other": 0
        }

        # Checkpoint file for batch processing
        self.checkpoint_file = self.output_dir / ".scraping_checkpoint.json"

    def _categorize_error(self, error_message: str) -> str:
        """
        Categorize error type for smart handling

        Returns:
            Error category: timeout, rate_limit, bot_detection, network, or other
        """
        error_lower = error_message.lower()

        if "timeout" in error_lower or "timed out" in error_lower:
            return "timeout"
        elif "rate" in error_lower or "quota" in error_lower or "429" in error_lower:
            return "rate_limit"
        elif "aborted" in error_lower or "blocked" in error_lower or "403" in error_lower:
            return "bot_detection"
        elif "network" in error_lower or "connection" in error_lower or "dns" in error_lower:
            return "network"
        else:
            return "other"

    def _should_stop_scraping(self) -> tuple[bool, str]:
        """
        Determine if scraping should stop based on error patterns

        Returns:
            (should_stop, reason)
        """
        total_errors = sum(self.error_counts.values())

        # Stop if bot detection is consistently triggering
        if self.error_counts["bot_detection"] >= 5:
            return True, "Too many bot detection errors - site has strong anti-scraping"

        # Stop if rate limited multiple times
        if self.error_counts["rate_limit"] >= 3:
            return True, "Rate limit exceeded - please wait before retrying"

        # Stop if network is consistently failing
        if self.error_counts["network"] >= 5:
            return True, "Network issues - check your internet connection"

        # Stop if too many errors overall
        if total_errors >= 8:
            return True, "Too many errors overall - scraping may not be viable for this site"

        return False, ""

    def save_checkpoint(self, completed_urls: List[str], remaining_urls: List[str]):
        """Save checkpoint for batch processing"""
        checkpoint = {
            "completed": completed_urls,
            "remaining": remaining_urls,
            "timestamp": datetime.now().isoformat()
        }
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load checkpoint if it exists"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                if self.verbose:
                    console.print(f"[yellow]Warning:[/yellow] Could not load checkpoint: {e}")
        return None

    def clear_checkpoint(self):
        """Clear checkpoint file"""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

    async def scrape_companies_batch(
        self,
        urls: List[str],
        resume: bool = True
    ) -> List[ScraperResult]:
        """
        Scrape multiple companies with checkpoint/resume support

        Args:
            urls: List of company URLs to scrape
            resume: If True, resume from checkpoint if available

        Returns:
            List of ScraperResult objects
        """
        # Check for checkpoint
        remaining_urls = urls.copy()
        completed_urls = []
        results = []

        if resume:
            checkpoint = self.load_checkpoint()
            if checkpoint:
                completed_urls = checkpoint.get("completed", [])
                checkpoint_remaining = checkpoint.get("remaining", [])

                # Filter out already completed URLs
                remaining_urls = [url for url in urls if url not in completed_urls]

                if self.verbose:
                    console.print(f"\n[cyan]📍 Resuming from checkpoint:[/cyan]")
                    console.print(f"  Already completed: {len(completed_urls)} companies")
                    console.print(f"  Remaining: {len(remaining_urls)} companies\n")

        # Create progress table for batch
        if self.verbose and len(remaining_urls) > 1:
            panel = Panel(
                f"[bold cyan]Batch Scraping[/bold cyan]\n\n"
                f"[white]Total Companies:[/white] {len(urls)}\n"
                f"[white]Already Completed:[/white] {len(completed_urls)}\n"
                f"[white]Remaining:[/white] {len(remaining_urls)}\n"
                f"[white]Total Estimated Cost:[/white] [green]${self._estimate_llm_cost(self.max_pages * len(remaining_urls)):.4f}[/green]",
                title="[bold]Batch Processing[/bold]",
                border_style="cyan",
                box=box.ROUNDED
            )
            console.print(panel)
            console.print()

        # Scrape each company
        for i, url in enumerate(remaining_urls, 1):
            if self.verbose:
                console.print(f"\n[bold cyan]Company {i}/{len(remaining_urls)}[/bold cyan]\n")

            try:
                result = await self.scrape_company(url)
                results.append(result)
                completed_urls.append(url)

                # Update checkpoint after each successful scrape
                still_remaining = remaining_urls[i:]
                self.save_checkpoint(completed_urls, still_remaining)

                # Small delay between companies to be respectful
                if i < len(remaining_urls):
                    await asyncio.sleep(2)

            except KeyboardInterrupt:
                if self.verbose:
                    console.print("\n[yellow]⚠️  Interrupted by user[/yellow]")
                    console.print(f"[cyan]Progress saved. Resume later with --resume flag[/cyan]\n")
                break
            except Exception as e:
                if self.verbose:
                    console.print(f"[red]Error scraping {url}: {e}[/red]")
                # Continue with next company

        # Clear checkpoint if all completed
        if len(completed_urls) == len(urls):
            self.clear_checkpoint()
            if self.verbose:
                console.print(f"\n[green]✓ All companies scraped successfully![/green]\n")

        return results

    def _estimate_llm_cost(self, num_pages: int) -> float:
        """
        Estimate LLM API cost based on pages to be scraped

        Assumptions:
        - Average page: ~3000 tokens input
        - Average extraction: ~500 tokens output
        """
        pricing = self.llm_pricing.get(self.llm_provider, {"input": 2.50, "output": 10.00})

        tokens_input = num_pages * 3000  # ~3k tokens per page
        tokens_output = num_pages * 500  # ~500 tokens per response

        cost_input = (tokens_input / 1_000_000) * pricing["input"]
        cost_output = (tokens_output / 1_000_000) * pricing["output"]

        return cost_input + cost_output

    def _calculate_quality_score(self, company_info: CompanyInformation, stats: ScraperStats) -> QualityScore:
        """Calculate quality score for extracted data"""
        issues = []
        warnings = []

        # Completeness: Check how many fields are filled
        total_fields = 0
        filled_fields = 0

        # Core fields (required)
        if company_info.company_name and company_info.company_name != "Unknown":
            filled_fields += 1
        else:
            issues.append("Company name not found")
        total_fields += 1

        if company_info.description and company_info.description != "No description available":
            filled_fields += 1
        else:
            issues.append("Company description missing or generic")
        total_fields += 1

        # Products/services
        if company_info.products_services:
            filled_fields += 1
            if len(company_info.products_services) < 2:
                warnings.append(f"Only {len(company_info.products_services)} product/service found")
        else:
            issues.append("No products or services identified")
        total_fields += 1

        # Industries
        if company_info.target_industries:
            filled_fields += 1
            if len(company_info.target_industries) < 2:
                warnings.append(f"Only {len(company_info.target_industries)} industry found")
        else:
            warnings.append("No target industries identified")
        total_fields += 1

        # Optional but valuable fields
        optional_fields = [
            ("tagline", company_info.tagline),
            ("headquarters", company_info.headquarters),
            ("year_founded", company_info.year_founded),
            ("company_size", company_info.company_size),
            ("technologies_used", company_info.technologies_used),
            ("production_methods", company_info.production_methods)
        ]

        for field_name, field_value in optional_fields:
            total_fields += 1
            if field_value:
                filled_fields += 1

        completeness = (filled_fields / total_fields) * 100

        # Confidence: Based on success rate and data availability
        confidence = stats.success_rate

        # Reduce confidence if we have issues
        if len(issues) > 0:
            confidence *= 0.7
        if len(warnings) > 2:
            confidence *= 0.9

        # Page coverage: Did we get the expected pages?
        expected_page_types = ["about", "products", "services", "industries"]
        found_page_types = 0

        for page in company_info.pages_analyzed:
            page_lower = page.lower()
            for expected in expected_page_types:
                if expected in page_lower:
                    found_page_types += 1
                    break

        page_coverage = (found_page_types / len(expected_page_types)) * 100

        # Add recommendations based on error patterns
        if self.error_counts["bot_detection"] > 2:
            warnings.append("High bot detection - consider more conservative scraping settings")
        if self.error_counts["timeout"] > 3:
            warnings.append("Many timeouts - try increasing page_timeout or reducing max_depth")
        if self.error_counts["rate_limit"] > 0:
            warnings.append("Rate limiting detected - wait before re-scraping this site")

        return QualityScore(
            completeness=round(completeness, 1),
            confidence=round(confidence, 1),
            page_coverage=round(page_coverage, 1),
            issues=issues,
            warnings=warnings
        )

    def _print_start_banner(self, url: str):
        """Print a beautiful start banner"""
        panel = Panel(
            f"[bold cyan]Company Website Scraper[/bold cyan]\n\n"
            f"[white]Target:[/white] [yellow]{url}[/yellow]\n"
            f"[white]Max Depth:[/white] {self.max_depth}\n"
            f"[white]Max Pages:[/white] {self.max_pages}\n"
            f"[white]LLM:[/white] {self.llm_provider}\n"
            f"[white]Estimated Cost:[/white] [green]${self._estimate_llm_cost(self.max_pages):.4f}[/green]",
            title="[bold]Starting Scrape[/bold]",
            border_style="cyan",
            box=box.ROUNDED
        )
        console.print(panel)

    def _print_summary(self, result: ScraperResult):
        """Print a beautiful results summary"""
        stats = result.stats
        quality = result.quality_score
        company = result.company_info

        # Create summary table
        table = Table(title="Scraping Results", box=box.ROUNDED, show_header=False, border_style="cyan")
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", style="white")

        # Company info
        table.add_row("[bold]Company Name[/bold]", company.company_name)
        table.add_row("Description", company.description[:80] + "..." if len(company.description) > 80 else company.description)

        # Stats
        table.add_row("", "")  # Spacer
        table.add_row("[bold]Statistics[/bold]", "")
        table.add_row("Pages Attempted", str(stats.total_pages_attempted))
        table.add_row("Pages Succeeded", f"[green]{stats.total_pages_succeeded}[/green]")
        table.add_row("Pages Failed", f"[red]{stats.total_pages_failed}[/red]" if stats.total_pages_failed > 0 else "0")
        table.add_row("Success Rate", f"{stats.success_rate:.1f}%")

        # Show error breakdown if there were failures
        if stats.total_pages_failed > 0 and sum(self.error_counts.values()) > 0:
            table.add_row("", "")  # Spacer
            table.add_row("[bold]Error Breakdown[/bold]", "")
            for error_type, count in self.error_counts.items():
                if count > 0:
                    emoji_map = {
                        "timeout": "⏱️",
                        "rate_limit": "🚫",
                        "bot_detection": "🛡️",
                        "network": "🌐",
                        "other": "❌"
                    }
                    table.add_row(f"{emoji_map[error_type]} {error_type.replace('_', ' ').title()}", str(count))
        table.add_row("Time Taken", f"{stats.total_time_seconds:.1f}s")
        table.add_row("Speed", f"{stats.pages_per_minute:.1f} pages/min")

        # LLM costs
        table.add_row("LLM API Calls", str(stats.llm_api_calls))
        table.add_row("Estimated Cost", f"[green]${stats.estimated_cost:.4f}[/green]")

        # Data extracted
        table.add_row("", "")  # Spacer
        table.add_row("[bold]Data Extracted[/bold]", "")
        table.add_row("Products/Services", str(len(company.products_services)))
        table.add_row("Target Industries", str(len(company.target_industries)))
        if company.technologies_used:
            table.add_row("Technologies", str(len(company.technologies_used)))
        if company.production_methods:
            table.add_row("Production Methods", str(len(company.production_methods)))

        # Quality scores
        table.add_row("", "")  # Spacer
        table.add_row("[bold]Quality Scores[/bold]", "")

        # Color code quality scores
        def color_score(score):
            if score >= 80:
                return f"[green]{score}%[/green]"
            elif score >= 60:
                return f"[yellow]{score}%[/yellow]"
            else:
                return f"[red]{score}%[/red]"

        table.add_row("Completeness", color_score(quality.completeness))
        table.add_row("Confidence", color_score(quality.confidence))
        table.add_row("Page Coverage", color_score(quality.page_coverage))

        console.print(table)

        # Print issues and warnings
        if quality.issues:
            console.print("\n[bold red]Issues:[/bold red]")
            for issue in quality.issues:
                console.print(f"  [red]✗[/red] {issue}")

        if quality.warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in quality.warnings:
                console.print(f"  [yellow]![/yellow] {warning}")

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
        # Initialize stats tracking
        stats = ScraperStats()
        start_time = time.time()

        if self.verbose:
            self._print_start_banner(url)
            console.print()

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

                # Use rich progress bar
                if self.verbose:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        TaskProgressColumn(),
                        TimeRemainingColumn(),
                        console=console
                    ) as progress:
                        task = progress.add_task(
                            f"[cyan]Crawling {url}...",
                            total=self.max_pages
                        )

                        # Crawl the website (streaming results)
                        async for result in await crawler.arun(url=url, config=config):
                            stats.total_pages_attempted += 1

                            if result.success:
                                stats.total_pages_succeeded += 1
                                depth = result.metadata.get('depth', 0)

                                # Update progress
                                progress.update(task, advance=1, description=f"[green]✓[/green] Scraped: {result.url[:60]}...")

                                # Store markdown content
                                markdown_content[result.url] = result.markdown.fit_markdown

                                # Store extracted data
                                if result.extracted_content:
                                    stats.llm_api_calls += 1
                                    try:
                                        extracted_data = json.loads(result.extracted_content)
                                        all_results.append({
                                            'url': result.url,
                                            'data': extracted_data,
                                            'depth': depth
                                        })
                                    except json.JSONDecodeError as e:
                                        console.print(f"[yellow]Warning:[/yellow] Failed to parse JSON from {result.url}")
                            else:
                                stats.total_pages_failed += 1

                                # Categorize and track error
                                error_type = self._categorize_error(result.error_message or "Unknown error")
                                self.error_counts[error_type] += 1

                                # Update progress with error indicator
                                error_emoji = {
                                    "timeout": "⏱️",
                                    "rate_limit": "🚫",
                                    "bot_detection": "🛡️",
                                    "network": "🌐",
                                    "other": "❌"
                                }
                                progress.update(task, advance=1, description=f"[red]{error_emoji[error_type]}[/red] Failed ({error_type}): {result.url[:50]}...")

                                # Check if we should stop scraping
                                should_stop, stop_reason = self._should_stop_scraping()
                                if should_stop:
                                    console.print(f"\n[bold yellow]⚠️  Stopping scrape:[/bold yellow] {stop_reason}")
                                    break

                        # Finish progress
                        progress.update(task, completed=self.max_pages)
                else:
                    # Non-verbose mode
                    async for result in await crawler.arun(url=url, config=config):
                        stats.total_pages_attempted += 1

                        if result.success:
                            stats.total_pages_succeeded += 1
                            markdown_content[result.url] = result.markdown.fit_markdown

                            if result.extracted_content:
                                stats.llm_api_calls += 1
                                try:
                                    extracted_data = json.loads(result.extracted_content)
                                    all_results.append({
                                        'url': result.url,
                                        'data': extracted_data,
                                        'depth': result.metadata.get('depth', 0)
                                    })
                                except json.JSONDecodeError:
                                    pass
                        else:
                            stats.total_pages_failed += 1

                            # Track error even in non-verbose mode
                            error_type = self._categorize_error(result.error_message or "Unknown error")
                            self.error_counts[error_type] += 1

                            # Check if we should stop
                            should_stop, stop_reason = self._should_stop_scraping()
                            if should_stop:
                                break

                # Clean up session
                await crawler.crawler_strategy.kill_session(session_id)

            # Calculate stats
            stats.total_time_seconds = time.time() - start_time
            if stats.total_pages_attempted > 0:
                stats.success_rate = (stats.total_pages_succeeded / stats.total_pages_attempted) * 100
            if stats.total_time_seconds > 0:
                stats.pages_per_minute = (stats.total_pages_succeeded / stats.total_time_seconds) * 60
            stats.estimated_cost = self._estimate_llm_cost(stats.llm_api_calls)

            # Merge all extracted data intelligently
            if self.verbose:
                console.print()
                with console.status("[cyan]Merging extracted data...", spinner="dots"):
                    time.sleep(0.5)  # Brief pause for effect
                    company_info = self._merge_extracted_data(all_results, url)
            else:
                company_info = self._merge_extracted_data(all_results, url)

            # Calculate quality score
            quality_score = self._calculate_quality_score(company_info, stats)

            # Create result
            result = ScraperResult(
                company_info=company_info,
                markdown_content=markdown_content,
                stats=stats,
                quality_score=quality_score,
                success=True
            )

            # Print summary
            if self.verbose:
                console.print()
                self._print_summary(result)

            return result

        except Exception as e:
            # Calculate time even for failures
            stats.total_time_seconds = time.time() - start_time

            error_msg = f"Error scraping {url}: {str(e)}"
            if self.verbose:
                console.print(f"\n[bold red]ERROR:[/bold red] {error_msg}\n")

            return ScraperResult(
                company_info=CompanyInformation(
                    company_name="Unknown",
                    description="Failed to extract",
                    url=url
                ),
                stats=stats,
                quality_score=QualityScore(
                    issues=["Scraping failed with exception"]
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
            console.print(f"\n[green]✓[/green] Results saved to: [yellow]{filepath}[/yellow]")

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
            console.print(f"[green]✓[/green] Markdown summary saved to: [yellow]{filepath}[/yellow]")

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
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from checkpoint if batch scraping was interrupted'
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

    # Use batch processing if multiple URLs
    if len(args.urls) > 1:
        # Batch mode
        results = await scraper.scrape_companies_batch(args.urls, resume=args.resume)

        # Save all results
        for result in results:
            if result.success:
                json_path = scraper.save_results(result)
                if args.save_markdown:
                    scraper.save_markdown_summary(result)
    else:
        # Single company mode
        result = await scraper.scrape_company(args.urls[0])

        if result.success:
            # Save JSON results
            json_path = scraper.save_results(result)

            # Optionally save markdown
            if args.save_markdown:
                md_path = scraper.save_markdown_summary(result)

            # In quiet mode, show minimal output
            if args.quiet:
                console.print(f"\n[green]✓[/green] Successfully scraped [cyan]{result.company_info.company_name}[/cyan]")
                console.print(f"  Results saved to: [yellow]{json_path}[/yellow]\n")
            # In verbose mode, the summary was already printed by scrape_company()
        else:
            console.print(f"\n[red]✗ Failed to scrape {args.urls[0]}:[/red] {result.error_message}\n")


if __name__ == "__main__":
    asyncio.run(main())
