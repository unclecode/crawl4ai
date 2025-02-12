import click
import os
from typing import Dict, Any, Optional
import json
import yaml
import anyio
from crawl4ai import (
    CacheMode,
    AsyncWebCrawler, 
    CrawlResult,
    BrowserConfig, 
    CrawlerRunConfig,
    LLMExtractionStrategy, 
    JsonCssExtractionStrategy,
    JsonXPathExtractionStrategy,
    BM25ContentFilter, 
    PruningContentFilter
)
from litellm import completion
from pathlib import Path

def get_global_config() -> dict:
    config_dir = Path.home() / ".crawl4ai"
    config_file = config_dir / "global.yml"
    
    if not config_file.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        return {}
        
    with open(config_file) as f:
        return yaml.safe_load(f) or {}

def save_global_config(config: dict):
    config_file = Path.home() / ".crawl4ai" / "global.yml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)

def setup_llm_config() -> tuple[str, str]:
    config = get_global_config()
    provider = config.get("DEFAULT_LLM_PROVIDER")
    token = config.get("DEFAULT_LLM_PROVIDER_TOKEN")
    
    if not provider:
        click.echo("\nNo default LLM provider configured.")
        click.echo("Provider format: 'company/model' (e.g., 'openai/gpt-4o', 'anthropic/claude-3-sonnet')")
        click.echo("See available providers at: https://docs.litellm.ai/docs/providers")
        provider = click.prompt("Enter provider")
        
    if not provider.startswith("ollama/"):
        if not token:
            token = click.prompt("Enter API token for " + provider, hide_input=True)
    else:
        token = "no-token"
    
    if not config.get("DEFAULT_LLM_PROVIDER") or not config.get("DEFAULT_LLM_PROVIDER_TOKEN"):
        config["DEFAULT_LLM_PROVIDER"] = provider
        config["DEFAULT_LLM_PROVIDER_TOKEN"] = token
        save_global_config(config)
        click.echo("\nConfiguration saved to ~/.crawl4ai/global.yml")
    
    return provider, token

async def stream_llm_response(url: str, markdown: str, query: str, provider: str, token: str):
    response = completion(
        model=provider,
        api_key=token,
        messages=[
            {
                "content": f"You are Crawl4ai assistant, answering user question based on the provided context which is crawled from {url}.",
                "role": "system"
            },
            {
                "content": f"<|start of context|>\n{markdown}\n<|end of context|>\n\n{query}",
                "role": "user"
            },
        ],
        stream=True,
    )
    
    for chunk in response:
        if content := chunk["choices"][0]["delta"].get("content"):
            print(content, end="", flush=True)
    print()  # New line at end



def parse_key_values(ctx, param, value) -> Dict[str, Any]:
    if not value:
        return {}
    result = {}
    pairs = value.split(',')
    for pair in pairs:
        try:
            k, v = pair.split('=', 1)
            # Handle common value types 
            if v.lower() == 'true': v = True
            elif v.lower() == 'false': v = False
            elif v.isdigit(): v = int(v)
            elif v.replace('.','',1).isdigit(): v = float(v)
            elif v.startswith('[') and v.endswith(']'):
                v = [x.strip() for x in v[1:-1].split(',') if x.strip()]
            elif v.startswith('{') and v.endswith('}'):
                try:
                    v = json.loads(v)
                except json.JSONDecodeError:
                    raise click.BadParameter(f'Invalid JSON object: {v}')
            result[k.strip()] = v
        except ValueError:
            raise click.BadParameter(f'Invalid key=value pair: {pair}')
    return result

def load_config_file(path: Optional[str]) -> dict:
    if not path:
        return {}
    
    try:
        with open(path) as f:
            if path.endswith((".yaml", ".yml")):
                return yaml.safe_load(f)
            return json.load(f)
    except Exception as e:
        raise click.BadParameter(f'Error loading config file {path}: {str(e)}')

def load_schema_file(path: Optional[str]) -> dict:
    if not path:
        return None
    return load_config_file(path)

async def run_crawler(url: str, browser_cfg: BrowserConfig, crawler_cfg: CrawlerRunConfig, verbose: bool):
    if verbose:
        click.echo("Starting crawler with configurations:")
        click.echo(f"Browser config: {browser_cfg.dump()}")
        click.echo(f"Crawler config: {crawler_cfg.dump()}")

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        try:
            result = await crawler.arun(url=url, config=crawler_cfg)
            return result
        except Exception as e:
            raise click.ClickException(f"Crawling failed: {str(e)}")

