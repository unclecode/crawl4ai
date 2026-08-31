# 🚀 Crawl4AI v0.7.3: The Multi-Config Intelligence Update

*August 6, 2025 • 5 min read*

---

Today I'm releasing Crawl4AI v0.7.3—the Multi-Config Intelligence Update. This release brings smarter URL-specific configurations, flexible Docker deployments, important bug fixes, and documentation improvements that make Crawl4AI more robust and production-ready.

## 🎯 What's New at a Glance

- **Multi-URL Configurations**: Different crawling strategies for different URL patterns in a single batch
- **Flexible Docker LLM Providers**: Configure LLM providers via environment variables
- **Bug Fixes**: Resolved several critical issues for better stability
- **Documentation Updates**: Clearer examples and improved API documentation

## 🎨 Multi-URL Configurations: One Size Doesn't Fit All

**The Problem:** You're crawling a mix of documentation sites, blogs, and API endpoints. Each needs different handling—caching for docs, fresh content for news, structured extraction for APIs. Previously, you'd run separate crawls or write complex conditional logic.

**My Solution:** I implemented URL-specific configurations that let you define different strategies for different URL patterns in a single crawl batch. First match wins, with optional fallback support.

### Technical Implementation

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, MatchMode

# Define specialized configs for different content types
configs = [
    # Documentation sites - aggressive caching, include links
    CrawlerRunConfig(
        url_matcher=["*docs*", "*documentation*"],
        cache_mode="write",
        markdown_generator_options={"include_links": True}
    ),
    
    # News/blog sites - fresh content, scroll for lazy loading
    CrawlerRunConfig(
        url_matcher=lambda url: 'blog' in url or 'news' in url,
        cache_mode="bypass",
        js_code="window.scrollTo(0, document.body.scrollHeight/2);"
    ),
    
    # API endpoints - structured extraction
    CrawlerRunConfig(
        url_matcher=["*.json", "*api*"],
        extraction_strategy=LLMExtractionStrategy(
            provider="openai/gpt-4o-mini",
            extraction_type="structured"
        )
    ),
    
    # Default fallback for everything else
    CrawlerRunConfig()  # No url_matcher = matches everything
]

# Crawl multiple URLs with appropriate configs
async with AsyncWebCrawler() as crawler:
    results = await crawler.arun_many(
        urls=[
            "https://docs.python.org/3/",      # → Uses documentation config
            "https://blog.python.org/",        # → Uses blog config  
            "https://api.github.com/users",    # → Uses API config
            "https://example.com/"             # → Uses default config
        ],
        config=configs
    )
```

**Matching Capabilities:**
- **String Patterns**: Wildcards like `"*.pdf"`, `"*/blog/*"`
- **Function Matchers**: Lambda functions for complex logic
- **Mixed Matchers**: Combine strings and functions with AND/OR logic
- **Fallback Support**: Default config when nothing matches

**Expected Real-World Impact:**
- **Mixed Content Sites**: Handle blogs, docs, and downloads in one crawl
- **Multi-Domain Crawling**: Different strategies per domain without separate runs
- **Reduced Complexity**: No more if/else forests in your extraction code
- **Better Performance**: Each URL gets exactly the processing it needs

## 🐳 Docker: Flexible LLM Provider Configuration

**The Problem:** Hardcoded LLM providers in Docker deployments. Want to switch from OpenAI to Groq? Rebuild and redeploy. Testing different models? Multiple Docker images.

**My Solution:** Configure LLM providers via environment variables. Switch providers without touching code or rebuilding images.

### Deployment Flexibility

```bash
# Option 1: Direct environment variables
docker run -d \
  -e LLM_PROVIDER="groq/llama-3.2-3b-preview" \
  -e GROQ_API_KEY="your-key" \
  -p 11235:11235 \
  unclecode/crawl4ai:latest

# Option 2: Using .llm.env file (recommended for production)
# Create .llm.env file:
# LLM_PROVIDER=openai/gpt-4o-mini
# OPENAI_API_KEY=your-openai-key
# GROQ_API_KEY=your-groq-key

docker run -d \
  --env-file .llm.env \
  -p 11235:11235 \
  unclecode/crawl4ai:latest
```

Override per request when needed:
```python
# Use default provider from .llm.env
response = requests.post("http://localhost:11235/crawl", json={
    "url": "https://example.com",
    "extraction_strategy": {"type": "llm"}
})

# Override to use different provider for this specific request
response = requests.post("http://localhost:11235/crawl", json={
    "url": "https://complex-page.com",
    "extraction_strategy": {
        "type": "llm",
        "provider": "openai/gpt-4"  # Override default
    }
})
```

**Expected Real-World Impact:**
- **Cost Optimization**: Use cheaper models for simple tasks, premium for complex
- **A/B Testing**: Compare provider performance without deployment changes
- **Fallback Strategies**: Switch providers on-the-fly during outages
- **Development Flexibility**: Test locally with one provider, deploy with another
- **Secure Configuration**: Keep API keys in `.llm.env` file, not in commands

## 🔧 Bug Fixes & Improvements

This release includes several important bug fixes that improve stability and reliability:

- **URL Matcher Fallback**: Fixed edge cases in URL pattern matching logic
- **Memory Management**: Resolved memory leaks in long-running crawl sessions
- **Sitemap Processing**: Fixed redirect handling in sitemap fetching
- **Table Extraction**: Improved table detection and extraction accuracy
- **Error Handling**: Better error messages and recovery from network failures

## 📚 Documentation Enhancements

Based on community feedback, we've updated:
- Clearer examples for multi-URL configuration
- Improved CrawlResult documentation with all available fields
- Fixed typos and inconsistencies across documentation
- Added real-world URLs in examples for better understanding
- New comprehensive demo showcasing all v0.7.3 features

## 🙏 Acknowledgments

Thanks to our contributors and the entire community for feedback and bug reports.

## 📚 Resources

- [Full Documentation](https://docs.crawl4ai.com)
- [GitHub Repository](https://github.com/unclecode/crawl4ai)
- [Discord Community](https://discord.gg/crawl4ai)
- [Feature Demo](https://github.com/unclecode/crawl4ai/blob/main/docs/releases_review/demo_v0.7.3.py)

---

*Crawl4AI continues to evolve with your needs. This release makes it smarter, more flexible, and more stable. Try the new multi-config feature and flexible Docker deployment—they're game changers!*

**Happy Crawling! 🕷️**

*- The Crawl4AI Team*