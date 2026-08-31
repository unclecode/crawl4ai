# Crawl4AI Chrome Extension

Visual extraction tools for Crawl4AI - Click to extract data and content from any webpage!

## 🚀 Features

- **Click2Crawl**: Click on elements to build data extraction schemas instantly
- **Markdown Extraction**: Select elements and export as clean markdown
- **Script Builder (Alpha)**: Record browser actions to create automation scripts
- **Smart Element Selection**: Container and field selection with visual feedback
- **Code Generation**: Generates complete Python code for Crawl4AI
- **Beautiful Dark UI**: Consistent with Crawl4AI's design language

## 📦 Installation

### Method 1: Load Unpacked Extension (Recommended for Development)

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top right corner
3. Click "Load unpacked"
4. Select the `crawl4ai-assistant` folder
5. The extension icon (🚀🤖) will appear in your toolbar

### Method 2: Generate Icons First

If you want proper icons:

1. Open `icons/generate_icons.html` in your browser
2. Right-click each canvas and save as:
   - `icon-16.png`
   - `icon-48.png`
   - `icon-128.png`
3. Then follow Method 1 above

## 🎯 How to Use

### Using Click2Crawl

1. **Navigate to any website** you want to extract data from
2. **Click the Crawl4AI extension icon** in your toolbar
3. **Click "Click2Crawl"** to start the capture mode
4. **Select a container element**:
   - Hover over elements (they'll highlight in blue)
   - Click on a repeating container (e.g., product card, article block)
5. **Select fields within the container**:
   - Elements will now highlight in green
   - Click on each piece of data you want to extract
   - Name each field (e.g., "title", "price", "description")
6. **Test and Export**:
   - Click "Test Schema" to see extracted data instantly
   - Export as Python code, JSON schema, or markdown

### Running the Generated Code

The downloaded Python file contains:

```python
# 1. The HTML snippet of your selected container
HTML_SNIPPET = """..."""

# 2. The extraction query based on your selections
EXTRACTION_QUERY = """..."""

# 3. Functions to generate and test the schema
async def generate_schema():
    # Generates the extraction schema using LLM
    
async def test_extraction():
    # Tests the schema on the actual website
```

To use it:

1. Install Crawl4AI: `pip install crawl4ai`
2. Run the script: `python crawl4ai_schema_*.py`
3. The script will generate a `generated_schema.json` file
4. Use this schema in your Crawl4AI projects!

## 🎨 Visual Feedback

- **Blue dashed outline**: Container selection mode
- **Green dashed outline**: Field selection mode
- **Solid blue outline**: Selected container
- **Solid green outline**: Selected fields
- **Floating toolbar**: Shows current mode and selection status

## ⌨️ Keyboard Shortcuts

- **ESC**: Cancel current capture session

## 🔧 Technical Details

- Built with Manifest V3 for security and performance
- Pure client-side - no data sent to external servers
- Generates code that uses Crawl4AI's LLM integration
- Smart selector generation prioritizes stable attributes

## 🐛 Troubleshooting

### Extension doesn't load
- Make sure you're in Developer Mode
- Check the console for any errors
- Ensure all files are in the correct directories

### Can't select elements
- Some websites may block extensions
- Try refreshing the page
- Make sure you clicked "Schema Builder" first

### Generated code doesn't work
- Ensure you have Crawl4AI installed
- Check that you have an LLM API key configured
- Make sure the website structure hasn't changed

## 🤝 Contributing

This extension is part of the Crawl4AI project. Contributions are welcome!

- Report issues: [GitHub Issues](https://github.com/unclecode/crawl4ai/issues)
- Join discussion: [Discord](https://discord.gg/crawl4ai)

## 📄 License

Same as Crawl4AI - see main project for details.