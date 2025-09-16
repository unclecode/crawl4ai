class ContentAnalyzer {
  constructor() {
    this.patterns = {
      article: ['article', 'main', 'content', 'post', 'entry'],
      navigation: ['nav', 'menu', 'navigation', 'breadcrumb'],
      sidebar: ['sidebar', 'aside', 'widget'],
      header: ['header', 'masthead', 'banner'],
      footer: ['footer', 'copyright', 'contact'],
      list: ['list', 'items', 'results', 'products', 'cards'],
      table: ['table', 'grid', 'data'],
      media: ['gallery', 'carousel', 'slideshow', 'video', 'media']
    };
  }
  
  async analyze(elements) {
    const analysis = {
      structure: await this.analyzeStructure(elements),
      contentType: this.identifyContentType(elements),
      hierarchy: this.buildHierarchy(elements),
      mediaAssets: this.collectMediaAssets(elements),
      textDensity: this.calculateTextDensity(elements),
      semanticRegions: this.identifySemanticRegions(elements),
      relationships: this.analyzeRelationships(elements),
      metadata: this.extractMetadata(elements)
    };
    
    return analysis;
  }
  
  analyzeStructure(elements) {
    const structure = {
      hasHeadings: false,
      hasLists: false,
      hasTables: false,
      hasMedia: false,
      hasCode: false,
      hasLinks: false,
      layout: 'linear', // linear, grid, mixed
      depth: 0,
      elementTypes: new Map()
    };
    
    // Analyze each element
    for (const element of elements) {
      this.analyzeElementStructure(element, structure);
    }
    
    // Determine layout type
    structure.layout = this.determineLayout(elements);
    
    // Calculate max depth
    structure.depth = this.calculateMaxDepth(elements);
    
    return structure;
  }
  
  analyzeElementStructure(element, structure, visited = new Set()) {
    if (visited.has(element)) return;
    visited.add(element);
    
    const tagName = element.tagName;
    
    // Update element type count
    structure.elementTypes.set(
      tagName, 
      (structure.elementTypes.get(tagName) || 0) + 1
    );
    
    // Check for specific structures
    if (/^H[1-6]$/.test(tagName)) {
      structure.hasHeadings = true;
    } else if (['UL', 'OL', 'DL'].includes(tagName)) {
      structure.hasLists = true;
    } else if (tagName === 'TABLE') {
      structure.hasTables = true;
    } else if (['IMG', 'VIDEO', 'IFRAME', 'PICTURE'].includes(tagName)) {
      structure.hasMedia = true;
    } else if (['CODE', 'PRE'].includes(tagName)) {
      structure.hasCode = true;
    } else if (tagName === 'A') {
      structure.hasLinks = true;
    }
    
    // Analyze children
    for (const child of element.children) {
      this.analyzeElementStructure(child, structure, visited);
    }
  }
  
  identifyContentType(elements) {
    const scores = {
      article: 0,
      list: 0,
      table: 0,
      form: 0,
      media: 0,
      mixed: 0
    };
    
    for (const element of elements) {
      // Score based on element types and classes
      const tagName = element.tagName;
      const className = element.className.toLowerCase();
      const id = element.id.toLowerCase();
      
      // Check for article patterns
      if (tagName === 'ARTICLE' || 
          this.matchesPattern(className + ' ' + id, this.patterns.article)) {
        scores.article += 10;
      }
      
      // Check for list patterns
      if (['UL', 'OL'].includes(tagName) || 
          this.matchesPattern(className, this.patterns.list)) {
        scores.list += 5;
      }
      
      // Check for table
      if (tagName === 'TABLE') {
        scores.table += 10;
      }
      
      // Check for form
      if (tagName === 'FORM' || element.querySelector('input, select, textarea')) {
        scores.form += 5;
      }
      
      // Check for media gallery
      if (this.matchesPattern(className, this.patterns.media) ||
          element.querySelectorAll('img, video').length > 3) {
        scores.media += 5;
      }
    }
    
    // Determine primary content type
    const maxScore = Math.max(...Object.values(scores));
    if (maxScore === 0) return 'unknown';
    
    for (const [type, score] of Object.entries(scores)) {
      if (score === maxScore) {
        return type;
      }
    }
    
    return 'mixed';
  }
  
  buildHierarchy(elements) {
    const hierarchy = {
      root: null,
      levels: [],
      headingStructure: []
    };
    
    // Find common ancestor
    if (elements.length > 0) {
      hierarchy.root = this.findCommonAncestor(elements);
    }
    
    // Build heading hierarchy
    const headings = [];
    for (const element of elements) {
      const foundHeadings = element.querySelectorAll('h1, h2, h3, h4, h5, h6');
      headings.push(...Array.from(foundHeadings));
    }
    
    // Sort headings by document position
    headings.sort((a, b) => {
      const position = a.compareDocumentPosition(b);
      if (position & Node.DOCUMENT_POSITION_FOLLOWING) {
        return -1;
      } else if (position & Node.DOCUMENT_POSITION_PRECEDING) {
        return 1;
      }
      return 0;
    });
    
    // Build heading structure
    let currentLevel = 0;
    const stack = [];
    
    for (const heading of headings) {
      const level = parseInt(heading.tagName.substring(1));
      const item = {
        level,
        text: heading.textContent.trim(),
        element: heading,
        children: []
      };
      
      // Find parent in stack
      while (stack.length > 0 && stack[stack.length - 1].level >= level) {
        stack.pop();
      }
      
      if (stack.length > 0) {
        stack[stack.length - 1].children.push(item);
      } else {
        hierarchy.headingStructure.push(item);
      }
      
      stack.push(item);
    }
    
    return hierarchy;
  }
  
  collectMediaAssets(elements) {
    const media = {
      images: [],
      videos: [],
      iframes: [],
      audio: []
    };
    
    for (const element of elements) {
      // Collect images
      const images = element.querySelectorAll('img');
      for (const img of images) {
        media.images.push({
          src: img.src,
          alt: img.alt,
          title: img.title,
          width: img.width,
          height: img.height,
          element: img
        });
      }
      
      // Collect videos
      const videos = element.querySelectorAll('video');
      for (const video of videos) {
        media.videos.push({
          src: video.src,
          poster: video.poster,
          width: video.width,
          height: video.height,
          element: video
        });
      }
      
      // Collect iframes
      const iframes = element.querySelectorAll('iframe');
      for (const iframe of iframes) {
        media.iframes.push({
          src: iframe.src,
          width: iframe.width,
          height: iframe.height,
          title: iframe.title,
          element: iframe
        });
      }
      
      // Collect audio
      const audios = element.querySelectorAll('audio');
      for (const audio of audios) {
        media.audio.push({
          src: audio.src,
          element: audio
        });
      }
    }
    
    return media;
  }
  
  calculateTextDensity(elements) {
    let totalText = 0;
    let totalElements = 0;
    let linkText = 0;
    let codeText = 0;
    
    for (const element of elements) {
      const stats = this.getTextStats(element);
      totalText += stats.textLength;
      totalElements += stats.elementCount;
      linkText += stats.linkTextLength;
      codeText += stats.codeTextLength;
    }
    
    return {
      textLength: totalText,
      elementCount: totalElements,
      averageTextPerElement: totalElements > 0 ? totalText / totalElements : 0,
      linkDensity: totalText > 0 ? linkText / totalText : 0,
      codeDensity: totalText > 0 ? codeText / totalText : 0
    };
  }
  
  getTextStats(element, visited = new Set()) {
    if (visited.has(element)) {
      return { textLength: 0, elementCount: 0, linkTextLength: 0, codeTextLength: 0 };
    }
    visited.add(element);
    
    let stats = {
      textLength: 0,
      elementCount: 1,
      linkTextLength: 0,
      codeTextLength: 0
    };
    
    // Get direct text content
    for (const node of element.childNodes) {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent.trim();
        stats.textLength += text.length;
        
        // Check if this text is within a link
        if (element.tagName === 'A') {
          stats.linkTextLength += text.length;
        }
        
        // Check if this text is within code
        if (['CODE', 'PRE'].includes(element.tagName)) {
          stats.codeTextLength += text.length;
        }
      }
    }
    
    // Process children
    for (const child of element.children) {
      const childStats = this.getTextStats(child, visited);
      stats.textLength += childStats.textLength;
      stats.elementCount += childStats.elementCount;
      stats.linkTextLength += childStats.linkTextLength;
      stats.codeTextLength += childStats.codeTextLength;
    }
    
    return stats;
  }
  
  identifySemanticRegions(elements) {
    const regions = {
      headers: [],
      navigation: [],
      main: [],
      sidebars: [],
      footers: [],
      articles: []
    };
    
    for (const element of elements) {
      // Check element and its ancestors for semantic regions
      let current = element;
      while (current) {
        const tagName = current.tagName;
        const className = current.className.toLowerCase();
        const role = current.getAttribute('role');
        
        // Check semantic HTML5 elements
        if (tagName === 'HEADER' || role === 'banner') {
          regions.headers.push(current);
        } else if (tagName === 'NAV' || role === 'navigation') {
          regions.navigation.push(current);
        } else if (tagName === 'MAIN' || role === 'main') {
          regions.main.push(current);
        } else if (tagName === 'ASIDE' || role === 'complementary') {
          regions.sidebars.push(current);
        } else if (tagName === 'FOOTER' || role === 'contentinfo') {
          regions.footers.push(current);
        } else if (tagName === 'ARTICLE' || role === 'article') {
          regions.articles.push(current);
        }
        
        // Check class patterns
        if (this.matchesPattern(className, this.patterns.header)) {
          regions.headers.push(current);
        } else if (this.matchesPattern(className, this.patterns.navigation)) {
          regions.navigation.push(current);
        } else if (this.matchesPattern(className, this.patterns.sidebar)) {
          regions.sidebars.push(current);
        } else if (this.matchesPattern(className, this.patterns.footer)) {
          regions.footers.push(current);
        }
        
        current = current.parentElement;
      }
    }
    
    // Deduplicate
    for (const key of Object.keys(regions)) {
      regions[key] = Array.from(new Set(regions[key]));
    }
    
    return regions;
  }
  
  analyzeRelationships(elements) {
    const relationships = {
      siblings: [],
      parents: [],
      children: [],
      relatedByClass: new Map(),
      relatedByStructure: []
    };
    
    // Find sibling relationships
    for (let i = 0; i < elements.length; i++) {
      for (let j = i + 1; j < elements.length; j++) {
        if (elements[i].parentElement === elements[j].parentElement) {
          relationships.siblings.push([elements[i], elements[j]]);
        }
      }
    }
    
    // Find parent-child relationships
    for (const element of elements) {
      for (const other of elements) {
        if (element !== other) {
          if (element.contains(other)) {
            relationships.parents.push({ parent: element, child: other });
          } else if (other.contains(element)) {
            relationships.children.push({ parent: other, child: element });
          }
        }
      }
    }
    
    // Group by similar classes
    for (const element of elements) {
      const classes = Array.from(element.classList);
      for (const className of classes) {
        if (!relationships.relatedByClass.has(className)) {
          relationships.relatedByClass.set(className, []);
        }
        relationships.relatedByClass.get(className).push(element);
      }
    }
    
    // Find structurally similar elements
    for (let i = 0; i < elements.length; i++) {
      for (let j = i + 1; j < elements.length; j++) {
        if (this.areStructurallySimilar(elements[i], elements[j])) {
          relationships.relatedByStructure.push([elements[i], elements[j]]);
        }
      }
    }
    
    return relationships;
  }
  
  areStructurallySimilar(element1, element2) {
    // Same tag name
    if (element1.tagName !== element2.tagName) {
      return false;
    }
    
    // Similar class structure
    const classes1 = Array.from(element1.classList).sort();
    const classes2 = Array.from(element2.classList).sort();
    
    // At least 50% overlap in classes
    const intersection = classes1.filter(c => classes2.includes(c));
    const union = Array.from(new Set([...classes1, ...classes2]));
    
    if (union.length > 0 && intersection.length / union.length >= 0.5) {
      return true;
    }
    
    // Similar child structure
    if (element1.children.length === element2.children.length) {
      const childTags1 = Array.from(element1.children).map(c => c.tagName).sort();
      const childTags2 = Array.from(element2.children).map(c => c.tagName).sort();
      
      if (JSON.stringify(childTags1) === JSON.stringify(childTags2)) {
        return true;
      }
    }
    
    return false;
  }
  
  extractMetadata(elements) {
    const metadata = {
      title: null,
      description: null,
      author: null,
      date: null,
      tags: [],
      microdata: []
    };
    
    for (const element of elements) {
      // Look for title
      const h1 = element.querySelector('h1');
      if (h1 && !metadata.title) {
        metadata.title = h1.textContent.trim();
      }
      
      // Look for meta information
      const metaElements = element.querySelectorAll('[itemprop], [property], [name]');
      for (const meta of metaElements) {
        const prop = meta.getAttribute('itemprop') || 
                    meta.getAttribute('property') || 
                    meta.getAttribute('name');
        const content = meta.getAttribute('content') || meta.textContent.trim();
        
        if (prop && content) {
          if (prop.includes('author')) {
            metadata.author = content;
          } else if (prop.includes('date') || prop.includes('time')) {
            metadata.date = content;
          } else if (prop.includes('description')) {
            metadata.description = content;
          } else if (prop.includes('tag') || prop.includes('keyword')) {
            metadata.tags.push(content);
          }
          
          metadata.microdata.push({ property: prop, value: content });
        }
      }
      
      // Look for time elements
      const timeElements = element.querySelectorAll('time');
      for (const time of timeElements) {
        if (!metadata.date && time.dateTime) {
          metadata.date = time.dateTime;
        }
      }
    }
    
    return metadata;
  }
  
  determineLayout(elements) {
    // Check if elements form a grid
    const positions = elements.map(el => {
      const rect = el.getBoundingClientRect();
      return { x: rect.left, y: rect.top, width: rect.width, height: rect.height };
    });
    
    // Check for grid layout (multiple elements on same row)
    const rows = new Map();
    for (const pos of positions) {
      const row = Math.round(pos.y / 10) * 10; // Round to nearest 10px
      if (!rows.has(row)) {
        rows.set(row, []);
      }
      rows.get(row).push(pos);
    }
    
    // If multiple elements share rows, it's likely a grid
    const hasGrid = Array.from(rows.values()).some(row => row.length > 1);
    
    if (hasGrid) {
      return 'grid';
    }
    
    // Check for mixed layout (significant variation in widths)
    const widths = positions.map(p => p.width);
    const avgWidth = widths.reduce((a, b) => a + b, 0) / widths.length;
    const variance = widths.reduce((sum, w) => sum + Math.pow(w - avgWidth, 2), 0) / widths.length;
    const stdDev = Math.sqrt(variance);
    
    if (stdDev / avgWidth > 0.3) {
      return 'mixed';
    }
    
    return 'linear';
  }
  
  calculateMaxDepth(elements) {
    let maxDepth = 0;
    
    for (const element of elements) {
      const depth = this.getElementDepth(element);
      maxDepth = Math.max(maxDepth, depth);
    }
    
    return maxDepth;
  }
  
  getElementDepth(element, depth = 0) {
    if (element.children.length === 0) {
      return depth;
    }
    
    let maxChildDepth = depth;
    for (const child of element.children) {
      const childDepth = this.getElementDepth(child, depth + 1);
      maxChildDepth = Math.max(maxChildDepth, childDepth);
    }
    
    return maxChildDepth;
  }
  
  findCommonAncestor(elements) {
    if (elements.length === 0) return null;
    if (elements.length === 1) return elements[0].parentElement;
    
    // Start with the first element's ancestors
    let ancestor = elements[0];
    const ancestors = [];
    
    while (ancestor) {
      ancestors.push(ancestor);
      ancestor = ancestor.parentElement;
    }
    
    // Find the deepest common ancestor
    for (const ancestorCandidate of ancestors) {
      let isCommon = true;
      
      for (const element of elements) {
        if (!ancestorCandidate.contains(element)) {
          isCommon = false;
          break;
        }
      }
      
      if (isCommon) {
        return ancestorCandidate;
      }
    }
    
    return document.body;
  }
  
  matchesPattern(text, patterns) {
    return patterns.some(pattern => text.includes(pattern));
  }
}