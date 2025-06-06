# C4A-Script Language Documentation

C4A-Script (Crawl4AI Script) is a simple, powerful language for web automation. Write human-readable commands that compile to JavaScript for browser automation.

## Quick Start

```python
from c4a_compile import compile

# Write your script
script = """
GO https://example.com
WAIT `#content` 5
CLICK `button.submit`
"""

# Compile to JavaScript
result = compile(script)

if result.success:
    # Use with Crawl4AI
    config = CrawlerRunConfig(js_code=result.js_code)
else:
    print(f"Error at line {result.first_error.line}: {result.first_error.message}")
```

## Language Basics

- **One command per line**
- **Selectors in backticks**: `` `button.submit` ``
- **Strings in quotes**: `"Hello World"`
- **Variables with $**: `$username`
- **Comments with #**: `# This is a comment`

## Commands Reference

### Navigation

```c4a
GO https://example.com          # Navigate to URL
RELOAD                          # Reload current page
BACK                            # Go back in history
FORWARD                         # Go forward in history
```

### Waiting

```c4a
WAIT 3                          # Wait 3 seconds
WAIT `#content` 10              # Wait for element (max 10 seconds)
WAIT "Loading complete" 5       # Wait for text to appear
```

### Mouse Actions

```c4a
CLICK `button.submit`           # Click element
DOUBLE_CLICK `.item`            # Double-click element
RIGHT_CLICK `#menu`             # Right-click element
CLICK 100 200                   # Click at coordinates

MOVE 500 300                    # Move mouse to position
DRAG 100 100 500 300           # Drag from one point to another

SCROLL DOWN 500                 # Scroll down 500 pixels
SCROLL UP                       # Scroll up (default 500px)
SCROLL LEFT 200                 # Scroll left 200 pixels
SCROLL RIGHT                    # Scroll right
```

### Keyboard

```c4a
TYPE "hello@example.com"        # Type text
TYPE $email                     # Type variable value

PRESS Tab                       # Press and release key
PRESS Enter
PRESS Escape

KEY_DOWN Shift                  # Hold key down
KEY_UP Shift                    # Release key
```

### Control Flow

#### IF-THEN-ELSE

```c4a
# Check if element exists
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept`
IF (EXISTS `#user`) THEN CLICK `.logout` ELSE CLICK `.login`

# JavaScript conditions
IF (`window.innerWidth < 768`) THEN CLICK `.mobile-menu`
IF (`document.querySelectorAll('.item').length > 10`) THEN SCROLL DOWN
```

#### REPEAT

```c4a
# Repeat fixed number of times
REPEAT (CLICK `.next`, 5)

# Repeat based on JavaScript expression
REPEAT (SCROLL DOWN 300, `document.querySelectorAll('.item').length`)

# Repeat while condition is true (like while loop)
REPEAT (CLICK `.load-more`, `document.querySelector('.load-more') !== null`)
```

### Variables & JavaScript

```c4a
# Set variables
SET username = "john@example.com"
SET count = "10"

# Use variables
TYPE $username

# Execute JavaScript
EVAL `console.log('Hello')`
EVAL `localStorage.setItem('key', 'value')`
```

### Procedures

```c4a
# Define reusable procedure
PROC login
  CLICK `#email`
  TYPE $email
  CLICK `#password`  
  TYPE $password
  CLICK `button[type="submit"]`
ENDPROC

# Use procedure
SET email = "user@example.com"
SET password = "secure123"
login

# Procedures work with control flow
IF (EXISTS `.login-form`) THEN login
REPEAT (process_item, 10)
```

## API Reference

### Functions

```python
from c4a_compile import compile, validate, compile_file

# Compile script
result = compile("GO https://example.com")

# Validate syntax only
result = validate(script)

# Compile from file
result = compile_file("script.c4a")
```

### Working with Results

```python
result = compile(script)

if result.success:
    # Access generated JavaScript
    js_code = result.js_code  # List[str]
    
    # Use with Crawl4AI
    config = CrawlerRunConfig(js_code=js_code)
else:
    # Handle errors
    error = result.first_error
    print(f"Line {error.line}, Column {error.column}: {error.message}")
    
    # Get suggestions
    for suggestion in error.suggestions:
        print(f"Fix: {suggestion.message}")
    
    # Get JSON for UI integration
    error_json = result.to_json()
```

## Examples

### Basic Automation

```c4a
GO https://example.com
WAIT `#content` 5
IF (EXISTS `.cookie-notice`) THEN CLICK `.accept`
CLICK `.main-button`
```

### Form Filling

```c4a
SET email = "user@example.com"
SET message = "Hello, I need help with my order"

GO https://example.com/contact
WAIT `form` 5
CLICK `input[name="email"]`
TYPE $email
CLICK `textarea[name="message"]`
TYPE $message
CLICK `button[type="submit"]`
WAIT "Thank you" 10
```

### Dynamic Content Loading

```c4a
GO https://shop.example.com
WAIT `.product-list` 10

# Load all products
REPEAT (CLICK `.load-more`, `document.querySelector('.load-more') !== null`)

# Extract data
EVAL `
  const count = document.querySelectorAll('.product').length;
  console.log('Found ' + count + ' products');
`
```

### Smart Navigation

```c4a
PROC handle_popups
  IF (EXISTS `.cookie-banner`) THEN CLICK `.accept-all`
  IF (EXISTS `.newsletter-modal`) THEN CLICK `.close`
ENDPROC

GO https://example.com
handle_popups
WAIT `.main-content` 5

# Navigate based on login state
IF (EXISTS `.user-avatar`) THEN CLICK `.dashboard` ELSE CLICK `.login`
```

## Error Messages

C4A-Script provides clear, helpful error messages:

```
============================================================
Syntax Error [E001]
============================================================
Location: Line 3, Column 23
Error: Missing 'THEN' keyword after IF condition

Code:
    3 | IF (EXISTS `.button`) CLICK `.button`
      |                       ^

Suggestions:
  1. Add 'THEN' after the condition
============================================================
```

Common error codes:
- **E001**: Missing 'THEN' keyword
- **E002**: Missing closing parenthesis
- **E003**: Missing comma in REPEAT
- **E004**: Missing ENDPROC
- **E005**: Undefined procedure
- **E006**: Missing backticks for selector

## Best Practices

1. **Always use backticks for selectors**: `` CLICK `button` `` not `CLICK button`
2. **Check element existence before interaction**: `IF (EXISTS `.modal`) THEN CLICK `.close`
3. **Set appropriate wait times**: Don't wait too long or too short
4. **Use procedures for repeated actions**: Keep your code DRY
5. **Add comments for clarity**: `# Check if user is logged in`

## Integration with Crawl4AI

```python
from c4a_compile import compile
from crawl4ai import CrawlerRunConfig, WebCrawler

# Compile your script
script = """
GO https://example.com
WAIT `.content` 5
CLICK `.load-more`
"""

result = compile(script)

if result.success:
    # Create crawler config with compiled JS
    config = CrawlerRunConfig(
        js_code=result.js_code,
        wait_for="css:.results"
    )
    
    # Run crawler
    async with WebCrawler() as crawler:
        result = await crawler.arun(config=config)
```

That's it! You're ready to automate the web with C4A-Script.