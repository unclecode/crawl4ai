# C4A-Script API Reference

Complete reference for all C4A-Script commands, syntax, and advanced features.

## Command Categories

### 🧭 Navigation Commands

Navigate between pages and manage browser history.

#### `GO <url>`
Navigate to a specific URL.

**Syntax:**
```c4a
GO <url>
```

**Parameters:**
- `url` - Target URL (string)

**Examples:**
```c4a
GO https://example.com
GO https://api.example.com/login
GO /relative/path
```

**Notes:**
- Supports both absolute and relative URLs
- Automatically handles protocol detection
- Waits for page load to complete

---

#### `RELOAD`
Refresh the current page.

**Syntax:**
```c4a
RELOAD
```

**Examples:**
```c4a
RELOAD
```

**Notes:**
- Equivalent to pressing F5 or clicking browser refresh
- Waits for page reload to complete
- Preserves current URL

---

#### `BACK`
Navigate back in browser history.

**Syntax:**
```c4a
BACK
```

**Examples:**
```c4a
BACK
```

**Notes:**
- Equivalent to clicking browser back button
- Does nothing if no previous page exists
- Waits for navigation to complete

---

#### `FORWARD`
Navigate forward in browser history.

**Syntax:**
```c4a
FORWARD
```

**Examples:**
```c4a
FORWARD
```

**Notes:**
- Equivalent to clicking browser forward button
- Does nothing if no next page exists
- Waits for navigation to complete

### ⏱️ Wait Commands

Control timing and synchronization with page elements.

#### `WAIT <time>`
Wait for a specified number of seconds.

**Syntax:**
```c4a
WAIT <seconds>
```

**Parameters:**
- `seconds` - Number of seconds to wait (number)

**Examples:**
```c4a
WAIT 3
WAIT 1.5
WAIT 10
```

**Notes:**
- Accepts decimal values
- Useful for giving dynamic content time to load
- Non-blocking for other browser operations

---

#### `WAIT <selector> <timeout>`
Wait for an element to appear on the page.

**Syntax:**
```c4a
WAIT `<selector>` <timeout>
```

**Parameters:**
- `selector` - CSS selector for the element (string in backticks)
- `timeout` - Maximum seconds to wait (number)

