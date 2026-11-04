# Crawl4AI CrewAI Integration Examples

This directory contains practical examples of using Crawl4AI with CrewAI to build autonomous agents that can crawl and analyze websites.

## Prerequisites

Install both Crawl4AI and CrewAI:

```bash
pip install crawl4ai crewai
```

You'll also need an OpenAI API key set as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Examples

### 1. Basic Web Crawling (`crewai_example_1_basic.py`)

The simplest example showing how to create an agent that crawls a website and summarizes the content.

**What it does:**
- Creates a single research assistant agent
- Crawls a website (example.com)
- Summarizes the main content

**Run it:**
```bash
python crewai_example_1_basic.py
```

**Key concepts:**
- Creating a basic agent with web crawling tools
- Simple task execution
- Getting structured output

---

### 2. Multi-Agent Workflow (`crewai_example_2_multi_agent.py`)

Demonstrates how multiple agents can collaborate on complex research tasks.

**What it does:**
- Agent 1 (Researcher): Crawls multiple sources for AI development information
- Agent 2 (Analyst): Analyzes findings and identifies trends
- Tasks share context and build on each other

**Run it:**
```bash
python crewai_example_2_multi_agent.py
```

**Key concepts:**
- Multiple agent collaboration
- Task dependencies and context passing
- Specialization of agent roles

---

### 3. Competitive Analysis (`crewai_example_3_competitive_analysis.py`)

Shows how to gather competitive intelligence from multiple sources.

**What it does:**
- Crawls competitor websites
- Gathers information on products, pricing, positioning
- Analyzes competitive landscape
- Recommends strategic positioning

**Run it:**
```bash
python crewai_example_3_competitive_analysis.py
```

**Key concepts:**
- Multiple parallel crawls
- Competitive intelligence gathering
- Strategic analysis and recommendations
- Business use case application

---

### 4. Data Extraction (`crewai_example_4_data_extraction.py`)

Demonstrates structured data extraction from websites.

**What it does:**
- Extracts news articles with structured fields
- Collects data from multiple sources
- Categorizes and aggregates information
- Includes two sub-examples

**Run it:**
```bash
python crewai_example_4_data_extraction.py
```

**Key concepts:**
- Structured data extraction
- Multi-source data collection
- Data aggregation and categorization

---

## How to Build Your Own Example

### Step 1: Create agents with appropriate roles

```python
from crewai import Agent
from crawl4ai import create_crawl4ai_tools

tools = create_crawl4ai_tools()

my_agent = Agent(
    role="Your Agent's Role",
    goal="What the agent should accomplish",
    tools=tools,
    llm="gpt-4"
)
```

### Step 2: Define tasks for the agents

```python
from crewai import Task

my_task = Task(
    description="Detailed instructions for what to do",
    agent=my_agent,
    expected_output="What the output should look like"
)
```

### Step 3: Create and run a crew

```python
from crewai import Crew

crew = Crew(
    agents=[my_agent],
    tasks=[my_task],
    verbose=True
)

result = crew.kickoff()
```

## Available Tools

All examples use the tools from `crawl4ai.create_crawl4ai_tools()`:

1. **crawl_website** - Crawl a single website
2. **extract_data_from_url** - Extract structured data from a URL
3. **crawl_multiple_urls** - Crawl multiple URLs in parallel
4. **search_and_crawl** - Search and crawl results (placeholder)

See the main documentation at `docs/crewai_integration.md` for detailed tool descriptions.

## Tips for Success

### 1. Be Specific in Task Descriptions

Good: "Extract the product name, price, and availability status from each product listing"

Bad: "Get product information"

### 2. Use Appropriate Agent Goals

The agent's goal guides its decision-making. Make it clear and achievable.

### 3. Leverage Task Context

```python
task2 = Task(
    description="Based on the gathered information, analyze trends",
    agent=analyst,
    context=[task1]  # Uses output from task1
)
```

### 4. Set Expected Output Format

```python
task = Task(
    description="Extract data",
    expected_output="JSON object with fields: name, price, description"
)
```

### 5. Handle Large Numbers of URLs

For many URLs, use `crawl_multiple_urls` for parallel processing:

```python
# Instead of crawling one at a time, pass a list
result = crawl_multiple_urls(
    urls=["url1", "url2", "url3", ...],
    js_enabled=True
)
```

## Troubleshooting

### Agent takes too long

- Reduce the `timeout` parameter
- Set `js_enabled=False` if JavaScript isn't needed
- Use simpler task descriptions

### No results or empty responses

- Check that the websites are accessible
- Enable JavaScript if the site is dynamic: mention in task description
- Check for any permission or robot.txt restrictions

### Error: CrewAI not found

Install CrewAI:
```bash
pip install crewai
```

### Error: OpenAI API key not set

Set your API key:
```bash
export OPENAI_API_KEY="your-key-here"
```

## Next Steps

1. Read the full documentation: `docs/crewai_integration.md`
2. Modify these examples for your use case
3. Combine multiple examples to create complex workflows
4. Experiment with different agents, tools, and task configurations

## Additional Resources

- [Crawl4AI Documentation](https://docs.crawl4ai.com)
- [CrewAI Documentation](https://docs.crewai.com)
- [OpenAI API Documentation](https://platform.openai.com/docs)
