// Click2Crawl class for Crawl4AI Chrome Extension
// Click elements to build extraction schemas

// Singleton instance to prevent multiple toolbars
let click2CrawlInstance = null;

class Click2Crawl {
  constructor() {
    // Prevent multiple instances
    if (click2CrawlInstance) {
      click2CrawlInstance.stop();
    }
    click2CrawlInstance = this;
    
    this.container = null;
    this.fields = [];
    this.overlay = null;
    this.toolbar = null;
    this.highlightBox = null; // For hover preview
    this.selectedBox = null; // For selected element
    this.currentElement = null; // Currently hovered element
    this.selectedElement = null; // Currently selected element (container)
    this.selectedElements = new Set();
    this.inspectingFields = false; // Field inspection mode
    this.codeModal = null;
    this.previewMode = false;
    this.previewElements = [];
    this.schema = null;
    this.parentLevels = 1; // Default parent levels for base container
    
    this.handleMouseMove = this.handleMouseMove.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.handleKeyPress = this.handleKeyPress.bind(this);
    this.handleMouseLeave = this.handleMouseLeave.bind(this);
  }

  start() {
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
    this.selectedBox?.remove();
    this.removeAllHighlights();
    this.clearPreview();
    this.container = null;
    this.fields = [];
    this.selectedElements.clear();
    this.schema = null;
    this.currentElement = null;
    this.selectedElement = null;
    this.inspectingFields = false;
    this.parentLevels = 1;
    
    // Clean up markdown preview modal
    if (this.markdownPreviewModal) {
      this.markdownPreviewModal.destroy();
      this.markdownPreviewModal = null;
    }
    
    // Clear singleton reference
    if (click2CrawlInstance === this) {
      click2CrawlInstance = null;
    }
  }
  
  // Alias for content script compatibility
  deactivate() {
    this.stop();
  }

  createOverlay() {
    // Create highlight box for hover preview
    this.highlightBox = document.createElement('div');
    this.highlightBox.className = 'c4ai-highlight-box';
    document.body.appendChild(this.highlightBox);
    
    // Create selected box for permanent selection
    this.selectedBox = document.createElement('div');
    this.selectedBox.className = 'c4ai-selected-box';
    this.selectedBox.style.display = 'none';
    document.body.appendChild(this.selectedBox);
  }

