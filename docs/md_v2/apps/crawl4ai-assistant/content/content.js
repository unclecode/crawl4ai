// Content script for Crawl4AI Assistant
class SchemaBuilder {
  constructor() {
    this.mode = null;
    this.container = null;
    this.fields = [];
    this.overlay = null;
    this.toolbar = null;
    this.highlightBox = null;
    this.selectedElements = new Set();
    this.isPaused = false;
    this.codeModal = null;
    
    this.handleMouseMove = this.handleMouseMove.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.handleKeyPress = this.handleKeyPress.bind(this);
  }

  start() {
    this.mode = 'container';
    this.createOverlay();
    this.createToolbar();
    this.attachEventListeners();
    this.updateToolbar();
  }

  stop() {
    this.detachEventListeners();
    this.overlay?.remove();
    this.toolbar?.remove();
    this.highlightBox?.remove();
    this.removeAllHighlights();
    this.mode = null;
    this.container = null;
    this.fields = [];
    this.selectedElements.clear();
  }

  createOverlay() {
    // Create highlight box
    this.highlightBox = document.createElement('div');
    this.highlightBox.className = 'c4ai-highlight-box';
    document.body.appendChild(this.highlightBox);
  }

  createToolbar() {
    this.toolbar = document.createElement('div');
    this.toolbar.className = 'c4ai-toolbar';
    this.toolbar.innerHTML = `
      <div class="c4ai-toolbar-titlebar">
        <div class="c4ai-titlebar-dots">
          <button class="c4ai-dot c4ai-dot-close" id="c4ai-close"></button>
          <button class="c4ai-dot c4ai-dot-minimize"></button>
          <button class="c4ai-dot c4ai-dot-maximize"></button>
        </div>
        <img src="${chrome.runtime.getURL('icons/icon-16.png')}" class="c4ai-titlebar-icon" alt="Crawl4AI">
        <div class="c4ai-titlebar-title">Crawl4AI Schema Builder</div>
      </div>
      <div class="c4ai-toolbar-content">
        <div class="c4ai-toolbar-status">
          <div class="c4ai-status-item">
            <span class="c4ai-status-label">Mode:</span>
            <span class="c4ai-status-value" id="c4ai-mode">Select Container</span>
          </div>
          <div class="c4ai-status-item">
            <span class="c4ai-status-label">Container:</span>
            <span class="c4ai-status-value" id="c4ai-container">Not selected</span>
          </div>
        </div>
        <div class="c4ai-fields-list" id="c4ai-fields-list" style="display: none;">
          <div class="c4ai-fields-header">Selected Fields:</div>
          <ul class="c4ai-fields-items" id="c4ai-fields-items"></ul>
        </div>
        <div class="c4ai-toolbar-hint" id="c4ai-hint">
          Click on a container element (e.g., product card, article, etc.)
        </div>
        <div class="c4ai-toolbar-actions">
          <button id="c4ai-pause" class="c4ai-action-btn c4ai-pause-btn">
            <span class="c4ai-pause-icon">⏸</span> Pause
          </button>
          <button id="c4ai-generate" class="c4ai-action-btn c4ai-generate-btn">
            <span class="c4ai-generate-icon">⚡</span> Generate Code
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(this.toolbar);
    
    // Add event listeners for toolbar buttons
    document.getElementById('c4ai-pause').addEventListener('click', () => this.togglePause());
    document.getElementById('c4ai-generate').addEventListener('click', () => this.stopAndGenerate());
    document.getElementById('c4ai-close').addEventListener('click', () => this.stop());
    
    // Make toolbar draggable
    this.makeDraggable(this.toolbar);
  }

  attachEventListeners() {
    document.addEventListener('mousemove', this.handleMouseMove, true);
    document.addEventListener('click', this.handleClick, true);
    document.addEventListener('keydown', this.handleKeyPress, true);
  }

  detachEventListeners() {
    document.removeEventListener('mousemove', this.handleMouseMove, true);
    document.removeEventListener('click', this.handleClick, true);
    document.removeEventListener('keydown', this.handleKeyPress, true);
  }

  handleMouseMove(e) {
    if (this.isPaused) return;
    
    const element = document.elementFromPoint(e.clientX, e.clientY);
    if (element && !this.isOurElement(element)) {
      this.highlightElement(element);
    }
  }

  handleClick(e) {
    if (this.isPaused) return;
    
    const element = e.target;
    
    if (this.isOurElement(element)) {
      return;
    }

    e.preventDefault();
    e.stopPropagation();

    if (this.mode === 'container') {
      this.selectContainer(element);
    } else if (this.mode === 'field') {
      this.selectField(element);
    }
  }

  handleKeyPress(e) {
    if (e.key === 'Escape') {
      this.stop();
    }
  }

  isOurElement(element) {
    return element.classList.contains('c4ai-highlight-box') ||
           element.classList.contains('c4ai-toolbar') ||
           element.closest('.c4ai-toolbar') ||
           element.closest('.c4ai-field-dialog') ||
           element.closest('.c4ai-code-modal');
  }

  makeDraggable(element) {
    let isDragging = false;
    let startX, startY, initialX, initialY;
    
    const titlebar = element.querySelector('.c4ai-toolbar-titlebar');
    
    titlebar.addEventListener('mousedown', (e) => {
      // Don't drag if clicking on buttons
      if (e.target.classList.contains('c4ai-dot')) return;
      
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      
      const rect = element.getBoundingClientRect();
      initialX = rect.left;
      initialY = rect.top;
      
      element.style.transition = 'none';
      titlebar.style.cursor = 'grabbing';
    });
    
    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      
      const deltaX = e.clientX - startX;
      const deltaY = e.clientY - startY;
      
      element.style.left = `${initialX + deltaX}px`;
      element.style.top = `${initialY + deltaY}px`;
      element.style.right = 'auto';
    });
    
    document.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        element.style.transition = '';
        titlebar.style.cursor = 'grab';
      }
    });
  }

  togglePause() {
    this.isPaused = !this.isPaused;
    const pauseBtn = document.getElementById('c4ai-pause');
    if (this.isPaused) {
      pauseBtn.innerHTML = '<span class="c4ai-play-icon">▶</span> Resume';
      pauseBtn.classList.add('c4ai-paused');
      this.highlightBox.style.display = 'none';
    } else {
      pauseBtn.innerHTML = '<span class="c4ai-pause-icon">⏸</span> Pause';
      pauseBtn.classList.remove('c4ai-paused');
    }
  }

  stopAndGenerate() {
    if (!this.container || this.fields.length === 0) {
      alert('Please select a container and at least one field before generating code.');
      return;
    }
    
    const code = this.generateCode();
    this.showCodeModal(code);
  }

  highlightElement(element) {
    const rect = element.getBoundingClientRect();
    this.highlightBox.style.cssText = `
      left: ${rect.left + window.scrollX}px;
      top: ${rect.top + window.scrollY}px;
      width: ${rect.width}px;
      height: ${rect.height}px;
      display: block;
    `;

    if (this.mode === 'container') {
      this.highlightBox.className = 'c4ai-highlight-box c4ai-container-mode';
    } else {
      this.highlightBox.className = 'c4ai-highlight-box c4ai-field-mode';
    }
  }

  selectContainer(element) {
    // Remove previous container highlight
    if (this.container) {
      this.container.element.classList.remove('c4ai-selected-container');
    }

    this.container = {
      element: element,
      html: element.outerHTML,
      selector: this.generateSelector(element),
      tagName: element.tagName.toLowerCase()
    };

    element.classList.add('c4ai-selected-container');
    this.mode = 'field';
    this.updateToolbar();
    this.updateStats();
  }

  selectField(element) {
    // Don't select the container itself
    if (element === this.container.element) {
      return;
    }

    // Check if already selected - if so, deselect it
    if (this.selectedElements.has(element)) {
      this.deselectField(element);
      return;
    }

    // Must be inside the container
    if (!this.container.element.contains(element)) {
      return;
    }

    this.showFieldDialog(element);
  }

  deselectField(element) {
    // Remove from fields array
    this.fields = this.fields.filter(f => f.element !== element);
    
    // Remove from selected elements set
    this.selectedElements.delete(element);
    
    // Remove visual selection
    element.classList.remove('c4ai-selected-field');
    
    // Update UI
    this.updateToolbar();
    this.updateStats();
  }

  showFieldDialog(element) {
    const dialog = document.createElement('div');
    dialog.className = 'c4ai-field-dialog';
    
    const rect = element.getBoundingClientRect();
    dialog.style.cssText = `
      left: ${rect.left + window.scrollX}px;
      top: ${rect.bottom + window.scrollY + 10}px;
    `;

    dialog.innerHTML = `
      <div class="c4ai-field-dialog-content">
        <h4>Name this field:</h4>
        <input type="text" id="c4ai-field-name" placeholder="e.g., title, price, description" autofocus>
        <div class="c4ai-field-preview">
          <strong>Content:</strong> ${element.textContent.trim().substring(0, 50)}...
        </div>
        <div class="c4ai-field-actions">
          <button id="c4ai-field-save">Save</button>
          <button id="c4ai-field-cancel">Cancel</button>
        </div>
      </div>
    `;

    document.body.appendChild(dialog);

    const input = dialog.querySelector('#c4ai-field-name');
    const saveBtn = dialog.querySelector('#c4ai-field-save');
    const cancelBtn = dialog.querySelector('#c4ai-field-cancel');

    const save = () => {
      const fieldName = input.value.trim();
      if (fieldName) {
        this.fields.push({
          name: fieldName,
          value: element.textContent.trim(),
          element: element,
          selector: this.generateSelector(element, this.container.element)
        });
        
        element.classList.add('c4ai-selected-field');
        this.selectedElements.add(element);
        this.updateToolbar();
        this.updateStats();
      }
      dialog.remove();
    };

    const cancel = () => {
      dialog.remove();
    };

    saveBtn.addEventListener('click', save);
    cancelBtn.addEventListener('click', cancel);
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') save();
      if (e.key === 'Escape') cancel();
    });

    input.focus();
  }

  generateSelector(element, context = document) {
    // Try to generate a robust selector
    if (element.id) {
      return `#${CSS.escape(element.id)}`;
    }

