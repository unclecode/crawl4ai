# C4A-Script: Visual Web Automation Made Simple

## What is C4A-Script?

C4A-Script is a powerful, human-readable domain-specific language (DSL) designed for web automation and interaction. Think of it as a simplified programming language that anyone can read and write, perfect for automating repetitive web tasks, testing user interfaces, or creating interactive demos.

### Why C4A-Script?

**Simple Syntax, Powerful Results**
```c4a
# Navigate and interact in plain English
GO https://example.com
WAIT `#search-box` 5
TYPE "Hello World"
CLICK `button[type="submit"]`
```

**Visual Programming Support**
C4A-Script comes with a built-in Blockly visual editor, allowing you to create scripts by dragging and dropping blocks - no coding experience required!

**Perfect for:**
- **UI Testing**: Automate user interaction flows
- **Demo Creation**: Build interactive product demonstrations  
- **Data Entry**: Automate form filling and submissions
- **Testing Workflows**: Validate complex user journeys
- **Training**: Teach web automation without code complexity

## Getting Started: Your First Script

Let's create a simple script that searches for something on a website:

```c4a
# My first C4A-Script
GO https://duckduckgo.com

# Wait for the search box to appear
WAIT `input[name="q"]` 10

# Type our search query
TYPE "Crawl4AI"

# Press Enter to search
PRESS Enter

# Wait for results
WAIT `.results` 5
```

That's it! In just a few lines, you've automated a complete search workflow.

## Interactive Tutorial & Live Demo

Want to learn by doing? We've got you covered:

**🚀 [Live Demo](https://docs.crawl4ai.com/apps/c4a-script/)** - Try C4A-Script in your browser right now!

**📁 [Tutorial Examples](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/c4a_script/)** - Complete examples with source code

### Running the Tutorial Locally

The tutorial includes a Flask-based web interface with:
- **Live Code Editor** with syntax highlighting
- **Visual Blockly Editor** for drag-and-drop programming
- **Recording Mode** to capture your actions and generate scripts
- **Timeline View** to see and edit your automation steps

```bash
# Clone and navigate to the tutorial
cd docs/examples/c4a_script/tutorial/

# Install dependencies
pip install flask

# Launch the tutorial server
python app.py

# Open http://localhost:5000 in your browser
```

## Core Concepts

### Commands and Syntax

C4A-Script uses simple, English-like commands. Each command does one specific thing:

```c4a
# Comments start with #
COMMAND parameter1 parameter2

# Most commands use CSS selectors in backticks
CLICK `#submit-button`

# Text content goes in quotes
TYPE "Hello, World!"

# Numbers are used directly
WAIT 3
```

### Selectors: Finding Elements

C4A-Script uses CSS selectors to identify elements on the page:

```c4a
# By ID
CLICK `#login-button`

# By class
CLICK `.submit-btn`

# By attribute
CLICK `button[type="submit"]`

# By text content
CLICK `button:contains("Sign In")`

# Complex selectors
CLICK `.form-container input[name="email"]`
```

### Variables and Dynamic Content

Store and reuse values with variables:

```c4a
# Set a variable
SETVAR username = "john@example.com"
SETVAR password = "secret123"

# Use variables (prefix with $)
TYPE $username
PRESS Tab
TYPE $password
```

## Command Categories

### 🧭 Navigation Commands
Move around the web like a user would:

| Command | Purpose | Example |
|---------|---------|---------|
| `GO` | Navigate to URL | `GO https://example.com` |
| `RELOAD` | Refresh current page | `RELOAD` |
| `BACK` | Go back in history | `BACK` |
| `FORWARD` | Go forward in history | `FORWARD` |

### ⏱️ Wait Commands
Ensure elements are ready before interacting:

| Command | Purpose | Example |
|---------|---------|---------|
| `WAIT` | Wait for time/element/text | `WAIT 3` or `WAIT \`#element\` 10` |

### 🖱️ Mouse Commands
Click, drag, and move like a human:

| Command | Purpose | Example |
|---------|---------|---------|
| `CLICK` | Click element or coordinates | `CLICK \`button\`` or `CLICK 100 200` |
| `DOUBLE_CLICK` | Double-click element | `DOUBLE_CLICK \`.item\`` |
| `RIGHT_CLICK` | Right-click element | `RIGHT_CLICK \`#menu\`` |
| `SCROLL` | Scroll in direction | `SCROLL DOWN 500` |
| `DRAG` | Drag from point to point | `DRAG 100 100 500 300` |

### ⌨️ Keyboard Commands  
Type text and press keys naturally:

| Command | Purpose | Example |
|---------|---------|---------|
| `TYPE` | Type text or variable | `TYPE "Hello"` or `TYPE $username` |
| `PRESS` | Press special keys | `PRESS Tab` or `PRESS Enter` |
| `CLEAR` | Clear input field | `CLEAR \`#search\`` |
| `SET` | Set input value directly | `SET \`#email\` "user@example.com"` |

### 🔀 Control Flow
Add logic and repetition to your scripts:

| Command | Purpose | Example |
|---------|---------|---------|
| `IF` | Conditional execution | `IF (EXISTS \`#popup\`) THEN CLICK \`#close\`` |
| `REPEAT` | Loop commands | `REPEAT (SCROLL DOWN 300, 5)` |

### 💾 Variables & Advanced
Store data and execute custom code:

| Command | Purpose | Example |
|---------|---------|---------|
| `SETVAR` | Create variable | `SETVAR email = "test@example.com"` |
| `EVAL` | Execute JavaScript | `EVAL \`console.log('Hello')\`` |

