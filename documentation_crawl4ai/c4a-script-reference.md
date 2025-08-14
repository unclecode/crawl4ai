[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/api/c4a-script-reference/)


[ unclecode/crawl4ai ](https://github.com/unclecode/crawl4ai)
×
  * [Home](https://docs.crawl4ai.com/)
  * [Ask AI](https://docs.crawl4ai.com/core/ask-ai/)
  * [Quick Start](https://docs.crawl4ai.com/core/quickstart/)
  * [Code Examples](https://docs.crawl4ai.com/core/examples/)
  * Apps
    * [Demo Apps](https://docs.crawl4ai.com/apps/)
    * [C4A-Script Editor](https://docs.crawl4ai.com/apps/c4a-script/)
    * [LLM Context Builder](https://docs.crawl4ai.com/apps/llmtxt/)
  * Setup & Installation
    * [Installation](https://docs.crawl4ai.com/core/installation/)
    * [Docker Deployment](https://docs.crawl4ai.com/core/docker-deployment/)
  * Blog & Changelog
    * [Blog Home](https://docs.crawl4ai.com/blog/)
    * [Changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md)
  * Core
    * [Command Line Interface](https://docs.crawl4ai.com/core/cli/)
    * [Simple Crawling](https://docs.crawl4ai.com/core/simple-crawling/)
    * [Deep Crawling](https://docs.crawl4ai.com/core/deep-crawling/)
    * [Adaptive Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/)
    * [URL Seeding](https://docs.crawl4ai.com/core/url-seeding/)
    * [C4A-Script](https://docs.crawl4ai.com/core/c4a-script/)
    * [Crawler Result](https://docs.crawl4ai.com/core/crawler-result/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/core/browser-crawler-config/)
    * [Markdown Generation](https://docs.crawl4ai.com/core/markdown-generation/)
    * [Fit Markdown](https://docs.crawl4ai.com/core/fit-markdown/)
    * [Page Interaction](https://docs.crawl4ai.com/core/page-interaction/)
    * [Content Selection](https://docs.crawl4ai.com/core/content-selection/)
    * [Cache Modes](https://docs.crawl4ai.com/core/cache-modes/)
    * [Local Files & Raw HTML](https://docs.crawl4ai.com/core/local-files/)
    * [Link & Media](https://docs.crawl4ai.com/core/link-media/)
  * Advanced
    * [Overview](https://docs.crawl4ai.com/advanced/advanced-features/)
    * [Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)
    * [Virtual Scroll](https://docs.crawl4ai.com/advanced/virtual-scroll/)
    * [File Downloading](https://docs.crawl4ai.com/advanced/file-downloading/)
    * [Lazy Loading](https://docs.crawl4ai.com/advanced/lazy-loading/)
    * [Hooks & Auth](https://docs.crawl4ai.com/advanced/hooks-auth/)
    * [Proxy & Security](https://docs.crawl4ai.com/advanced/proxy-security/)
    * [Undetected Browser](https://docs.crawl4ai.com/advanced/undetected-browser/)
    * [Session Management](https://docs.crawl4ai.com/advanced/session-management/)
    * [Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/)
    * [Crawl Dispatcher](https://docs.crawl4ai.com/advanced/crawl-dispatcher/)
    * [Identity Based Crawling](https://docs.crawl4ai.com/advanced/identity-based-crawling/)
    * [SSL Certificate](https://docs.crawl4ai.com/advanced/ssl-certificate/)
    * [Network & Console Capture](https://docs.crawl4ai.com/advanced/network-console-capture/)
    * [PDF Parsing](https://docs.crawl4ai.com/advanced/pdf-parsing/)
  * Extraction
    * [LLM-Free Strategies](https://docs.crawl4ai.com/extraction/no-llm-strategies/)
    * [LLM Strategies](https://docs.crawl4ai.com/extraction/llm-strategies/)
    * [Clustering Strategies](https://docs.crawl4ai.com/extraction/clustring-strategies/)
    * [Chunking](https://docs.crawl4ai.com/extraction/chunking/)
  * API Reference
    * [AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler/)
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * C4A-Script Reference


* * *
  * [C4A-Script API Reference](https://docs.crawl4ai.com/api/c4a-script-reference/#c4a-script-api-reference)
  * [Command Categories](https://docs.crawl4ai.com/api/c4a-script-reference/#command-categories)
  * [Error Handling Best Practices](https://docs.crawl4ai.com/api/c4a-script-reference/#error-handling-best-practices)
  * [Common Patterns](https://docs.crawl4ai.com/api/c4a-script-reference/#common-patterns)
  * [Integration with Crawl4AI](https://docs.crawl4ai.com/api/c4a-script-reference/#integration-with-crawl4ai)


# C4A-Script API Reference
Complete reference for all C4A-Script commands, syntax, and advanced features.
## Command Categories
### 🧭 Navigation Commands
Navigate between pages and manage browser history.
#### `GO <url>`
Navigate to a specific URL.
**Syntax:**
```
GO <url>
Copy
```

**Parameters:** - `url` - Target URL (string)
**Examples:**
```
GO https://example.com
GO https://api.example.com/login
GO /relative/path
Copy
```

**Notes:** - Supports both absolute and relative URLs - Automatically handles protocol detection - Waits for page load to complete
* * *
#### `RELOAD`
Refresh the current page.
**Syntax:**
```
RELOAD
Copy
```

**Examples:**
```
RELOAD
Copy
```

**Notes:** - Equivalent to pressing F5 or clicking browser refresh - Waits for page reload to complete - Preserves current URL
* * *
#### `BACK`
Navigate back in browser history.
**Syntax:**
```
BACK
Copy
```

**Examples:**
```
BACK
Copy
```

**Notes:** - Equivalent to clicking browser back button - Does nothing if no previous page exists - Waits for navigation to complete
* * *
#### `FORWARD`
Navigate forward in browser history.
**Syntax:**
```
FORWARD
Copy
```

**Examples:**
```
FORWARD
Copy
```

**Notes:** - Equivalent to clicking browser forward button - Does nothing if no next page exists - Waits for navigation to complete
### ⏱️ Wait Commands
Control timing and synchronization with page elements.
#### `WAIT <time>`
Wait for a specified number of seconds.
**Syntax:**
```
WAIT <seconds>
Copy
```

**Parameters:** - `seconds` - Number of seconds to wait (number)
**Examples:**
```
WAIT 3
WAIT 1.5
WAIT 10
Copy
```

**Notes:** - Accepts decimal values - Useful for giving dynamic content time to load - Non-blocking for other browser operations
* * *
#### `WAIT <selector> <timeout>`
Wait for an element to appear on the page.
**Syntax:**
```
WAIT `<selector>` <timeout>
Copy
```

**Parameters:** - `selector` - CSS selector for the element (string in backticks) - `timeout` - Maximum seconds to wait (number)
**Examples:**
```
WAIT `#content` 10
WAIT `.loading-spinner` 5
WAIT `button[type="submit"]` 15
WAIT `.results .item:first-child` 8
Copy
```

**Notes:** - Fails if element doesn't appear within timeout - More reliable than fixed time waits - Supports complex CSS selectors
* * *
#### `WAIT "<text>" <timeout>`
Wait for specific text to appear anywhere on the page.
**Syntax:**
```
WAIT "<text>" <timeout>
Copy
```

**Parameters:** - `text` - Text content to wait for (string in quotes) - `timeout` - Maximum seconds to wait (number)
**Examples:**
```
WAIT "Loading complete" 10
WAIT "Welcome back" 5
WAIT "Search results" 15
Copy
```

**Notes:** - Case-sensitive text matching - Searches entire page content - Useful for dynamic status messages
### 🖱️ Mouse Commands
Simulate mouse interactions and movements.
#### `CLICK <selector>`
Click on an element specified by CSS selector.
**Syntax:**
```
CLICK `<selector>`
Copy
```

**Parameters:** - `selector` - CSS selector for the element (string in backticks)
**Examples:**
```
CLICK `#submit-button`
CLICK `.menu-item:first-child`
CLICK `button[data-action="save"]`
CLICK `a[href="/dashboard"]`
Copy
```

**Notes:** - Waits for element to be clickable - Scrolls element into view if necessary - Handles overlapping elements intelligently
* * *
#### `CLICK <x> <y>`
Click at specific coordinates on the page.
**Syntax:**
```
CLICK <x> <y>
Copy
```

**Parameters:** - `x` - X coordinate in pixels (number) - `y` - Y coordinate in pixels (number)
**Examples:**
```
CLICK 100 200
CLICK 500 300
CLICK 0 0
Copy
```

**Notes:** - Coordinates are relative to viewport - Useful when element selectors are unreliable - Consider responsive design implications
* * *
#### `DOUBLE_CLICK <selector>`
Double-click on an element.
**Syntax:**
```
DOUBLE_CLICK `<selector>`
Copy
```

**Parameters:** - `selector` - CSS selector for the element (string in backticks)
**Examples:**
```
DOUBLE_CLICK `.file-icon`
DOUBLE_CLICK `#editable-cell`
DOUBLE_CLICK `.expandable-item`
Copy
```

**Notes:** - Triggers dblclick event - Common for opening files or editing inline content - Timing between clicks is automatically handled
* * *
#### `RIGHT_CLICK <selector>`
Right-click on an element to open context menu.
**Syntax:**
```
RIGHT_CLICK `<selector>`
Copy
```

**Parameters:** - `selector` - CSS selector for the element (string in backticks)
**Examples:**
```
RIGHT_CLICK `#context-target`
RIGHT_CLICK `.menu-trigger`
RIGHT_CLICK `img.thumbnail`
Copy
```

**Notes:** - Opens browser/application context menu - Useful for testing context menu interactions - May be blocked by some applications
* * *
#### `SCROLL <direction> <amount>`
Scroll the page in a specified direction.
**Syntax:**
```
SCROLL <direction> <amount>
Copy
```

**Parameters:** - `direction` - Direction to scroll: `UP`, `DOWN`, `LEFT`, `RIGHT` - `amount` - Number of pixels to scroll (number)
**Examples:**
```
SCROLL DOWN 500
SCROLL UP 200
SCROLL LEFT 100
SCROLL RIGHT 300
Copy
```

**Notes:** - Smooth scrolling animation - Useful for infinite scroll pages - Amount can be larger than viewport
* * *
#### `MOVE <x> <y>`
Move mouse cursor to specific coordinates.
**Syntax:**
```
MOVE <x> <y>
Copy
```

**Parameters:** - `x` - X coordinate in pixels (number) - `y` - Y coordinate in pixels (number)
**Examples:**
```
MOVE 200 100
MOVE 500 400
Copy
```

**Notes:** - Triggers hover effects - Useful for testing mouseover interactions - Does not click, only moves cursor
* * *
#### `DRAG <x1> <y1> <x2> <y2>`
Drag from one point to another.
**Syntax:**
```
DRAG <x1> <y1> <x2> <y2>
Copy
```

**Parameters:** - `x1`, `y1` - Starting coordinates (numbers) - `x2`, `y2` - Ending coordinates (numbers)
**Examples:**
```
DRAG 100 100 500 300
DRAG 0 200 400 200
Copy
```

**Notes:** - Simulates click, drag, and release - Useful for sliders, resizing, reordering - Smooth drag animation
### ⌨️ Keyboard Commands
Simulate keyboard input and key presses.
#### `TYPE "<text>"`
Type text into the currently focused element.
**Syntax:**
```
TYPE "<text>"
Copy
```

**Parameters:** - `text` - Text to type (string in quotes)
**Examples:**
```
TYPE "Hello, World!"
TYPE "user@example.com"
TYPE "Password123!"
Copy
```

**Notes:** - Requires an input element to be focused - Types character by character with realistic timing - Supports special characters and Unicode
* * *
#### `TYPE $<variable>`
Type the value of a variable.
**Syntax:**
```
TYPE $<variable>
Copy
```

**Parameters:** - `variable` - Variable name (without quotes)
**Examples:**
```
SETVAR email = "user@example.com"
TYPE $email
Copy
```

**Notes:** - Variable must be defined with SETVAR first - Variable values are strings - Useful for reusable credentials or data
* * *
#### `PRESS <key>`
Press and release a special key.
**Syntax:**
```
PRESS <key>
Copy
```

**Parameters:** - `key` - Key name (see supported keys below)
**Supported Keys:** - `Tab`, `Enter`, `Escape`, `Space` - `ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight` - `Delete`, `Backspace` - `Home`, `End`, `PageUp`, `PageDown`
**Examples:**
```
PRESS Tab
PRESS Enter
PRESS Escape
PRESS ArrowDown
Copy
```

**Notes:** - Simulates actual key press and release - Useful for form navigation and shortcuts - Case-sensitive key names
* * *
#### `KEY_DOWN <key>`
Hold down a modifier key.
**Syntax:**
```
KEY_DOWN <key>
Copy
```

**Parameters:** - `key` - Modifier key: `Shift`, `Control`, `Alt`, `Meta`
**Examples:**
```
KEY_DOWN Shift
KEY_DOWN Control
Copy
```

**Notes:** - Must be paired with KEY_UP - Useful for key combinations - Meta key is Cmd on Mac, Windows key on PC
* * *
#### `KEY_UP <key>`
Release a modifier key.
**Syntax:**
```
KEY_UP <key>
Copy
```

**Parameters:** - `key` - Modifier key: `Shift`, `Control`, `Alt`, `Meta`
**Examples:**
```
KEY_UP Shift
KEY_UP Control
Copy
```

**Notes:** - Must be paired with KEY_DOWN - Releases the specified modifier key - Good practice to always release held keys
* * *
#### `CLEAR <selector>`
Clear the content of an input field.
**Syntax:**
```
CLEAR `<selector>`
Copy
```

**Parameters:** - `selector` - CSS selector for input element (string in backticks)
**Examples:**
```
CLEAR `#search-box`
CLEAR `input[name="email"]`
CLEAR `.form-input:first-child`
Copy
```

**Notes:** - Works with input, textarea elements - Faster than selecting all and deleting - Triggers appropriate change events
* * *
#### `SET <selector> "<value>"`
Set the value of an input field directly.
**Syntax:**
```
SET `<selector>` "<value>"
Copy
```

**Parameters:** - `selector` - CSS selector for input element (string in backticks) - `value` - Value to set (string in quotes)
**Examples:**
```
SET `#email` "user@example.com"
SET `#age` "25"
SET `textarea#message` "Hello, this is a test message."
Copy
```

**Notes:** - Directly sets value without typing animation - Faster than TYPE for long text - Triggers change and input events
### 🔀 Control Flow Commands
Add conditional logic and loops to your scripts.
#### `IF (EXISTS <selector>) THEN <command>`
Execute command if element exists.
**Syntax:**
```
IF (EXISTS `<selector>`) THEN <command>
Copy
```

**Parameters:** - `selector` - CSS selector to check (string in backticks) - `command` - Command to execute if condition is true
**Examples:**
```
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept-cookies`
IF (EXISTS `#popup-modal`) THEN CLICK `.close-button`
IF (EXISTS `.error-message`) THEN RELOAD
Copy
```

**Notes:** - Checks for element existence at time of execution - Does not wait for element to appear - Can be combined with ELSE
* * *
#### `IF (EXISTS <selector>) THEN <command> ELSE <command>`
Execute command based on element existence.
**Syntax:**
```
IF (EXISTS `<selector>`) THEN <command> ELSE <command>
Copy
```

**Parameters:** - `selector` - CSS selector to check (string in backticks) - First `command` - Execute if condition is true - Second `command` - Execute if condition is false
**Examples:**
```
IF (EXISTS `.user-menu`) THEN CLICK `.logout` ELSE CLICK `.login`
IF (EXISTS `.loading`) THEN WAIT 5 ELSE CLICK `#continue`
Copy
```

**Notes:** - Exactly one command will be executed - Useful for handling different page states - Commands must be on same line
* * *
#### `IF (NOT EXISTS <selector>) THEN <command>`
Execute command if element does not exist.
**Syntax:**
```
IF (NOT EXISTS `<selector>`) THEN <command>
Copy
```

**Parameters:** - `selector` - CSS selector to check (string in backticks) - `command` - Command to execute if element doesn't exist
**Examples:**
```
IF (NOT EXISTS `.logged-in`) THEN GO /login
IF (NOT EXISTS `.results`) THEN CLICK `#search-button`
Copy
```

**Notes:** - Inverse of EXISTS condition - Useful for error handling - Can check for missing required elements
* * *
#### `IF (<javascript>) THEN <command>`
Execute command based on JavaScript condition.
**Syntax:**
```
IF (`<javascript>`) THEN <command>
Copy
```

**Parameters:** - `javascript` - JavaScript expression that returns boolean (string in backticks) - `command` - Command to execute if condition is true
**Examples:**
```
IF (`window.innerWidth < 768`) THEN CLICK `.mobile-menu`
IF (`document.readyState === "complete"`) THEN CLICK `#start`
IF (`localStorage.getItem("user")`) THEN GO /dashboard
Copy
```

**Notes:** - JavaScript executes in browser context - Must return boolean value - Access to all browser APIs and globals
* * *
#### `REPEAT (<command>, <count>)`
Repeat a command a specific number of times.
**Syntax:**
```
REPEAT (<command>, <count>)
Copy
```

**Parameters:** - `command` - Command to repeat - `count` - Number of times to repeat (number)
**Examples:**
```
REPEAT (SCROLL DOWN 300, 5)
REPEAT (PRESS Tab, 3)
REPEAT (CLICK `.load-more`, 10)
Copy
```

**Notes:** - Executes command exactly count times - Useful for pagination, scrolling, navigation - No delay between repetitions (add WAIT if needed)
* * *
#### `REPEAT (<command>, <condition>)`
Repeat a command while condition is true.
**Syntax:**
```
REPEAT (<command>, `<condition>`)
Copy
```

**Parameters:** - `command` - Command to repeat - `condition` - JavaScript condition to check (string in backticks)
**Examples:**
```
REPEAT (SCROLL DOWN 500, `document.querySelector(".load-more")`)
REPEAT (PRESS ArrowDown, `window.scrollY < document.body.scrollHeight`)
Copy
```

**Notes:** - Condition checked before each iteration - JavaScript condition must return boolean - Be careful to avoid infinite loops
### 💾 Variables and Data
Store and manipulate data within scripts.
#### `SETVAR <name> = "<value>"`
Create or update a variable.
**Syntax:**
```
SETVAR <name> = "<value>"
Copy
```

**Parameters:** - `name` - Variable name (alphanumeric, underscore) - `value` - Variable value (string in quotes)
**Examples:**
```
SETVAR username = "john@example.com"
SETVAR password = "secret123"
SETVAR base_url = "https://api.example.com"
SETVAR counter = "0"
Copy
```

**Notes:** - Variables are global within script scope - Values are always strings - Can be used with TYPE command using $variable syntax
* * *
#### `EVAL <javascript>`
Execute arbitrary JavaScript code.
**Syntax:**
```
EVAL `<javascript>`
Copy
```

**Parameters:** - `javascript` - JavaScript code to execute (string in backticks)
**Examples:**
```
EVAL `console.log("Script started")`
EVAL `window.scrollTo(0, 0)`
EVAL `localStorage.setItem("test", "value")`
EVAL `document.title = "Automated Test"`
Copy
```

**Notes:** - Full access to browser JavaScript APIs - Useful for custom logic and debugging - Return values are not captured - Be careful with security implications
### 📝 Comments and Documentation
#### `# <comment>`
Add comments to scripts for documentation.
**Syntax:**
```
# <comment text>
Copy
```

**Examples:**
```
# This script logs into the application
# Step 1: Navigate to login page
GO /login

# Step 2: Fill credentials
TYPE "user@example.com"
Copy
```

**Notes:** - Comments are ignored during execution - Useful for documentation and debugging - Can appear anywhere in script - Supports multi-line documentation blocks
### 🔧 Procedures (Advanced)
Define reusable command sequences.
#### `PROC <name> ... ENDPROC`
Define a reusable procedure.
**Syntax:**
```
PROC <name>
  <commands>
ENDPROC
Copy
```

**Parameters:** - `name` - Procedure name (alphanumeric, underscore) - `commands` - Commands to include in procedure
**Examples:**
```
PROC login
  CLICK `#email`
  TYPE $email
  CLICK `#password`
  TYPE $password
  CLICK `#submit`
ENDPROC

PROC handle_popups
  IF (EXISTS `.cookie-banner`) THEN CLICK `.accept`
  IF (EXISTS `.newsletter-modal`) THEN CLICK `.close`
ENDPROC
Copy
```

**Notes:** - Procedures must be defined before use - Support nested command structures - Variables are shared with main script scope
* * *
#### `<procedure_name>`
Call a defined procedure.
**Syntax:**
```
<procedure_name>
Copy
```

**Examples:**
```
# Define procedure first
PROC setup
  GO /login
  WAIT `#form` 5
ENDPROC

# Call procedure
setup
login
Copy
```

**Notes:** - Procedure must be defined before calling - Can be called multiple times - No parameters supported (use variables instead)
## Error Handling Best Practices
### 1. Always Use Waits
```
# Bad - element might not be ready
CLICK `#button`

# Good - wait for element first
WAIT `#button` 5
CLICK `#button`
Copy
```

### 2. Handle Optional Elements
```
# Check before interacting
IF (EXISTS `.popup`) THEN CLICK `.close`
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept`

# Then proceed with main flow
CLICK `#main-action`
Copy
```

### 3. Use Descriptive Variables
```
# Set up reusable data
SETVAR admin_email = "admin@company.com"
SETVAR test_password = "TestPass123!"
SETVAR staging_url = "https://staging.example.com"

# Use throughout script
GO $staging_url
TYPE $admin_email
Copy
```

### 4. Add Debugging Information
```
# Log progress
EVAL `console.log("Starting login process")`
GO /login

# Verify page state
IF (`document.title.includes("Login")`) THEN EVAL `console.log("On login page")`

# Continue with login
TYPE $username
Copy
```

## Common Patterns
### Login Flow
```
# Complete login automation
SETVAR email = "user@example.com"
SETVAR password = "mypassword"

GO /login
WAIT `#login-form` 5

# Handle optional cookie banner
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept-cookies`

# Fill and submit form
CLICK `#email`
TYPE $email
PRESS Tab
TYPE $password
CLICK `button[type="submit"]`

# Wait for redirect
WAIT `.dashboard` 10
Copy
```

### Infinite Scroll
```
# Load all content with infinite scroll
GO /products

# Scroll and load more content
REPEAT (SCROLL DOWN 500, `document.querySelector(".load-more")`)

# Alternative: Fixed number of scrolls
REPEAT (SCROLL DOWN 800, 10)
WAIT 2
Copy
```

### Form Validation
```
# Handle form with validation
SET `#email` "invalid-email"
CLICK `#submit`

# Check for validation error
IF (EXISTS `.error-email`) THEN SET `#email` "valid@example.com"

# Retry submission
CLICK `#submit`
WAIT `.success-message` 5
Copy
```

### Multi-step Process
```
# Complex multi-step workflow
PROC navigate_to_step
  CLICK `.next-button`
  WAIT `.step-content` 5
ENDPROC

# Step 1
WAIT `.step-1` 5
SET `#name` "John Doe"
navigate_to_step

# Step 2
SET `#email` "john@example.com"
navigate_to_step

# Step 3
CLICK `#submit-final`
WAIT `.confirmation` 10
Copy
```

## Integration with Crawl4AI
Use C4A-Script with Crawl4AI for dynamic content interaction:
```
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

# Define interaction script
script = """
# Handle dynamic content loading
WAIT `.content` 5
IF (EXISTS `.load-more-button`) THEN CLICK `.load-more-button`
WAIT `.additional-content` 5

# Accept cookies if needed
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept-all`
"""

config = CrawlerRunConfig(
    c4a_script=script,
    wait_for=".content",
    screenshot=True
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com", config=config)
    print(result.markdown)
Copy
```

This reference covers all available C4A-Script commands and patterns. For interactive learning, try the [tutorial](https://docs.crawl4ai.com/api/examples/c4a_script/tutorial/) or [live demo](https://docs.crawl4ai.com/c4a-script/demo).
#### On this page
  * [Command Categories](https://docs.crawl4ai.com/api/c4a-script-reference/#command-categories)
  * [🧭 Navigation Commands](https://docs.crawl4ai.com/api/c4a-script-reference/#navigation-commands)
  * [GO <url>](https://docs.crawl4ai.com/api/c4a-script-reference/#go-url)
  * [RELOAD](https://docs.crawl4ai.com/api/c4a-script-reference/#reload)
  * [BACK](https://docs.crawl4ai.com/api/c4a-script-reference/#back)
  * [FORWARD](https://docs.crawl4ai.com/api/c4a-script-reference/#forward)
  * [⏱️ Wait Commands](https://docs.crawl4ai.com/api/c4a-script-reference/#wait-commands)
  * [WAIT <time>](https://docs.crawl4ai.com/api/c4a-script-reference/#wait-time)
  * [WAIT <selector> <timeout>](https://docs.crawl4ai.com/api/c4a-script-reference/#wait-selector-timeout)
  * [WAIT "<text>" <timeout>](https://docs.crawl4ai.com/api/c4a-script-reference/#wait-text-timeout)
  * [🖱️ Mouse Commands](https://docs.crawl4ai.com/api/c4a-script-reference/#mouse-commands)
  * [CLICK <selector>](https://docs.crawl4ai.com/api/c4a-script-reference/#click-selector)
  * [CLICK <x> <y>](https://docs.crawl4ai.com/api/c4a-script-reference/#click-x-y)
  * [DOUBLE_CLICK <selector>](https://docs.crawl4ai.com/api/c4a-script-reference/#double_click-selector)
  * [RIGHT_CLICK <selector>](https://docs.crawl4ai.com/api/c4a-script-reference/#right_click-selector)
  * [SCROLL <direction> <amount>](https://docs.crawl4ai.com/api/c4a-script-reference/#scroll-direction-amount)
  * [MOVE <x> <y>](https://docs.crawl4ai.com/api/c4a-script-reference/#move-x-y)
  * [DRAG <x1> <y1> <x2> <y2>](https://docs.crawl4ai.com/api/c4a-script-reference/#drag-x1-y1-x2-y2)
  * [⌨️ Keyboard Commands](https://docs.crawl4ai.com/api/c4a-script-reference/#keyboard-commands)
  * [TYPE "<text>"](https://docs.crawl4ai.com/api/c4a-script-reference/#type-text)
  * [TYPE $<variable>](https://docs.crawl4ai.com/api/c4a-script-reference/#type-variable)
  * [PRESS <key>](https://docs.crawl4ai.com/api/c4a-script-reference/#press-key)
  * [KEY_DOWN <key>](https://docs.crawl4ai.com/api/c4a-script-reference/#key_down-key)
  * [KEY_UP <key>](https://docs.crawl4ai.com/api/c4a-script-reference/#key_up-key)
  * [CLEAR <selector>](https://docs.crawl4ai.com/api/c4a-script-reference/#clear-selector)
  * [SET <selector> "<value>"](https://docs.crawl4ai.com/api/c4a-script-reference/#set-selector-value)
  * [🔀 Control Flow Commands](https://docs.crawl4ai.com/api/c4a-script-reference/#control-flow-commands)
  * [IF (EXISTS <selector>) THEN <command>](https://docs.crawl4ai.com/api/c4a-script-reference/#if-exists-selector-then-command)
  * [IF (EXISTS <selector>) THEN <command> ELSE <command>](https://docs.crawl4ai.com/api/c4a-script-reference/#if-exists-selector-then-command-else-command)
  * [IF (NOT EXISTS <selector>) THEN <command>](https://docs.crawl4ai.com/api/c4a-script-reference/#if-not-exists-selector-then-command)
  * [IF (<javascript>) THEN <command>](https://docs.crawl4ai.com/api/c4a-script-reference/#if-javascript-then-command)
  * [REPEAT (<command>, <count>)](https://docs.crawl4ai.com/api/c4a-script-reference/#repeat-command-count)
  * [REPEAT (<command>, <condition>)](https://docs.crawl4ai.com/api/c4a-script-reference/#repeat-command-condition)
  * [💾 Variables and Data](https://docs.crawl4ai.com/api/c4a-script-reference/#variables-and-data)
  * [SETVAR <name> = "<value>"](https://docs.crawl4ai.com/api/c4a-script-reference/#setvar-name-value)
  * [EVAL <javascript>](https://docs.crawl4ai.com/api/c4a-script-reference/#eval-javascript)
  * [📝 Comments and Documentation](https://docs.crawl4ai.com/api/c4a-script-reference/#comments-and-documentation)
  * [# <comment>](https://docs.crawl4ai.com/api/c4a-script-reference/#comment)
  * [🔧 Procedures (Advanced)](https://docs.crawl4ai.com/api/c4a-script-reference/#procedures-advanced)
  * [PROC <name> ... ENDPROC](https://docs.crawl4ai.com/api/c4a-script-reference/#proc-name-endproc)
  * [<procedure_name>](https://docs.crawl4ai.com/api/c4a-script-reference/#procedure_name)
  * [Error Handling Best Practices](https://docs.crawl4ai.com/api/c4a-script-reference/#error-handling-best-practices)
  * [1. Always Use Waits](https://docs.crawl4ai.com/api/c4a-script-reference/#1-always-use-waits)
  * [2. Handle Optional Elements](https://docs.crawl4ai.com/api/c4a-script-reference/#2-handle-optional-elements)
  * [3. Use Descriptive Variables](https://docs.crawl4ai.com/api/c4a-script-reference/#3-use-descriptive-variables)
  * [4. Add Debugging Information](https://docs.crawl4ai.com/api/c4a-script-reference/#4-add-debugging-information)
  * [Common Patterns](https://docs.crawl4ai.com/api/c4a-script-reference/#common-patterns)
  * [Login Flow](https://docs.crawl4ai.com/api/c4a-script-reference/#login-flow)
  * [Infinite Scroll](https://docs.crawl4ai.com/api/c4a-script-reference/#infinite-scroll)
  * [Form Validation](https://docs.crawl4ai.com/api/c4a-script-reference/#form-validation)
  * [Multi-step Process](https://docs.crawl4ai.com/api/c4a-script-reference/#multi-step-process)
  * [Integration with Crawl4AI](https://docs.crawl4ai.com/api/c4a-script-reference/#integration-with-crawl4ai)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