    // Check for data attributes (most stable)
    const dataAttrs = ['data-testid', 'data-id', 'data-test', 'data-cy'];
    for (const attr of dataAttrs) {
      const value = element.getAttribute(attr);
      if (value) {
        return `[${attr}="${value}"]`;
      }
    }

    // Check for aria-label
    if (element.getAttribute('aria-label')) {
      return `[aria-label="${element.getAttribute('aria-label')}"]`;
    }

    // Try semantic HTML elements with text
    const tagName = element.tagName.toLowerCase();
    if (['button', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName)) {
      const text = element.textContent.trim();
      if (text && text.length < 50) {
        // Use tag name with partial text match
        return `${tagName}`;
      }
    }

    // Check for simple, non-utility classes
    const classes = Array.from(element.classList)
      .filter(c => !c.startsWith('c4ai-')) // Exclude our classes
      .filter(c => !c.includes('[') && !c.includes('(') && !c.includes(':')) // Exclude utility classes
      .filter(c => c.length < 30); // Exclude very long classes
    
    if (classes.length > 0 && classes.length <= 3) {
      const selector = classes.map(c => `.${CSS.escape(c)}`).join('');
      try {
        if (context.querySelectorAll(selector).length === 1) {
          return selector;
        }
      } catch (e) {
        // Invalid selector, continue
      }
    }

