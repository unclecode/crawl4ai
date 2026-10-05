# Crawl4AI CrewAI Integration

This guide explains how to use Crawl4AI with CrewAI to enable AI agents to crawl and extract data from websites.

## Installation

First, install both Crawl4AI and CrewAI:

```bash
pip install crawl4ai crewai
```

## Quick Start

### Basic Web Crawling

```python
from crewai import Agent, Task, Crew
from crawl4ai import create_crawl4ai_tools

# Create tools
tools = create_crawl4ai_tools()

# Create an agent that can crawl websites
research_agent = Agent(
    role="Research Assistant",
    goal="Find and analyze information from websites",
    tools=tools,
    llm="gpt-4"
)

# Create a task
task = Task(
    description="Find information about Python on the official Python website",
    agent=research_agent,
    expected_output="Summary of Python features and latest news"
)

# Create and run a crew
crew = Crew(
    agents=[research_agent],
    tasks=[task],
    verbose=True
)

result = crew.kickoff()
print(result)
```

## Available Tools

The CrewAI integration provides four main tools:

### 1. `crawl_website`

Crawl a single website and extract its content.

**Parameters:**
- `url` (string): The URL to crawl
- `cache_mode` (string): Cache mode - "BYPASS", "CACHED", or "CACHE_FIRST" (default: "BYPASS")
- `include_links` (boolean): Include all links found on the page (default: False)
- `include_images` (boolean): Include image metadata (default: False)
- `js_enabled` (boolean): Enable JavaScript rendering (default: False)
- `timeout` (integer): Request timeout in seconds (default: 30)
- `extraction_strategy` (string): Extraction strategy - "cosine", "llm", or None (default: None)

**Returns:**
- Dictionary with:
  - `success`: Whether the crawl was successful
  - `url`: The crawled URL
  - `status_code`: HTTP status code
  - `markdown`: Page content in Markdown format
  - `html`: Original HTML (if available)
  - `links`: List of links (if include_links=True)
  - `media`: Media elements (if include_images=True)
  - `error`: Error message (if failed)

**Example:**
```python
task = Task(
    description="Crawl https://example.com and summarize the main content",
    agent=research_agent,
    expected_output="Summary of the website content"
)
```

### 2. `extract_data_from_url`

Extract structured data from a website using a defined schema.

**Parameters:**
- `url` (string): The URL to crawl and extract from
- `extraction_schema` (dict): Dictionary defining the data extraction pattern
- `js_enabled` (boolean): Enable JavaScript rendering (default: False)
- `timeout` (integer): Request timeout in seconds (default: 30)

**Returns:**
- Dictionary with:
  - `success`: Whether extraction was successful
  - `url`: The crawled URL
  - `extracted_data`: Extracted structured data
  - `raw_markdown`: Raw page content
  - `error`: Error message (if failed)

**Example:**
```python
task = Task(
    description="Extract all product names and prices from https://shop.example.com",
    agent=research_agent,
    expected_output="Structured list of products with prices"
)
```

### 3. `crawl_multiple_urls`

Crawl multiple websites in parallel for efficiency.

**Parameters:**
- `urls` (list): List of URLs to crawl
- `cache_mode` (string): Cache mode - "BYPASS", "CACHED", or "CACHE_FIRST" (default: "BYPASS")
- `js_enabled` (boolean): Enable JavaScript rendering (default: False)
- `timeout` (integer): Request timeout in seconds (default: 30)

**Returns:**
- Dictionary with:
  - `results`: List of crawl results for each URL
  - `success_count`: Number of successful crawls
  - `failed_count`: Number of failed crawls

**Example:**
```python
task = Task(
    description="Compare the same product across three competitors",
    agent=research_agent,
    expected_output="Comparison table with features and prices"
)
```

### 4. `search_and_crawl`

Search for a query and crawl top results (placeholder for future search API integration).

**Note:** This tool currently requires manual URL specification. Use `crawl_website()` with specific URLs instead.

## Use Cases

### 1. Market Research

```python
researcher = Agent(
    role="Market Researcher",
    goal="Analyze competitor websites and market trends",
    tools=create_crawl4ai_tools(),
    llm="gpt-4"
)

task = Task(
    description="Analyze pricing strategies on competitor websites",
    agent=researcher,
    expected_output="Competitive analysis report with pricing recommendations"
)
```

### 2. Content Analysis

```python
analyst = Agent(
    role="Content Analyst",
    goal="Summarize and analyze web content",
    tools=create_crawl4ai_tools(),
    llm="gpt-4"
)

task = Task(
    description="Read recent news from techcrunch.com and summarize top 5 stories",
    agent=analyst,
    expected_output="Summary of latest technology news"
)
```

### 3. Data Collection

```python
collector = Agent(
    role="Data Collector",
    goal="Gather structured data from websites",
    tools=create_crawl4ai_tools(),
    llm="gpt-4"
)

task = Task(
    description="Extract all product information from an e-commerce site",
    agent=collector,
    expected_output="Structured dataset of all products"
)
```

### 4. Research Assistant