  createToolbar() {
    // Remove any existing toolbar first
    const existingToolbar = document.querySelector('.c4ai-toolbar');
    if (existingToolbar) {
      existingToolbar.remove();
    }
    
    this.toolbar = document.createElement('div');
    this.toolbar.className = 'c4ai-toolbar';
    this.toolbar.innerHTML = `
      <div class="c4ai-toolbar-titlebar">
        <div class="c4ai-titlebar-dots">
          <button class="c4ai-dot c4ai-dot-close" id="c4ai-close"></button>
          <button class="c4ai-dot c4ai-dot-minimize"></button>
          <button class="c4ai-dot c4ai-dot-maximize"></button>
        </div>
        <div class="c4ai-titlebar-title">  Click2Crawl</div>
        <img src="${chrome.runtime.getURL('icons/icon-16.png')}" class="c4ai-titlebar-icon" alt="Crawl4AI" style="margin-left: auto;">
      </div>
      <div class="c4ai-toolbar-content">
        <div class="c4ai-toolbar-status">
          <div class="c4ai-status-item">
            <span class="c4ai-status-label">Mode:</span>
            <span class="c4ai-status-value" id="c4ai-mode">Select Container</span>
          </div>
          <div class="c4ai-status-item" id="c4ai-container-item" style="display: none;">
            <span class="c4ai-status-label">Container:</span>
            <span class="c4ai-status-value" id="c4ai-container">Not selected</span>
            <button class="c4ai-nav-btn c4ai-nav-btn-small" id="c4ai-nav-up" title="Select parent">↑</button>
            <button class="c4ai-nav-btn c4ai-nav-btn-small" id="c4ai-nav-down" title="Select child">↓</button>
            <button class="c4ai-nav-btn c4ai-nav-btn-small c4ai-nav-deselect" id="c4ai-nav-close" title="Deselect">×</button>
          </div>
          <div class="c4ai-status-item" id="c4ai-selector-display" style="display: none;">
            <div class="c4ai-container-selector" id="c4ai-container-selector"></div>
          </div>
          <div class="c4ai-status-item" id="c4ai-parent-levels" style="display: none;">
            <span class="c4ai-status-label">Parent Levels:</span>
            <div class="c4ai-parent-controls">
              <button class="c4ai-parent-btn" id="c4ai-parent-minus">-</button>
              <span class="c4ai-parent-value" id="c4ai-parent-value">1</span>
              <button class="c4ai-parent-btn" id="c4ai-parent-plus">+</button>
            </div>
          </div>
        </div>
        
        <div class="c4ai-schema-section" id="c4ai-schema-section" style="display: none;">
          <div class="c4ai-section-header">
            <span>SCHEMA FIELDS (<span id="c4ai-field-count">0</span>)</span>
          </div>
          <div class="c4ai-fields-list" id="c4ai-fields-list"></div>
        </div>
        
        <div class="c4ai-actions-section" id="c4ai-actions-section" style="display: none;">
          <div class="c4ai-section-header">ACTIONS</div>
          <div class="c4ai-toolbar-actions">
            <button id="c4ai-preview" class="c4ai-action-btn c4ai-preview-btn" disabled>
              <span>👁️</span> Preview Matches
            </button>
            <button id="c4ai-test" class="c4ai-action-btn c4ai-test-btn" disabled>
              <span>🧪</span> Test Schema
            </button>
            <button id="c4ai-deploy-cloud" class="c4ai-action-btn c4ai-export-btn c4ai-cloud-btn" disabled>
              <span>☁️</span> Deploy
            </button>
            <button id="c4ai-export-schema" class="c4ai-action-btn c4ai-export-btn" disabled>
              <span>📄</span> Schema
            </button>
            <button id="c4ai-export-data" class="c4ai-action-btn c4ai-export-btn" disabled>
              <span>📊</span> Data
            </button>
            <button id="c4ai-export-markdown" class="c4ai-action-btn c4ai-export-btn" disabled>
              <span>📝</span> Markdown
            </button>
          </div>
        </div>
        
        <div class="c4ai-stats-section" id="c4ai-stats-section" style="display: none;">
          <div class="c4ai-section-header">STATS</div>
          <div class="c4ai-stats">
            <div class="c4ai-stat-item">
              <span>Matches Found:</span>
              <span id="c4ai-matches-count">0 items</span>
            </div>
            <div class="c4ai-stat-item">
              <span>Schema Valid:</span>
              <span id="c4ai-schema-valid">Not tested</span>
            </div>
          </div>
        </div>
        
        <div class="c4ai-toolbar-hint" id="c4ai-hint">
          Click on a container element (e.g., product card, article, etc.)
        </div>
        
        <div class="c4ai-toolbar-footer" id="c4ai-footer-section" style="display: none;">
          <button id="c4ai-inspect-fields" class="c4ai-action-btn c4ai-primary-btn">
            <span>🏷️</span> Fields
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(this.toolbar);
    
    // Force toolbar to top of z-index stack
    this.toolbar.style.zIndex = '2147483647'; // Maximum z-index
    
    // Add event listeners for toolbar buttons with error handling
    const addClickHandler = (id, handler) => {
      const element = document.getElementById(id);
      if (element) {
        element.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          handler();
        });
      }
    };
    
    // Add all event listeners
      addClickHandler('c4ai-inspect-fields', () => this.toggleFieldInspection());
      addClickHandler('c4ai-preview', () => this.togglePreview());
      addClickHandler('c4ai-test', () => this.testSchema());
      addClickHandler('c4ai-export-schema', () => this.exportSchema());
      addClickHandler('c4ai-export-data', () => this.exportData());
      addClickHandler('c4ai-export-markdown', () => this.exportMarkdown());
      addClickHandler('c4ai-deploy-cloud', () => this.deployToCloud());
      addClickHandler('c4ai-close', () => this.stop());
      
      // Navigation controls
      addClickHandler('c4ai-nav-up', () => this.navigateUp());
      addClickHandler('c4ai-nav-down', () => this.navigateDown());
      addClickHandler('c4ai-nav-close', () => this.deselectContainer());
      
      // Parent level controls
      addClickHandler('c4ai-parent-minus', () => this.adjustParentLevels(-1));
      addClickHandler('c4ai-parent-plus', () => this.adjustParentLevels(1));
    
    // Make toolbar draggable
    if (window.C4AI_Utils && window.C4AI_Utils.makeDraggable) {
      window.C4AI_Utils.makeDraggable(this.toolbar);
    }
  }

  attachEventListeners() {
    document.addEventListener('mousemove', this.handleMouseMove, true);
    document.addEventListener('click', this.handleClick, true);
    document.addEventListener('keydown', this.handleKeyPress, true);
    document.addEventListener('mouseleave', this.handleMouseLeave, true);
  }

  detachEventListeners() {
    document.removeEventListener('mousemove', this.handleMouseMove, true);
    document.removeEventListener('click', this.handleClick, true);
    document.removeEventListener('keydown', this.handleKeyPress, true);
    document.removeEventListener('mouseleave', this.handleMouseLeave, true);
  }

  handleMouseMove(e) {
    const element = document.elementFromPoint(e.clientX, e.clientY);
    
    // Don't highlight if hovering over our UI elements
    if (this.isOurElement(element)) {
      this.highlightBox.style.display = 'none';
      return;
    }
    
    // Only show highlight if:
    // 1. No container selected (selection mode)
    // 2. Or inspecting fields inside container
    if (!this.container || (this.inspectingFields && this.container)) {
      if (element) {
        // If inspecting fields, only highlight elements inside container
        if (this.inspectingFields && !this.container.element.contains(element)) {
          this.highlightBox.style.display = 'none';
          return;
        }
        
        this.currentElement = element;
        this.highlightElement(element);
      }
    } else {
      // Container selected but not inspecting fields - no highlight
      this.highlightBox.style.display = 'none';
    }
  }
  
  handleMouseLeave(e) {
    // Hide highlight when mouse leaves
    if (e.target === document) {
      this.highlightBox.style.display = 'none';
    }
  }

  handleClick(e) {
    const element = e.target;
    
    // Check if clicking on our UI elements (including markdown preview modal)
    if (this.isOurElement(element)) {
      return; // Let toolbar clicks work normally
    }
    
    // Additional check for markdown preview modal classes
    if (element.closest('.c4ai-c2c-preview') || element.closest('.c4ai-preview-options')) {
      return; // Don't interfere with markdown preview modal
    }

    // Use current element
    const targetElement = this.currentElement || element;

    if (!this.container) {
      // Container selection mode - prevent default
      e.preventDefault();
      e.stopPropagation();
      this.selectContainer(targetElement);
    } else if (this.inspectingFields && this.container.element.contains(targetElement)) {
      // Field selection mode AND clicking inside container - prevent default
      e.preventDefault();
      e.stopPropagation();
      this.selectField(targetElement);
    }
    // Otherwise, let the click work normally
  }

  handleKeyPress(e) {
    if (e.key === 'Escape') {
      this.stop();
    }
  }

  isOurElement(element) {
    return window.C4AI_Utils.isOurElement(element) || 
           (this.selectedBox && element === this.selectedBox) ||
           (this.markdownPreviewModal && this.markdownPreviewModal.modal && 
            (element === this.markdownPreviewModal.modal || this.markdownPreviewModal.modal.contains(element)));
  }
  
  showSelectedBox(element) {
    if (!element) return;
    
    const rect = element.getBoundingClientRect();
    this.selectedBox.style.cssText = `
      position: absolute;
      left: ${rect.left + window.scrollX}px;
      top: ${rect.top + window.scrollY}px;
      width: ${rect.width}px;
      height: ${rect.height}px;
      display: block;
    `;
    
    this.selectedBox.className = 'c4ai-selected-box c4ai-selected-container';
  }
  
  updateNavButtonStates() {
    const upBtn = document.getElementById('c4ai-nav-up');
    const downBtn = document.getElementById('c4ai-nav-down');
    
    if (this.selectedElement) {
      // Disable up button if no parent or parent is body
      upBtn.disabled = !this.selectedElement.parentElement || this.selectedElement.parentElement === document.body;
      
      // Disable down button if no children
      downBtn.disabled = this.selectedElement.children.length === 0;
    }
  }
  
  navigateUp() {
    if (!this.selectedElement || !this.selectedElement.parentElement) return;
    
    const parent = this.selectedElement.parentElement;
    if (parent === document.body) return;
    
    // Update selected element and container
    this.selectedElement = parent;
    this.container.element = parent;
    this.container.tagName = parent.tagName.toLowerCase();
    this.container.selector = this.generateContainerSelector(parent);
    
    // Update visual selection
    this.showSelectedBox(parent);
    this.updateNavButtonStates();
    this.updateToolbar();
    this.updateStats();
  }
  
  navigateDown() {
    if (!this.selectedElement || this.selectedElement.children.length === 0) return;
    
    const firstChild = this.selectedElement.children[0];
    
    // Update selected element and container
    this.selectedElement = firstChild;
    this.container.element = firstChild;
    this.container.tagName = firstChild.tagName.toLowerCase();
    this.container.selector = this.generateContainerSelector(firstChild);
    
    // Update visual selection
    this.showSelectedBox(firstChild);
    this.updateNavButtonStates();
    this.updateToolbar();
    this.updateStats();
  }
  
  deselectContainer() {
    if (this.container) {
      // Remove visual selection
      this.container.element.classList.remove('c4ai-selected-container');
      this.selectedBox.style.display = 'none';
      
      // Clear container and related state
      this.container = null;
      this.selectedElement = null;
      this.inspectingFields = false;
      
      // Clear all fields
      this.fields.forEach(field => {
        field.element.classList.remove('c4ai-selected-field');
        field.element.removeAttribute('data-c4ai-field');
      });
      this.fields = [];
      this.selectedElements.clear();
      
      this.updateToolbar();
      this.updateStats();
    }
  }
  
  toggleFieldInspection() {
    this.inspectingFields = !this.inspectingFields;
    const fieldsBtn = document.getElementById('c4ai-inspect-fields');
    
    if (this.inspectingFields) {
      fieldsBtn.classList.add('c4ai-active');
      fieldsBtn.innerHTML = '<span>✓</span> Fields';
    } else {
      fieldsBtn.classList.remove('c4ai-active');
      fieldsBtn.innerHTML = '<span>🏷️</span> Fields';
      this.highlightBox.style.display = 'none';
    }
    
    this.updateToolbar();
  }


  // Legacy method - kept for compatibility but now redirects to test schema
  stopAndGenerate() {
    this.testSchema();
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

    if (!this.container) {
      // Container selection mode
      this.highlightBox.className = 'c4ai-highlight-box c4ai-container-mode';
    } else {
      // Field selection mode
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
      selector: this.generateContainerSelector(element),
      tagName: element.tagName.toLowerCase()
    };

    element.classList.add('c4ai-selected-container');
    this.selectedElement = element;
    this.showSelectedBox(element);
    
    // Hide hover highlight after selection
    this.highlightBox.style.display = 'none';
    
    // Update navigation button states
    this.updateNavButtonStates();
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
    // Remove any existing field dialogs first
    document.querySelectorAll('.c4ai-field-dialog').forEach(d => d.remove());
    
    const dialog = document.createElement('div');
    dialog.className = 'c4ai-field-dialog';
    
    const rect = element.getBoundingClientRect();
    dialog.style.cssText = `
      left: ${rect.left + window.scrollX}px;
      top: ${rect.bottom + window.scrollY + 10}px;
    `;

    // Get available attributes
    const attributes = this.getElementAttributes(element);
    const attributeOptions = attributes.map(attr => 
      `<option value="${attr.name}">${attr.name}: "${attr.value.substring(0, 30)}${attr.value.length > 30 ? '...' : ''}"</option>`
    ).join('');

    dialog.innerHTML = `
      <div class="c4ai-field-dialog-content">
        <h4>Configure Field</h4>
        
        <div class="c4ai-field-input">
          <label>Field Name:</label>
          <input type="text" id="c4ai-field-name" placeholder="e.g., title, price, description" autofocus>
        </div>
        
        <div class="c4ai-field-input">
          <label>Field Type:</label>
          <select id="c4ai-field-type">
            <option value="text">Text Content</option>
            <option value="attribute">Attribute</option>
            <option value="link">Link (href)</option>
            <option value="image">Image (src)</option>
            <option value="list">List</option>
            <option value="nested">Nested Object</option>
          </select>
        </div>
        
        <div class="c4ai-field-input" id="c4ai-attribute-select" style="display: none;">
          <label>Select Attribute:</label>
          <select id="c4ai-field-attribute">
            ${attributeOptions}
          </select>
        </div>
        
        <div class="c4ai-field-preview">
          <strong>Preview Value:</strong>
          <div id="c4ai-preview-value">${element.textContent.trim().substring(0, 100)}</div>
        </div>
        
        <div class="c4ai-field-selector">
          <strong>Selector (auto-generated):</strong>
          <div id="c4ai-selector-preview">${this.generateSmartSelector(element, this.container.element)}</div>
        </div>
        
        <div class="c4ai-field-actions">
          <button id="c4ai-field-save" class="c4ai-primary">✓ Save</button>
          <button id="c4ai-field-cancel">✗ Cancel</button>
        </div>
      </div>
    `;

    document.body.appendChild(dialog);

    const nameInput = dialog.querySelector('#c4ai-field-name');
    const typeSelect = dialog.querySelector('#c4ai-field-type');
    const attributeSelect = dialog.querySelector('#c4ai-field-attribute');
    const attributeContainer = dialog.querySelector('#c4ai-attribute-select');
    const previewValue = dialog.querySelector('#c4ai-preview-value');
    const saveBtn = dialog.querySelector('#c4ai-field-save');
    const cancelBtn = dialog.querySelector('#c4ai-field-cancel');

    // Update preview based on type selection
    const updatePreview = () => {
      const type = typeSelect.value;
      let value = '';
      
      switch(type) {
        case 'text':
          value = element.textContent.trim();
          attributeContainer.style.display = 'none';
          break;
        case 'attribute':
          attributeContainer.style.display = 'block';
          value = element.getAttribute(attributeSelect.value) || '';
          break;
        case 'link':
          value = element.getAttribute('href') || element.querySelector('a')?.getAttribute('href') || '';
          attributeContainer.style.display = 'none';
          break;
        case 'image':
          value = element.getAttribute('src') || element.querySelector('img')?.getAttribute('src') || '';
          attributeContainer.style.display = 'none';
          break;
        case 'list':
          const listItems = element.querySelectorAll('li, option');
          value = `[${listItems.length} items]`;
          attributeContainer.style.display = 'none';
          break;
        case 'nested':
          value = '[Complex nested structure]';
          attributeContainer.style.display = 'none';
          break;
      }
      
      previewValue.textContent = value.substring(0, 100) + (value.length > 100 ? '...' : '');
    };

    typeSelect.addEventListener('change', updatePreview);
    attributeSelect.addEventListener('change', updatePreview);

    const save = () => {
      const fieldName = nameInput.value.trim();
      if (fieldName) {
        const type = typeSelect.value;
        const selector = this.generateSmartSelector(element, this.container.element);
        
        const field = {
          name: fieldName,
          type: type,
          selector: selector,
          element: element,
          value: previewValue.textContent
        };
        
        // Add attribute if needed
        if (type === 'attribute') {
          field.attribute = attributeSelect.value;
        } else if (type === 'link') {
          field.type = 'attribute';
          field.attribute = 'href';
        } else if (type === 'image') {
          field.type = 'attribute';
          field.attribute = 'src';
        }
        
        this.fields.push(field);
        element.classList.add('c4ai-selected-field');
        element.setAttribute('data-c4ai-field', fieldName);
        this.selectedElements.add(element);
        this.updateToolbar();
        this.updateStats();
        this.generateSchema();
      }
      dialog.remove(); // Always close dialog
    };

    const cancel = () => {
      dialog.remove();
    };

    saveBtn.addEventListener('click', save);
    cancelBtn.addEventListener('click', cancel);
    nameInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') save();
      if (e.key === 'Escape') cancel();
    });

    nameInput.focus();
  }

  adjustParentLevels(delta) {
    if (!this.container) return;
    
    const newLevel = this.parentLevels + delta;
    if (newLevel < 0 || newLevel > 5) return;
    
    this.parentLevels = newLevel;
    document.getElementById('c4ai-parent-value').textContent = newLevel;
    
    // Update container selector with new parent levels
    this.updateContainerSelector();
  }
  
  updateContainerSelector() {
    if (!this.container || !this.selectedElement) return;
    
    this.container.selector = this.generateContainerSelector(this.selectedElement);
    this.container.element = this.selectedElement;
    
    // Update the schema
    this.generateSchema();
    
    // Update display
    const containerDisplay = document.getElementById('c4ai-container');
    // containerDisplay.textContent = `${this.container.tagName} (${this.parentLevels} levels)`;
    containerDisplay.textContent = `${this.container.tagName}`;
    
    // Update selector display
    const containerSelector = document.getElementById('c4ai-container-selector');
    if (containerSelector) {
      containerSelector.textContent = this.container.selector;
    }
  }
  
  generateContainerSelector(element) {
    // For container, include parent levels
    let current = element;
    const parts = [];
    
    // Start from the target element
    for (let i = 0; i <= this.parentLevels; i++) {
      if (!current || current === document.body) break;
      
      const selector = this.generateSingleElementSelector(current);
      parts.unshift(selector);
      
      if (i < this.parentLevels) {
        current = current.parentElement;
      }
    }
    
    // If we have parent levels, show them clearly
    if (this.parentLevels > 0 && parts.length > 1) {
      // Make it clear which part is the container
      const containerPart = parts[parts.length - 1];
      const parentParts = parts.slice(0, -1);
      return parentParts.join(' > ') + ' > ' + containerPart;
    }
    
    return parts.join(' > ');
  }
  
  generateSingleElementSelector(element) {
    // Generate selector for a single element
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

    const tagName = element.tagName.toLowerCase();
    
    // Check for simple, non-utility classes
    const classes = Array.from(element.classList)
      .filter(c => !c.startsWith('c4ai-')) // Exclude our classes
      .filter(c => !c.includes('[') && !c.includes('(') && !c.includes(':')) // Exclude utility classes
      .filter(c => c.length < 30); // Exclude very long classes
    
    if (classes.length > 0 && classes.length <= 2) {
      return tagName + classes.map(c => `.${CSS.escape(c)}`).join('');
    }
    
    return tagName;
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
    // Update mode display
    if (!this.container) {
      document.getElementById('c4ai-mode').textContent = 'Select Container';
    } else if (this.inspectingFields) {
      document.getElementById('c4ai-mode').textContent = 'Select Fields';
    } else {
      document.getElementById('c4ai-mode').textContent = 'Container Selected';
    }
    
    // Show/hide container info and controls
    const containerItem = document.getElementById('c4ai-container-item');
    const parentLevelControls = document.getElementById('c4ai-parent-levels');
    const footerSection = document.getElementById('c4ai-footer-section');
    const selectorDisplay = document.getElementById('c4ai-selector-display');
    const containerSelector = document.getElementById('c4ai-container-selector');
    
    if (this.container) {
      containerItem.style.display = 'flex';
      parentLevelControls.style.display = 'flex';
      footerSection.style.display = 'flex';
      selectorDisplay.style.display = 'block';
      
      // Update container display
      document.getElementById('c4ai-container').textContent = 
        `${this.container.tagName} (${this.parentLevels} levels)`;
      
      // Update selector display
      containerSelector.textContent = this.container.selector;
    } else {
      containerItem.style.display = 'none';
      parentLevelControls.style.display = 'none';
      footerSection.style.display = 'none';
      selectorDisplay.style.display = 'none';
    }

    // Show/hide sections based on state
    const schemaSection = document.getElementById('c4ai-schema-section');
    const actionsSection = document.getElementById('c4ai-actions-section');
    const statsSection = document.getElementById('c4ai-stats-section');
    
    if (this.fields.length > 0) {
      schemaSection.style.display = 'block';
      actionsSection.style.display = 'block';
      statsSection.style.display = 'block';
      
      // Update field count
      document.getElementById('c4ai-field-count').textContent = this.fields.length;
      
      // Update fields list with enhanced UI
      const fieldsList = document.getElementById('c4ai-fields-list');
      fieldsList.innerHTML = this.fields.map((field, index) => {
        const icon = this.getFieldIcon(field.type);
        return `
          <div class="c4ai-field-item" data-index="${index}">
            <div class="c4ai-field-header">
              <span class="c4ai-field-icon">${icon}</span>
              <span class="c4ai-field-name">${field.name}</span>
              <div class="c4ai-field-actions">
                <button class="c4ai-field-edit" data-index="${index}" title="Edit field">✏️</button>
                <button class="c4ai-field-delete" data-index="${index}" title="Remove field">×</button>
              </div>
            </div>
            <div class="c4ai-field-selector" contenteditable="true" data-index="${index}">${field.selector}</div>
          </div>
        `;
      }).join('');
      
      // Add event handlers
      fieldsList.querySelectorAll('.c4ai-field-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const index = parseInt(e.target.dataset.index);
          this.removeField(index);
        });
      });
      
      fieldsList.querySelectorAll('.c4ai-field-edit').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const index = parseInt(e.target.dataset.index);
          this.editField(index);
        });
      });
      
      fieldsList.querySelectorAll('.c4ai-field-selector').forEach(selector => {
        selector.addEventListener('blur', (e) => {
          const index = parseInt(e.target.dataset.index);
          const newSelector = e.target.textContent.trim();
          if (newSelector && this.fields[index]) {
            this.fields[index].selector = newSelector;
            this.generateSchema();
          }
        });
        
        selector.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            e.target.blur();
          }
        });
      });
      
      // Enable action buttons
      document.getElementById('c4ai-preview').disabled = false;
      document.getElementById('c4ai-test').disabled = false;
      document.getElementById('c4ai-export-schema').disabled = false;
      document.getElementById('c4ai-export-data').disabled = false;
      document.getElementById('c4ai-export-markdown').disabled = false;
      document.getElementById('c4ai-deploy-cloud').disabled = false;
    } else {
      schemaSection.style.display = 'none';
      actionsSection.style.display = 'none';
      statsSection.style.display = 'none';
    }

    const hint = document.getElementById('c4ai-hint');
    if (!this.container) {
      hint.textContent = 'Click on a container element (e.g., product card, article, etc.)';
    } else if (this.inspectingFields && this.fields.length === 0) {
      hint.textContent = 'Click on fields inside the container to extract (title, price, etc.)';
    } else if (this.inspectingFields) {
      hint.innerHTML = `Continue selecting fields or click Fields button to stop.`;
    } else if (this.fields.length === 0) {
      hint.innerHTML = `Click <strong>Fields</strong> button to start selecting fields.`;
    } else {
      hint.innerHTML = `Use action buttons above or click <strong>Fields</strong> to add more.`;
    }
  }

  getFieldIcon(type) {
    const icons = {
      'text': '📝',
      'attribute': '📊',
      'link': '🔗',
      'image': '🖼️',
      'list': '📚',
      'nested': '📁'
    };
    return icons[type] || '📝';
  }

  removeField(index) {
    const field = this.fields[index];
    
    // Remove from arrays
    this.fields.splice(index, 1);
    
    // Remove visual selection
    field.element.classList.remove('c4ai-selected-field');
    field.element.removeAttribute('data-c4ai-field');
    this.selectedElements.delete(field.element);
    
    // Update UI
    this.updateToolbar();
    this.updateStats();
    this.generateSchema();
  }
  
  editField(index) {
    const field = this.fields[index];
    if (!field) return;
    
    // Remove any existing field dialogs first
    document.querySelectorAll('.c4ai-field-dialog').forEach(d => d.remove());
    
    // Re-show the field dialog with existing values
    const dialog = document.createElement('div');
    dialog.className = 'c4ai-field-dialog';
    
    const rect = field.element.getBoundingClientRect();
    dialog.style.cssText = `
      left: ${rect.left + window.scrollX}px;
      top: ${rect.bottom + window.scrollY + 10}px;
    `;

    // Get available attributes
    const attributes = this.getElementAttributes(field.element);
    const attributeOptions = attributes.map(attr => 
      `<option value="${attr.name}" ${field.attribute === attr.name ? 'selected' : ''}>${attr.name}: "${attr.value.substring(0, 30)}${attr.value.length > 30 ? '...' : ''}"</option>`
    ).join('');

    dialog.innerHTML = `
      <div class="c4ai-field-dialog-content">
        <h4>Edit Field</h4>
        
        <div class="c4ai-field-input">
          <label>Field Name:</label>
          <input type="text" id="c4ai-field-name" value="${field.name}" placeholder="e.g., title, price, description" autofocus>
        </div>
        
        <div class="c4ai-field-input">
          <label>Field Type:</label>
          <select id="c4ai-field-type">
            <option value="text" ${field.type === 'text' ? 'selected' : ''}>Text Content</option>
            <option value="attribute" ${field.type === 'attribute' ? 'selected' : ''}>Attribute</option>
            <option value="link" ${field.type === 'link' ? 'selected' : ''}>Link (href)</option>
            <option value="image" ${field.type === 'image' ? 'selected' : ''}>Image (src)</option>
            <option value="list" ${field.type === 'list' ? 'selected' : ''}>List</option>
            <option value="nested" ${field.type === 'nested' ? 'selected' : ''}>Nested Object</option>
          </select>
        </div>
        
        <div class="c4ai-field-input" id="c4ai-attribute-select" style="display: ${field.type === 'attribute' ? 'block' : 'none'};">
          <label>Select Attribute:</label>
          <select id="c4ai-field-attribute">
            ${attributeOptions}
          </select>
        </div>
        
        <div class="c4ai-field-preview">
          <strong>Preview Value:</strong>
          <div id="c4ai-preview-value">${field.value}</div>
        </div>
        
        <div class="c4ai-field-selector">
          <strong>Selector (auto-generated):</strong>
          <div id="c4ai-selector-preview">${field.selector}</div>
        </div>
        
        <div class="c4ai-field-actions">
          <button id="c4ai-field-save" class="c4ai-primary">✓ Update</button>
          <button id="c4ai-field-cancel">✗ Cancel</button>
        </div>
      </div>
    `;

    document.body.appendChild(dialog);

    const nameInput = dialog.querySelector('#c4ai-field-name');
    const typeSelect = dialog.querySelector('#c4ai-field-type');
    const attributeSelect = dialog.querySelector('#c4ai-field-attribute');
    const attributeContainer = dialog.querySelector('#c4ai-attribute-select');
    const previewValue = dialog.querySelector('#c4ai-preview-value');
    const saveBtn = dialog.querySelector('#c4ai-field-save');
    const cancelBtn = dialog.querySelector('#c4ai-field-cancel');

    // Update preview based on type selection
    const updatePreview = () => {
      const type = typeSelect.value;
      let value = '';
      
      switch(type) {
        case 'text':
          value = field.element.textContent.trim();
          attributeContainer.style.display = 'none';
          break;
        case 'attribute':
          attributeContainer.style.display = 'block';
          value = field.element.getAttribute(attributeSelect.value) || '';
          break;
        case 'link':
          value = field.element.getAttribute('href') || field.element.querySelector('a')?.getAttribute('href') || '';
          attributeContainer.style.display = 'none';
          break;
        case 'image':
          value = field.element.getAttribute('src') || field.element.querySelector('img')?.getAttribute('src') || '';
          attributeContainer.style.display = 'none';
          break;
        case 'list':
          const listItems = field.element.querySelectorAll('li, option');
          value = `[${listItems.length} items]`;
          attributeContainer.style.display = 'none';
          break;
        case 'nested':
          value = '[Complex nested structure]';
          attributeContainer.style.display = 'none';
          break;
      }
      
      previewValue.textContent = value.substring(0, 100) + (value.length > 100 ? '...' : '');
    };

    typeSelect.addEventListener('change', updatePreview);
    attributeSelect.addEventListener('change', updatePreview);

    const save = () => {
      const fieldName = nameInput.value.trim();
      if (fieldName) {
        const type = typeSelect.value;
        
        // Update field
        field.name = fieldName;
        field.type = type;
        field.value = previewValue.textContent;
        
        // Update attribute if needed
        if (type === 'attribute') {
          field.attribute = attributeSelect.value;
        } else if (type === 'link') {
          field.type = 'attribute';
          field.attribute = 'href';
        } else if (type === 'image') {
          field.type = 'attribute';
          field.attribute = 'src';
        } else {
          delete field.attribute;
        }
        
        // Update element attribute
        field.element.setAttribute('data-c4ai-field', fieldName);
        
        this.updateToolbar();
        this.updateStats();
        this.generateSchema();
      }
      dialog.remove();
    };

    const cancel = () => {
      dialog.remove();
    };

    saveBtn.addEventListener('click', save);
    cancelBtn.addEventListener('click', cancel);
    nameInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') save();
      if (e.key === 'Escape') cancel();
    });

    nameInput.focus();
    nameInput.select();
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

  // New helper methods for enhanced functionality
  getElementAttributes(element) {
    const attributes = [];
    for (const attr of element.attributes) {
      attributes.push({
        name: attr.name,
        value: attr.value
      });
    }
    return attributes;
  }

  generateSmartSelector(element, container) {
    // Smart selector generation with 2-level parent context
    const parts = [];
    let current = element;
    let depth = 0;
    
    // Build path from element up to container (max 3 levels)
    while (current && current !== container && depth < 3) {
      let selector = current.tagName.toLowerCase();
      
      // Add ID if available
      if (current.id && !current.id.includes(':') && !current.id.includes('[')) {
        selector = `#${CSS.escape(current.id)}`;
        parts.unshift(selector);
        break; // ID is unique enough
      }
      
