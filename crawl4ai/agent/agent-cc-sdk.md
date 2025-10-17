```python
# c4ai_tools.py
"""Crawl4AI tools for Claude Code SDK agent."""

import json
import asyncio
from typing import Any, Dict
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from claude_agent_sdk import tool

# Global session storage
CRAWLER_SESSIONS: Dict[str, AsyncWebCrawler] = {}

@tool("quick_crawl", "One-shot crawl for simple extraction. Returns markdown, HTML, or structured data.", {
    "url": str,
    "output_format": str,  # "markdown" | "html" | "structured" | "screenshot"
    "extraction_schema": str,  # Optional: JSON schema for structured extraction
    "js_code": str,  # Optional: JavaScript to execute before extraction
    "wait_for": str,  # Optional: CSS selector to wait for
})
async def quick_crawl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Fast single-page crawl without session management."""
    
    crawler_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        js_code=args.get("js_code"),
        wait_for=args.get("wait_for"),
    )
    
    # Add extraction strategy if structured data requested
    if args.get("extraction_schema"):
        run_config.extraction_strategy = LLMExtractionStrategy(
            provider="openai/gpt-4o-mini",
            schema=json.loads(args["extraction_schema"]),
            instruction="Extract data according to the provided schema."
        )
    
    async with AsyncWebCrawler(config=crawler_config) as crawler:
        result = await crawler.arun(url=args["url"], config=run_config)
        
        if not result.success:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({"error": result.error_message, "success": False})
                }]
            }
        
        output_map = {
            "markdown": result.markdown_v2.raw_markdown if result.markdown_v2 else "",
            "html": result.html,
            "structured": result.extracted_content,
            "screenshot": result.screenshot,
        }
        
        response = {
            "success": True,
            "url": result.url,
            "data": output_map.get(args["output_format"], result.markdown_v2.raw_markdown)
        }
        
        return {"content": [{"type": "text", "text": json.dumps(response, indent=2)}]}


@tool("start_session", "Start a persistent browser session for multi-step crawling and automation.", {
    "session_id": str,
    "headless": bool,  # Default True
})
async def start_session(args: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize a persistent crawler session."""
    
    session_id = args["session_id"]
    if session_id in CRAWLER_SESSIONS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": f"Session {session_id} already exists",
            "success": False
        })}]}
    
    crawler_config = BrowserConfig(
        headless=args.get("headless", True),
        verbose=False
    )
    
    crawler = AsyncWebCrawler(config=crawler_config)
    await crawler.__aenter__()
    CRAWLER_SESSIONS[session_id] = crawler
    
    return {"content": [{"type": "text", "text": json.dumps({
        "success": True,
        "session_id": session_id,
        "message": f"Browser session {session_id} started"
    })}]}


@tool("navigate", "Navigate to a URL in an active session.", {
    "session_id": str,
    "url": str,
    "wait_for": str,  # Optional: CSS selector to wait for
    "js_code": str,  # Optional: JavaScript to execute after load
})
async def navigate(args: Dict[str, Any]) -> Dict[str, Any]:
    """Navigate to URL in session."""
    
    session_id = args["session_id"]
    if session_id not in CRAWLER_SESSIONS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        })}]}
    
    crawler = CRAWLER_SESSIONS[session_id]
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for=args.get("wait_for"),
        js_code=args.get("js_code"),
    )
    
    result = await crawler.arun(url=args["url"], config=run_config)
    
    return {"content": [{"type": "text", "text": json.dumps({
        "success": result.success,
        "url": result.url,
        "message": f"Navigated to {args['url']}"
    })}]}


@tool("extract_data", "Extract data from current page in session using schema or return markdown.", {
    "session_id": str,
    "output_format": str,  # "markdown" | "structured"
    "extraction_schema": str,  # Required for structured, JSON schema
    "wait_for": str,  # Optional: Wait for element before extraction
    "js_code": str,  # Optional: Execute JS before extraction
})
async def extract_data(args: Dict[str, Any]) -> Dict[str, Any]:
    """Extract data from current page."""
    
    session_id = args["session_id"]
    if session_id not in CRAWLER_SESSIONS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        })}]}
    
    crawler = CRAWLER_SESSIONS[session_id]
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for=args.get("wait_for"),
        js_code=args.get("js_code"),
    )
    
    if args["output_format"] == "structured" and args.get("extraction_schema"):
        run_config.extraction_strategy = LLMExtractionStrategy(
            provider="openai/gpt-4o-mini",
            schema=json.loads(args["extraction_schema"]),
            instruction="Extract data according to schema."
        )
    
    result = await crawler.arun(config=run_config)
    
    if not result.success:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": result.error_message,
            "success": False
        })}]}
    
    data = (result.extracted_content if args["output_format"] == "structured" 
            else result.markdown_v2.raw_markdown if result.markdown_v2 else "")
    
    return {"content": [{"type": "text", "text": json.dumps({
        "success": True,
        "data": data
    }, indent=2)}]}


@tool("execute_js", "Execute JavaScript in the current page context.", {
    "session_id": str,
    "js_code": str,
    "wait_for": str,  # Optional: Wait for element after execution
})
async def execute_js(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute JavaScript in session."""
    
    session_id = args["session_id"]
    if session_id not in CRAWLER_SESSIONS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        })}]}
    
    crawler = CRAWLER_SESSIONS[session_id]
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        js_code=args["js_code"],
        wait_for=args.get("wait_for"),
    )
    
    result = await crawler.arun(config=run_config)
    
    return {"content": [{"type": "text", "text": json.dumps({
        "success": result.success,
        "message": "JavaScript executed"
    })}]}


@tool("screenshot", "Take a screenshot of the current page.", {
    "session_id": str,
})
async def screenshot(args: Dict[str, Any]) -> Dict[str, Any]:
    """Capture screenshot."""
    
    session_id = args["session_id"]
    if session_id not in CRAWLER_SESSIONS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        })}]}
    
    crawler = CRAWLER_SESSIONS[session_id]
    result = await crawler.arun(config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS))
    
    return {"content": [{"type": "text", "text": json.dumps({
        "success": True,
        "screenshot": result.screenshot if result.success else None
    })}]}


@tool("close_session", "Close and cleanup a browser session.", {
    "session_id": str,
})
async def close_session(args: Dict[str, Any]) -> Dict[str, Any]:
    """Close crawler session."""
    
    session_id = args["session_id"]
    if session_id not in CRAWLER_SESSIONS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        })}]}
    
    crawler = CRAWLER_SESSIONS.pop(session_id)
    await crawler.__aexit__(None, None, None)
    
    return {"content": [{"type": "text", "text": json.dumps({
        "success": True,
        "message": f"Session {session_id} closed"
    })}]}


# Export all tools
CRAWL_TOOLS = [
    quick_crawl,
    start_session,
    navigate,
    extract_data,
    execute_js,
    screenshot,
    close_session,
]
```

