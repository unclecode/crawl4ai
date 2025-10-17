# Crawl4AI Agent Technical Specification
*AI-to-AI Knowledge Transfer Document*

## Context Documents
**MUST READ FIRST:**
1. `/Users/unclecode/devs/crawl4ai/tmp/CRAWL4AI_SDK.md` - Crawl4AI complete API reference
2. `/Users/unclecode/devs/crawl4ai/tmp/cc_stream.md` - Claude SDK streaming input mode
3. `/Users/unclecode/devs/crawl4ai/tmp/CC_PYTHON_SDK.md` - Claude Code Python SDK complete reference

## Architecture Overview

**Core Principle:** Singleton browser instance + streaming chat mode + MCP tools

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Entry Point                         │
│         agent_crawl.py (CLI: --chat | single-shot)          │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   [Chat Mode]         [Single-shot]    [Browser Manager]
        │                   │                   │
        ▼                   ▼                   ▼
  ChatMode.run()    CrawlAgent.run()   BrowserManager
  - Streaming        - One prompt          (Singleton)
  - Interactive      - Exit after           │
  - Commands         - Uses same            ▼
        │              browser         AsyncWebCrawler
        │                   │             (persistent)
        └───────────────────┴────────────────┘
                            │
                    ┌───────┴────────┐
                    │                │
              MCP Tools        Claude SDK
            (Crawl4AI)        (Built-in)
                    │                │
        ┌───────────┴────┐    ┌──────┴──────┐
        │                │    │             │
   quick_crawl    session    Read        Edit
   navigate       tools      Write       Glob
   extract_data              Bash        Grep
   execute_js
   screenshot
   close_session
```

## File Structure

```
crawl4ai/agent/
├── __init__.py                 # Module exports
├── agent_crawl.py              # Main CLI entry (190 lines)
│   ├── SessionStorage          # JSONL logging to ~/.crawl4ai/agents/projects/
│   ├── CrawlAgent             # Single-shot wrapper
│   └── main()                 # CLI parser (--chat flag)
│
├── browser_manager.py          # Singleton pattern (70 lines)
│   └── BrowserManager         # Class methods only, no instances
│       ├── get_browser()      # Returns singleton AsyncWebCrawler
│       ├── reconfigure_browser()
│       ├── close_browser()
│       └── is_browser_active()
│
├── c4ai_tools.py               # 7 MCP tools (310 lines)
│   ├── @tool decorators       # Claude SDK decorator
│   ├── CRAWLER_SESSIONS       # Dict[str, AsyncWebCrawler] for named sessions
│   ├── CRAWLER_SESSION_URLS   # Dict[str, str] track current URL per session
│   └── CRAWL_TOOLS            # List of tool functions
│
├── c4ai_prompts.py             # System prompt (130 lines)
│   └── SYSTEM_PROMPT          # Agent behavior definition
│
├── terminal_ui.py              # Rich-based UI (120 lines)
│   └── TerminalUI             # Console rendering
│       ├── show_header()
│       ├── print_markdown()
│       ├── print_code()
│       └── with_spinner()
│
├── chat_mode.py                # Streaming chat (160 lines)
│   └── ChatMode
│       ├── message_generator() # AsyncGenerator per cc_stream.md
│       ├── _handle_command()   # /exit /clear /help /browser
│       └── run()              # Main chat loop
│
├── test_tools.py               # Direct tool tests (130 lines)
├── test_chat.py                # Component tests (90 lines)
└── test_scenarios.py           # Multi-turn scenarios (500 lines)
    ├── SIMPLE_SCENARIOS
    ├── MEDIUM_SCENARIOS
    ├── COMPLEX_SCENARIOS
    └── ScenarioRunner
```

## Critical Implementation Details

### 1. Browser Singleton Pattern

**Key:** ONE browser instance for ENTIRE agent session

```python
# browser_manager.py
class BrowserManager:
    _crawler: Optional[AsyncWebCrawler] = None  # Singleton
    _config: Optional[BrowserConfig] = None

    @classmethod
    async def get_browser(cls, config=None) -> AsyncWebCrawler:
        if cls._crawler is None:
            cls._crawler = AsyncWebCrawler(config or BrowserConfig())
            await cls._crawler.start()  # Manual lifecycle
        return cls._crawler
```

**Behavior:**
- First call: creates browser with `config` (or default)
- Subsequent calls: returns same instance, **ignores config param**
- To change config: `reconfigure_browser(new_config)` (closes old, creates new)
- Tools use: `crawler = await BrowserManager.get_browser()`
- No `async with` context manager - manual `start()` / `close()`

### 2. Tool Architecture

**Two types of browser usage:**

**A) Quick operations** (quick_crawl):
```python
@tool("quick_crawl", ...)
async def quick_crawl(args):
    crawler = await BrowserManager.get_browser()  # Singleton
    result = await crawler.arun(url=args["url"], config=run_config)
    # No close - browser stays alive