```python
from crewai import Agent, Task, Crew
from crawl4ai import create_crawl4ai_tools

research_agent = Agent(
    role="Research Assistant",
    goal="Find accurate information from authoritative sources",
    tools=create_crawl4ai_tools(),
    llm="gpt-4",
    verbose=True
)

analysis_agent = Agent(
    role="Data Analyst",
    goal="Synthesize research findings into actionable insights",
    tools=[],
    llm="gpt-4",
    verbose=True
)

# First task: gather information
gather_task = Task(
    description="Research the latest developments in AI/ML from official sources",
    agent=research_agent,
    expected_output="Comprehensive summary of AI/ML developments"
)

# Second task: analyze findings
analyze_task = Task(
    description="Analyze the gathered information and provide strategic insights",
    agent=analysis_agent,
    expected_output="Strategic analysis of AI/ML market trends",
    context=[gather_task]  # Use output from first task
)

crew = Crew(
    agents=[research_agent, analysis_agent],
    tasks=[gather_task, analyze_task],
    verbose=True
)

result = crew.kickoff()
```

## Configuration

You can customize the crawler behavior by passing configuration:

```python
from crawl4ai import BrowserConfig, CrawlerRunConfig

# Advanced configuration example
browser_config = BrowserConfig(
    headless=True,
    use_managed_browser=False,
)

crawler_config = CrawlerRunConfig(
    timeout=60,
    js_enabled=True,
)
```

## Best Practices

### 1. Use Appropriate Cache Modes

- **BYPASS**: Always fetch fresh content (useful for real-time data)
- **CACHED**: Use cache if available (faster, may be stale)
- **CACHE_FIRST**: Prefer cache, fall back to live (useful for reliability)

### 2. Enable JavaScript When Needed

```python
task = Task(
    description="Extract data from a JavaScript-heavy website",
    agent=research_agent,
    expected_output="Extracted data"
)
# Tell the agent to use js_enabled=True for this task
```

### 3. Use Multiple Agents for Complex Tasks

```python
# Crawler agent
crawler = Agent(
    role="Web Crawler",
    goal="Collect data from websites",
    tools=create_crawl4ai_tools(),
    llm="gpt-4"
)

# Analyst agent
analyst = Agent(
    role="Data Analyst",
    goal="Analyze collected data",
    tools=[],  # No tools needed, uses output from crawler
    llm="gpt-4"
)

crew = Crew(
    agents=[crawler, analyst],
    tasks=[
        Task(description="Crawl website", agent=crawler),
        Task(description="Analyze data", agent=analyst)
    ]
)
```

### 4. Handle Errors Gracefully

The tools return error information in the response. Make sure your agent is aware of potential failures:

```python
task = Task(
    description="""
    Crawl the website and extract data. 
    If the crawl fails, report the error clearly.
    Retry with simpler parameters if needed.
    """,
    agent=research_agent,
    expected_output="Successfully extracted data or clear error report"
)
```

## Performance Tips

1. **Use parallel crawling** with `crawl_multiple_urls()` for multiple websites
2. **Cache results** with `CACHE_FIRST` mode when appropriate
3. **Disable JavaScript** (`js_enabled=False`) when not needed for faster crawling
4. **Set reasonable timeouts** to prevent hanging on slow websites
5. **Reuse the crawler instance** - the integration uses a global crawler instance for efficiency

## Cleanup

When you're done with web crawling tasks, clean up resources:

```python
from crawl4ai import cleanup_crawler
import asyncio

# Clean up after crew execution
asyncio.run(cleanup_crawler())
```

## Troubleshooting

### CrewAI Not Found
If you get an ImportError about CrewAI, install it:
```bash
pip install crewai
```

### Crawler Timeouts
If crawling takes too long, try:
- Reducing the `timeout` parameter
- Setting `js_enabled=False` if you don't need JavaScript
- Using specific URLs instead of complex sites

### JavaScript Not Rendering
If JavaScript-heavy sites aren't loading properly:
- Set `js_enabled=True` in your task description
- Increase the `timeout` value
- Check the website's JavaScript implementation

## Advanced Examples

### Multi-Agent Research Workflow

```python
from crewai import Agent, Task, Crew
from crawl4ai import create_crawl4ai_tools

tools = create_crawl4ai_tools()

# Agent 1: Gather information
researcher = Agent(
    role="Research Specialist",
    goal="Find comprehensive information on assigned topics",
    tools=tools,
    llm="gpt-4"
)

# Agent 2: Analyze findings
analyst = Agent(
    role="Data Analyst",
    goal="Synthesize research into actionable insights",
    tools=[],
    llm="gpt-4"
)

# Agent 3: Generate report
reporter = Agent(
    role="Technical Writer",
    goal="Create clear, well-structured reports",
    tools=[],
    llm="gpt-4"
)

# Define tasks
research_task = Task(
    description="Research the latest technologies in Web3",
    agent=researcher,
    expected_output="Detailed findings on Web3 technologies"
)

analysis_task = Task(
    description="Analyze the research and identify trends",
    agent=analyst,
    expected_output="Trend analysis and market insights",
    context=[research_task]
)

report_task = Task(
    description="Create a comprehensive report",
    agent=reporter,
    expected_output="Professional research report",
    context=[analysis_task]
)

crew = Crew(
    agents=[researcher, analyst, reporter],
    tasks=[research_task, analysis_task, report_task],
    verbose=True
)

result = crew.kickoff()
print(result)
```

## Support

For issues or feature requests related to the CrewAI integration, please visit:
- [Crawl4AI GitHub](https://github.com/unclecode/crawl4ai)
- [CrewAI GitHub](https://github.com/joaomdmoura/crewAI)
