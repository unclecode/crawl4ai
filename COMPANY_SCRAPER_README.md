# Company Website Scraper

A powerful Python script built on Crawl4AI for intelligently scraping company websites to extract business information including products, services, target markets, and manufacturing processes.

## Features

- **Deep Crawling**: Intelligently explores company websites, prioritizing relevant pages (Products, Services, About, Industries, etc.)
- **Anti-Scraping Bypass**: Handles cookies, bot detection, and other anti-scraping measures using stealth mode
- **LLM-Powered Extraction**: Uses GPT-4 or other LLMs to intelligently extract structured company information
- **Comprehensive Data Collection**:
  - Company overview (name, tagline, description)
  - Products and services
  - Target industries and markets
  - Manufacturing/production methods
  - Technologies used
  - Company metadata (size, location, founding year)
- **Multiple Output Formats**:
  - Structured JSON with all extracted data
  - Markdown content for LLM post-processing
- **Session Management**: Handles complex sites requiring cookies and state persistence

## Installation

### Prerequisites

```bash
# Install Crawl4AI (if not already installed)
pip install crawl4ai

# Install required dependencies
pip install pydantic
```

### API Keys

The scraper requires an LLM API key. By default it uses OpenAI's GPT-4:

```bash
export OPENAI_API_KEY='your-openai-api-key'
```

You can also use other providers (Anthropic Claude, local Ollama, etc.) - see Configuration section.

## Quick Start

### Basic Usage

```bash
# Scrape a single company website
python company_website_scraper.py https://example.com

# Scrape multiple companies
python company_website_scraper.py https://company1.com https://company2.com

# Save markdown content for LLM processing
python company_website_scraper.py https://example.com --save-markdown
```

### Programmatic Usage

```python
import asyncio
from company_website_scraper import CompanyWebsiteScraper

async def scrape_company():
    # Initialize scraper
    scraper = CompanyWebsiteScraper(
        llm_provider="openai/gpt-4o",
        max_depth=3,
        max_pages=20,
        verbose=True
    )

    # Scrape company website
    result = await scraper.scrape_company("https://example.com")

    if result.success:
        # Save results
        scraper.save_results(result)

        # Access data
        company = result.company_info
        print(f"Company: {company.company_name}")
        print(f"Products: {len(company.products_services)}")
        print(f"Industries: {len(company.target_industries)}")
    else:
        print(f"Error: {result.error_message}")

asyncio.run(scrape_company())
```

## Configuration

### Command Line Options

```bash
python company_website_scraper.py [URL] [OPTIONS]

Options:
  --llm-provider TEXT       LLM provider (default: openai/gpt-4o)
                           Options: openai/gpt-4o, openai/gpt-4o-mini,
                                   anthropic/claude-3-opus, ollama/qwen2
  --llm-api-key TEXT       LLM API key (defaults to OPENAI_API_KEY env var)
  --max-depth INT          Maximum crawling depth (default: 3)
  --max-pages INT          Maximum pages to crawl (default: 20)
  --output-dir PATH        Output directory (default: ./scraped_companies)
  --no-stealth             Disable stealth mode
  --no-headless            Run browser in visible mode
  --quiet                  Disable verbose output
  --save-markdown          Save markdown content for LLM processing
```

### Programmatic Configuration

```python
scraper = CompanyWebsiteScraper(
    # LLM Configuration
    llm_provider="openai/gpt-4o",          # or "anthropic/claude-3-opus"
    llm_api_key="your-api-key",            # or use env variable

    # Crawling Configuration
    max_depth=3,                           # How deep to crawl
    max_pages=20,                          # Maximum pages to visit

    # Browser Configuration
    use_stealth=True,                      # Enable anti-detection
    headless=True,                         # Headless browser

    # Output Configuration
    output_dir="./scraped_companies",      # Where to save results
    verbose=True                            # Show progress
)
```

### LLM Provider Options

