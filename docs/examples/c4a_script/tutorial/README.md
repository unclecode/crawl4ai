# C4A-Script Interactive Tutorial

Welcome to the C4A-Script Interactive Tutorial! This hands-on tutorial teaches you how to write web automation scripts using C4A-Script, a domain-specific language for Crawl4AI.

## 🚀 Quick Start

### 1. Start the Tutorial Server

```bash
cd docs/examples/c4a_script/tutorial
python server.py
```

Then open your browser to: http://localhost:8080

### 2. Try Your First Script

```c4a
# Basic interaction
GO playground/
WAIT `body` 2
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept`
CLICK `#start-tutorial`
```

## 📚 What You'll Learn

### Basic Commands
- **Navigation**: `GO url`
- **Waiting**: `WAIT selector timeout` or `WAIT seconds`
- **Clicking**: `CLICK selector`
- **Typing**: `TYPE "text"`
- **Scrolling**: `SCROLL DOWN/UP amount`

### Control Flow
- **Conditionals**: `IF (condition) THEN action`
- **Loops**: `REPEAT (action, condition)`
- **Procedures**: Define reusable command sequences

### Advanced Features
- **JavaScript evaluation**: `EVAL code`
- **Variables**: `SET name = "value"`
- **Complex selectors**: CSS selectors in backticks

## 🎮 Interactive Playground Features

The tutorial includes a fully interactive web app with:

### 1. **Authentication System**
- Login form with validation
- Session management
- Protected content

### 2. **Dynamic Content**
- Infinite scroll products
- Pagination controls
- Load more buttons

### 3. **Complex Forms**
- Multi-step wizards
- Dynamic field visibility
- Form validation

### 4. **Interactive Elements**
- Tabs and accordions
- Modals and popups
- Expandable content

### 5. **Data Tables**
- Sortable columns
- Search functionality
- Export options

## 🛠️ Tutorial Features

### Live Code Editor
- Syntax highlighting
- Real-time compilation
- Error messages with suggestions

### JavaScript Output Viewer
- See generated JavaScript code
- Edit and test JS directly
- Understand the compilation

### Visual Execution
- Step-by-step progress
- Element highlighting
- Console output

### Example Scripts
Load pre-written examples demonstrating:
- Cookie banner handling
- Login workflows
- Infinite scroll automation
- Multi-step form completion
- Complex interaction sequences

## 📖 Tutorial Sections

### 1. Getting Started
Learn basic commands and syntax:
```c4a
GO https://example.com
WAIT `.content` 5
CLICK `.button`
```

### 2. Handling Dynamic Content
Master waiting strategies and conditionals:
```c4a
IF (EXISTS `.popup`) THEN CLICK `.close`
WAIT `.results` 10
```

### 3. Form Automation
Fill and submit forms:
```c4a
CLICK `#email`
TYPE "user@example.com"
CLICK `button[type="submit"]`
```

### 4. Advanced Workflows
Build complex automation flows:
```c4a
PROC login
  CLICK `#username`
  TYPE $username
  CLICK `#password`
  TYPE $password
  CLICK `#login-btn`
ENDPROC

SET username = "demo"
SET password = "pass123"
login
```

## 🎯 Practice Challenges

### Challenge 1: Cookie & Popups
Handle the cookie banner and newsletter popup that appear on page load.

### Challenge 2: Complete Login
Successfully log into the application using the demo credentials.

### Challenge 3: Load All Products
Use infinite scroll to load all 100 products in the catalog.

### Challenge 4: Multi-step Survey
Complete the entire multi-step survey form.

### Challenge 5: Full Workflow
Create a script that logs in, browses products, and exports data.

## 💡 Tips & Tricks

### 1. Use Specific Selectors
```c4a
# Good - specific
CLICK `button.submit-order`

# Bad - too generic
CLICK `button`
```

### 2. Always Handle Popups
```c4a
# Check for common popups
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept`
IF (EXISTS `.newsletter-modal`) THEN CLICK `.close`
```

### 3. Add Appropriate Waits
```c4a
# Wait for elements before interacting
WAIT `.form` 5
CLICK `#submit`
```

### 4. Use Procedures for Reusability
```c4a
PROC handle_popups
  IF (EXISTS `.popup`) THEN CLICK `.close`
  IF (EXISTS `.cookie-banner`) THEN CLICK `.accept`
ENDPROC

# Use anywhere
handle_popups
```

## 🔧 Troubleshooting

### Common Issues

1. **"Element not found"**
   - Add a WAIT before clicking
   - Check selector specificity
   - Verify element exists with IF

2. **"Timeout waiting for selector"**
   - Increase timeout value
   - Check if element is dynamically loaded
   - Verify selector is correct

3. **"Missing THEN keyword"**
   - All IF statements need THEN
   - Format: `IF (condition) THEN action`

## 🚀 Using with Crawl4AI

Once you've mastered C4A-Script in the tutorial, use it with Crawl4AI:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

config = CrawlerRunConfig(
    url="https://example.com",
    c4a_script="""
    WAIT `.content` 5
    IF (EXISTS `.load-more`) THEN CLICK `.load-more`
    WAIT `.new-content` 3
    """
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(config=config)
```

## 📝 Example Scripts

Check the `scripts/` folder for complete examples:
- `01-basic-interaction.c4a` - Getting started
- `02-login-flow.c4a` - Authentication
- `03-infinite-scroll.c4a` - Dynamic content
- `04-multi-step-form.c4a` - Complex forms
- `05-complex-workflow.c4a` - Full automation

## 🤝 Contributing

Found a bug or have a suggestion? Please open an issue on GitHub!

---

Happy automating with C4A-Script! 🎉