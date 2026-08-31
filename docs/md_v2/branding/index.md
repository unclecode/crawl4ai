# 🎨 Crawl4AI Brand Book

<style>
/* Brand Book Styles */
.brand-hero {
    background: linear-gradient(135deg, #070708 0%, #1a1a1a 100%);
    border: 2px solid #50ffff;
    padding: 3rem;
    margin: 2rem 0;
    border-radius: 12px;
    text-align: center;
}

.brand-hero h1 {
    font-size: 2.5rem;
    margin: 0 0 1rem 0;
    background: linear-gradient(135deg, #50ffff 0%, #f380f5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.brand-hero p {
    font-size: 1.1rem;
    color: #d5cec0;
    margin: 0;
}

/* Color System */
.color-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.color-card {
    background: #1a1a1a;
    border: 1px solid #3f3f44;
    border-radius: 8px;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: pointer;
}

.color-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(80, 255, 255, 0.2);
}

.color-swatch {
    height: 120px;
    width: 100%;
    position: relative;
}

.color-info {
    padding: 1rem;
}

.color-name {
    font-weight: 600;
    color: #e8e9ed;
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
}

.color-value {
    font-family: 'Monaco', monospace;
    font-size: 0.875rem;
    color: #09b5a5;
    background: #070708;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    display: inline-block;
}

.color-usage {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: #a3abba;
}

/* Typography Showcase */
.type-specimen {
    background: #1a1a1a;
    border: 1px solid #3f3f44;
    padding: 2rem;
    margin: 1.5rem 0;
    border-radius: 8px;
}

.type-specimen h1,
.type-specimen h2,
.type-specimen h3,
.type-specimen h4 {
    margin-top: 0;
}

.type-label {
    display: inline-block;
    background: #50ffff;
    color: #070708;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.type-details {
    display: flex;
    gap: 2rem;
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: #a3abba;
    font-family: 'Monaco', monospace;
}

/* Component Showcase */
.component-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin: 2rem 0;
}

.component-card {
    background: #1a1a1a;
    border: 1px solid #3f3f44;
    border-radius: 8px;
    padding: 1.5rem;
}

.component-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #e8e9ed;
    margin: 0 0 1rem 0;
}

.component-demo {
    background: #070708;
    padding: 1.5rem;
    border-radius: 8px;
    margin: 1rem 0;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
}

/* Buttons */
.brand-btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 6px;
    font-family: 'Dank Mono', Monaco, monospace;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    display: inline-block;
}

.brand-btn-primary {
    background: #50ffff;
    color: #070708;
}

.brand-btn-primary:hover {
    background: #09b5a5;
    transform: scale(1.05);
}

.brand-btn-secondary {
    background: #3f3f44;
    color: #e8e9ed;
    border: 1px solid #50ffff;
}

.brand-btn-secondary:hover {
    background: #50ffff;
    color: #070708;
}

.brand-btn-accent {
    background: #f380f5;
    color: #070708;
}

.brand-btn-accent:hover {
    background: #d060d5;
    transform: scale(1.05);
}

.brand-btn-ghost {
    background: transparent;
    color: #50ffff;
    border: 2px solid #50ffff;
}

.brand-btn-ghost:hover {
    background: #50ffff;
    color: #070708;
}

.brand-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none !important;
}

/* Badges */
.brand-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.badge-available {
    background: #50ffff;
    color: #070708;
}

.badge-beta {
    background: #f59e0b;
    color: #070708;
}

.badge-alpha {
    background: #f380f5;
    color: #070708;
}

.badge-new {
    background: #50ff50;
    color: #070708;
}

.badge-coming-soon {
    background: #2a2a2a;
    color: #888;
}

/* Cards */
.brand-card {
    background: #3f3f44;
    border: 1px solid #3f3f44;
    border-radius: 8px;
    padding: 1.5rem;
    transition: all 0.3s ease;
}

.brand-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
    border-color: #50ffff;
}

.brand-card-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #e8e9ed;
    margin: 0 0 0.5rem 0;
}

.brand-card-description {
    color: #a3abba;
    line-height: 1.6;
    margin: 0;
}

/* Terminal Window */
.terminal-window {
    background: #1a1a1a;
    border: 1px solid #3f3f44;
    border-radius: 8px;
    overflow: hidden;
    margin: 1.5rem 0;
}

.terminal-header {
    background: #3f3f44;
    padding: 0.75rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.terminal-dots {
    display: flex;
    gap: 0.5rem;
}

.terminal-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}