    // Use nth-child with simple parent tag
    const parent = element.parentElement;
    if (parent && parent !== context) {
      const siblings = Array.from(parent.children);
      const index = siblings.indexOf(element) + 1;
      // Just use parent tag name to avoid recursion
      const parentTag = parent.tagName.toLowerCase();
      return `${parentTag} > ${tagName}:nth-child(${index})`;
    }

    // Final fallback
    return tagName;
  }

  updateToolbar() {
    document.getElementById('c4ai-mode').textContent = 
      this.mode === 'container' ? 'Select Container' : 'Select Fields';
    
    document.getElementById('c4ai-container').textContent = 
      this.container ? `${this.container.tagName} ✓` : 'Not selected';

    // Update fields list
    const fieldsList = document.getElementById('c4ai-fields-list');
    const fieldsItems = document.getElementById('c4ai-fields-items');
    
    if (this.fields.length > 0) {
      fieldsList.style.display = 'block';
      fieldsItems.innerHTML = this.fields.map(field => `
        <li class="c4ai-field-item">
          <span class="c4ai-field-name">${field.name}</span>
          <span class="c4ai-field-value">${field.value.substring(0, 30)}${field.value.length > 30 ? '...' : ''}</span>
        </li>
      `).join('');
    } else {
      fieldsList.style.display = 'none';
    }

    const hint = document.getElementById('c4ai-hint');
    if (this.mode === 'container') {
      hint.textContent = 'Click on a container element (e.g., product card, article, etc.)';
    } else if (this.fields.length === 0) {
      hint.textContent = 'Click on fields inside the container to extract (title, price, etc.)';
    } else {
      hint.innerHTML = `Continue selecting fields or click <strong>Stop & Generate</strong> to finish.`;
    }
  }

  updateStats() {
    chrome.runtime.sendMessage({
      action: 'updateStats',
      stats: {
        container: !!this.container,
        fields: this.fields.length
      }
    });
  }

  removeAllHighlights() {
    document.querySelectorAll('.c4ai-selected-container').forEach(el => {
      el.classList.remove('c4ai-selected-container');
    });
    document.querySelectorAll('.c4ai-selected-field').forEach(el => {
      el.classList.remove('c4ai-selected-field');
    });
  }

  generateCode() {
    const fieldDescriptions = this.fields.map(f => 
      `- ${f.name} (example: "${f.value.substring(0, 50)}...")`
    ).join('\n');

    return `#!/usr/bin/env python3
"""
Generated by Crawl4AI Chrome Extension
URL: ${window.location.href}
Generated: ${new Date().toISOString()}
"""

import asyncio
import json
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# HTML snippet of the selected container element
HTML_SNIPPET = """
${this.container.html}
"""

# Extraction query based on your field selections
EXTRACTION_QUERY = """
Create a JSON CSS extraction schema to extract the following fields:
${fieldDescriptions}

The schema should handle multiple ${this.container.tagName} elements on the page.
Each item should be extracted as a separate object in the results array.
"""

async def generate_schema():
    """Generate extraction schema using LLM"""
    print("🔧 Generating extraction schema...")
    
    try:
        # Generate the schema using Crawl4AI's built-in LLM integration
        schema = JsonCssExtractionStrategy.generate_schema(
            html=HTML_SNIPPET,
            query=EXTRACTION_QUERY,
        )
        
        # Save the schema for reuse
        schema_path = Path('generated_schema.json')
        with open(schema_path, 'w') as f:
            json.dump(schema, f, indent=2)
        
        print("✅ Schema generated successfully!")
        print(f"📄 Schema saved to: {schema_path}")
        print("\\nGenerated schema:")
        print(json.dumps(schema, indent=2))
        
        return schema
        
    except Exception as e:
        print(f"❌ Error generating schema: {e}")
        return None

async def test_extraction(url: str = "${window.location.href}"):
    """Test the generated schema on the actual webpage"""
    print("\\n🧪 Testing extraction on live webpage...")
    
    # Load the generated schema
    try:
        with open('generated_schema.json', 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print("❌ Schema file not found. Run generate_schema() first.")
        return
    
    # Configure browser
    browser_config = BrowserConfig(
        headless=True,
        verbose=False
    )
    
    # Configure extraction
    crawler_config = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(schema=schema)
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=crawler_config
        )
        
        if result.success and result.extracted_content:
            data = json.loads(result.extracted_content)
            print(f"\\n✅ Successfully extracted {len(data)} items!")
            
            # Save results
            with open('extracted_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            # Show sample results
            print("\\n📊 Sample results (first 2 items):")
            for i, item in enumerate(data[:2], 1):
                print(f"\\nItem {i}:")
                for key, value in item.items():
                    print(f"  {key}: {value}")
        else:
            print("❌ Extraction failed:", result.error_message)

if __name__ == "__main__":
    # Step 1: Generate the schema from HTML snippet
    asyncio.run(generate_schema())
    
    # Step 2: Test extraction on the live webpage
    # Uncomment the line below to test extraction:
    # asyncio.run(test_extraction())
    
    print("\\n🎯 Next steps:")
    print("1. Review the generated schema in 'generated_schema.json'")
    print("2. Uncomment the test_extraction() line to test on the live site")
    print("3. Use the schema in your Crawl4AI projects!")
`;

    return code;
  }

  showCodeModal(code) {
    // Create modal
    this.codeModal = document.createElement('div');
    this.codeModal.className = 'c4ai-code-modal';
    this.codeModal.innerHTML = `
      <div class="c4ai-code-modal-content">
        <div class="c4ai-code-modal-header">
          <h2>Generated Python Code</h2>
          <button class="c4ai-close-modal" id="c4ai-close-modal">✕</button>
        </div>
        <div class="c4ai-code-modal-body">
          <pre class="c4ai-code-block"><code class="language-python">${this.escapeHtml(code)}</code></pre>
        </div>
        <div class="c4ai-code-modal-footer">
          <button class="c4ai-action-btn c4ai-cloud-btn" id="c4ai-run-cloud" disabled>
            <span>☁️</span> Run on C4AI Cloud (Coming Soon)
          </button>
          <button class="c4ai-action-btn c4ai-download-btn" id="c4ai-download-code">
            <span>⬇</span> Download Code
          </button>
          <button class="c4ai-action-btn c4ai-copy-btn" id="c4ai-copy-code">
            <span>📋</span> Copy to Clipboard
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(this.codeModal);
    
    // Add event listeners
    document.getElementById('c4ai-close-modal').addEventListener('click', () => {
      this.codeModal.remove();
      this.codeModal = null;
      // Don't stop the capture session
    });
    
    document.getElementById('c4ai-download-code').addEventListener('click', () => {
      chrome.runtime.sendMessage({
        action: 'downloadCode',
        code: code,
        filename: `crawl4ai_schema_${Date.now()}.py`
      }, (response) => {
        if (response && response.success) {
          const btn = document.getElementById('c4ai-download-code');
          const originalHTML = btn.innerHTML;
          btn.innerHTML = '<span>✓</span> Downloaded!';
          setTimeout(() => {
            btn.innerHTML = originalHTML;
          }, 2000);
        } else {
          console.error('Download failed:', response?.error);
          alert('Download failed. Please check your browser settings.');
        }
      });
    });
    
    document.getElementById('c4ai-copy-code').addEventListener('click', () => {
      navigator.clipboard.writeText(code).then(() => {
        const btn = document.getElementById('c4ai-copy-code');
        btn.innerHTML = '<span>✓</span> Copied!';
        setTimeout(() => {
          btn.innerHTML = '<span>📋</span> Copy to Clipboard';
        }, 2000);
      });
    });
    
    // Apply syntax highlighting if possible
    this.applySyntaxHighlighting();
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  applySyntaxHighlighting() {
    // Simple Python syntax highlighting - using a different approach
    const codeElement = this.codeModal.querySelector('.language-python');
    const code = codeElement.textContent;
    
    // Split by lines to handle line-by-line
    const lines = code.split('\n');
    const highlightedLines = lines.map(line => {
      let highlightedLine = this.escapeHtml(line);
      
      // Skip if line is empty
      if (!highlightedLine.trim()) return highlightedLine;
      
      // Comments (lines starting with #)
      if (highlightedLine.trim().startsWith('#')) {
        return `<span class="c4ai-comment">${highlightedLine}</span>`;
      }
      
      // Triple quoted strings
      if (highlightedLine.includes('"""')) {
        highlightedLine = highlightedLine.replace(/(""".*?""")/g, '<span class="c4ai-string">$1</span>');
      }
      
      // Regular strings - single and double quotes
      highlightedLine = highlightedLine.replace(/(["'])([^"']*)\1/g, '<span class="c4ai-string">$1$2$1</span>');
      
      // Keywords - only highlight if not inside a string
      const keywords = ['import', 'from', 'async', 'def', 'await', 'try', 'except', 'with', 'as', 'for', 'if', 'else', 'elif', 'return', 'print', 'open', 'and', 'or', 'not', 'in', 'is', 'class', 'self', 'None', 'True', 'False', '__name__', '__main__'];
      
      keywords.forEach(keyword => {
        // Use word boundaries and lookahead/lookbehind to ensure we're not in a string
        const regex = new RegExp(`\\b(${keyword})\\b(?![^<]*</span>)`, 'g');
        highlightedLine = highlightedLine.replace(regex, '<span class="c4ai-keyword">$1</span>');
      });
      
      // Functions (word followed by parenthesis)
      highlightedLine = highlightedLine.replace(/\b([a-zA-Z_]\w*)\s*\(/g, '<span class="c4ai-function">$1</span>(');
      
      return highlightedLine;
    });
    
    codeElement.innerHTML = highlightedLines.join('\n');
  }
}

// Initialize
let schemaBuilder = null;

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.action) {
    case 'startSchemaCapture':
      if (!schemaBuilder) {
        schemaBuilder = new SchemaBuilder();
      }
      schemaBuilder.start();
      sendResponse({ success: true });
      break;
      
    case 'stopCapture':
      if (schemaBuilder) {
        schemaBuilder.stop();
        schemaBuilder = null;
      }
      sendResponse({ success: true });
      break;
      
    case 'generateCode':
      if (schemaBuilder) {
        const code = schemaBuilder.generateCode();
        schemaBuilder.showCodeModal(code);
      }
      sendResponse({ success: true });
      break;
  }
  
  return true;
});