```

**B) Named sessions** (start_session, navigate, extract_data, etc.):
```python
CRAWLER_SESSIONS: Dict[str, AsyncWebCrawler] = {}  # Named refs
CRAWLER_SESSION_URLS: Dict[str, str] = {}  # Track current URL

@tool("start_session", ...)
async def start_session(args):
    crawler = await BrowserManager.get_browser()
    CRAWLER_SESSIONS[args["session_id"]] = crawler  # Store ref

@tool("navigate", ...)
async def navigate(args):
    crawler = CRAWLER_SESSIONS[args["session_id"]]
    result = await crawler.arun(url=args["url"], ...)
    CRAWLER_SESSION_URLS[args["session_id"]] = result.url  # Track URL

@tool("extract_data", ...)
async def extract_data(args):
    crawler = CRAWLER_SESSIONS[args["session_id"]]
    current_url = CRAWLER_SESSION_URLS[args["session_id"]]  # Must have URL
    result = await crawler.arun(url=current_url, ...)  # Re-crawl current page

@tool("close_session", ...)
async def close_session(args):
    CRAWLER_SESSIONS.pop(args["session_id"])  # Remove ref
    CRAWLER_SESSION_URLS.pop(args["session_id"], None)
    # Browser stays alive (singleton)
```

**Important:** Named sessions are just **references** to singleton browser. Multiple sessions = same browser instance.

### 3. Markdown Handling (CRITICAL BUG FIX)

**OLD (WRONG):**
```python
result.markdown_v2.raw_markdown  # DEPRECATED
```

**NEW (CORRECT):**
```python
# result.markdown can be:
# - str (simple mode)
# - MarkdownGenerationResult object (with filters)

if isinstance(result.markdown, str):
    markdown_content = result.markdown
elif hasattr(result.markdown, 'raw_markdown'):
    markdown_content = result.markdown.raw_markdown
```

Reference: `CRAWL4AI_SDK.md` line 614 - `markdown_v2` deprecated, use `markdown`

### 4. Chat Mode Streaming Input

**Per cc_stream.md:** Use message generator pattern

```python
# chat_mode.py
async def message_generator(self) -> AsyncGenerator[Dict[str, Any], None]:
    while not self._exit_requested:
        user_input = await asyncio.to_thread(self.ui.get_user_input)

        if user_input.startswith('/'):
            await self._handle_command(user_input)
            continue

        # Yield in streaming input format
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": user_input
            }
        }

async def run(self):
    async with ClaudeSDKClient(options=self.options) as client:
        await client.query(self.message_generator())  # Pass generator

        async for message in client.receive_messages():
            # Process streaming responses
```

**Key:** Generator keeps yielding user inputs, SDK streams responses back.

### 5. Claude SDK Integration

**Setup:**
```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeSDKClient, ClaudeAgentOptions

# 1. Define tools with @tool decorator
@tool("quick_crawl", "description", {"url": str, "output_format": str})
async def quick_crawl(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(result)}]}

# 2. Create MCP server
crawler_server = create_sdk_mcp_server(
    name="crawl4ai",
    version="1.0.0",
    tools=[quick_crawl, start_session, ...]  # List of @tool functions
)

# 3. Configure options
options = ClaudeAgentOptions(
    mcp_servers={"crawler": crawler_server},
    allowed_tools=[
        "mcp__crawler__quick_crawl",  # Format: mcp__{server}__{tool}
        "mcp__crawler__start_session",
        # Built-in tools:
        "Read", "Write", "Edit", "Glob", "Grep", "Bash", "NotebookEdit"
    ],
    system_prompt=SYSTEM_PROMPT,
    permission_mode="acceptEdits"
)

# 4. Use client
async with ClaudeSDKClient(options=options) as client:
    await client.query(prompt_or_generator)
    async for message in client.receive_messages():
        # Process AssistantMessage, ResultMessage, etc.
```

**Tool response format:**
```python
return {
    "content": [{
        "type": "text",
        "text": json.dumps({"success": True, "data": "..."})
    }]
}
```

## Operating Modes

### Single-Shot Mode
```bash
python -m crawl4ai.agent.agent_crawl "Crawl example.com"
```
- One prompt → execute → exit
- Uses singleton browser
- No cleanup of browser (process exit handles it)

### Chat Mode
```bash
python -m crawl4ai.agent.agent_crawl --chat
```
- Interactive loop with streaming I/O
- Commands: `/exit` `/clear` `/help` `/browser`
- Browser persists across all turns
- Cleanup on exit: `BrowserManager.close_browser()`

## Testing Architecture

**3 test levels:**

1. **Component tests** (`test_chat.py`): Non-interactive, tests individual classes
2. **Tool tests** (`test_tools.py`): Direct AsyncWebCrawler calls, validates Crawl4AI integration
3. **Scenario tests** (`test_scenarios.py`): Automated multi-turn conversations
   - Injects messages programmatically
   - Validates tool calls, keywords, files created
   - Categories: SIMPLE (2), MEDIUM (3), COMPLEX (4)

## Dependencies

```python
# External
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from claude_agent_sdk import (
    tool, create_sdk_mcp_server, ClaudeSDKClient, ClaudeAgentOptions,
    AssistantMessage, TextBlock, ResultMessage, ToolUseBlock
)
from rich.console import Console  # Already installed
from rich.markdown import Markdown
from rich.syntax import Syntax