.terminal-dot.red { background: #ff3c74; }
.terminal-dot.yellow { background: #f59e0b; }
.terminal-dot.green { background: #50ff50; }

.terminal-title {
    color: #d5cec0;
    font-size: 0.875rem;
}

.terminal-content {
    padding: 1.5rem;
}

/* Code Display */
.code-showcase {
    background: #070708;
    border: 1px solid #3f3f44;
    border-radius: 8px;
    overflow: hidden;
    margin: 1rem 0;
}

.code-header {
    background: #1a1a1a;
    padding: 0.5rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.code-language {
    color: #09b5a5;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.copy-code-btn {
    background: transparent;
    border: 1px solid #3f3f44;
    color: #a3abba;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.copy-code-btn:hover {
    background: #50ffff;
    color: #070708;
    border-color: #50ffff;
}

/* Spacing System */
.spacing-demo {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin: 1.5rem 0;
}

.spacing-item {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.spacing-visual {
    height: 40px;
    background: #50ffff;
    border-radius: 4px;
    transition: all 0.2s ease;
}

.spacing-label {
    font-family: 'Monaco', monospace;
    color: #e8e9ed;
    font-size: 0.875rem;
}

/* Layout Patterns */
.layout-example {
    background: #1a1a1a;
    border: 1px solid #3f3f44;
    border-radius: 8px;
    padding: 1rem;
    margin: 1.5rem 0;
}

.layout-preview {
    background: #070708;
    padding: 1rem;
    border-radius: 4px;
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #a3abba;
    font-size: 0.875rem;
}

/* Usage Guidelines */
.guideline-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    margin: 2rem 0;
}

.do-card,
.dont-card {
    background: #1a1a1a;
    border-radius: 8px;
    overflow: hidden;
}

.do-card {
    border: 2px solid #50ff50;
}

.dont-card {
    border: 2px solid #ff3c74;
}

.card-header {
    padding: 0.75rem 1rem;
    font-weight: 600;
    text-align: center;
}

.do-card .card-header {
    background: #50ff5020;
    color: #50ff50;
}

.dont-card .card-header {
    background: #ff3c7420;
    color: #ff3c74;
}

.card-example {
    padding: 2rem;
    min-height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Section Headers */
.section-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 3rem 0 1.5rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #3f3f44;
}

.section-icon {
    font-size: 2rem;
}

.section-title {
    font-size: 1.75rem;
    margin: 0;
    color: #e8e9ed;
}

/* Interactive Demo */
.interactive-demo {
    background: #1a1a1a;
    border: 1px solid #3f3f44;
    border-radius: 8px;
    padding: 2rem;
    margin: 2rem 0;
}

.demo-controls {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
}

.demo-output {
    background: #070708;
    border: 1px solid #3f3f44;
    border-radius: 8px;
    padding: 2rem;
    min-height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Responsive */
@media (max-width: 768px) {
    .color-grid {
        grid-template-columns: 1fr;
    }

    .component-grid {
        grid-template-columns: 1fr;
    }

    .guideline-grid {
        grid-template-columns: 1fr;
    }

    .brand-hero {
        padding: 2rem 1rem;
    }

    .brand-hero h1 {
        font-size: 1.75rem;
    }
}

/* Click to copy */
.click-to-copy {
    cursor: pointer;
    position: relative;
}

.click-to-copy:hover::after {
    content: 'Click to copy';
    position: absolute;
    bottom: -2rem;
    left: 50%;
    transform: translateX(-50%);
    background: #070708;
    border: 1px solid #50ffff;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.75rem;
    white-space: nowrap;
    z-index: 10;
}

.copied-indicator {
    position: fixed;
    top: 2rem;
    right: 2rem;
    background: #50ff50;
    color: #070708;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    opacity: 0;
    animation: fadeInOut 2s ease-in-out;
    z-index: 1000;
}

@keyframes fadeInOut {
    0%, 100% { opacity: 0; }
    10%, 90% { opacity: 1; }
}
</style>

<div class="brand-hero">
    <h1>Crawl4AI Brand Guidelines</h1>
    <p>A comprehensive design system for building consistent, terminal-inspired experiences</p>
</div>

## 📖 About This Guide

This brand book documents the complete visual language of Crawl4AI. Whether you're building documentation pages, interactive apps, or Chrome extensions, these guidelines ensure consistency while maintaining the unique terminal-aesthetic that defines our brand.

---

<div class="section-header">
    <span class="section-icon">🎨</span>
    <h2 class="section-title">Color System</h2>
</div>

Our color palette is built around a terminal-dark aesthetic with vibrant cyan and pink accents. Every color serves a purpose and maintains accessibility standards.

### Primary Colors

<div class="color-grid">
    <div class="color-card click-to-copy" onclick="copyToClipboard('#50ffff', this)">
        <div class="color-swatch" style="background: #50ffff;"></div>
        <div class="color-info">
            <p class="color-name">Primary Cyan</p>
            <code class="color-value">#50ffff</code>
            <p class="color-usage">Main brand color, links, highlights, CTAs</p>
        </div>
    </div>

    <div class="color-card click-to-copy" onclick="copyToClipboard('#09b5a5', this)">
        <div class="color-swatch" style="background: #09b5a5;"></div>
        <div class="color-info">
            <p class="color-name">Primary Teal</p>
            <code class="color-value">#09b5a5</code>
            <p class="color-usage">Hover states, dimmed accents, progress bars</p>
        </div>
    </div>

    <div class="color-card click-to-copy" onclick="copyToClipboard('#0fbbaa', this)">
        <div class="color-swatch" style="background: #0fbbaa;"></div>
        <div class="color-info">
            <p class="color-name">Primary Green</p>
            <code class="color-value">#0fbbaa</code>
            <p class="color-usage">Alternative primary, buttons, nav links</p>
        </div>
    </div>

    <div class="color-card click-to-copy" onclick="copyToClipboard('#f380f5', this)">
        <div class="color-swatch" style="background: #f380f5;"></div>
        <div class="color-info">
            <p class="color-name">Accent Pink</p>
            <code class="color-value">#f380f5</code>
            <p class="color-usage">Secondary accents, keywords, highlights</p>
        </div>
    </div>
</div>

### Background Colors

<div class="color-grid">
    <div class="color-card click-to-copy" onclick="copyToClipboard('#070708', this)">
        <div class="color-swatch" style="background: #070708; border: 1px solid #3f3f44;"></div>
        <div class="color-info">
            <p class="color-name">Deep Black</p>
            <code class="color-value">#070708</code>
            <p class="color-usage">Main background, code blocks, deep containers</p>
        </div>
    </div>

    <div class="color-card click-to-copy" onclick="copyToClipboard('#1a1a1a', this)">
        <div class="color-swatch" style="background: #1a1a1a;"></div>
        <div class="color-info">
            <p class="color-name">Secondary Dark</p>
            <code class="color-value">#1a1a1a</code>
            <p class="color-usage">Headers, sidebars, secondary containers</p>
        </div>
    </div>

    <div class="color-card click-to-copy" onclick="copyToClipboard('#3f3f44', this)">
        <div class="color-swatch" style="background: #3f3f44;"></div>
        <div class="color-info">
            <p class="color-name">Tertiary Gray</p>
            <code class="color-value">#3f3f44</code>
            <p class="color-usage">Cards, borders, code backgrounds, modals</p>
        </div>
    </div>

    <div class="color-card click-to-copy" onclick="copyToClipboard('#202020', this)">
        <div class="color-swatch" style="background: #202020;"></div>
        <div class="color-info">
            <p class="color-name">Block Background</p>
            <code class="color-value">#202020</code>
            <p class="color-usage">Block elements, alternate rows</p>
        </div>
    </div>
</div>

### Text Colors

<div class="color-grid">
    <div class="color-card click-to-copy" onclick="copyToClipboard('#e8e9ed', this)">
        <div class="color-swatch" style="background: #e8e9ed;"></div>
        <div class="color-info">
            <p class="color-name">Primary Text</p>
            <code class="color-value">#e8e9ed</code>
            <p class="color-usage">Headings, body text, primary content</p>
        </div>
    </div>

    <div class="color-card click-to-copy" onclick="copyToClipboard('#d5cec0', this)">
        <div class="color-swatch" style="background: #d5cec0;"></div>
        <div class="color-info">
            <p class="color-name">Secondary Text</p>
            <code class="color-value">#d5cec0</code>
            <p class="color-usage">Body text, descriptions, warm tone</p>
        </div>
    </div>

    <div class="color-card click-to-copy" onclick="copyToClipboard('#a3abba', this)">
        <div class="color-swatch" style="background: #a3abba;"></div>
        <div class="color-info">
            <p class="color-name">Tertiary Text</p>
            <code class="color-value">#a3abba</code>
            <p class="color-usage">Captions, labels, metadata, cool tone</p>
        </div>
    </div>

    <div class="color-card click-to-copy" onclick="copyToClipboard('#8b857a', this)">
        <div class="color-swatch" style="background: #8b857a;"></div>
        <div class="color-info">
            <p class="color-name">Dimmed Text</p>
            <code class="color-value">#8b857a</code>
            <p class="color-usage">Disabled states, comments, subtle text</p>
        </div>
    </div>
</div>

### Semantic Colors

<div class="color-grid">
    <div class="color-card click-to-copy" onclick="copyToClipboard('#50ff50', this)">
        <div class="color-swatch" style="background: #50ff50;"></div>
        <div class="color-info">
            <p class="color-name">Success Green</p>
            <code class="color-value">#50ff50</code>
            <p class="color-usage">Success messages, completed states, valid</p>
        </div>
    </div>

    <div class="color-card click-to-copy" onclick="copyToClipboard('#ff3c74', this)">
        <div class="color-swatch" style="background: #ff3c74;"></div>
        <div class="color-info">
            <p class="color-name">Error Red</p>
            <code class="color-value">#ff3c74</code>
            <p class="color-usage">Errors, warnings, destructive actions</p>
        </div>
    </div>

    <div class="color-card click-to-copy" onclick="copyToClipboard('#f59e0b', this)">
        <div class="color-swatch" style="background: #f59e0b;"></div>
        <div class="color-info">
            <p class="color-name">Warning Orange</p>
            <code class="color-value">#f59e0b</code>
            <p class="color-usage">Warnings, beta status, caution</p>
        </div>
    </div>

    <div class="color-card click-to-copy" onclick="copyToClipboard('#4a9eff', this)">
        <div class="color-swatch" style="background: #4a9eff;"></div>
        <div class="color-info">
            <p class="color-name">Info Blue</p>
            <code class="color-value">#4a9eff</code>
            <p class="color-usage">Info messages, external links</p>
        </div>
    </div>
</div>

---

<div class="section-header">
    <span class="section-icon">✍️</span>
    <h2 class="section-title">Typography</h2>
</div>

Our typography system is built around **Dank Mono**, a monospace font that reinforces the terminal aesthetic while maintaining excellent readability.

### Font Family

```css
--font-primary: 'Dank Mono', dm, Monaco, Courier New, monospace;
--font-code: 'Dank Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
```

**Font Weights:**
- Regular: 400
- Bold: 700
- Italic: 400 (italic variant)

### Type Scale

<div class="type-specimen">
    <span class="type-label">H1 / Hero</span>
    <div class="type-details">
        <span>Size: 2.5rem (40px)</span>
        <span>Weight: 700</span>
        <span>Line-height: 1.2</span>
    </div>
    <h1 style="font-size: 2.5rem; margin-top: 1rem;">The Quick Brown Fox Jumps Over</h1>
</div>

<div class="type-specimen">
    <span class="type-label">H2 / Section</span>
    <div class="type-details">
        <span>Size: 1.75rem (28px)</span>
        <span>Weight: 700</span>
        <span>Line-height: 1.3</span>
    </div>
    <h2 style="font-size: 1.75rem; margin-top: 1rem;">Advanced Web Scraping Features</h2>
</div>

<div class="type-specimen">
    <span class="type-label">H3 / Subsection</span>
    <div class="type-details">
        <span>Size: 1.3rem (20.8px)</span>
        <span>Weight: 600</span>
        <span>Line-height: 1.4</span>
    </div>
    <h3 style="font-size: 1.3rem; margin-top: 1rem;">Installation and Setup Guide</h3>
</div>

<div class="type-specimen">
    <span class="type-label">H4 / Component</span>
    <div class="type-details">
        <span>Size: 1.1rem (17.6px)</span>
        <span>Weight: 600</span>
        <span>Line-height: 1.4</span>
    </div>
    <h4 style="font-size: 1.1rem; margin-top: 1rem;">Quick Start Instructions</h4>
</div>

<div class="type-specimen">
    <span class="type-label">Body / Regular</span>
    <div class="type-details">
        <span>Size: 14px</span>
        <span>Weight: 400</span>
        <span>Line-height: 1.6</span>
    </div>
    <p style="margin-top: 1rem; font-size: 14px;">Crawl4AI is the #1 trending GitHub repository, actively maintained by a vibrant community. It delivers blazing-fast, AI-ready web crawling tailored for large language models and data pipelines.</p>
</div>

<div class="type-specimen">
    <span class="type-label">Code / Monospace</span>
    <div class="type-details">
        <span>Size: 13px</span>
        <span>Weight: 400</span>
        <span>Line-height: 1.5</span>
    </div>
    <code style="margin-top: 1rem; display: block; background: #070708; padding: 1rem; border-radius: 4px;">async with AsyncWebCrawler() as crawler:</code>
</div>

<div class="type-specimen">
    <span class="type-label">Small / Caption</span>
    <div class="type-details">
        <span>Size: 12px</span>
        <span>Weight: 400</span>
        <span>Line-height: 1.5</span>
    </div>
    <p style="margin-top: 1rem; font-size: 12px; color: #a3abba;">Updated 2 hours ago • v0.7.2</p>
</div>

---

<div class="section-header">
    <span class="section-icon">🧩</span>
    <h2 class="section-title">Components</h2>
</div>

### Buttons

<div class="component-grid">
    <div class="component-card">
        <h3 class="component-title">Primary Button</h3>
        <div class="component-demo">
            <button class="brand-btn brand-btn-primary">Launch Editor →</button>
            <button class="brand-btn brand-btn-primary" disabled>Processing...</button>
        </div>
        <div class="code-showcase">
            <div class="code-header">
                <span class="code-language">HTML + CSS</span>
                <button class="copy-code-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre style="margin: 0; padding: 1rem; background: #070708;"><code>&lt;button class="brand-btn brand-btn-primary"&gt;
  Launch Editor →
&lt;/button&gt;</code></pre>
        </div>
    </div>

    <div class="component-card">
        <h3 class="component-title">Secondary Button</h3>
        <div class="component-demo">
            <button class="brand-btn brand-btn-secondary">View Documentation</button>
            <button class="brand-btn brand-btn-secondary" disabled>Loading...</button>
        </div>
        <div class="code-showcase">
            <div class="code-header">
                <span class="code-language">HTML + CSS</span>
                <button class="copy-code-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre style="margin: 0; padding: 1rem; background: #070708;"><code>&lt;button class="brand-btn brand-btn-secondary"&gt;
  View Documentation
&lt;/button&gt;</code></pre>
        </div>
    </div>

    <div class="component-card">
        <h3 class="component-title">Accent Button</h3>
        <div class="component-demo">
            <button class="brand-btn brand-btn-accent">Try Beta Features</button>
            <button class="brand-btn brand-btn-accent" disabled>Unavailable</button>
        </div>
        <div class="code-showcase">
            <div class="code-header">
                <span class="code-language">HTML + CSS</span>
                <button class="copy-code-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre style="margin: 0; padding: 1rem; background: #070708;"><code>&lt;button class="brand-btn brand-btn-accent"&gt;
  Try Beta Features
&lt;/button&gt;</code></pre>
        </div>
    </div>

    <div class="component-card">
        <h3 class="component-title">Ghost Button</h3>
        <div class="component-demo">
            <button class="brand-btn brand-btn-ghost">Learn More</button>
            <button class="brand-btn brand-btn-ghost" disabled>Coming Soon</button>
        </div>
        <div class="code-showcase">
            <div class="code-header">
                <span class="code-language">HTML + CSS</span>
                <button class="copy-code-btn" onclick="copyCode(this)">Copy</button>
            </div>
            <pre style="margin: 0; padding: 1rem; background: #070708;"><code>&lt;button class="brand-btn brand-btn-ghost"&gt;
  Learn More
&lt;/button&gt;</code></pre>
        </div>
    </div>
</div>

### Badges & Status Indicators

<div class="component-card" style="max-width: 800px; margin: 2rem 0;">
    <h3 class="component-title">Status Badges</h3>
    <div class="component-demo" style="flex-direction: row; flex-wrap: wrap;">
        <span class="brand-badge badge-available">Available</span>
        <span class="brand-badge badge-beta">Beta</span>
        <span class="brand-badge badge-alpha">Alpha</span>
        <span class="brand-badge badge-new">New!</span>
        <span class="brand-badge badge-coming-soon">Coming Soon</span>
    </div>
    <div class="code-showcase">
        <div class="code-header">
            <span class="code-language">HTML + CSS</span>
            <button class="copy-code-btn" onclick="copyCode(this)">Copy</button>
        </div>
        <pre style="margin: 0; padding: 1rem; background: #070708;"><code>&lt;span class="brand-badge badge-available"&gt;Available&lt;/span&gt;
&lt;span class="brand-badge badge-beta"&gt;Beta&lt;/span&gt;
&lt;span class="brand-badge badge-alpha"&gt;Alpha&lt;/span&gt;
&lt;span class="brand-badge badge-new"&gt;New!&lt;/span&gt;</code></pre>
    </div>
</div>

### Cards

<div class="component-grid">
    <div class="brand-card">
        <h3 class="brand-card-title">🎨 C4A-Script Editor</h3>
        <p class="brand-card-description">A visual, block-based programming environment for creating browser automation scripts. Perfect for beginners and experts alike!</p>
        <button class="brand-btn brand-btn-primary" style="margin-top: 1rem;">Launch Editor →</button>
    </div>

    <div class="brand-card">
        <h3 class="brand-card-title">🧠 LLM Context Builder</h3>
        <p class="brand-card-description">Generate optimized context files for your favorite LLM when working with Crawl4AI. Get focused, relevant documentation based on your needs.</p>
        <button class="brand-btn brand-btn-primary" style="margin-top: 1rem;">Launch Builder →</button>
    </div>
</div>

<div class="code-showcase" style="margin-top: 2rem;">
    <div class="code-header">
        <span class="code-language">HTML + CSS</span>
        <button class="copy-code-btn" onclick="copyCode(this)">Copy</button>
    </div>
    <pre style="margin: 0; padding: 1rem; background: #070708;"><code>&lt;div class="brand-card"&gt;
  &lt;h3 class="brand-card-title"&gt;Card Title&lt;/h3&gt;
  &lt;p class="brand-card-description"&gt;Card description...&lt;/p&gt;
&lt;/div&gt;</code></pre>
</div>

### Terminal Window

<div class="terminal-window">
    <div class="terminal-header">
        <div class="terminal-dots">
            <span class="terminal-dot red"></span>
            <span class="terminal-dot yellow"></span>
            <span class="terminal-dot green"></span>
        </div>
        <span class="terminal-title">crawl4ai@terminal ~ %</span>
    </div>
    <div class="terminal-content">
        <p style="color: #09b5a5; margin: 0;">$ pip install crawl4ai</p>
        <p style="color: #d5cec0; margin: 0.5rem 0 0 0;">Successfully installed crawl4ai-0.7.2</p>
    </div>
</div>

<div class="code-showcase">
    <div class="code-header">
        <span class="code-language">HTML + CSS</span>
        <button class="copy-code-btn" onclick="copyCode(this)">Copy</button>
    </div>
    <pre style="margin: 0; padding: 1rem; background: #070708;"><code>&lt;div class="terminal-window"&gt;
  &lt;div class="terminal-header"&gt;
    &lt;div class="terminal-dots"&gt;
      &lt;span class="terminal-dot red"&gt;&lt;/span&gt;
      &lt;span class="terminal-dot yellow"&gt;&lt;/span&gt;
      &lt;span class="terminal-dot green"&gt;&lt;/span&gt;
    &lt;/div&gt;
    &lt;span class="terminal-title"&gt;Terminal Title&lt;/span&gt;
  &lt;/div&gt;
  &lt;div class="terminal-content"&gt;
    Your content here
  &lt;/div&gt;
&lt;/div&gt;</code></pre>
</div>

---

<div class="section-header">
    <span class="section-icon">📐</span>
    <h2 class="section-title">Spacing & Layout</h2>
</div>

### Spacing System

Our spacing system is based on multiples of **10px** for consistency and ease of calculation.

<div class="spacing-demo">
    <div class="spacing-item">
        <div class="spacing-visual" style="width: 10px;"></div>
        <span class="spacing-label">10px - Extra Small (xs)</span>
    </div>
    <div class="spacing-item">
        <div class="spacing-visual" style="width: 20px;"></div>
        <span class="spacing-label">20px - Small (sm)</span>
    </div>
    <div class="spacing-item">
        <div class="spacing-visual" style="width: 30px;"></div>
        <span class="spacing-label">30px - Medium (md)</span>
    </div>
    <div class="spacing-item">
        <div class="spacing-visual" style="width: 40px;"></div>
        <span class="spacing-label">40px - Large (lg)</span>
    </div>
    <div class="spacing-item">
        <div class="spacing-visual" style="width: 60px;"></div>
        <span class="spacing-label">60px - Extra Large (xl)</span>
    </div>
    <div class="spacing-item">
        <div class="spacing-visual" style="width: 80px;"></div>
        <span class="spacing-label">80px - 2XL</span>
    </div>
</div>

### Layout Patterns

#### Terminal Container
Full-height, flex-column layout with sticky header

```css
.terminal-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}
```

#### Content Grid
Auto-fit responsive grid for cards and components

```css
.component-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}
```

#### Centered Content
Maximum width with auto margins for centered layouts

```css
.content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}
```

---

<div class="section-header">
    <span class="section-icon">✅</span>
    <h2 class="section-title">Usage Guidelines</h2>
</div>

### When to Use Each Style

**Documentation Pages (`docs/md_v2/core`, `/advanced`, etc.)**
- Use main documentation styles from `styles.css` and `layout.css`
- Terminal theme with sidebar navigation
- Dense, informative content
- ToC on the right side
- Focus on readability and technical accuracy

**Landing Pages (`docs/md_v2/apps/crawl4ai-assistant`, etc.)**
- Use `assistant.css` style approach
- Hero sections with gradients
- Feature cards with hover effects
- Video/demo sections
- Sticky header with navigation
- Marketing-focused, visually engaging

**App Home (`docs/md_v2/apps/index.md`)**
- Grid-based card layouts
- Status badges
- Call-to-action buttons
- Feature highlights
- Mix of informational and promotional

**Interactive Apps (`docs/md_v2/apps/llmtxt`, `/c4a-script`)**
- Full-screen application layouts
- Interactive controls
- Real-time feedback
- Tool-specific UI patterns
- Functional over decorative

**Chrome Extension (`popup.css`)**
- Compact, fixed-width design (380px)
- Clear mode selection
- Session indicators
- Minimal but effective
- Fast loading, no heavy assets

### Do's and Don'ts

<div class="guideline-grid">
    <div class="do-card">
        <div class="card-header">✅ DO</div>
        <div class="card-example">
            <button class="brand-btn brand-btn-primary">Launch App →</button>
        </div>
        <div style="padding: 1rem; font-size: 0.875rem; color: #d5cec0;">
            Use primary cyan for main CTAs and important actions
        </div>
    </div>

    <div class="dont-card">
        <div class="card-header">❌ DON'T</div>
        <div class="card-example">
            <button style="padding: 0.75rem 1.5rem; background: #ff0000; color: white; border: none; border-radius: 6px;">Launch App →</button>
        </div>
        <div style="padding: 1rem; font-size: 0.875rem; color: #d5cec0;">
            Don't use arbitrary colors not in the brand palette
        </div>
    </div>
</div>

<div class="guideline-grid">
    <div class="do-card">
        <div class="card-header">✅ DO</div>
        <div class="card-example">
            <div style="font-family: 'Dank Mono', monospace; color: #e8e9ed;">
                <code>async with AsyncWebCrawler():</code>
            </div>
        </div>
        <div style="padding: 1rem; font-size: 0.875rem; color: #d5cec0;">
            Use Dank Mono for all text to maintain terminal aesthetic
        </div>
    </div>

    <div class="dont-card">
        <div class="card-header">❌ DON'T</div>
        <div class="card-example">
            <div style="font-family: 'Arial', sans-serif; color: #e8e9ed;">
                async with AsyncWebCrawler():
            </div>
        </div>
        <div style="padding: 1rem; font-size: 0.875rem; color: #d5cec0;">
            Don't use non-monospace fonts (breaks terminal feel)
        </div>
    </div>
</div>

<div class="guideline-grid">
    <div class="do-card">
        <div class="card-header">✅ DO</div>
        <div class="card-example">
            <div class="brand-card" style="padding: 1rem;">
                <span class="brand-badge badge-beta">Beta</span>
                <h4 style="margin: 0.5rem 0; font-size: 1rem;">New Feature</h4>
            </div>
        </div>
        <div style="padding: 1rem; font-size: 0.875rem; color: #d5cec0;">
            Use status badges to indicate feature maturity
        </div>
    </div>

    <div class="dont-card">
        <div class="card-header">❌ DON'T</div>
        <div class="card-example">
            <div class="brand-card" style="padding: 1rem;">
                <h4 style="margin: 0; font-size: 1rem;">New Feature (Beta)</h4>
            </div>
        </div>
        <div style="padding: 1rem; font-size: 0.875rem; color: #d5cec0;">
            Don't put status indicators in plain text
        </div>
    </div>
</div>

---

<div class="section-header">
    <span class="section-icon">🎯</span>
    <h2 class="section-title">Accessibility</h2>
</div>

### Color Contrast

All color combinations meet WCAG AA standards:

- **Primary Cyan (#50ffff) on Dark (#070708)**: 12.4:1 ✅
- **Primary Text (#e8e9ed) on Dark (#070708)**: 11.8:1 ✅
- **Secondary Text (#d5cec0) on Dark (#070708)**: 9.2:1 ✅
- **Tertiary Text (#a3abba) on Dark (#070708)**: 6.8:1 ✅

### Focus States

All interactive elements must have visible focus indicators:

```css
button:focus,
a:focus {
    outline: 2px solid #50ffff;
    outline-offset: 2px;
}
```

### Motion

Respect `prefers-reduced-motion` for users who need it:

```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

---

<div class="section-header">
    <span class="section-icon">💾</span>
    <h2 class="section-title">CSS Variables</h2>
</div>

Use these CSS variables for consistency across all styles:

```css
:root {
    /* Colors */
    --primary-color: #50ffff;
    --primary-dimmed: #09b5a5;
    --primary-green: #0fbbaa;
    --accent-color: #f380f5;

    /* Backgrounds */
    --background-color: #070708;
    --bg-secondary: #1a1a1a;
    --code-bg-color: #3f3f44;
    --border-color: #3f3f44;

    /* Text */
    --font-color: #e8e9ed;
    --secondary-color: #d5cec0;
    --tertiary-color: #a3abba;

    /* Semantic */
    --success-color: #50ff50;
    --error-color: #ff3c74;
    --warning-color: #f59e0b;

    /* Typography */
    --font-primary: 'Dank Mono', dm, Monaco, Courier New, monospace;
    --global-font-size: 14px;
    --global-line-height: 1.6;

    /* Spacing */
    --global-space: 10px;

    /* Layout */
    --header-height: 65px;
    --sidebar-width: 280px;
    --toc-width: 340px;
    --content-max-width: 90em;
}
```

---

<div class="section-header">
    <span class="section-icon">📚</span>
    <h2 class="section-title">Resources</h2>
</div>

### Download Assets

- [Dank Mono Font Files](/docs/md_v2/assets/) (Regular, Bold, Italic)
- [Brand CSS Template](/docs/md_v2/branding/assets/brand-examples.css)
- [Component Library](/docs/md_v2/apps/)

### Reference Files

- Main Documentation Styles: `docs/md_v2/assets/styles.css`
- Layout System: `docs/md_v2/assets/layout.css`
- Landing Page Style: `docs/md_v2/apps/crawl4ai-assistant/assistant.css`
- App Home Style: `docs/md_v2/apps/index.md`
- Extension Style: `docs/md_v2/apps/crawl4ai-assistant/popup/popup.css`

### Questions?

If you're unsure about which style to use or need help implementing these guidelines:

- Check existing examples in the relevant section
- Review the "When to Use Each Style" guidelines above
- Ask in our [Discord community](https://discord.gg/crawl4ai)
- Open an issue on [GitHub](https://github.com/unclecode/crawl4ai)

---

<div style="background: #1a1a1a; border: 1px solid #50ffff; border-radius: 8px; padding: 2rem; margin: 3rem 0; text-align: center;">
    <h3 style="margin: 0 0 1rem 0; color: #50ffff;">🎨 Keep It Terminal</h3>
    <p style="margin: 0; color: #d5cec0; font-size: 1rem;">
        When in doubt, ask yourself: "Does this feel like a terminal?" If yes, you're on brand.
    </p>
</div>

<script>
// Copy to clipboard functionality
function copyToClipboard(text, element) {
    navigator.clipboard.writeText(text).then(() => {
        // Show copied indicator
        const indicator = document.createElement('div');
        indicator.className = 'copied-indicator';
        indicator.textContent = `Copied: ${text}`;
        document.body.appendChild(indicator);

        setTimeout(() => {
            indicator.remove();
        }, 2000);
    });
}

function copyCode(button) {
    const codeBlock = button.closest('.code-showcase').querySelector('code');
    const text = codeBlock.textContent;

    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.style.background = '#50ff50';
        button.style.color = '#070708';

        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = 'transparent';
            button.style.color = '#a3abba';
        }, 2000);
    });
}

// Add click-to-copy to all color values
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.color-value').forEach(el => {
        el.style.cursor = 'pointer';
        el.addEventListener('click', (e) => {
            e.stopPropagation();
            copyToClipboard(el.textContent, el);
        });
    });
});
</script>
