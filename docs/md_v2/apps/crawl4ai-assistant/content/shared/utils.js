// Shared utilities for Crawl4AI Chrome Extension

// Make element draggable by its titlebar
function makeDraggable(element) {
  let isDragging = false;
  let startX, startY, initialX, initialY;
  
  const titlebar = element.querySelector('.c4ai-toolbar-titlebar, .c4ai-titlebar');
  if (!titlebar) return;
  
  titlebar.addEventListener('mousedown', (e) => {
    // Don't drag if clicking on buttons
    if (e.target.classList.contains('c4ai-dot') || e.target.closest('button')) return;
    
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

// Make element draggable by a specific header element
function makeDraggableByHeader(element) {
  let isDragging = false;
  let startX, startY, initialX, initialY;
  
  const header = element.querySelector('.c4ai-debugger-header');
  if (!header) return;
  
  header.addEventListener('mousedown', (e) => {
    // Don't drag if clicking on close button
    if (e.target.id === 'c4ai-close-debugger' || e.target.closest('#c4ai-close-debugger')) return;
    
    isDragging = true;
    startX = e.clientX;
    startY = e.clientY;
    
    const rect = element.getBoundingClientRect();
    initialX = rect.left;
    initialY = rect.top;
    
    element.style.transition = 'none';
    header.style.cursor = 'grabbing';
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
      header.style.cursor = 'grab';
    }
  });
}

// Escape HTML for safe display
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Apply syntax highlighting to Python code
function applySyntaxHighlighting(codeElement) {
  const code = codeElement.textContent;
  
  // Split by lines to handle line-by-line
  const lines = code.split('\n');
  const highlightedLines = lines.map(line => {
    let highlightedLine = escapeHtml(line);
    
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

// Apply syntax highlighting to JavaScript code
function applySyntaxHighlightingJS(codeElement) {
  const code = codeElement.textContent;
  
  // Split by lines to handle line-by-line
  const lines = code.split('\n');
  const highlightedLines = lines.map(line => {
    let highlightedLine = escapeHtml(line);
    
    // Skip if line is empty
    if (!highlightedLine.trim()) return highlightedLine;
    
    // Comments
    if (highlightedLine.trim().startsWith('//')) {
      return `<span class="c4ai-comment">${highlightedLine}</span>`;
    }
    
    // Multi-line comments
    highlightedLine = highlightedLine.replace(/(\/\*.*?\*\/)/g, '<span class="c4ai-comment">$1</span>');
    
    // Template literals
    highlightedLine = highlightedLine.replace(/(`[^`]*`)/g, '<span class="c4ai-string">$1</span>');
    
    // Regular strings - single and double quotes
    highlightedLine = highlightedLine.replace(/(["'])([^"']*)\1/g, '<span class="c4ai-string">$1$2$1</span>');
    
    // Keywords
    const keywords = ['const', 'let', 'var', 'function', 'async', 'await', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 'return', 'try', 'catch', 'finally', 'throw', 'new', 'this', 'class', 'extends', 'import', 'export', 'default', 'from', 'null', 'undefined', 'true', 'false'];
    
    keywords.forEach(keyword => {
      const regex = new RegExp(`\\b(${keyword})\\b(?![^<]*</span>)`, 'g');
      highlightedLine = highlightedLine.replace(regex, '<span class="c4ai-keyword">$1</span>');
    });
    
    // Functions and methods
    highlightedLine = highlightedLine.replace(/\b([a-zA-Z_$][\w$]*)\s*\(/g, '<span class="c4ai-function">$1</span>(');
    
    // Numbers
    highlightedLine = highlightedLine.replace(/\b(\d+)\b/g, '<span class="c4ai-number">$1</span>');
    
    return highlightedLine;
  });
  
  codeElement.innerHTML = highlightedLines.join('\n');
}

// Get element selector
function getElementSelector(element) {
  // Priority: ID > unique class > tag with position
  if (element.id) {
    return `#${element.id}`;
  }

  if (element.className && typeof element.className === 'string') {
    const classes = element.className.split(' ').filter(c => c && !c.startsWith('c4ai-'));
    if (classes.length > 0) {
      const selector = `.${classes[0]}`;
      if (document.querySelectorAll(selector).length === 1) {
        return selector;
      }
    }
  }

  // Build a path selector
  const path = [];
  let current = element;

  while (current && current !== document.body) {
    const tagName = current.tagName.toLowerCase();
    const parent = current.parentElement;
    
    if (parent) {
      const siblings = Array.from(parent.children);
      const index = siblings.indexOf(current) + 1;
      
      if (siblings.filter(s => s.tagName === current.tagName).length > 1) {
        path.unshift(`${tagName}:nth-child(${index})`);
      } else {
        path.unshift(tagName);
      }
    } else {
      path.unshift(tagName);
    }
    
    current = parent;
  }

  return path.join(' > ');
}

// Check if element is part of our extension UI
function isOurElement(element) {
  return element.classList.contains('c4ai-highlight-box') ||
         element.classList.contains('c4ai-toolbar') ||
         element.closest('.c4ai-toolbar') ||
         element.classList.contains('c4ai-script-toolbar') ||
         element.closest('.c4ai-script-toolbar') ||
         element.closest('.c4ai-field-dialog') ||
         element.closest('.c4ai-code-modal') ||
         element.closest('.c4ai-wait-dialog') ||
         element.closest('.c4ai-timeline-modal');
}

// Export utilities
window.C4AI_Utils = {
  makeDraggable,
  makeDraggableByHeader,
  escapeHtml,
  applySyntaxHighlighting,
  applySyntaxHighlightingJS,
  getElementSelector,
  isOurElement
};