#### OpenAI (Default)
```python
scraper = CompanyWebsiteScraper(
    llm_provider="openai/gpt-4o",
    llm_api_key=os.getenv('OPENAI_API_KEY')
)
```

#### Anthropic Claude
```python
scraper = CompanyWebsiteScraper(
    llm_provider="anthropic/claude-3-opus",
    llm_api_key=os.getenv('ANTHROPIC_API_KEY')
)
```

#### Local LLM (Ollama)
```python
scraper = CompanyWebsiteScraper(
    llm_provider="ollama/qwen2",
    llm_api_key="no-token"  # Not needed for local
)
```

## Output Format

### JSON Output

The scraper saves comprehensive data in JSON format:

```json
{
  "company_info": {
    "company_name": "Acme Corporation",
    "tagline": "Building the future",
    "description": "Acme is a leading manufacturer of...",
    "products_services": [
      {
        "name": "Widget Pro",
        "description": "Advanced widget solution...",
        "category": "Hardware",
        "target_market": "Enterprise",
        "key_features": ["Feature 1", "Feature 2"]
      }
    ],
    "target_industries": [
      {
        "name": "Manufacturing",
        "description": "Solutions for manufacturers"
      }
    ],
    "production_methods": [
      "CNC Machining",
      "3D Printing"
    ],
    "technologies_used": [
      "AI/ML",
      "Cloud Computing"
    ],
    "headquarters": "San Francisco, CA",
    "year_founded": "2020",
    "company_size": "50-200 employees",
    "url": "https://example.com",
    "pages_analyzed": [
      "https://example.com",
      "https://example.com/products",
      "https://example.com/about"
    ]
  },
  "markdown_content": {
    "https://example.com": "# Homepage content...",
    "https://example.com/products": "# Products..."
  },
  "timestamp": "2025-01-15T10:30:00",
  "success": true
}
```

### Markdown Output

When using `--save-markdown`, creates a consolidated markdown file with all page content:

```markdown
# Acme Corporation

**URL:** https://example.com
**Scraped:** 2025-01-15T10:30:00

---

## Page: https://example.com

[Homepage content in markdown...]

---

## Page: https://example.com/products

[Products page content...]
```

## Examples

See `company_scraper_example.py` for detailed examples:

### Example 1: Basic Scraping
```python
scraper = CompanyWebsiteScraper(verbose=True)
result = await scraper.scrape_company("https://example.com")
scraper.save_results(result)
```

### Example 2: Multiple Companies
```python
companies = ["https://co1.com", "https://co2.com"]
for url in companies:
    result = await scraper.scrape_company(url)
    scraper.save_results(result)
```

### Example 3: Custom Configuration
```python
scraper = CompanyWebsiteScraper(
    max_depth=4,
    max_pages=30,
    llm_provider="openai/gpt-4o-mini"
)
```

### Example 4: Programmatic Data Access
```python
result = await scraper.scrape_company(url)
company = result.company_info

# Filter software products
software = [p for p in company.products_services
            if 'software' in p.get('category', '').lower()]

# Export to CSV
import csv
with open('products.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=company.products_services[0].keys())
    writer.writeheader()
    writer.writerows(company.products_services)
```

### Example 5: Sites with Cookies
```python
# Maintains session/cookies across pages
result = await scraper.scrape_company(
    url="https://protected-site.com",
    session_id="persistent_session"
)
```

## How It Works

### 1. Deep Crawling Strategy
The scraper uses a **Best-First Crawling** approach that:
- Starts from the homepage
- Scores and prioritizes URLs based on relevance keywords
- Focuses on pages like `/products`, `/about`, `/services`, `/industries`
- Avoids irrelevant pages like `/blog`, `/careers`, `/news`

### 2. Anti-Scraping Measures
- **Stealth Mode**: Uses playwright-stealth to avoid bot detection
- **Random User Agents**: Rotates user agents to appear as different browsers
- **Human Simulation**: Scrolls pages, adds delays, simulates mouse movements
- **Cookie Handling**: Automatically manages cookies and session state
- **Session Persistence**: Maintains state across multiple page visits