```python
# c4ai_prompts.py
"""System prompts for Crawl4AI agent."""

SYSTEM_PROMPT = """You are an expert web crawling and browser automation agent powered by Crawl4AI.

# Core Capabilities

You can perform sophisticated multi-step web scraping and automation tasks through two modes:

## Quick Mode (simple tasks)
- Use `quick_crawl` for single-page data extraction
- Best for: simple scrapes, getting page content, one-time extractions

## Session Mode (complex tasks)
- Use `start_session` to create persistent browser sessions
- Navigate, interact, extract data across multiple pages
- Essential for: workflows requiring JS execution, pagination, filtering, multi-step automation

# Tool Usage Patterns

## Simple Extraction
1. Use `quick_crawl` with appropriate output_format
2. Provide extraction_schema for structured data

## Multi-Step Workflow
1. `start_session` - Create browser session with unique ID
2. `navigate` - Go to target URL
3. `execute_js` - Interact with page (click buttons, scroll, fill forms)
4. `extract_data` - Get data using schema or markdown
5. Repeat steps 2-4 as needed
6. `close_session` - Clean up when done

# Critical Instructions

1. **Iteration & Validation**: When tasks require filtering or conditional logic:
   - Extract data first, analyze results
   - Filter/validate in your reasoning
   - Make subsequent tool calls based on validation
   - Continue until task criteria are met

2. **Structured Extraction**: Always use JSON schemas for structured data:
   ```json
   {
     "type": "object",
     "properties": {
       "field_name": {"type": "string"},
       "price": {"type": "number"}
     }
   }
   ```

3. **Session Management**:
   - Generate unique session IDs (e.g., "product_scrape_001")
   - Always close sessions when done
   - Use sessions for tasks requiring multiple page visits

4. **JavaScript Execution**:
   - Use for: clicking buttons, scrolling, waiting for dynamic content
   - Example: `js_code: "document.querySelector('.load-more').click()"`
   - Combine with `wait_for` to ensure content loads

5. **Error Handling**:
   - Check `success` field in all responses
   - Retry with different strategies if extraction fails
   - Report specific errors to user

6. **Data Persistence**:
   - Save results using `Write` tool to JSON files
   - Use descriptive filenames with timestamps
   - Structure data clearly for user consumption

# Example Workflows

## Workflow 1: Filter & Crawl
Task: "Find products >$10, crawl each, extract details"

1. `quick_crawl` product listing page with schema for [name, price, url]
2. Analyze results, filter price > 10 in reasoning
3. `start_session` for detailed crawling
4. For each filtered product:
   - `navigate` to product URL
   - `extract_data` with detail schema
5. Aggregate results
6. `close_session`
7. `Write` results to JSON

## Workflow 2: Paginated Scraping
Task: "Scrape all items across multiple pages"

1. `start_session`
2. `navigate` to page 1
3. `extract_data` items from current page
4. Check for "next" button
5. `execute_js` to click next
6. Repeat 3-5 until no more pages
7. `close_session`
8. Save aggregated data

## Workflow 3: Dynamic Content
Task: "Scrape reviews after clicking 'Load More'"

1. `start_session`
2. `navigate` to product page
3. `execute_js` to click load more button
4. `wait_for` reviews container
5. `extract_data` all reviews
6. `close_session`

# Quality Guidelines

- **Be thorough**: Don't stop until task requirements are fully met
- **Validate data**: Check extracted data matches expected format
- **Handle edge cases**: Empty results, pagination limits, rate limiting
- **Clear reporting**: Summarize what was found, any issues encountered
- **Efficient**: Use quick_crawl when possible, sessions only when needed

# Output Format

When saving data, use clean JSON structure:
```json
{
  "metadata": {
    "scraped_at": "ISO timestamp",
    "source_url": "...",
    "total_items": 0
  },
  "data": [...]
}
```

Always provide a final summary of:
- Items found/processed
- Time taken
- Files created
- Any warnings/errors

Remember: You have unlimited turns to complete the task. Take your time, validate each step, and ensure quality results."""
```

