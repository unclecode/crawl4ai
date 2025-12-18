class MarkdownExtraction {
  constructor() {
    this.selectedElements = new Set();
    this.highlightBoxes = new Map();
    this.selectionMode = false;
    this.toolbar = null;
    this.markdownPreviewModal = null;
    this.selectionCounter = 0;
    this.markdownConverter = null;
    this.contentAnalyzer = null;
    
    this.init();
  }
  
  async init() {
    // Initialize dependencies
    this.markdownConverter = new MarkdownConverter();
    this.contentAnalyzer = new ContentAnalyzer();
    
    this.createToolbar();
    this.setupEventListeners();
  }
  
  createToolbar() {
    // Create floating toolbar
    this.toolbar = document.createElement('div');
    this.toolbar.className = 'c4ai-c2c-toolbar';
    this.toolbar.innerHTML = `
      <div class="c4ai-toolbar-header">
        <div class="c4ai-toolbar-dots">
          <span class="c4ai-dot c4ai-dot-red"></span>
          <span class="c4ai-dot c4ai-dot-yellow"></span>
          <span class="c4ai-dot c4ai-dot-green"></span>
        </div>
        <span class="c4ai-toolbar-title">Markdown Extraction</span>
        <button class="c4ai-close-btn" title="Close">×</button>
      </div>
      <div class="c4ai-toolbar-content">
        <div class="c4ai-selection-info">
          <span class="c4ai-selection-count">0 elements selected</span>
          <button class="c4ai-clear-btn" title="Clear selection" disabled>Clear</button>
        </div>
        <div class="c4ai-toolbar-actions">
          <button class="c4ai-preview-btn" disabled>Preview Markdown</button>
          <button class="c4ai-copy-btn" disabled>Copy to Clipboard</button>
        </div>
        <div class="c4ai-toolbar-instructions">
          <p>💡 <strong>Ctrl/Cmd + Click</strong> to select multiple elements</p>
          <p>📝 Selected elements will be converted to clean markdown</p>
          <p>⌨️ Press <strong>ESC</strong> to exit</p>
        </div>
      </div>
    `;
    
    document.body.appendChild(this.toolbar);
    makeDraggableByHeader(this.toolbar);
    
    // Position toolbar
    this.toolbar.style.position = 'fixed';
    this.toolbar.style.top = '20px';
    this.toolbar.style.right = '20px';
    this.toolbar.style.zIndex = '999999';
  }
  
  setupEventListeners() {
    // Close button
    this.toolbar.querySelector('.c4ai-close-btn').addEventListener('click', () => {
      this.deactivate();
    });
    
    // Clear selection button
    this.toolbar.querySelector('.c4ai-clear-btn').addEventListener('click', () => {
      this.clearSelection();
    });
    
    // Preview button
    this.toolbar.querySelector('.c4ai-preview-btn').addEventListener('click', () => {
      this.showPreview();
    });
    
    // Copy button
    this.toolbar.querySelector('.c4ai-copy-btn').addEventListener('click', () => {
      this.copyToClipboard();
    });
    
    // Document click handler for element selection
    this.documentClickHandler = (event) => this.handleElementClick(event);
    document.addEventListener('click', this.documentClickHandler, true);
    
    // Prevent default link behavior during selection mode
    this.linkClickHandler = (event) => {
      if (event.ctrlKey || event.metaKey) {
        event.preventDefault();
        event.stopPropagation();
      }
    };
    document.addEventListener('click', this.linkClickHandler, true);
    
    // Hover effect
    this.documentHoverHandler = (event) => this.handleElementHover(event);
    document.addEventListener('mouseover', this.documentHoverHandler, true);
    
    // Remove hover on mouseout
    this.documentMouseOutHandler = (event) => this.handleElementMouseOut(event);
    document.addEventListener('mouseout', this.documentMouseOutHandler, true);
    
    // Keyboard shortcuts
    this.keyboardHandler = (event) => this.handleKeyboard(event);
    document.addEventListener('keydown', this.keyboardHandler);
  }
  
  handleElementClick(event) {
    // Check if Ctrl/Cmd is pressed
    if (!event.ctrlKey && !event.metaKey) return;
    
    // Prevent default behavior
    event.preventDefault();
    event.stopPropagation();
    
    const element = event.target;
    
    // Don't select our own UI elements
    if (element.closest('.c4ai-c2c-toolbar') || 
        element.closest('.c4ai-c2c-preview') ||
        element.closest('.c4ai-highlight-box')) {
      return;
    }
    
    // Toggle element selection
    if (this.selectedElements.has(element)) {
      this.deselectElement(element);
    } else {
      this.selectElement(element);
    }
    
    this.updateUI();
  }
  
  handleElementHover(event) {
    const element = event.target;
    
    // Don't hover our own UI elements
    if (element.closest('.c4ai-c2c-toolbar') || 
        element.closest('.c4ai-c2c-preview') ||
        element.closest('.c4ai-highlight-box') ||
        element.hasAttribute('data-c4ai-badge')) {
      return;
    }
    
    // Add hover class
    element.classList.add('c4ai-hover-candidate');
  }
  
  handleElementMouseOut(event) {
    const element = event.target;
    element.classList.remove('c4ai-hover-candidate');
  }
  
  handleKeyboard(event) {
    // ESC to deactivate
    if (event.key === 'Escape') {
      this.deactivate();
    }
    // Ctrl/Cmd + A to select all visible elements
    else if ((event.ctrlKey || event.metaKey) && event.key === 'a') {
      event.preventDefault();
      // Select all visible text-containing elements
      const elements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, td, th, div, span, article, section');
      elements.forEach(el => {
        if (el.textContent.trim() && this.isVisible(el) && !this.selectedElements.has(el)) {
          this.selectElement(el);
        }
      });
      this.updateUI();
    }
  }
  
  isVisible(element) {
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);
    return rect.width > 0 && 
           rect.height > 0 && 
           style.display !== 'none' && 
           style.visibility !== 'hidden' && 
           style.opacity !== '0';
  }
  
  selectElement(element) {
    this.selectedElements.add(element);
    
    // Create highlight box
    const box = this.createHighlightBox(element);
    this.highlightBoxes.set(element, box);
    
    // Add selected class
    element.classList.add('c4ai-selected');
    
    this.selectionCounter++;
  }
  
  deselectElement(element) {
    this.selectedElements.delete(element);
    
    // Remove highlight box (badge)
    const badge = this.highlightBoxes.get(element);
    if (badge) {
      // Remove scroll/resize listeners
      if (badge._updatePosition) {
        window.removeEventListener('scroll', badge._updatePosition, true);
        window.removeEventListener('resize', badge._updatePosition);
      }
      badge.remove();
      this.highlightBoxes.delete(element);
    }
    
    // Remove outline
    element.style.outline = '';
    element.style.outlineOffset = '';
    
    // Remove attributes
    element.removeAttribute('data-c4ai-selection-order');
    element.classList.remove('c4ai-selected');
    
    this.selectionCounter--;
  }
  
  createHighlightBox(element) {
    // Add a data attribute to track selection order
    element.setAttribute('data-c4ai-selection-order', this.selectionCounter + 1);
    
    // Add selection outline directly to the element
    element.style.outline = '2px solid #0fbbaa';
    element.style.outlineOffset = '2px';
    
    // Create badge with fixed positioning
    const badge = document.createElement('div');
    badge.className = 'c4ai-selection-badge-fixed';
    badge.textContent = this.selectionCounter + 1;
    badge.setAttribute('data-c4ai-badge', 'true');
    badge.title = 'Click to deselect';
    
    // Get element position and set badge position
    const rect = element.getBoundingClientRect();
    badge.style.cssText = `
      position: fixed !important;
      top: ${rect.top - 12}px !important;
      left: ${rect.left - 12}px !important;
      width: 24px !important;
      height: 24px !important;
      background: #0fbbaa !important;
      color: #070708 !important;
      border-radius: 50% !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      font-size: 12px !important;
      font-weight: bold !important;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
      z-index: 999998 !important;
      cursor: pointer !important;
      transition: all 0.2s ease !important;
      pointer-events: auto !important;
      border: none !important;
      padding: 0 !important;
      margin: 0 !important;
      line-height: 1 !important;
      text-align: center !important;
      text-decoration: none !important;
      box-sizing: border-box !important;
    `;
    
    // Add hover styles dynamically
    badge.addEventListener('mouseenter', () => {
      badge.style.setProperty('background', '#ff3c74', 'important');
      badge.style.setProperty('transform', 'scale(1.1)', 'important');
    });
    
    badge.addEventListener('mouseleave', () => {
      badge.style.setProperty('background', '#0fbbaa', 'important');
      badge.style.setProperty('transform', 'scale(1)', 'important');
    });
    
    // Add click handler to badge for deselection
    badge.addEventListener('click', (e) => {
      e.stopPropagation();
      e.preventDefault();
      this.deselectElement(element);
      this.updateUI();
    });
    
    // Add scroll listener to update position
    const updatePosition = () => {
      const newRect = element.getBoundingClientRect();
      badge.style.top = `${newRect.top - 12}px`;
      badge.style.left = `${newRect.left - 12}px`;
    };
    
    // Store the update function so we can remove it later
    badge._updatePosition = updatePosition;
    window.addEventListener('scroll', updatePosition, true);
    window.addEventListener('resize', updatePosition);
    
    document.body.appendChild(badge);
    
    return badge;
  }
  
  clearSelection() {
    // Clear all selections
    this.selectedElements.forEach(element => {
      // Remove badge
      const badge = this.highlightBoxes.get(element);
      if (badge) {
        // Remove scroll/resize listeners
        if (badge._updatePosition) {
          window.removeEventListener('scroll', badge._updatePosition, true);
          window.removeEventListener('resize', badge._updatePosition);
        }
        badge.remove();
      }
      
      // Remove outline
      element.style.outline = '';
      element.style.outlineOffset = '';
      
      // Remove attributes
      element.removeAttribute('data-c4ai-selection-order');
      element.classList.remove('c4ai-selected');
    });
    
    this.selectedElements.clear();
    this.highlightBoxes.clear();
    this.selectionCounter = 0;
    
    this.updateUI();
  }
  
  updateUI() {
    const count = this.selectedElements.size;
    
    // Update selection count
    this.toolbar.querySelector('.c4ai-selection-count').textContent = 
      `${count} element${count !== 1 ? 's' : ''} selected`;
    
    // Enable/disable buttons
    const hasSelection = count > 0;
    this.toolbar.querySelector('.c4ai-preview-btn').disabled = !hasSelection;
    this.toolbar.querySelector('.c4ai-copy-btn').disabled = !hasSelection;
    this.toolbar.querySelector('.c4ai-clear-btn').disabled = !hasSelection;
  }
  
  async showPreview() {
    // Initialize markdown preview modal if not already done
    if (!this.markdownPreviewModal) {
      this.markdownPreviewModal = new MarkdownPreviewModal();
    }
    
    // Show modal with callback to generate markdown
    this.markdownPreviewModal.show(async (options) => {
      return await this.generateMarkdown(options);
    });
  }
  
  /* createPreviewPanel() {
    this.previewPanel = document.createElement('div');
    this.previewPanel.className = 'c4ai-c2c-preview';
    this.previewPanel.innerHTML = `
      <div class="c4ai-preview-header">
        <div class="c4ai-toolbar-dots">
          <span class="c4ai-dot c4ai-dot-red"></span>
          <span class="c4ai-dot c4ai-dot-yellow"></span>
          <span class="c4ai-dot c4ai-dot-green"></span>
        </div>
        <span class="c4ai-preview-title">Markdown Preview</span>
        <button class="c4ai-preview-close">×</button>
      </div>
      <div class="c4ai-preview-options">
        <label><input type="checkbox" name="textOnly"> 👁️ Visual Text Mode (As You See) TRY THIS!!!</label>
        <label><input type="checkbox" name="includeImages" checked> Include Images</label>
        <label><input type="checkbox" name="preserveTables" checked> Preserve Tables</label>
        <label><input type="checkbox" name="preserveLinks" checked> Preserve Links</label>
        <label><input type="checkbox" name="keepCodeFormatting" checked> Keep Code Formatting</label>
        <label><input type="checkbox" name="simplifyLayout"> Simplify Layout</label>
        <label><input type="checkbox" name="addSeparators" checked> Add Separators</label>
        <label><input type="checkbox" name="includeXPath"> Include XPath Headers</label>
      </div>
      <div class="c4ai-preview-content">
        <div class="c4ai-preview-tabs">
          <button class="c4ai-tab active" data-tab="preview">Preview</button>
          <button class="c4ai-tab" data-tab="markdown">Markdown</button>
          <button class="c4ai-wrap-toggle" title="Toggle word wrap">↔️ Wrap</button>
        </div>
        <div class="c4ai-preview-pane active" data-pane="preview"></div>
        <div class="c4ai-preview-pane" data-pane="markdown"></div>
      </div>
      <div class="c4ai-preview-actions">
        <button class="c4ai-download-btn">Download .md</button>
        <button class="c4ai-copy-markdown-btn">Copy Markdown</button>
        <button class="c4ai-cloud-btn" disabled>Send to Cloud (Coming Soon)</button>
      </div>
    `;
    
    document.body.appendChild(this.previewPanel);
    makeDraggableByHeader(this.previewPanel);
    
    // Position preview panel
    this.previewPanel.style.position = 'fixed';
    this.previewPanel.style.top = '50%';
    this.previewPanel.style.left = '50%';
    this.previewPanel.style.transform = 'translate(-50%, -50%)';
    this.previewPanel.style.zIndex = '999999';
    
    this.setupPreviewEventListeners();
  } */
  
  /* setupPreviewEventListeners() {
    // Close button
    this.previewPanel.querySelector('.c4ai-preview-close').addEventListener('click', () => {
      this.previewPanel.style.display = 'none';
    });
    
    // Tab switching
    this.previewPanel.querySelectorAll('.c4ai-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const tabName = e.target.dataset.tab;
        this.switchPreviewTab(tabName);
      });
    });
    
    // Wrap toggle
    const wrapToggle = this.previewPanel.querySelector('.c4ai-wrap-toggle');
    wrapToggle.addEventListener('click', () => {
      const panes = this.previewPanel.querySelectorAll('.c4ai-preview-pane');
      panes.forEach(pane => {
        pane.classList.toggle('wrap');
      });
      wrapToggle.classList.toggle('active');
    });
    
    // Options change
    this.previewPanel.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
      checkbox.addEventListener('change', async (e) => {
        this.options[e.target.name] = e.target.checked;
        
        // If text-only is enabled, automatically disable certain options
        if (e.target.name === 'textOnly' && e.target.checked) {
          // Update UI checkboxes
          const preserveLinksCheckbox = this.previewPanel.querySelector('input[name="preserveLinks"]');
          if (preserveLinksCheckbox) {
            preserveLinksCheckbox.checked = false;
            preserveLinksCheckbox.disabled = true;
          }
          
          // Optionally disable images in text-only mode
          const includeImagesCheckbox = this.previewPanel.querySelector('input[name="includeImages"]');
          if (includeImagesCheckbox) {
            includeImagesCheckbox.disabled = true;
          }
        } else if (e.target.name === 'textOnly' && !e.target.checked) {
          // Re-enable options when text-only is disabled
          const preserveLinksCheckbox = this.previewPanel.querySelector('input[name="preserveLinks"]');
          if (preserveLinksCheckbox) {
            preserveLinksCheckbox.disabled = false;
          }
          
          const includeImagesCheckbox = this.previewPanel.querySelector('input[name="includeImages"]');
          if (includeImagesCheckbox) {
            includeImagesCheckbox.disabled = false;
          }
        }
        
        const markdown = await this.generateMarkdown();
        await this.updatePreviewContent(markdown);
      });
    });
    
    // Action buttons
    this.previewPanel.querySelector('.c4ai-copy-markdown-btn').addEventListener('click', () => {
      this.copyToClipboard();
    });
    
    this.previewPanel.querySelector('.c4ai-download-btn').addEventListener('click', () => {
      this.downloadMarkdown();
    });
  } */
  
  /* switchPreviewTab(tabName) {
    // Update active tab
    this.previewPanel.querySelectorAll('.c4ai-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update active pane
    this.previewPanel.querySelectorAll('.c4ai-preview-pane').forEach(pane => {
      pane.classList.toggle('active', pane.dataset.pane === tabName);
    });
  } */
  
  /* async updatePreviewContent(markdown) {
    // Update markdown pane
    const markdownPane = this.previewPanel.querySelector('[data-pane="markdown"]');
    markdownPane.innerHTML = `<pre><code>${this.escapeHtml(markdown)}</code></pre>`;
    
    // Update preview pane using marked.js
    const previewPane = this.previewPanel.querySelector('[data-pane="preview"]');
    
    // Configure marked options (marked.js is already loaded via manifest)
    if (window.marked) {
      marked.setOptions({
        gfm: true,
        breaks: true,
        tables: true,
        headerIds: false,
        mangle: false
      });
      
      // Render markdown to HTML
      const html = marked.parse(markdown);
      previewPane.innerHTML = `<div class="c4ai-markdown-preview">${html}</div>`;
    } else {
      // Fallback if marked.js is not available
      previewPane.innerHTML = `<div class="c4ai-markdown-preview"><pre>${this.escapeHtml(markdown)}</pre></div>`;
    }
  } */
  
  
  /* escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  } */
  
  async generateMarkdown(options) {
    // Get selected elements as array
    const elements = Array.from(this.selectedElements);
    
    // Sort elements by their selection order
    const sortedElements = elements.sort((a, b) => {
      const orderA = parseInt(a.getAttribute('data-c4ai-selection-order') || '0');
      const orderB = parseInt(b.getAttribute('data-c4ai-selection-order') || '0');
      return orderA - orderB;
    });
    
    // Convert each element separately
    const markdownParts = [];
    
    for (let i = 0; i < sortedElements.length; i++) {
      const element = sortedElements[i];
      
      // Add XPath header if enabled
      if (options.includeXPath) {
        const xpath = this.getXPath(element);
        markdownParts.push(`### Element ${i + 1} - XPath: \`${xpath}\`\n`);
      }
      
      // Check if element is part of a table structure that should be processed specially
      let elementsToConvert = [element];
      
      // If text-only mode and element is a TR, process the entire table for better context
      if (options.textOnly && element.tagName === 'TR') {
        const table = element.closest('table');
        if (table && !sortedElements.includes(table)) {
          // Only include this table row, not the whole table
          elementsToConvert = [element];
        }
      }
      
      // Analyze and convert individual element
      const analysis = await this.contentAnalyzer.analyze(elementsToConvert);
      const markdown = await this.markdownConverter.convert(elementsToConvert, {
        ...options,
        analysis
      });
      
      // Trim the markdown before adding
      const trimmedMarkdown = markdown.trim();
      markdownParts.push(trimmedMarkdown);
      
      // Add separator if enabled and not last element
      if (options.addSeparators && i < sortedElements.length - 1) {
        markdownParts.push('\n---\n');
      }
    }
    
    return markdownParts.join('\n');
  }
  
  getXPath(element) {
    if (element.id) {
      return `//*[@id="${element.id}"]`;
    }
    
    const parts = [];
    let current = element;
    
    while (current && current.nodeType === Node.ELEMENT_NODE) {
      let index = 0;
      let sibling = current.previousSibling;
      
      while (sibling) {
        if (sibling.nodeType === Node.ELEMENT_NODE && sibling.nodeName === current.nodeName) {
          index++;
        }
        sibling = sibling.previousSibling;
      }
      
      const tagName = current.nodeName.toLowerCase();
      const part = index > 0 ? `${tagName}[${index + 1}]` : tagName;
      parts.unshift(part);
      
      current = current.parentNode;
    }
    
    return '/' + parts.join('/');
  }
  
  sortElementsByPosition(elements) {
    return elements.sort((a, b) => {
      const position = a.compareDocumentPosition(b);
      if (position & Node.DOCUMENT_POSITION_FOLLOWING) {
        return -1;
      } else if (position & Node.DOCUMENT_POSITION_PRECEDING) {
        return 1;
      }
      return 0;
    });
  }
  
  async copyToClipboard() {
    if (this.markdownPreviewModal) {
      await this.markdownPreviewModal.copyToClipboard();
    }
  }
  
  async downloadMarkdown() {
    if (this.markdownPreviewModal) {
      await this.markdownPreviewModal.downloadMarkdown();
    }
  }
  
  showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `c4ai-notification c4ai-notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }
  
  deactivate() {
    // Remove event listeners
    document.removeEventListener('click', this.documentClickHandler, true);
    document.removeEventListener('click', this.linkClickHandler, true);
    document.removeEventListener('mouseover', this.documentHoverHandler, true);
    document.removeEventListener('mouseout', this.documentMouseOutHandler, true);
    document.removeEventListener('keydown', this.keyboardHandler);
    
    // Clear selections
    this.clearSelection();
    
    // Remove UI elements
    if (this.toolbar) {
      this.toolbar.remove();
      this.toolbar = null;
    }
    
    if (this.markdownPreviewModal) {
      this.markdownPreviewModal.destroy();
      this.markdownPreviewModal = null;
    }
    
    // Remove hover styles
    document.querySelectorAll('.c4ai-hover-candidate').forEach(el => {
      el.classList.remove('c4ai-hover-candidate');
    });
    
    // Notify background script (with error handling)
    try {
      if (chrome.runtime && chrome.runtime.sendMessage) {
        chrome.runtime.sendMessage({
          action: 'c2cDeactivated'
        });
      }
    } catch (error) {
      // Extension context might be invalidated, ignore the error
      console.log('Markdown Extraction deactivated (extension context unavailable)');
    }
  }
}