**Examples:**
```c4a
WAIT `#content` 10
WAIT `.loading-spinner` 5
WAIT `button[type="submit"]` 15
WAIT `.results .item:first-child` 8
```

**Notes:**
- Fails if element doesn't appear within timeout
- More reliable than fixed time waits
- Supports complex CSS selectors

---

#### `WAIT "<text>" <timeout>`
Wait for specific text to appear anywhere on the page.

**Syntax:**
```c4a
WAIT "<text>" <timeout>
```

**Parameters:**
- `text` - Text content to wait for (string in quotes)
- `timeout` - Maximum seconds to wait (number)

**Examples:**
```c4a
WAIT "Loading complete" 10
WAIT "Welcome back" 5
WAIT "Search results" 15
```

**Notes:**
- Case-sensitive text matching
- Searches entire page content
- Useful for dynamic status messages

### 🖱️ Mouse Commands

Simulate mouse interactions and movements.

#### `CLICK <selector>`
Click on an element specified by CSS selector.

**Syntax:**
```c4a
CLICK `<selector>`
```

**Parameters:**
- `selector` - CSS selector for the element (string in backticks)

**Examples:**
```c4a
CLICK `#submit-button`
CLICK `.menu-item:first-child`
CLICK `button[data-action="save"]`
CLICK `a[href="/dashboard"]`
```

**Notes:**
- Waits for element to be clickable
- Scrolls element into view if necessary
- Handles overlapping elements intelligently

---

#### `CLICK <x> <y>`
Click at specific coordinates on the page.

**Syntax:**
```c4a
CLICK <x> <y>
```

**Parameters:**
- `x` - X coordinate in pixels (number)
- `y` - Y coordinate in pixels (number)

**Examples:**
```c4a
CLICK 100 200
CLICK 500 300
CLICK 0 0
```

**Notes:**
- Coordinates are relative to viewport
- Useful when element selectors are unreliable
- Consider responsive design implications

---

#### `DOUBLE_CLICK <selector>`
Double-click on an element.

**Syntax:**
```c4a
DOUBLE_CLICK `<selector>`
```

**Parameters:**
- `selector` - CSS selector for the element (string in backticks)

**Examples:**
```c4a
DOUBLE_CLICK `.file-icon`
DOUBLE_CLICK `#editable-cell`
DOUBLE_CLICK `.expandable-item`
```

**Notes:**
- Triggers dblclick event
- Common for opening files or editing inline content
- Timing between clicks is automatically handled

---

#### `RIGHT_CLICK <selector>`
Right-click on an element to open context menu.

**Syntax:**
```c4a
RIGHT_CLICK `<selector>`
```

**Parameters:**
- `selector` - CSS selector for the element (string in backticks)

**Examples:**
```c4a
RIGHT_CLICK `#context-target`
RIGHT_CLICK `.menu-trigger`
RIGHT_CLICK `img.thumbnail`
```

**Notes:**
- Opens browser/application context menu
- Useful for testing context menu interactions
- May be blocked by some applications

---

#### `SCROLL <direction> <amount>`
Scroll the page in a specified direction.

**Syntax:**
```c4a
SCROLL <direction> <amount>
```

**Parameters:**
- `direction` - Direction to scroll: `UP`, `DOWN`, `LEFT`, `RIGHT`
- `amount` - Number of pixels to scroll (number)

**Examples:**
```c4a
SCROLL DOWN 500
SCROLL UP 200
SCROLL LEFT 100
SCROLL RIGHT 300
```

**Notes:**
- Smooth scrolling animation
- Useful for infinite scroll pages
- Amount can be larger than viewport

---

#### `MOVE <x> <y>`
Move mouse cursor to specific coordinates.

**Syntax:**
```c4a
MOVE <x> <y>
```

**Parameters:**
- `x` - X coordinate in pixels (number)
- `y` - Y coordinate in pixels (number)

**Examples:**
```c4a
MOVE 200 100
MOVE 500 400
```

**Notes:**
- Triggers hover effects
- Useful for testing mouseover interactions
- Does not click, only moves cursor

---

#### `DRAG <x1> <y1> <x2> <y2>`
Drag from one point to another.

**Syntax:**
```c4a
DRAG <x1> <y1> <x2> <y2>
```

**Parameters:**
- `x1`, `y1` - Starting coordinates (numbers)
- `x2`, `y2` - Ending coordinates (numbers)

**Examples:**
```c4a
DRAG 100 100 500 300
DRAG 0 200 400 200
```

**Notes:**
- Simulates click, drag, and release
- Useful for sliders, resizing, reordering
- Smooth drag animation

### ⌨️ Keyboard Commands

Simulate keyboard input and key presses.

#### `TYPE "<text>"`
Type text into the currently focused element.

**Syntax:**
```c4a
TYPE "<text>"
```

**Parameters:**
- `text` - Text to type (string in quotes)

**Examples:**
```c4a
TYPE "Hello, World!"
TYPE "user@example.com"
TYPE "Password123!"
```

**Notes:**
- Requires an input element to be focused
- Types character by character with realistic timing
- Supports special characters and Unicode

---

#### `TYPE $<variable>`
Type the value of a variable.

**Syntax:**
```c4a
TYPE $<variable>
```

**Parameters:**
- `variable` - Variable name (without quotes)

**Examples:**
```c4a
SETVAR email = "user@example.com"
TYPE $email
```

**Notes:**
- Variable must be defined with SETVAR first
- Variable values are strings
- Useful for reusable credentials or data

---

#### `PRESS <key>`
Press and release a special key.

**Syntax:**
```c4a
PRESS <key>
```

**Parameters:**
- `key` - Key name (see supported keys below)

**Supported Keys:**
- `Tab`, `Enter`, `Escape`, `Space`
- `ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight`
- `Delete`, `Backspace`
- `Home`, `End`, `PageUp`, `PageDown`

**Examples:**
```c4a
PRESS Tab
PRESS Enter
PRESS Escape
PRESS ArrowDown
```

**Notes:**
- Simulates actual key press and release
- Useful for form navigation and shortcuts
- Case-sensitive key names

---

#### `KEY_DOWN <key>`
Hold down a modifier key.

**Syntax:**
```c4a
KEY_DOWN <key>
```

**Parameters:**
- `key` - Modifier key: `Shift`, `Control`, `Alt`, `Meta`

**Examples:**
```c4a
KEY_DOWN Shift
KEY_DOWN Control
```

**Notes:**
- Must be paired with KEY_UP
- Useful for key combinations
- Meta key is Cmd on Mac, Windows key on PC

---

#### `KEY_UP <key>`
Release a modifier key.

**Syntax:**
```c4a
KEY_UP <key>
```

**Parameters:**
- `key` - Modifier key: `Shift`, `Control`, `Alt`, `Meta`

**Examples:**
```c4a
KEY_UP Shift
KEY_UP Control
```

**Notes:**
- Must be paired with KEY_DOWN
- Releases the specified modifier key
- Good practice to always release held keys

---

#### `CLEAR <selector>`
Clear the content of an input field.

**Syntax:**
```c4a
CLEAR `<selector>`
```

**Parameters:**
- `selector` - CSS selector for input element (string in backticks)

**Examples:**
```c4a
CLEAR `#search-box`
CLEAR `input[name="email"]`
CLEAR `.form-input:first-child`
```

**Notes:**
- Works with input, textarea elements
- Faster than selecting all and deleting
- Triggers appropriate change events

---

#### `SET <selector> "<value>"`
Set the value of an input field directly.

**Syntax:**
```c4a
SET `<selector>` "<value>"
```

**Parameters:**
- `selector` - CSS selector for input element (string in backticks)
- `value` - Value to set (string in quotes)

**Examples:**
```c4a
SET `#email` "user@example.com"
SET `#age` "25"
SET `textarea#message` "Hello, this is a test message."
```

**Notes:**
- Directly sets value without typing animation
- Faster than TYPE for long text
- Triggers change and input events

### 🔀 Control Flow Commands

Add conditional logic and loops to your scripts.

#### `IF (EXISTS <selector>) THEN <command>`
Execute command if element exists.

**Syntax:**
```c4a
IF (EXISTS `<selector>`) THEN <command>
```

**Parameters:**
- `selector` - CSS selector to check (string in backticks)
- `command` - Command to execute if condition is true

**Examples:**
```c4a
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept-cookies`
IF (EXISTS `#popup-modal`) THEN CLICK `.close-button`
IF (EXISTS `.error-message`) THEN RELOAD
```

**Notes:**
- Checks for element existence at time of execution
- Does not wait for element to appear
- Can be combined with ELSE

---

#### `IF (EXISTS <selector>) THEN <command> ELSE <command>`
Execute command based on element existence.

**Syntax:**
```c4a
IF (EXISTS `<selector>`) THEN <command> ELSE <command>
```

**Parameters:**
- `selector` - CSS selector to check (string in backticks)
- First `command` - Execute if condition is true
- Second `command` - Execute if condition is false

**Examples:**
```c4a
IF (EXISTS `.user-menu`) THEN CLICK `.logout` ELSE CLICK `.login`
IF (EXISTS `.loading`) THEN WAIT 5 ELSE CLICK `#continue`
```

**Notes:**
- Exactly one command will be executed
- Useful for handling different page states
- Commands must be on same line

---

#### `IF (NOT EXISTS <selector>) THEN <command>`
Execute command if element does not exist.

**Syntax:**
```c4a
IF (NOT EXISTS `<selector>`) THEN <command>
```

**Parameters:**
- `selector` - CSS selector to check (string in backticks)
- `command` - Command to execute if element doesn't exist

**Examples:**
```c4a
IF (NOT EXISTS `.logged-in`) THEN GO /login
IF (NOT EXISTS `.results`) THEN CLICK `#search-button`
```

**Notes:**
- Inverse of EXISTS condition
- Useful for error handling
- Can check for missing required elements

---

#### `IF (<javascript>) THEN <command>`
Execute command based on JavaScript condition.

**Syntax:**
```c4a
IF (`<javascript>`) THEN <command>
```

**Parameters:**
- `javascript` - JavaScript expression that returns boolean (string in backticks)
- `command` - Command to execute if condition is true

**Examples:**
```c4a
IF (`window.innerWidth < 768`) THEN CLICK `.mobile-menu`
IF (`document.readyState === "complete"`) THEN CLICK `#start`
IF (`localStorage.getItem("user")`) THEN GO /dashboard
```

**Notes:**
- JavaScript executes in browser context
- Must return boolean value
- Access to all browser APIs and globals

---

#### `REPEAT (<command>, <count>)`
Repeat a command a specific number of times.

**Syntax:**
```c4a
REPEAT (<command>, <count>)
```

**Parameters:**
- `command` - Command to repeat
- `count` - Number of times to repeat (number)

**Examples:**
```c4a
REPEAT (SCROLL DOWN 300, 5)
REPEAT (PRESS Tab, 3)
REPEAT (CLICK `.load-more`, 10)
```

**Notes:**
- Executes command exactly count times
- Useful for pagination, scrolling, navigation
- No delay between repetitions (add WAIT if needed)

---

#### `REPEAT (<command>, <condition>)`
Repeat a command while condition is true.

**Syntax:**
```c4a
REPEAT (<command>, `<condition>`)
```

**Parameters:**
- `command` - Command to repeat
- `condition` - JavaScript condition to check (string in backticks)

**Examples:**
```c4a
REPEAT (SCROLL DOWN 500, `document.querySelector(".load-more")`)
REPEAT (PRESS ArrowDown, `window.scrollY < document.body.scrollHeight`)
```

**Notes:**
- Condition checked before each iteration
- JavaScript condition must return boolean
- Be careful to avoid infinite loops

### 💾 Variables and Data

Store and manipulate data within scripts.

#### `SETVAR <name> = "<value>"`
Create or update a variable.

**Syntax:**
```c4a
SETVAR <name> = "<value>"
```

**Parameters:**
- `name` - Variable name (alphanumeric, underscore)
- `value` - Variable value (string in quotes)

**Examples:**
```c4a
SETVAR username = "john@example.com"
SETVAR password = "secret123"
SETVAR base_url = "https://api.example.com"
SETVAR counter = "0"
```

**Notes:**
- Variables are global within script scope
- Values are always strings
- Can be used with TYPE command using $variable syntax

---

#### `EVAL <javascript>`
Execute arbitrary JavaScript code.

**Syntax:**
```c4a
EVAL `<javascript>`
```

**Parameters:**
- `javascript` - JavaScript code to execute (string in backticks)

**Examples:**
```c4a
EVAL `console.log("Script started")`
EVAL `window.scrollTo(0, 0)`
EVAL `localStorage.setItem("test", "value")`
EVAL `document.title = "Automated Test"`
```

**Notes:**
- Full access to browser JavaScript APIs
- Useful for custom logic and debugging
- Return values are not captured
- Be careful with security implications

### 📝 Comments and Documentation

#### `# <comment>`
Add comments to scripts for documentation.

