// App Detail Page JavaScript
const { API_BASE, API_ORIGIN } = (() => {
    const { hostname, port, protocol } = window.location;
    const isLocalHost = ['localhost', '127.0.0.1', '0.0.0.0'].includes(hostname);

    if (isLocalHost && port && port !== '8100') {
        const origin = `${protocol}//127.0.0.1:8100`;
        return { API_BASE: `${origin}/marketplace/api`, API_ORIGIN: origin };
    }

    return { API_BASE: '/marketplace/api', API_ORIGIN: '' };
})();

class AppDetailPage {
    constructor() {
        this.appSlug = this.getAppSlugFromURL();
        this.appData = null;
        this.init();
    }

    getAppSlugFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get('app') || '';
    }

    async init() {
        if (!this.appSlug) {
            window.location.href = 'index.html';
            return;
        }

        await this.loadAppDetails();
        this.setupEventListeners();
        await this.loadRelatedApps();
    }

    async loadAppDetails() {
        try {
            const response = await fetch(`${API_BASE}/apps/${this.appSlug}`);
            if (!response.ok) throw new Error('App not found');

            this.appData = await response.json();
            this.renderAppDetails();
        } catch (error) {
            console.error('Error loading app details:', error);
            // Fallback to loading all apps and finding the right one
            try {
                const response = await fetch(`${API_BASE}/apps`);
                const apps = await response.json();
                this.appData = apps.find(app => app.slug === this.appSlug || app.name.toLowerCase().replace(/\s+/g, '-') === this.appSlug);
                if (this.appData) {
                    this.renderAppDetails();
                } else {
                    window.location.href = 'index.html';
                }
            } catch (err) {
                console.error('Error loading apps:', err);
                window.location.href = 'index.html';
            }
        }
    }

    renderAppDetails() {
        if (!this.appData) return;

        // Update title
        document.title = `${this.appData.name} - Crawl4AI Marketplace`;

        // Hero image
        const appImage = document.getElementById('app-image');
        if (this.appData.image) {
            appImage.style.backgroundImage = `url('${this.appData.image}')`;
            appImage.innerHTML = '';
        } else {
            appImage.innerHTML = `[${this.appData.category || 'APP'}]`;
        }

        // Basic info
        document.getElementById('app-name').textContent = this.appData.name;
        document.getElementById('app-description').textContent = this.appData.description;
        document.getElementById('app-type').textContent = this.appData.type || 'Open Source';
        document.getElementById('app-category').textContent = this.appData.category;
        document.getElementById('app-pricing').textContent = this.appData.pricing || 'Free';

        // Badges
        if (this.appData.featured) {
            document.getElementById('app-featured').style.display = 'inline-block';
        }
        if (this.appData.sponsored) {
            document.getElementById('app-sponsored').style.display = 'inline-block';
        }

        // Stats
        const rating = this.appData.rating || 0;
        const stars = '★'.repeat(Math.floor(rating)) + '☆'.repeat(5 - Math.floor(rating));
        document.getElementById('app-rating').textContent = stars + ` ${rating}/5`;
        document.getElementById('app-downloads').textContent = this.formatNumber(this.appData.downloads || 0);

        // Action buttons
        const websiteBtn = document.getElementById('app-website');
        const githubBtn = document.getElementById('app-github');

        if (this.appData.website_url) {
            websiteBtn.href = this.appData.website_url;
        } else {
            websiteBtn.style.display = 'none';
        }

        if (this.appData.github_url) {
            githubBtn.href = this.appData.github_url;
        } else {
            githubBtn.style.display = 'none';
        }

        // Contact
        document.getElementById('app-contact').textContent = this.appData.contact_email || 'Not available';

        // Integration guide
        this.renderIntegrationGuide();
    }

    renderIntegrationGuide() {
        // Installation code
        const installCode = document.getElementById('install-code');
        if (this.appData.type === 'Open Source' && this.appData.github_url) {
            installCode.textContent = `# Clone from GitHub
git clone ${this.appData.github_url}

# Install dependencies
pip install -r requirements.txt`;
        } else if (this.appData.name.toLowerCase().includes('api')) {
            installCode.textContent = `# Install via pip
pip install ${this.appData.slug}

# Or install from source
pip install git+${this.appData.github_url || 'https://github.com/example/repo'}`;
        }

        // Usage code - customize based on category
        const usageCode = document.getElementById('usage-code');
        if (this.appData.category === 'Browser Automation') {
            usageCode.textContent = `from crawl4ai import AsyncWebCrawler
from ${this.appData.slug.replace(/-/g, '_')} import ${this.appData.name.replace(/\s+/g, '')}

async def main():
    # Initialize ${this.appData.name}
    automation = ${this.appData.name.replace(/\s+/g, '')}()

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            browser_config=automation.config,
            wait_for="css:body"
        )
        print(result.markdown)`;
        } else if (this.appData.category === 'Proxy Services') {
            usageCode.textContent = `from crawl4ai import AsyncWebCrawler
import ${this.appData.slug.replace(/-/g, '_')}

# Configure proxy
proxy_config = {
    "server": "${this.appData.website_url || 'https://proxy.example.com'}",
    "username": "your_username",
    "password": "your_password"
}

async with AsyncWebCrawler(proxy=proxy_config) as crawler:
    result = await crawler.arun(
        url="https://example.com",
        bypass_cache=True
    )
    print(result.status_code)`;
        } else if (this.appData.category === 'LLM Integration') {
            usageCode.textContent = `from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

# Configure LLM extraction
strategy = LLMExtractionStrategy(
    provider="${this.appData.name.toLowerCase().includes('gpt') ? 'openai' : 'anthropic'}",
    api_key="your-api-key",
    model="${this.appData.name.toLowerCase().includes('gpt') ? 'gpt-4' : 'claude-3'}",
    instruction="Extract structured data"
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        extraction_strategy=strategy
    )
    print(result.extracted_content)`;
        }

        // Integration example
        const integrationCode = document.getElementById('integration-code');
        integrationCode.textContent = this.appData.integration_guide ||
`# Complete ${this.appData.name} Integration Example

from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import json

async def crawl_with_${this.appData.slug.replace(/-/g, '_')}():
    """
    Complete example showing how to use ${this.appData.name}
    with Crawl4AI for production web scraping
    """

    # Define extraction schema
    schema = {
        "name": "ProductList",
        "baseSelector": "div.product",
        "fields": [
            {"name": "title", "selector": "h2", "type": "text"},
            {"name": "price", "selector": ".price", "type": "text"},
            {"name": "image", "selector": "img", "type": "attribute", "attribute": "src"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
        ]
    }

    # Initialize crawler with ${this.appData.name}
    async with AsyncWebCrawler(
        browser_type="chromium",
        headless=True,
        verbose=True
    ) as crawler:

        # Crawl with extraction
        result = await crawler.arun(
            url="https://example.com/products",
            extraction_strategy=JsonCssExtractionStrategy(schema),
            cache_mode="bypass",
            wait_for="css:.product",
            screenshot=True
        )

        # Process results
        if result.success:
            products = json.loads(result.extracted_content)
            print(f"Found {len(products)} products")

            for product in products[:5]:
                print(f"- {product['title']}: {product['price']}")

        return products

# Run the crawler
if __name__ == "__main__":
    import asyncio
    asyncio.run(crawl_with_${this.appData.slug.replace(/-/g, '_')}())`;
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    setupEventListeners() {
        // Tab switching
        const tabs = document.querySelectorAll('.nav-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Update active tab
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                // Show corresponding content
                const tabName = tab.dataset.tab;
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                document.getElementById(`${tabName}-tab`).classList.add('active');
            });
        });

        // Copy integration code
        document.getElementById('copy-integration').addEventListener('click', () => {
            const code = document.getElementById('integration-code').textContent;
            navigator.clipboard.writeText(code).then(() => {
                const btn = document.getElementById('copy-integration');
                const originalText = btn.innerHTML;
                btn.innerHTML = '<span>✓</span> Copied!';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                }, 2000);
            });
        });

        // Copy code buttons
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const codeBlock = e.target.closest('.code-block');
                const code = codeBlock.querySelector('code').textContent;
                navigator.clipboard.writeText(code).then(() => {
                    btn.textContent = 'Copied!';
                    setTimeout(() => {
                        btn.textContent = 'Copy';
                    }, 2000);
                });
            });
        });
    }

    async loadRelatedApps() {
        try {
            const response = await fetch(`${API_BASE}/apps?category=${encodeURIComponent(this.appData.category)}&limit=4`);
            const apps = await response.json();

            const relatedApps = apps.filter(app => app.slug !== this.appSlug).slice(0, 3);
            const grid = document.getElementById('related-apps-grid');

            grid.innerHTML = relatedApps.map(app => `
                <div class="related-app-card" onclick="window.location.href='app-detail.html?app=${app.slug || app.name.toLowerCase().replace(/\s+/g, '-')}'">
                    <h4>${app.name}</h4>
                    <p>${app.description.substring(0, 100)}...</p>
                    <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.75rem;">
                        <span style="color: var(--primary-cyan)">${app.type}</span>
                        <span style="color: var(--warning)">★ ${app.rating}/5</span>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading related apps:', error);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AppDetailPage();
});