## Real-World Examples

### Example 1: Login Flow
```c4a
# Complete login automation
GO https://myapp.com/login

# Wait for page to load
WAIT `#login-form` 5

# Fill credentials
CLICK `#email`
TYPE "user@example.com"
PRESS Tab
TYPE "mypassword"

# Submit form
CLICK `button[type="submit"]`

# Wait for dashboard
WAIT `.dashboard` 10
```

### Example 2: E-commerce Shopping
```c4a
# Shopping automation with variables
SETVAR product = "laptop"
SETVAR budget = "1000"

GO https://shop.example.com
WAIT `#search-box` 3

# Search for product
TYPE $product
PRESS Enter
WAIT `.product-list` 5

# Filter by price
CLICK `.price-filter`
SET `#max-price` $budget
CLICK `.apply-filters`

# Select first result
WAIT `.product-item` 3
CLICK `.product-item:first-child`
```

### Example 3: Form Automation with Conditions
```c4a
# Smart form filling with error handling
GO https://forms.example.com

# Check if user is already logged in
IF (EXISTS `.user-menu`) THEN GO https://forms.example.com/new
IF (NOT EXISTS `.user-menu`) THEN CLICK `#login-link`

# Fill form
WAIT `#contact-form` 5
SET `#name` "John Doe"
SET `#email` "john@example.com"
SET `#message` "Hello from C4A-Script!"

# Handle popup if it appears
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept-cookies`

# Submit
CLICK `#submit-button`
WAIT `.success-message` 10
```

## Visual Programming with Blockly

C4A-Script includes a powerful visual programming interface built on Google Blockly. Perfect for:

- **Non-programmers** who want to create automation
- **Rapid prototyping** of automation workflows  
- **Educational environments** for teaching automation concepts
- **Collaborative development** where visual representation helps communication

### Features:
- **Drag & Drop Interface**: Build scripts by connecting blocks
- **Real-time Sync**: Changes in visual mode instantly update the text script
- **Smart Block Types**: Blocks are categorized by function (Navigation, Actions, etc.)
- **Error Prevention**: Visual connections prevent syntax errors
- **Comment Support**: Add visual comment blocks for documentation

Try the visual editor in our [live demo](https://docs.crawl4ai.com/c4a-script/demo) or [local tutorial](/examples/c4a_script/tutorial/).

## Advanced Features

### Recording Mode
The tutorial interface includes a recording feature that watches your browser interactions and automatically generates C4A-Script commands:

1. Click "Record" in the tutorial interface
2. Perform actions in the browser preview
3. Watch as C4A-Script commands are generated in real-time
4. Edit and refine the generated script

### Error Handling and Debugging
C4A-Script provides clear error messages and debugging information:

```c4a
# Use comments for debugging
# This will wait up to 10 seconds for the element
WAIT `#slow-loading-element` 10

# Check if element exists before clicking
IF (EXISTS `#optional-button`) THEN CLICK `#optional-button`

# Use EVAL for custom debugging
EVAL `console.log("Current page title:", document.title)`
```

### Integration with Crawl4AI
C4A-Script integrates seamlessly with Crawl4AI's web crawling capabilities:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

# Use C4A-Script for interaction before crawling
script = """
GO https://example.com
CLICK `#load-more-content`
WAIT `.dynamic-content` 5
"""

config = CrawlerRunConfig(
    js_code=script,
    wait_for=".dynamic-content"
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com", config=config)
    print(result.markdown)
```

## Best Practices

### 1. Always Wait for Elements
```c4a
# Bad: Clicking immediately
CLICK `#button`

# Good: Wait for element to appear
WAIT `#button` 5
CLICK `#button`
```

### 2. Use Descriptive Comments
```c4a
# Login to user account
GO https://myapp.com/login
WAIT `#login-form` 5

# Enter credentials
TYPE "user@example.com"
PRESS Tab
TYPE "password123"

# Submit and wait for redirect
CLICK `#submit-button`
WAIT `.dashboard` 10
```

### 3. Handle Variable Conditions
```c4a
# Handle different page states
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept-cookies`
IF (EXISTS `.popup-modal`) THEN CLICK `.close-modal`

# Proceed with main workflow
CLICK `#main-action`
```

### 4. Use Variables for Reusability
```c4a
# Define once, use everywhere
SETVAR base_url = "https://myapp.com"
SETVAR test_email = "test@example.com"

GO $base_url/login
SET `#email` $test_email
```

## Getting Help

- **📖 [Complete Examples](/examples/c4a_script/)** - Real-world automation scripts
- **🎮 [Interactive Tutorial](/examples/c4a_script/tutorial/)** - Hands-on learning environment  
- **📋 [API Reference](/api/c4a-script-reference/)** - Detailed command documentation
- **🌐 [Live Demo](https://docs.crawl4ai.com/c4a-script/demo)** - Try it in your browser

## What's Next?

Ready to dive deeper? Check out:

1. **[API Reference](/api/c4a-script-reference/)** - Complete command documentation
2. **[Tutorial Examples](/examples/c4a_script/)** - Copy-paste ready scripts
3. **[Local Tutorial Setup](/examples/c4a_script/tutorial/)** - Run the full development environment

C4A-Script makes web automation accessible to everyone. Whether you're a developer automating tests, a designer creating interactive demos, or a business user streamlining repetitive tasks, C4A-Script has the tools you need.

*Start automating today - your future self will thank you!* 🚀