**Syntax:**
```c4a
# <comment text>
```

**Examples:**
```c4a
# This script logs into the application
# Step 1: Navigate to login page
GO /login

# Step 2: Fill credentials
TYPE "user@example.com"
```

**Notes:**
- Comments are ignored during execution
- Useful for documentation and debugging
- Can appear anywhere in script
- Supports multi-line documentation blocks

### 🔧 Procedures (Advanced)

Define reusable command sequences.

#### `PROC <name> ... ENDPROC`
Define a reusable procedure.

**Syntax:**
```c4a
PROC <name>
  <commands>
ENDPROC
```

**Parameters:**
- `name` - Procedure name (alphanumeric, underscore)
- `commands` - Commands to include in procedure

**Examples:**
```c4a
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
```

**Notes:**
- Procedures must be defined before use
- Support nested command structures
- Variables are shared with main script scope

---

#### `<procedure_name>`
Call a defined procedure.

**Syntax:**
```c4a
<procedure_name>
```

**Examples:**
```c4a
# Define procedure first
PROC setup
  GO /login
  WAIT `#form` 5
ENDPROC

# Call procedure
setup
login
```

**Notes:**
- Procedure must be defined before calling
- Can be called multiple times
- No parameters supported (use variables instead)

## Error Handling Best Practices

### 1. Always Use Waits
```c4a
# Bad - element might not be ready
CLICK `#button`