def show_examples():
    examples = """
🚀 Crawl4AI CLI Examples

1️⃣  Basic Usage:
    # Simple crawl with default settings
    crwl https://example.com

    # Get markdown output
    crwl https://example.com -o markdown

    # Verbose JSON output with cache bypass
    crwl https://example.com -o json -v --bypass-cache

2️⃣  Using Config Files:
    # Using browser and crawler configs
    crwl https://example.com -B browser.yml -C crawler.yml

    # CSS-based extraction
    crwl https://example.com -e extract_css.yml -s css_schema.json -o json

    # LLM-based extraction
    crwl https://example.com -e extract_llm.yml -s llm_schema.json -o json

3️⃣  Direct Parameters:
    # Browser settings
    crwl https://example.com -b "headless=true,viewport_width=1280,user_agent_mode=random"

    # Crawler settings
    crwl https://example.com -c "css_selector=#main,delay_before_return_html=2,scan_full_page=true"

4️⃣  Sample Config Files:

browser.yml:
    headless: true
    viewport_width: 1280
    user_agent_mode: "random"
    verbose: true
    ignore_https_errors: true

extract_css.yml:
    type: "json-css"
    params:
        verbose: true

css_schema.json:
    {
      "name": "ArticleExtractor",
      "baseSelector": ".article",
      "fields": [
        {
          "name": "title",
          "selector": "h1.title",
          "type": "text"
        },
        {
          "name": "link",
          "selector": "a.read-more",
          "type": "attribute",
          "attribute": "href"
        }
      ]
    }

extract_llm.yml:
    type: "llm"
    provider: "openai/gpt-4"
    instruction: "Extract all articles with their titles and links"
    api_token: "your-token"
    params:
        temperature: 0.3
        max_tokens: 1000

llm_schema.json:
    {
      "title": "Article",
      "type": "object",
      "properties": {
        "title": {
          "type": "string",
          "description": "The title of the article"
        },
        "link": {
          "type": "string",
          "description": "URL to the full article"
        }
      }
    }

5️⃣  Advanced Usage:
    # Combine configs with direct parameters
    crwl https://example.com -B browser.yml -b "headless=false,viewport_width=1920"

    # Full extraction pipeline
    crwl https://example.com \\
        -B browser.yml \\
        -C crawler.yml \\
        -e extract_llm.yml \\
        -s llm_schema.json \\
        -o json \\
        -v

    # Content filtering with BM25
    crwl https://example.com \\
        -f filter_bm25.yml \\
        -o markdown-fit

For more documentation visit: https://github.com/unclecode/crawl4ai

6️⃣  Q&A with LLM:
    # Ask a question about the content
    crwl https://example.com -q "What is the main topic discussed?"

    # First view content, then ask questions
    crwl https://example.com -o markdown  # See the crawled content first
    crwl https://example.com -q "Summarize the key points"
    crwl https://example.com -q "What are the conclusions?"

    # Advanced crawling with Q&A
    crwl https://example.com \\
        -B browser.yml \\
        -c "css_selector=article,scan_full_page=true" \\
        -q "What are the pros and cons mentioned?"

    Note: First time using -q will prompt for LLM provider and API token.
    These will be saved in ~/.crawl4ai/global.yml for future use.
    
    Supported provider format: 'company/model'
    Examples:
      - ollama/llama3.3
      - openai/gpt-4
      - anthropic/claude-3-sonnet
      - cohere/command
      - google/gemini-pro
    
    See full list of providers: https://docs.litellm.ai/docs/providers
"""
    click.echo(examples)

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("url", required=False)
@click.option("--example", is_flag=True, help="Show usage examples")
@click.option("--browser-config", "-B", type=click.Path(exists=True), help="Browser config file (YAML/JSON)")
@click.option("--crawler-config", "-C", type=click.Path(exists=True), help="Crawler config file (YAML/JSON)")
@click.option("--filter-config", "-f", type=click.Path(exists=True), help="Content filter config file")
@click.option("--extraction-config", "-e", type=click.Path(exists=True), help="Extraction strategy config file")
@click.option("--schema", "-s", type=click.Path(exists=True), help="JSON schema for extraction")
@click.option("--browser", "-b", type=str, callback=parse_key_values, help="Browser parameters as key1=value1,key2=value2")
@click.option("--crawler", "-c", type=str, callback=parse_key_values, help="Crawler parameters as key1=value1,key2=value2")
@click.option("--output", "-o", type=click.Choice(["all", "json", "markdown", "markdown-v2", "md", "md-fit"]), default="all")
@click.option("--bypass-cache", is_flag=True, default = True,  help="Bypass cache when crawling")
@click.option("--question", "-q", help="Ask a question about the crawled content")
@click.option("--verbose", "-v", is_flag=True)
def cli(url: str, example: bool, browser_config: str, crawler_config: str, filter_config: str, 
        extraction_config: str, schema: str, browser: Dict, crawler: Dict,
        output: str, bypass_cache: bool, question: str, verbose: bool):
    """Crawl4AI CLI - Web content extraction tool

    Simple Usage:
        crwl https://example.com
    
    Run with --example to see detailed usage examples."""

    if example:
        show_examples()
        return
        
    if not url:
        raise click.UsageError("URL argument is required unless using --example")
    
    try:
        # Load base configurations
        browser_cfg = BrowserConfig.load(load_config_file(browser_config))
        crawler_cfg = CrawlerRunConfig.load(load_config_file(crawler_config))
        
        # Override with CLI params
        if browser:
            browser_cfg = browser_cfg.clone(**browser)
        if crawler:
            crawler_cfg = crawler_cfg.clone(**crawler)
            
        # Handle content filter config
        if filter_config:
            filter_conf = load_config_file(filter_config)
            if filter_conf["type"] == "bm25":
                crawler_cfg.content_filter = BM25ContentFilter(
                    user_query=filter_conf.get("query"),
                    bm25_threshold=filter_conf.get("threshold", 1.0)
                )
            elif filter_conf["type"] == "pruning":
                crawler_cfg.content_filter = PruningContentFilter(
                    user_query=filter_conf.get("query"),
                    threshold=filter_conf.get("threshold", 0.48)
                )
                
        # Handle extraction strategy
        if extraction_config:
            extract_conf = load_config_file(extraction_config)
            schema_data = load_schema_file(schema)
            
            # Check if type does not exist show proper message
            if not extract_conf.get("type"):
                raise click.ClickException("Extraction type not specified")
            if extract_conf["type"] not in ["llm", "json-css", "json-xpath"]:
                raise click.ClickException(f"Invalid extraction type: {extract_conf['type']}")
            
            if extract_conf["type"] == "llm":
                # if no provider show error emssage
                if not extract_conf.get("provider") or not extract_conf.get("api_token"):
                    raise click.ClickException("LLM provider and API token are required for LLM extraction")

                crawler_cfg.extraction_strategy = LLMExtractionStrategy(
                    provider=extract_conf["provider"],
                    instruction=extract_conf["instruction"],
                    api_token=extract_conf.get("api_token", extract_conf.get("api_key")),
                    schema=schema_data,
                    **extract_conf.get("params", {})
                )
            elif extract_conf["type"] == "json-css":
                crawler_cfg.extraction_strategy = JsonCssExtractionStrategy(
                    schema=schema_data
                )
            elif extract_conf["type"] == "json-xpath":
                crawler_cfg.extraction_strategy = JsonXPathExtractionStrategy(
                    schema=schema_data
                )
                

        # No cache
        if bypass_cache:
            crawler_cfg.cache_mode = CacheMode.BYPASS
        
        # Run crawler
        result : CrawlResult = anyio.run(
            run_crawler,
            url,
            browser_cfg,
            crawler_cfg,
            verbose
        )

        # Handle question
        if question:
            provider, token = setup_llm_config()
            markdown = result.markdown_v2.raw_markdown
            anyio.run(stream_llm_response, url, markdown, question, provider, token)
            return
        
        # Handle output
        if output == "all":
            click.echo(json.dumps(result.model_dump(), indent=2))
        elif output == "json":
            click.echo(json.dumps(json.loads(result.extracted_content), indent=2))
        elif output in ["markdown", "md"]:
            click.echo(result.markdown_v2.raw_markdown)
        elif output in ["markdown-fit", "md-fit"]:
            click.echo(result.markdown_v2.fit_markdown)
            
    except Exception as e:
        raise click.ClickException(str(e))

if __name__ == "__main__":
    cli()