      // Add classes (filter out dynamic/utility classes)
      const classes = Array.from(current.classList)
        .filter(c => !c.startsWith('c4ai-'))
        .filter(c => !c.includes('[') && !c.includes('(') && !c.includes(':'))
        .filter(c => c.length < 30)
        .slice(0, 2); // Max 2 classes
      
      if (classes.length > 0) {
        selector += classes.map(c => `.${CSS.escape(c)}`).join('');
      }
      
      // Add data attributes for more specificity
      const dataAttrs = ['data-testid', 'data-id', 'data-test'];
      for (const attr of dataAttrs) {
        if (current.hasAttribute(attr)) {
          selector += `[${attr}="${CSS.escape(current.getAttribute(attr))}"]`;
          break;
        }
      }
      
      // Add nth-child if needed for disambiguation
      if (current.parentElement && depth === 0) {
        const siblings = Array.from(current.parentElement.children);
        const sameTagSiblings = siblings.filter(s => s.tagName === current.tagName);
        if (sameTagSiblings.length > 1) {
          const index = sameTagSiblings.indexOf(current) + 1;
          selector += `:nth-of-type(${index})`;
        }
      }
      
      parts.unshift(selector);
      current = current.parentElement;
      depth++;
    }
    
    // Create relative selector from container
    const fullSelector = parts.join(' > ');
    
    // Test selector uniqueness within container
    try {
      const matches = container.querySelectorAll(fullSelector);
      if (matches.length === 1 && matches[0] === element) {
        return fullSelector;
      }
    } catch (e) {
      // Invalid selector, continue with fallback
    }
    
    // Fallback to simple selector
    return parts[parts.length - 1] || element.tagName.toLowerCase();
  }

  generateSchema() {
    if (!this.container || this.fields.length === 0) {
      return null;
    }
    
    // Build schema object
    this.schema = {
      name: `${window.location.hostname} Schema`,
      baseSelector: this.container.selector,
      fields: this.fields.map(field => {
        const schemaField = {
          name: field.name,
          selector: field.selector,
          type: field.type
        };
        
        if (field.attribute) {
          schemaField.attribute = field.attribute;
        }
        
        return schemaField;
      })
    };
    
    return this.schema;
  }

  togglePreview() {
    this.previewMode = !this.previewMode;
    const previewBtn = document.getElementById('c4ai-preview');
    
    if (this.previewMode) {
      previewBtn.innerHTML = '<span>🔄</span> Hide Preview';
      this.showPreview();
    } else {
      previewBtn.innerHTML = '<span>👁️</span> Preview Matches';
      this.clearPreview();
    }
  }

  showPreview() {
    if (!this.schema) {
      this.generateSchema();
    }
    
    this.clearPreview();
    
    // Find all matching containers
    const containers = document.querySelectorAll(this.schema.baseSelector);
    let successCount = 0;
    
    containers.forEach((container, index) => {
      // Highlight container
      const containerBox = document.createElement('div');
      containerBox.className = 'c4ai-preview-container';
      const rect = container.getBoundingClientRect();
      containerBox.style.cssText = `
        position: absolute;
        left: ${rect.left + window.scrollX}px;
        top: ${rect.top + window.scrollY}px;
        width: ${rect.width}px;
        height: ${rect.height}px;
        pointer-events: none;
        z-index: 999997;
      `;
      document.body.appendChild(containerBox);
      this.previewElements.push(containerBox);
      
      // Check each field
      let fieldsFound = 0;
      this.schema.fields.forEach(field => {
        try {
          const fieldElement = container.querySelector(field.selector);
          if (fieldElement) {
            fieldsFound++;
            // Highlight successful field
            const fieldBox = document.createElement('div');
            fieldBox.className = 'c4ai-preview-field-success';
            const fieldRect = fieldElement.getBoundingClientRect();
            fieldBox.style.cssText = `
              position: absolute;
              left: ${fieldRect.left + window.scrollX}px;
              top: ${fieldRect.top + window.scrollY}px;
              width: ${fieldRect.width}px;
              height: ${fieldRect.height}px;
              pointer-events: none;
              z-index: 999998;
            `;
            document.body.appendChild(fieldBox);
            this.previewElements.push(fieldBox);
          }
        } catch (e) {
          // Invalid selector
        }
      });
      
      // Add count badge
      const badge = document.createElement('div');
      badge.className = 'c4ai-preview-badge';
      badge.textContent = `${index + 1}`;
      badge.style.cssText = `
        position: absolute;
        left: ${rect.left + window.scrollX - 20}px;
        top: ${rect.top + window.scrollY - 20}px;
        z-index: 999999;
      `;
      document.body.appendChild(badge);
      this.previewElements.push(badge);
      
      if (fieldsFound === this.schema.fields.length) {
        successCount++;
      }
    });
    
    // Update stats
    document.getElementById('c4ai-matches-count').textContent = `${containers.length} items`;
    document.getElementById('c4ai-schema-valid').textContent = 
      successCount === containers.length ? '✓ Yes' : `⚠️ Partial (${successCount}/${containers.length})`;
  }

  clearPreview() {
    this.previewElements.forEach(el => el.remove());
    this.previewElements = [];
  }

  async testSchema() {
    if (!this.schema) {
      this.generateSchema();
    }
    
    // Extract data using schema
    const results = [];
    const containers = document.querySelectorAll(this.schema.baseSelector);
    
    containers.forEach(container => {
      const item = {};
      
      this.schema.fields.forEach(field => {
        try {
          const element = container.querySelector(field.selector);
          if (element) {
            if (field.type === 'text') {
              item[field.name] = element.textContent.trim();
            } else if (field.type === 'attribute' && field.attribute) {
              item[field.name] = element.getAttribute(field.attribute);
            }
          } else {
            item[field.name] = null;
          }
        } catch (e) {
          item[field.name] = null;
        }
      });
      
      results.push(item);
    });
    
    // Show results modal
    this.showResultsModal(results);
  }

  showResultsModal(data) {
    const modal = document.createElement('div');
    modal.className = 'c4ai-code-modal';
    modal.innerHTML = `
      <div class="c4ai-code-modal-content">
        <div class="c4ai-code-modal-header">
          <h2>Extracted Data (${data.length} items)</h2>
          <button class="c4ai-close-modal" id="c4ai-close-results">✕</button>
        </div>
        <div class="c4ai-code-modal-body">
          <pre class="c4ai-code-block"><code>${JSON.stringify(data, null, 2)}</code></pre>
        </div>
        <div class="c4ai-code-modal-footer">
          <button class="c4ai-action-btn c4ai-download-btn" id="c4ai-download-data">
            <span>⬇</span> Download JSON
          </button>
          <button class="c4ai-action-btn c4ai-download-btn" id="c4ai-download-python">
            <span>🐍</span> Download Python Code
          </button>
          <button class="c4ai-action-btn c4ai-copy-btn" id="c4ai-copy-data">
            <span>📋</span> Copy to Clipboard
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Event listeners
    document.getElementById('c4ai-close-results').addEventListener('click', () => modal.remove());
    
    document.getElementById('c4ai-download-data').addEventListener('click', () => {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `extracted_data_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    });
    
    document.getElementById('c4ai-copy-data').addEventListener('click', () => {
      navigator.clipboard.writeText(JSON.stringify(data, null, 2)).then(() => {
        const btn = document.getElementById('c4ai-copy-data');
        btn.innerHTML = '<span>✓</span> Copied!';
        setTimeout(() => {
          btn.innerHTML = '<span>📋</span> Copy to Clipboard';
        }, 2000);
      });
    });
    
    document.getElementById('c4ai-download-python').addEventListener('click', () => {
      const pythonCode = this.generatePythonCode();
      const blob = new Blob([pythonCode], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `crawl4ai_schema_${Date.now()}.py`;
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  exportSchema() {
    if (!this.schema) {
      this.generateSchema();
    }
    
    const blob = new Blob([JSON.stringify(this.schema, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `schema_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async exportData() {
    await this.testSchema();
  }
  
  async exportMarkdown() {
    // Initialize markdown converter if not already done
    if (!this.markdownConverter) {
      this.markdownConverter = new MarkdownConverter();
    }
    if (!this.contentAnalyzer) {
      this.contentAnalyzer = new ContentAnalyzer();
    }
    
    // Initialize markdown preview modal if not already done
    if (!this.markdownPreviewModal) {
      this.markdownPreviewModal = new MarkdownPreviewModal();
    }
    
    // Get all matching containers
    const containers = document.querySelectorAll(this.container.selector);
    if (containers.length === 0) {
      this.showNotification('No matching containers found', 'error');
      return;
    }
    
    // Show modal with callback to generate markdown
    this.markdownPreviewModal.show(async (options) => {
      return await this.generateMarkdownFromSchema(options);
    });
  }
  
  
  
  
  
  async generateMarkdownFromSchema(options) {
    // Get all matching containers
    const containers = document.querySelectorAll(this.container.selector);
    const markdownParts = [];
    
    for (let i = 0; i < containers.length; i++) {
      const container = containers[i];
      
      // Add XPath header if enabled
      if (options.includeXPath) {
        const xpath = this.getXPath(container);
        markdownParts.push(`### Container ${i + 1} - XPath: \`${xpath}\`\n`);
      }
      
      // Extract data based on schema fields
      const extractedData = {};
      this.fields.forEach(field => {
        try {
          const element = container.querySelector(field.selector);
          if (element) {
            if (field.type === 'text') {
              extractedData[field.name] = element.textContent.trim();
            } else if (field.type === 'attribute' && field.attribute) {
              extractedData[field.name] = element.getAttribute(field.attribute);
            }
          }
        } catch (e) {
          // Skip invalid selectors
        }
      });
      
      // Convert container to markdown based on options
      const analysis = await this.contentAnalyzer.analyze([container]);
      const containerMarkdown = await this.markdownConverter.convert([container], {
        ...options,
        analysis,
        extractedData // Pass extracted data for context
      });
      
      // Trim the markdown before adding
      const trimmedMarkdown = containerMarkdown.trim();
      markdownParts.push(trimmedMarkdown);
      
      // Add separator if enabled and not last element
      if (options.addSeparators && i < containers.length - 1) {
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
  
  deployToCloud() {
    // Create cloud deployment modal
    const modal = document.createElement('div');
    modal.className = 'c4ai-code-modal';
    modal.innerHTML = `
      <div class="c4ai-cloud-modal-content">
        <div class="c4ai-cloud-header">
          <div class="c4ai-cloud-icon">🌩️</div>
          <h2>Deploy to Crawl4AI Cloud</h2>
        </div>
        <div class="c4ai-cloud-body">
          <div class="c4ai-cloud-features">
            <h3>🚀 Coming Soon!</h3>
            <p>Deploy your extraction schemas to the cloud with just one click:</p>
            <ul>
              <li>✨ <strong>Instant Deployment</strong> - Your schema live in seconds</li>
              <li>🌐 <strong>API Access</strong> - RESTful endpoints for your extractions</li>
              <li>⏰ <strong>Scheduled Runs</strong> - Automate data collection</li>
              <li>📊 <strong>Analytics Dashboard</strong> - Monitor your extractions</li>
              <li>🔄 <strong>Auto-scaling</strong> - Handle any volume seamlessly</li>
            </ul>
          </div>
          <div class="c4ai-cloud-cta">
            <p>Be the first to know when Crawl4AI Cloud launches!</p>
            <button class="c4ai-action-btn c4ai-primary-btn c4ai-waitlist-btn" id="c4ai-join-waitlist">
              <span>🎆</span> Join the Waiting List
            </button>
          </div>
        </div>
        <button class="c4ai-close-modal" id="c4ai-close-cloud-modal">✕</button>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    document.getElementById('c4ai-close-cloud-modal').addEventListener('click', () => modal.remove());
    document.getElementById('c4ai-join-waitlist').addEventListener('click', () => {
      window.open('https://crawl4ai.com/join-waiting-list', '_blank');
      modal.remove();
    });
    
    // Close on escape
    const escHandler = (e) => {
      if (e.key === 'Escape') {
        modal.remove();
        document.removeEventListener('keydown', escHandler);
      }
    };
    document.addEventListener('keydown', escHandler);
  }
  
  generatePythonCode() {
    if (!this.schema) {
      this.generateSchema();
    }
    
    const schemaJson = JSON.stringify(this.schema, null, 2);
    
    return `#!/usr/bin/env python3
"""
Generated by Crawl4AI Chrome Extension
URL: ${window.location.href}
Generated: ${new Date().toISOString()}
"""

import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai import JsonCssExtractionStrategy

# The extraction schema generated from your selections
EXTRACTION_SCHEMA = ${schemaJson}

async def extract_data(url: str = "${window.location.href}"):
    """Extract data using the generated schema"""
    
    # Configure browser (optional)
    browser_config = BrowserConfig(
        headless=True,  # Set to False to see the browser
        verbose=False
    )
    
    # Configure extraction strategy
    extraction_strategy = JsonCssExtractionStrategy(schema=EXTRACTION_SCHEMA)
    
    # Configure crawler
    crawler_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        # Add more options as needed:
        # wait_for="css:.product",  # Wait for specific elements
        # js_code="window.scrollTo(0, document.body.scrollHeight);",  # Execute JS
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
            with open('extracted_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Show sample results
            print("\\n📊 Sample results (first 2 items):")
            for i, item in enumerate(data[:2], 1):
                print(f"\\nItem {i}:")
                for key, value in item.items():
                    print(f"  {key}: {value}")
                    
            return data
        else:
            print("❌ Extraction failed:", result.error_message)
            return None

if __name__ == "__main__":
    # Run the extraction
    data = asyncio.run(extract_data())
    
    print("\\n🎯 Next steps:")
    print("1. Install Crawl4AI: pip install crawl4ai")
    print("2. Modify the URL or add multiple URLs")
    print("3. Customize crawler options as needed")
    print("4. Check 'extracted_data.json' for full results")
`;
  }

  // Legacy code generation - kept for reference but no longer used
  /*
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
from crawl4ai import JsonCssExtractionStrategy

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
  */

  /* Legacy modal - no longer used
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
          <pre class="c4ai-code-block"><code class="language-python">${window.C4AI_Utils.escapeHtml(code)}</code></pre>
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
    
    // Apply syntax highlighting
    window.C4AI_Utils.applySyntaxHighlighting(this.codeModal.querySelector('.language-python'));
  }
  */
}

// Export for use in content script
if (typeof window !== 'undefined') {
  window.Click2Crawl = Click2Crawl;
}