# Good - wait for element first
WAIT `#button` 5
CLICK `#button`
```

### 2. Handle Optional Elements
```c4a
# Check before interacting
IF (EXISTS `.popup`) THEN CLICK `.close`
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept`

# Then proceed with main flow
CLICK `#main-action`
```

### 3. Use Descriptive Variables
```c4a
# Set up reusable data
SETVAR admin_email = "admin@company.com"
SETVAR test_password = "TestPass123!"
SETVAR staging_url = "https://staging.example.com"

# Use throughout script
GO $staging_url
TYPE $admin_email
```

### 4. Add Debugging Information
```c4a
# Log progress
EVAL `console.log("Starting login process")`
GO /login

# Verify page state
IF (`document.title.includes("Login")`) THEN EVAL `console.log("On login page")`

# Continue with login
TYPE $username
```

## Common Patterns

### Login Flow
```c4a
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
```

### Infinite Scroll
```c4a
# Load all content with infinite scroll
GO /products

# Scroll and load more content
REPEAT (SCROLL DOWN 500, `document.querySelector(".load-more")`)

# Alternative: Fixed number of scrolls
REPEAT (SCROLL DOWN 800, 10)
WAIT 2
```

### Form Validation
```c4a
# Handle form with validation
SET `#email` "invalid-email"
CLICK `#submit`

# Check for validation error
IF (EXISTS `.error-email`) THEN SET `#email` "valid@example.com"

# Retry submission
CLICK `#submit`
WAIT `.success-message` 5
```

### Multi-step Process
```c4a
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
```

## Integration with Crawl4AI

Use C4A-Script with Crawl4AI for dynamic content interaction:

```python
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
```

This reference covers all available C4A-Script commands and patterns. For interactive learning, try the [tutorial](../examples/c4a_script/tutorial/) or [live demo](https://docs.crawl4ai.com/c4a-script/demo).