# Stdlib
import asyncio, json, uuid, argparse
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator
```

## Common Pitfalls

1. **DON'T** use `async with AsyncWebCrawler()` - breaks singleton pattern
2. **DON'T** use `result.markdown_v2` - deprecated field
3. **DON'T** call `crawler.arun()` without URL in session tools - needs current_url
4. **DON'T** close browser in tools - managed by BrowserManager
5. **DON'T** use `break` in message iteration - causes asyncio issues
6. **DO** track session URLs in `CRAWLER_SESSION_URLS` for session tools
7. **DO** handle both `str` and `MarkdownGenerationResult` for `result.markdown`
8. **DO** use manual lifecycle `await crawler.start()` / `await crawler.close()`

## Session Storage

**Location:** `~/.crawl4ai/agents/projects/{sanitized_cwd}/{uuid}.jsonl`

**Format:** JSONL with events:
```json
{"timestamp": "...", "event": "session_start", "data": {...}}
{"timestamp": "...", "event": "user_message", "data": {"text": "..."}}
{"timestamp": "...", "event": "assistant_message", "data": {"turn": 1, "text": "..."}}
{"timestamp": "...", "event": "session_end", "data": {"duration_ms": 1000, ...}}
```

## CLI Options

```
--chat                  Interactive chat mode
--model MODEL          Claude model override
--permission-mode MODE  acceptEdits|bypassPermissions|default|plan
--add-dir DIR [DIR...] Additional accessible directories
--system-prompt TEXT   Custom system prompt
--session-id UUID      Resume/specify session
--debug                Full tracebacks
```

## Performance Characteristics

- **Browser startup:** ~2-4s (once per session)
- **Quick crawl:** ~1-2s (reuses browser)
- **Session operations:** ~1-2s (same browser)
- **Chat latency:** Real-time streaming, no buffering
- **Memory:** One browser instance regardless of operations

## Extension Points

1. **New tools:** Add `@tool` function → add to `CRAWL_TOOLS` → add to `allowed_tools`
2. **New commands:** Add handler in `ChatMode._handle_command()`
3. **Custom UI:** Replace `TerminalUI` with different renderer
4. **Persistent sessions:** Serialize browser cookies/state to disk in `BrowserManager`
5. **Multi-browser:** Modify `BrowserManager` to support multiple configs (not recommended)

## Next Steps: Testing & Evaluation Pipeline

### Phase 1: Automated Testing (CURRENT)
**Objective:** Verify codebase correctness, not agent quality

**Test Execution:**
```bash
# 1. Component tests (fast, non-interactive)
python crawl4ai/agent/test_chat.py
# Expected: All components instantiate correctly

# 2. Tool integration tests (medium, requires browser)
python crawl4ai/agent/test_tools.py
# Expected: All 7 tools work with Crawl4AI

# 3. Multi-turn scenario tests (slow, comprehensive)
python crawl4ai/agent/test_scenarios.py
# Expected: 9 scenarios pass (2 simple, 3 medium, 4 complex)
# Output: test_agent_output/test_results.json
```

**Success Criteria:**
- All component tests pass
- All tool tests pass
- ≥80% scenario tests pass (7/9)
- No crashes, exceptions, or hangs
- Browser cleanup verified

**Automated Pipeline:**
```bash
# Run all tests in sequence, exit on first failure
cd /Users/unclecode/devs/crawl4ai
python crawl4ai/agent/test_chat.py && \
python crawl4ai/agent/test_tools.py && \
python crawl4ai/agent/test_scenarios.py
echo "Exit code: $?"  # 0 = all passed
```

### Phase 2: Evaluation (NEXT)
**Objective:** Measure agent performance quality

**Metrics to define:**
- Task completion rate
- Tool selection accuracy
- Context retention across turns
- Planning effectiveness
- Error recovery capability

**Eval framework needed:**
- Expand scenario tests with quality scoring
- Add ground truth comparisons
- Measure token efficiency
- Track reasoning quality

**Not in scope yet** - wait for Phase 1 completion

---
**Last Updated:** 2025-01-17
**Version:** 1.0.0
**Status:** Testing Phase - Ready for automated test runs