```python
# agent_crawl.py
"""Crawl4AI Agent CLI - Browser automation agent powered by Claude Code SDK."""

import asyncio
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server
from claude_agent_sdk import AssistantMessage, TextBlock, ResultMessage

from c4ai_tools import CRAWL_TOOLS
from c4ai_prompts import SYSTEM_PROMPT


class SessionStorage:
    """Manage session storage in ~/.crawl4ai/agents/projects/"""
    
    def __init__(self, cwd: Optional[str] = None):
        self.cwd = Path(cwd) if cwd else Path.cwd()
        self.base_dir = Path.home() / ".crawl4ai" / "agents" / "projects"
        self.project_dir = self.base_dir / self._sanitize_path(str(self.cwd.resolve()))
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = str(uuid.uuid4())
        self.log_file = self.project_dir / f"{self.session_id}.jsonl"
    
    @staticmethod
    def _sanitize_path(path: str) -> str:
        """Convert /Users/unclecode/devs/test to -Users-unclecode-devs-test"""
        return path.replace("/", "-").replace("\\", "-")
    
    def log(self, event_type: str, data: dict):
        """Append event to JSONL log."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "session_id": self.session_id,
            "data": data
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_session_path(self) -> str:
        """Return path to current session log."""
        return str(self.log_file)


class CrawlAgent:
    """Crawl4AI agent wrapper."""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.storage = SessionStorage(args.add_dir[0] if args.add_dir else None)
        self.client: Optional[ClaudeSDKClient] = None
        
        # Create MCP server with crawl tools
        self.crawler_server = create_sdk_mcp_server(
            name="crawl4ai",
            version="1.0.0",
            tools=CRAWL_TOOLS
        )
        
        # Build options
        self.options = ClaudeAgentOptions(
            mcp_servers={"crawler": self.crawler_server},
            allowed_tools=[
                "mcp__crawler__quick_crawl",
                "mcp__crawler__start_session",
                "mcp__crawler__navigate",
                "mcp__crawler__extract_data",
                "mcp__crawler__execute_js",
                "mcp__crawler__screenshot",
                "mcp__crawler__close_session",
                "Write", "Read", "Bash"
            ],
            system_prompt=SYSTEM_PROMPT if not args.system_prompt else args.system_prompt,
            permission_mode=args.permission_mode or "acceptEdits",
            cwd=args.add_dir[0] if args.add_dir else str(Path.cwd()),
            model=args.model,
            session_id=args.session_id or self.storage.session_id,
        )
    
    async def run(self, prompt: str):
        """Execute crawl task."""
        
        self.storage.log("session_start", {
            "prompt": prompt,
            "cwd": self.options.cwd,
            "model": self.options.model
        })
        
        print(f"\n🕷️  Crawl4AI Agent")
        print(f"📁 Session: {self.storage.session_id}")
        print(f"💾 Log: {self.storage.get_session_path()}")
        print(f"🎯 Task: {prompt}\n")
        
        async with ClaudeSDKClient(options=self.options) as client:
            self.client = client
            await client.query(prompt)
            
            turn = 0
            async for message in client.receive_messages():
                turn += 1
                
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"\n💭 [{turn}] {block.text}")
                            self.storage.log("assistant_message", {"turn": turn, "text": block.text})
                
                elif isinstance(message, ResultMessage):
                    print(f"\n✅ Completed in {message.duration_ms/1000:.2f}s")
                    print(f"💰 Cost: ${message.total_cost_usd:.4f}" if message.total_cost_usd else "")
                    print(f"🔄 Turns: {message.num_turns}")
                    
                    self.storage.log("session_end", {
                        "duration_ms": message.duration_ms,
                        "cost_usd": message.total_cost_usd,
                        "turns": message.num_turns,
                        "success": not message.is_error
                    })
                    break
        
        print(f"\n📊 Session log: {self.storage.get_session_path()}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Crawl4AI Agent - Browser automation powered by Claude Code SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("prompt", nargs="?", help="Your crawling task prompt")
    parser.add_argument("--system-prompt", help="Custom system prompt")
    parser.add_argument("--permission-mode", choices=["acceptEdits", "bypassPermissions", "default", "plan"],
                       help="Permission mode for tool execution")
    parser.add_argument("--model", help="Model to use (e.g., 'sonnet', 'opus')")
    parser.add_argument("--add-dir", nargs="+", help="Additional directories for file access")
    parser.add_argument("--session-id", help="Use specific session ID (UUID)")
    parser.add_argument("-v", "--version", action="version", version="Crawl4AI Agent 1.0.0")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    if not args.prompt:
        parser.print_help()
        print("\nExample usage:")
        print('  crawl-agent "Scrape all products from example.com with price > $10"')
        print('  crawl-agent --add-dir ~/projects "Find all Python files and analyze imports"')
        sys.exit(1)
    
    try:
        agent = CrawlAgent(args)
        asyncio.run(agent.run(args.prompt))
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Usage:**

```bash
# Simple scrape
python agent_crawl.py "Get all product names from example.com"

# Complex filtering
python agent_crawl.py "Find products >$10 from shop.com, crawl each, extract id/name/price"

# Multi-step automation
python agent_crawl.py "Go to amazon.com, search 'laptop', filter 4+ stars, scrape top 10"

# With options
python agent_crawl.py --add-dir ~/projects --model sonnet "Scrape competitor prices"
```

**Session logs stored at:**
`~/.crawl4ai/agents/projects/-Users-unclecode-devs-test/{uuid}.jsonl`