# C4A-Script Interactive Tutorial

A comprehensive web-based tutorial for learning and experimenting with C4A-Script - Crawl4AI's visual web automation language.

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Running the Tutorial

1. **Clone and Navigate**
   ```bash
   git clone https://github.com/unclecode/crawl4ai.git
   cd crawl4ai/docs/examples/c4a_script/tutorial/
   ```

2. **Install Dependencies**
   ```bash
   pip install flask
   ```

3. **Launch the Server**
   ```bash
   python server.py
   ```

4. **Open in Browser**
   ```
   http://localhost:8080
   ```

**🌐 Try Online**: [Live Demo](https://docs.crawl4ai.com/c4a-script/demo)

### 2. Try Your First Script

```c4a
# Basic interaction
GO playground/
WAIT `body` 2
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept`
CLICK `#start-tutorial`
```

## 🎯 What You'll Learn

### Core Features
- **📝 Text Editor**: Write C4A-Script with syntax highlighting
- **🧩 Visual Editor**: Build scripts using drag-and-drop Blockly interface  
- **🎬 Recording Mode**: Capture browser actions and auto-generate scripts
- **⚡ Live Execution**: Run scripts in real-time with instant feedback
- **📊 Timeline View**: Visualize and edit automation steps

## 📚 Tutorial Content

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

## 🏗️ Developer Guide

### Project Architecture

```
tutorial/
├── server.py              # Flask application server
├── assets/               # Tutorial-specific assets
│   ├── app.js            # Main application logic
│   ├── c4a-blocks.js     # Custom Blockly blocks
│   ├── c4a-generator.js  # Code generation
│   ├── blockly-manager.js # Blockly integration
│   └── styles.css        # Main styling
├── playground/           # Interactive demo environment
│   ├── index.html        # Demo web application
│   ├── app.js           # Demo app logic
│   └── styles.css       # Demo styling
├── scripts/             # Example C4A scripts
└── index.html           # Main tutorial interface
```

### Key Components

#### 1. TutorialApp (`assets/app.js`)
Main application controller managing:
- Code editor integration (CodeMirror)
- Script execution and browser preview
- Tutorial navigation and lessons
- State management and persistence

#### 2. BlocklyManager (`assets/blockly-manager.js`)
Visual programming interface:
- Custom C4A-Script block definitions
- Bidirectional sync between visual blocks and text
- Real-time code generation
- Dark theme integration

#### 3. Recording System
Powers the recording functionality:
- Browser event capture
- Smart event grouping and filtering
- Automatic C4A-Script generation
- Timeline visualization

### Customization

#### Adding New Commands
1. **Define Block** (`assets/c4a-blocks.js`)
2. **Add Generator** (`assets/c4a-generator.js`)
3. **Update Parser** (`assets/blockly-manager.js`)

#### Themes and Styling
- Main styles: `assets/styles.css`
- Theme variables: CSS custom properties
- Dark mode: Auto-applied based on system preference

### Configuration
```python
# server.py configuration
PORT = 8080
DEBUG = True
THREADED = True
```

### API Endpoints
- `GET /` - Main tutorial interface
- `GET /playground/` - Interactive demo environment
- `POST /execute` - Script execution endpoint
- `GET /examples/<script>` - Load example scripts

## 🔧 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Kill existing process
lsof -ti:8080 | xargs kill -9
# Or use different port
python server.py --port 8081
```

**Blockly Not Loading**
- Check browser console for JavaScript errors
- Verify all static files are served correctly
- Ensure proper script loading order

**Recording Issues**
- Verify iframe permissions
- Check cross-origin communication
- Ensure event listeners are attached

### Debug Mode
Enable detailed logging by setting `DEBUG = True` in `assets/app.js`

## 📚 Additional Resources

- **[C4A-Script Documentation](../../md_v2/core/c4a-script.md)** - Complete language guide
- **[API Reference](../../md_v2/api/c4a-script-reference.md)** - Detailed command documentation
- **[Live Demo](https://docs.crawl4ai.com/c4a-script/demo)** - Try without installation
- **[Example Scripts](../)** - More automation examples

## 🤝 Contributing

### Bug Reports
1. Check existing issues on GitHub
2. Provide minimal reproduction steps
3. Include browser and system information
4. Add relevant console logs

### Feature Requests
1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Test thoroughly with different browsers
4. Update documentation
5. Submit pull request

### Code Style
- Use consistent indentation (2 spaces for JS, 4 for Python)
- Add comments for complex logic
- Follow existing naming conventions
- Test with multiple browsers

---

**Happy Automating!** 🎉

Need help? Check our [documentation](https://docs.crawl4ai.com) or open an issue on [GitHub](https://github.com/unclecode/crawl4ai).