### 3. LLM Extraction
- Sends cleaned markdown content to LLM
- Uses structured Pydantic schema for consistent extraction
- Intelligently identifies products, services, markets, and technologies
- Merges data from multiple pages for comprehensive results

### 4. Data Merging
- Combines information from multiple pages
- Deduplicates products and industries
- Uses longest/most detailed descriptions
- Tracks which pages contributed to the final result

## Use Cases

### 1. Market Research
Quickly gather competitive intelligence on companies in your industry:
```python
competitors = ["https://competitor1.com", "https://competitor2.com"]
for url in competitors:
    result = await scraper.scrape_company(url)
    # Analyze products, target markets, technologies
```

### 2. Lead Qualification
Understand potential B2B customers:
```python
result = await scraper.scrape_company(lead_url)
if "manufacturing" in result.company_info.target_industries:
    # This lead is in our target market
    send_to_sales_team(result.company_info)
```

### 3. Partnership Discovery
Find companies with complementary products:
```python
result = await scraper.scrape_company(potential_partner_url)
technologies = result.company_info.technologies_used
if "API" in technologies and "SaaS" in technologies:
    # Good integration partner candidate
```

### 4. Data Enrichment
Enhance existing company databases:
```python
for company in database.get_companies_needing_enrichment():
    result = await scraper.scrape_company(company.url)
    database.update(company.id, result.company_info)
```

## Limitations and Considerations

### Rate Limiting
- Be respectful of target websites
- Add delays between requests when scraping multiple companies
- Consider the website's `robots.txt` file

### LLM Costs
- GPT-4 API calls can be expensive for large-scale scraping
- Consider using `gpt-4o-mini` for cost savings
- Or use local LLMs (Ollama) for free processing

### Accuracy
- LLM extraction is not 100% accurate
- Always verify critical information
- Some websites may not have structured information

### Legal and Ethical
- Respect website terms of service
- Only scrape publicly available information
- Don't overload servers with too many requests
- Consider reaching out to companies for official data

## Troubleshooting

### "No data extracted"
- Website might have heavy JavaScript - try increasing `delay_before_return_html`
- Content might be behind authentication - see session management examples
- Increase `max_depth` and `max_pages` to explore more thoroughly

### "LLM API Error"
- Check API key is set: `echo $OPENAI_API_KEY`
- Verify you have API credits
- Try a different LLM provider

### "Timeout errors"
- Increase `page_timeout` in configuration
- Some sites are slow - try `--no-headless` to see what's happening
- Website might be blocking bots - ensure `use_stealth=True`

### "Empty results"
- Check if relevant pages exist (Products, Services, About)
- Try adjusting `relevant_keywords` in the scraper class
- Some sites have information in images/PDFs (not captured)

## Advanced Features

### Custom Keyword Filtering
Modify the `relevant_keywords` list to focus on specific page types:
```python
scraper.relevant_keywords = [
    "products", "solutions", "technology", "platform"
]
```

### Custom URL Patterns
Adjust which URLs to prioritize:
```python
scraper.url_patterns = [
    "*products*", "*solutions*", "*platform*"
]
```

### Custom Extraction Instructions
Modify the LLM extraction prompt in `_create_extraction_strategy()` method.

## Future Enhancements

Planned features (see task description):
- [ ] LLM-based summarization of scraped content
- [ ] Comparison mode for multiple companies
- [ ] Export to different formats (CSV, Excel, PDF reports)
- [ ] Database integration
- [ ] Web UI for easy access
- [ ] Scheduled scraping for monitoring changes
- [ ] Image analysis for product catalogs
- [ ] Contact information extraction

## Support

For issues or questions:
1. Check the examples in `company_scraper_example.py`
2. Review Crawl4AI documentation: https://crawl4ai.com
3. Open an issue in the repository

## License

This script is part of the Crawl4AI project and follows the same license.
