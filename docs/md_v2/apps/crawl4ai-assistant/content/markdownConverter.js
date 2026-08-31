class MarkdownConverter {
  constructor() {
    // Conversion handlers for different element types
    this.converters = {
      'H1': async (el, ctx) => await this.convertHeading(el, 1, ctx),
      'H2': async (el, ctx) => await this.convertHeading(el, 2, ctx),
      'H3': async (el, ctx) => await this.convertHeading(el, 3, ctx),
      'H4': async (el, ctx) => await this.convertHeading(el, 4, ctx),
      'H5': async (el, ctx) => await this.convertHeading(el, 5, ctx),
      'H6': async (el, ctx) => await this.convertHeading(el, 6, ctx),
      'P': async (el, ctx) => await this.convertParagraph(el, ctx),
      'A': async (el, ctx) => await this.convertLink(el, ctx),
      'IMG': async (el, ctx) => await this.convertImage(el, ctx),
      'UL': async (el, ctx) => await this.convertList(el, 'ul', ctx),
      'OL': async (el, ctx) => await this.convertList(el, 'ol', ctx),
      'LI': async (el, ctx) => await this.convertListItem(el, ctx),
      'TABLE': async (el, ctx) => await this.convertTable(el, ctx),
      'BLOCKQUOTE': async (el, ctx) => await this.convertBlockquote(el, ctx),
      'PRE': async (el, ctx) => await this.convertPreformatted(el, ctx),
      'CODE': async (el, ctx) => await this.convertCode(el, ctx),
      'HR': async (el, ctx) => '\n---\n',
      'BR': async (el, ctx) => '  \n',
      'STRONG': async (el, ctx) => `**${await this.getTextContent(el, ctx)}**`,
      'B': async (el, ctx) => `**${await this.getTextContent(el, ctx)}**`,
      'EM': async (el, ctx) => `*${await this.getTextContent(el, ctx)}*`,
      'I': async (el, ctx) => `*${await this.getTextContent(el, ctx)}*`,
      'DEL': async (el, ctx) => `~~${await this.getTextContent(el, ctx)}~~`,
      'S': async (el, ctx) => `~~${await this.getTextContent(el, ctx)}~~`,
      'DIV': async (el, ctx) => await this.convertDiv(el, ctx),
      'SPAN': async (el, ctx) => await this.convertSpan(el, ctx),
      'ARTICLE': async (el, ctx) => await this.convertArticle(el, ctx),
      'SECTION': async (el, ctx) => await this.convertSection(el, ctx),
      'FIGURE': async (el, ctx) => await this.convertFigure(el, ctx),
      'FIGCAPTION': async (el, ctx) => await this.convertFigCaption(el, ctx),
      'VIDEO': async (el, ctx) => await this.convertVideo(el, ctx),
      'IFRAME': async (el, ctx) => await this.convertIframe(el, ctx),
      'DL': async (el, ctx) => await this.convertDefinitionList(el, ctx),
      'DT': async (el, ctx) => await this.convertDefinitionTerm(el, ctx),
      'DD': async (el, ctx) => await this.convertDefinitionDescription(el, ctx),
      'TR': async (el, ctx) => await this.convertTableRow(el, ctx)
    };
    
    // Maintain context during conversion
    this.conversionContext = {
      listDepth: 0,
      inTable: false,
      inCode: false,
      preserveWhitespace: false,
      references: [],
      imageCount: 0,
      linkCount: 0
    };
  }
  
  async convert(elements, options = {}) {
    // Reset context
    this.resetContext();
    
    // Apply options
    this.options = {
      includeImages: true,
      preserveTables: true,
      keepCodeFormatting: true,
      simplifyLayout: false,
      preserveLinks: true,
      ...options
    };
    
    // Convert elements
    const markdownParts = [];
    
    for (const element of elements) {
      const markdown = await this.convertElement(element, this.conversionContext);
      if (markdown.trim()) {
        markdownParts.push(markdown);
      }
    }
    
    // Join parts with appropriate spacing
    let result = markdownParts.join('\n\n');
    
    // Add references if using reference-style links
    if (this.conversionContext.references.length > 0) {
      result += '\n\n' + this.generateReferences();
    }
    
    // Post-process to clean up
    result = this.postProcess(result);
    
    return result;
  }
  
  resetContext() {
    this.conversionContext = {
      listDepth: 0,
      inTable: false,
      inCode: false,
      preserveWhitespace: false,
      references: [],
      imageCount: 0,
      linkCount: 0
    };
  }
  
  async convertElement(element, context) {
    // Skip hidden elements
    if (this.isHidden(element)) {
      return '';
    }
    
    // Skip script and style elements
    if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(element.tagName)) {
      return '';
    }
    
    // Get converter for this element type
    const converter = this.converters[element.tagName];
    
    if (converter) {
      return await converter(element, context);
    } else {
      // For unknown elements, process children
      return await this.processChildren(element, context);
    }
  }
  
  async processChildren(element, context) {
    const parts = [];
    
    for (const child of element.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) {
        const text = this.processTextNode(child, context);
        if (text) {
          parts.push(text);
        }
      } else if (child.nodeType === Node.ELEMENT_NODE) {
        const markdown = await this.convertElement(child, context);
        if (markdown) {
          parts.push(markdown);
        }
      }
    }
    
    return parts.join('');
  }
  
  processTextNode(node, context) {
    let text = node.textContent;
    
    // Preserve whitespace in code blocks
    if (!context.preserveWhitespace && !context.inCode) {
      // Normalize whitespace
      text = text.replace(/\s+/g, ' ');
      
      // Trim if at block boundaries
      if (this.isBlockBoundary(node.previousSibling)) {
        text = text.trimStart();
      }
      if (this.isBlockBoundary(node.nextSibling)) {
        text = text.trimEnd();
      }
    }
    
    // Escape markdown characters
    if (!context.inCode) {
      text = this.escapeMarkdown(text);
    }
    
    return text;
  }
  
  isBlockBoundary(node) {
    if (!node || node.nodeType !== Node.ELEMENT_NODE) {
      return true;
    }
    
    const blockElements = [
      'DIV', 'P', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
      'UL', 'OL', 'LI', 'BLOCKQUOTE', 'PRE', 'TABLE',
      'HR', 'ARTICLE', 'SECTION', 'HEADER', 'FOOTER',
      'NAV', 'ASIDE', 'MAIN'
    ];
    
    return blockElements.includes(node.tagName);
  }
  
  escapeMarkdown(text) {
    // In text-only mode, don't escape characters
    if (this.options.textOnly) {
      return text;
    }
    
    // Escape special markdown characters
    return text
      .replace(/\\/g, '\\\\')
      .replace(/\*/g, '\\*')
      .replace(/_/g, '\\_')
      .replace(/\[/g, '\\[')
      .replace(/\]/g, '\\]')
      .replace(/\(/g, '\\(')
      .replace(/\)/g, '\\)')
      .replace(/\#/g, '\\#')
      .replace(/\+/g, '\\+')
      .replace(/\-/g, '\\-')
      .replace(/\./g, '\\.')
      .replace(/\!/g, '\\!')
      .replace(/\|/g, '\\|');
  }
  
  async convertHeading(element, level, context) {
    const text = await this.getTextContent(element, context);
    return '#'.repeat(level) + ' ' + text + '\n';
  }
  
  async convertParagraph(element, context) {
    const content = await this.processChildren(element, context);
    return content.trim() ? content + '\n' : '';
  }
  
  async convertLink(element, context) {
    if (!this.options.preserveLinks || this.options.textOnly) {
      return await this.getTextContent(element, context);
    }
    
    const text = await this.getTextContent(element, context);
    const href = element.getAttribute('href');
    const title = element.getAttribute('title');
    
    if (!href) {
      return text;
    }
    
    // Convert relative URLs to absolute
    const absoluteUrl = this.makeAbsoluteUrl(href);
    
    // Use reference-style links for cleaner markdown
    if (text && absoluteUrl) {
      if (title) {
        return `[${text}](${absoluteUrl} "${title}")`;
      } else {
        return `[${text}](${absoluteUrl})`;
      }
    }
    
    return text;
  }
  
  async convertImage(element, context) {
    if (!this.options.includeImages || this.options.textOnly) {
      // In text-only mode, return alt text if available
      if (this.options.textOnly) {
        const alt = element.getAttribute('alt');
        return alt ? `[Image: ${alt}]` : '';
      }
      return '';
    }
    
    const src = element.getAttribute('src');
    const alt = element.getAttribute('alt') || '';
    const title = element.getAttribute('title');
    
    if (!src) {
      return '';
    }
    
    // Convert relative URLs to absolute
    const absoluteUrl = this.makeAbsoluteUrl(src);
    
    if (title) {
      return `![${alt}](${absoluteUrl} "${title}")`;
    } else {
      return `![${alt}](${absoluteUrl})`;
    }
  }
  
  async convertList(element, type, context) {
    const oldDepth = context.listDepth;
    context.listDepth++;
    
    const items = [];
    for (const child of element.children) {
      if (child.tagName === 'LI') {
        const markdown = await this.convertListItem(child, { ...context, listType: type });
        if (markdown) {
          items.push(markdown);
        }
      }
    }
    
    context.listDepth = oldDepth;
    
    return items.join('\n') + (context.listDepth === 0 ? '\n' : '');
  }
  
  async convertListItem(element, context) {
    const indent = '  '.repeat(Math.max(0, context.listDepth - 1));
    const bullet = context.listType === 'ol' ? '1.' : '-';
    const content = (await this.processChildren(element, context)).trim();
    
    return `${indent}${bullet} ${content}`;
  }
  
  async convertTable(element, context) {
    if (!this.options.preserveTables || this.options.textOnly) {
      // Fallback to simple text representation
      return await this.convertTableToText(element, context);
    }
    
    const rows = [];
    const headerRows = [];
    let maxCols = 0;
    
    // Process table rows
    for (const child of element.children) {
      if (child.tagName === 'THEAD') {
        for (const row of child.children) {
          if (row.tagName === 'TR') {
            const cells = await this.processTableRow(row, context);
            headerRows.push(cells);
            maxCols = Math.max(maxCols, cells.length);
          }
        }
      } else if (child.tagName === 'TBODY') {
        for (const row of child.children) {
          if (row.tagName === 'TR') {
            const cells = await this.processTableRow(row, context);
            rows.push(cells);
            maxCols = Math.max(maxCols, cells.length);
          }
        }
      } else if (child.tagName === 'TR') {
        const cells = await this.processTableRow(child, context);
        rows.push(cells);
        maxCols = Math.max(maxCols, cells.length);
      }
    }
    
    // Build markdown table
    const markdownRows = [];
    
    // Add headers
    if (headerRows.length > 0) {
      for (const headerRow of headerRows) {
        const paddedRow = this.padTableRow(headerRow, maxCols);
        markdownRows.push('| ' + paddedRow.join(' | ') + ' |');
      }
      
      // Add separator
      const separator = Array(maxCols).fill('---');
      markdownRows.push('| ' + separator.join(' | ') + ' |');
    }
    
    // Add body rows
    for (const row of rows) {
      const paddedRow = this.padTableRow(row, maxCols);
      markdownRows.push('| ' + paddedRow.join(' | ') + ' |');
    }
    
    return markdownRows.join('\n') + '\n';
  }
  
  async processTableRow(row, context) {
    const cells = [];
    
    for (const cell of row.children) {
      if (cell.tagName === 'TD' || cell.tagName === 'TH') {
        const content = (await this.getTextContent(cell, context)).trim();
        cells.push(content);
      }
    }
    
    return cells;
  }
  
  async convertTableRow(element, context) {
    // Convert a single table row to markdown
    if (this.options.textOnly) {
      const cells = await this.processTableRow(element, context);
      return cells.join(' ');
    }
    
    // For non-text-only mode, create a simple table representation
    const cells = await this.processTableRow(element, context);
    return '| ' + cells.join(' | ') + ' |';
  }
  
  padTableRow(row, targetLength) {
    const padded = [...row];
    while (padded.length < targetLength) {
      padded.push('');
    }
    return padded;
  }
  
  async convertTableToText(element, context) {
    // Convert table to clean text representation
    const lines = [];
    const rows = element.querySelectorAll('tr');
    
    for (const row of rows) {
      const cells = row.querySelectorAll('td, th');
      const cellTexts = [];
      
      for (const cell of cells) {
        const text = (await this.getTextContent(cell, context)).trim();
        if (text) {
          cellTexts.push(text);
        }
      }
      
      if (cellTexts.length > 0) {
        // Join cells with space, handling common patterns
        lines.push(cellTexts.join(' '));
      }
    }
    
    return lines.join('\n');
  }
  
  async convertBlockquote(element, context) {
    const lines = (await this.processChildren(element, context)).trim().split('\n');
    return lines.map(line => '> ' + line).join('\n') + '\n';
  }
  
  async convertPreformatted(element, context) {
    const oldInCode = context.inCode;
    const oldPreserveWhitespace = context.preserveWhitespace;
    
    context.inCode = true;
    context.preserveWhitespace = true;
    
    let content = '';
    let language = '';
    
    // Check if this is a code block with language
    const codeElement = element.querySelector('code');
    if (codeElement) {
      // Try to detect language from class
      const className = codeElement.className;
      const langMatch = className.match(/language-(\w+)/);
      if (langMatch) {
        language = langMatch[1];
      }
      
      content = codeElement.textContent;
    } else {
      content = element.textContent;
    }
    
    context.inCode = oldInCode;
    context.preserveWhitespace = oldPreserveWhitespace;
    
    // Use fenced code blocks
    return '```' + language + '\n' + content + '\n```\n';
  }
  
  async convertCode(element, context) {
    if (element.parentElement && element.parentElement.tagName === 'PRE') {
      // Already handled by convertPreformatted
      return element.textContent;
    }
    
    const content = element.textContent;
    return '`' + content + '`';
  }
  
  async convertDiv(element, context) {
    // Check for special div types
    if (element.className.includes('code-block') || 
        element.className.includes('highlight')) {
      return await this.convertPreformatted(element, context);
    }
    
    const content = await this.processChildren(element, context);
    return content.trim() ? content + '\n' : '';
  }
  
  async convertSpan(element, context) {
    // Check for special span types
    if (element.className.includes('code') || 
        element.className.includes('inline-code')) {
      return this.convertCode(element, context);
    }
    
    return await this.processChildren(element, context);
  }
  
  async convertArticle(element, context) {
    const content = await this.processChildren(element, context);
    return content.trim() ? content + '\n' : '';
  }
  
  async convertSection(element, context) {
    const content = await this.processChildren(element, context);
    return content.trim() ? content + '\n' : '';
  }
  
  async convertFigure(element, context) {
    const content = await this.processChildren(element, context);
    return content.trim() ? content + '\n' : '';
  }
  
  async convertFigCaption(element, context) {
    const caption = await this.getTextContent(element, context);
    return caption ? '\n*' + caption + '*\n' : '';
  }
  
  async convertVideo(element, context) {
    const title = element.getAttribute('title') || 'Video';
    
    if (this.options.textOnly) {
      return `[Video: ${title}]`;
    }
    
    const src = element.getAttribute('src');
    const poster = element.getAttribute('poster');
    
    if (!src) {
      return '';
    }
    
    // Convert to markdown with poster image if available
    if (poster) {
      const absolutePoster = this.makeAbsoluteUrl(poster);
      const absoluteSrc = this.makeAbsoluteUrl(src);
      return `[![${title}](${absolutePoster})](${absoluteSrc})`;
    } else {
      const absoluteSrc = this.makeAbsoluteUrl(src);
      return `[${title}](${absoluteSrc})`;
    }
  }
  
  async convertIframe(element, context) {
    const title = element.getAttribute('title') || 'Embedded content';
    
    if (this.options.textOnly) {
      const src = element.getAttribute('src') || '';
      if (src.includes('youtube.com') || src.includes('youtu.be')) {
        return `[Video: ${title}]`;
      } else if (src.includes('vimeo.com')) {
        return `[Video: ${title}]`;
      } else {
        return `[Embedded: ${title}]`;
      }
    }
    
    const src = element.getAttribute('src');
    if (!src) {
      return '';
    }
    
    // Check for common embeds
    if (src.includes('youtube.com') || src.includes('youtu.be')) {
      return `[▶️ ${title}](${src})`;
    } else if (src.includes('vimeo.com')) {
      return `[▶️ ${title}](${src})`;
    } else {
      return `[${title}](${src})`;
    }
  }
  
  async convertDefinitionList(element, context) {
    return await this.processChildren(element, context) + '\n';
  }
  
  async convertDefinitionTerm(element, context) {
    const term = await this.getTextContent(element, context);
    return '**' + term + '**\n';
  }
  
  async convertDefinitionDescription(element, context) {
    const description = await this.processChildren(element, context);
    return ': ' + description + '\n';
  }
  
  async getTextContent(element, context) {
    // Special handling for elements that might contain other markdown
    if (context.inCode) {
      return element.textContent;
    }
    
    return await this.processChildren(element, context);
  }
  
  makeAbsoluteUrl(url) {
    if (!url) return '';
    
    try {
      // Check if already absolute
      if (url.startsWith('http://') || url.startsWith('https://')) {
        return url;
      }
      
      // Handle protocol-relative URLs
      if (url.startsWith('//')) {
        return window.location.protocol + url;
      }
      
      // Convert relative to absolute
      const base = window.location.origin;
      const path = window.location.pathname;
      
      if (url.startsWith('/')) {
        return base + url;
      } else {
        // Relative to current path
        const pathDir = path.substring(0, path.lastIndexOf('/') + 1);
        return base + pathDir + url;
      }
    } catch (e) {
      return url;
    }
  }
  
  isHidden(element) {
    const style = window.getComputedStyle(element);
    return style.display === 'none' || 
           style.visibility === 'hidden' || 
           style.opacity === '0';
  }
  
  generateReferences() {
    return this.conversionContext.references
      .map((ref, index) => `[${index + 1}]: ${ref.url}`)
      .join('\n');
  }
  
  postProcess(markdown) {
    // Apply text-only specific processing
    if (this.options.textOnly) {
      markdown = this.postProcessTextOnly(markdown);
    }
    
    // Clean up excessive newlines
    markdown = markdown.replace(/\n{3,}/g, '\n\n');
    
    // Clean up spaces before punctuation
    markdown = markdown.replace(/ +([.,;:!?])/g, '$1');
    
    // Ensure proper spacing around headers
    markdown = markdown.replace(/\n(#{1,6} )/g, '\n\n$1');
    markdown = markdown.replace(/(#{1,6} .+)\n(?![\n#])/g, '$1\n\n');
    
    // Clean up list spacing
    markdown = markdown.replace(/\n\n(-|\d+\.) /g, '\n$1 ');
    
    // Trim final result
    return markdown.trim();
  }
  
  postProcessTextOnly(markdown) {
    // Smart pattern recognition for common formats
    const lines = markdown.split('\n');
    const processedLines = [];
    let inMetadata = false;
    let currentItem = null;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) {
        processedLines.push('');
        continue;
      }
      
      // Detect numbered list items (common in HN, Reddit, etc.)
      const numberPattern = /^(\d+)\.\s*(.+)$/;
      const numberMatch = line.match(numberPattern);
      
      if (numberMatch) {
        // Start of a new numbered item
        inMetadata = false;
        currentItem = numberMatch[1];
        const content = numberMatch[2];
        
        // Check if content has domain in parentheses
        const domainPattern = /^(.+?)\s*\(([^)]+)\)\s*(.*)$/;
        const domainMatch = content.match(domainPattern);
        
        if (domainMatch) {
          const [, title, domain, rest] = domainMatch;
          processedLines.push(`${currentItem}. **${title.trim()}** (${domain})`);
          if (rest.trim()) {
            processedLines.push(`   ${rest.trim()}`);
            inMetadata = true;
          }
        } else {
          processedLines.push(`${currentItem}. **${content}**`);
        }
      } else if (line.match(/\b(points?|by|ago|hide|comments?)\b/i) && currentItem) {
        // This looks like metadata for the current item
        const cleanedLine = line
          .replace(/\s+/g, ' ')
          .replace(/\s*\|\s*/g, ' | ')
          .trim();
        processedLines.push(`   ${cleanedLine}`);
        inMetadata = true;
      } else if (inMetadata && line.length < 100) {
        // Continue metadata if we're in metadata mode and line is short
        processedLines.push(`   ${line}`);
      } else {
        // Regular content
        inMetadata = false;
        processedLines.push(line);
      }
    }
    
    // Clean up the output
    let result = processedLines.join('\n');
    
    // Remove excessive blank lines
    result = result.replace(/\n{3,}/g, '\n\n');
    
    // Ensure proper spacing after numbered items
    result = result.replace(/^(\d+\..+)$\n^(?!\s)/gm, '$1\n\n');
    
    return result;
  }
}