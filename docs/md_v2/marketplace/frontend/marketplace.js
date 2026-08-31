// Marketplace JS - Magazine Layout
const API_BASE = '/marketplace/api';
const CACHE_TTL = 3600000; // 1 hour in ms

class MarketplaceCache {
    constructor() {
        this.prefix = 'c4ai_market_';
    }

    get(key) {
        const item = localStorage.getItem(this.prefix + key);
        if (!item) return null;

        const data = JSON.parse(item);
        if (Date.now() > data.expires) {
            localStorage.removeItem(this.prefix + key);
            return null;
        }
        return data.value;
    }

    set(key, value, ttl = CACHE_TTL) {
        const data = {
            value: value,
            expires: Date.now() + ttl
        };
        localStorage.setItem(this.prefix + key, JSON.stringify(data));
    }

    clear() {
        Object.keys(localStorage)
            .filter(k => k.startsWith(this.prefix))
            .forEach(k => localStorage.removeItem(k));
    }
}

class MarketplaceAPI {
    constructor() {
        this.cache = new MarketplaceCache();
        this.searchTimeout = null;
    }

    async fetch(endpoint, useCache = true) {
        const cacheKey = endpoint.replace(/[^\w]/g, '_');

        if (useCache) {
            const cached = this.cache.get(cacheKey);
            if (cached) return cached;
        }

        try {
            const response = await fetch(`${API_BASE}${endpoint}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            this.cache.set(cacheKey, data);
            return data;
        } catch (error) {
            console.error('API Error:', error);
            return null;
        }
    }

    async getStats() {
        return this.fetch('/stats');
    }

    async getCategories() {
        return this.fetch('/categories');
    }

    async getApps(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.fetch(`/apps${query ? '?' + query : ''}`);
    }

    async getArticles(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.fetch(`/articles${query ? '?' + query : ''}`);
    }

    async getSponsors() {
        return this.fetch('/sponsors');
    }

    async search(query) {
        if (query.length < 2) return {};
        return this.fetch(`/search?q=${encodeURIComponent(query)}`, false);
    }
}

class MarketplaceUI {
    constructor() {
        this.api = new MarketplaceAPI();
        this.currentCategory = 'all';
        this.currentType = '';
        this.searchTimeout = null;
        this.loadedApps = 10;
        this.init();
    }

    async init() {
        await this.loadStats();
        await this.loadCategories();
        await this.loadFeaturedContent();
        await this.loadSponsors();
        await this.loadMainContent();
        this.setupEventListeners();
    }

    async loadStats() {
        const stats = await this.api.getStats();
        if (stats) {
            document.getElementById('total-apps').textContent = stats.total_apps || '0';
            document.getElementById('total-articles').textContent = stats.total_articles || '0';
            document.getElementById('total-downloads').textContent = stats.total_downloads || '0';
            document.getElementById('last-update').textContent = new Date().toLocaleDateString();
        }
    }

    async loadCategories() {
        const categories = await this.api.getCategories();
        if (!categories) return;

        const filter = document.getElementById('category-filter');
        categories.forEach(cat => {
            const btn = document.createElement('button');
            btn.className = 'filter-btn';
            btn.dataset.category = cat.slug;
            btn.textContent = cat.name;
            btn.onclick = () => this.filterByCategory(cat.slug);
            filter.appendChild(btn);
        });
    }

    async loadFeaturedContent() {
        // Load hero featured
        const featured = await this.api.getApps({ featured: true, limit: 4 });
        if (!featured || !featured.length) return;

        // Hero card (first featured)
        const hero = featured[0];
        const heroCard = document.getElementById('featured-hero');
        if (hero) {
            const imageUrl = hero.image || '';
            heroCard.innerHTML = `
                <div class="hero-image" ${imageUrl ? `style="background-image: url('${imageUrl}')"` : ''}>
                    ${!imageUrl ? `[${hero.category || 'APP'}]` : ''}
                </div>
                <div class="hero-content">
                    <span class="hero-badge">${hero.type || 'PAID'}</span>
                    <h2 class="hero-title">${hero.name}</h2>
                    <p class="hero-description">${hero.description}</p>
                    <div class="hero-meta">
                        <span>★ ${hero.rating || 0}/5</span>
                        <span>${hero.downloads || 0} downloads</span>
                    </div>
                </div>
            `;
            heroCard.onclick = () => this.showAppDetail(hero);
        }

        // Secondary featured cards
        const secondary = document.getElementById('featured-secondary');
        secondary.innerHTML = '';
        if (featured.length > 1) {
            featured.slice(1, 4).forEach(app => {
                const card = document.createElement('div');
                card.className = 'secondary-card';
                const imageUrl = app.image || '';
                card.innerHTML = `
                    <div class="secondary-image" ${imageUrl ? `style="background-image: url('${imageUrl}')"` : ''}>
                        ${!imageUrl ? `[${app.category || 'APP'}]` : ''}
                    </div>
                    <div class="secondary-content">
                        <h3 class="secondary-title">${app.name}</h3>
                        <p class="secondary-desc">${(app.description || '').substring(0, 100)}...</p>
                        <div class="secondary-meta">
                            <span>${app.type || 'Open Source'}</span> · <span>★ ${app.rating || 0}/5</span>
                        </div>
                    </div>
                `;
                card.onclick = () => this.showAppDetail(app);
                secondary.appendChild(card);
            });
        }
    }

    async loadSponsors() {
        const sponsors = await this.api.getSponsors();
        if (!sponsors || !sponsors.length) {
            // Show placeholder if no sponsors
            const container = document.getElementById('sponsored-content');
            container.innerHTML = `
                <div class="sponsor-card">
                    <h4>Become a Sponsor</h4>
                    <p>Reach thousands of developers using Crawl4AI</p>
                    <a href="mailto:sponsors@crawl4ai.com">Contact Us →</a>
                </div>
            `;
            return;
        }

        const container = document.getElementById('sponsored-content');
        container.innerHTML = sponsors.slice(0, 5).map(sponsor => `
            <div class="sponsor-card">
                <h4>${sponsor.company_name}</h4>
                <p>${sponsor.tier} Sponsor - Premium Solutions</p>
                <a href="${sponsor.landing_url}" target="_blank">Learn More →</a>
            </div>
        `).join('');
    }

    async loadMainContent() {
        // Load apps column
        const apps = await this.api.getApps({ limit: 8 });
        if (apps && apps.length) {
            const appsGrid = document.getElementById('apps-grid');
            appsGrid.innerHTML = apps.map(app => `
                <div class="app-compact" onclick="marketplace.showAppDetail(${JSON.stringify(app).replace(/"/g, '&quot;')})">
                    <div class="app-compact-header">
                        <span>${app.category}</span>
                        <span>★ ${app.rating}/5</span>
                    </div>
                    <div class="app-compact-title">${app.name}</div>
                    <div class="app-compact-desc">${app.description}</div>
                </div>
            `).join('');
        }

        // Load articles column
        const articles = await this.api.getArticles({ limit: 6 });
        if (articles && articles.length) {
            const articlesList = document.getElementById('articles-list');
            articlesList.innerHTML = articles.map(article => `
                <div class="article-compact" onclick="marketplace.showArticle('${article.id}')">
                    <div class="article-meta">
                        <span>${article.category}</span> · <span>${new Date(article.published_at).toLocaleDateString()}</span>
                    </div>
                    <div class="article-title">${article.title}</div>
                    <div class="article-author">by ${article.author}</div>
                </div>
            `).join('');
        }

        // Load trending
        if (apps && apps.length) {
            const trending = apps.slice(0, 5);
            const trendingList = document.getElementById('trending-list');
            trendingList.innerHTML = trending.map((app, i) => `
                <div class="trending-item" onclick="marketplace.showAppDetail(${JSON.stringify(app).replace(/"/g, '&quot;')})">
                    <div class="trending-rank">${i + 1}</div>
                    <div class="trending-info">
                        <div class="trending-name">${app.name}</div>
                        <div class="trending-stats">${app.downloads} downloads</div>
                    </div>
                </div>
            `).join('');
        }

        // Load more apps grid
        const moreApps = await this.api.getApps({ offset: 8, limit: 12 });
        if (moreApps && moreApps.length) {
            const moreGrid = document.getElementById('more-apps-grid');
            moreGrid.innerHTML = moreApps.map(app => `
                <div class="app-compact" onclick="marketplace.showAppDetail(${JSON.stringify(app).replace(/"/g, '&quot;')})">
                    <div class="app-compact-header">
                        <span>${app.category}</span>
                        <span>${app.type}</span>
                    </div>
                    <div class="app-compact-title">${app.name}</div>
                </div>
            `).join('');
        }
    }

    setupEventListeners() {
        // Search
        const searchInput = document.getElementById('search-input');
        searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => this.search(e.target.value), 300);
        });

        // Keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && !searchInput.contains(document.activeElement)) {
                e.preventDefault();
                searchInput.focus();
            }
            if (e.key === 'Escape' && searchInput.contains(document.activeElement)) {
                searchInput.blur();
                searchInput.value = '';
            }
        });

        // Type filter
        const typeFilter = document.getElementById('type-filter');
        typeFilter.addEventListener('change', (e) => {
            this.currentType = e.target.value;
            this.loadMainContent();
        });

        // Load more
        const loadMore = document.getElementById('load-more');
        loadMore.addEventListener('click', () => this.loadMoreApps());
    }

    async filterByCategory(category) {
        // Update active state
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.category === category);
        });

        this.currentCategory = category;
        await this.loadMainContent();
    }

    async search(query) {
        if (!query) {
            await this.loadMainContent();
            return;
        }

        const results = await this.api.search(query);
        if (!results) return;

        // Update apps grid with search results
        if (results.apps && results.apps.length) {
            const appsGrid = document.getElementById('apps-grid');
            appsGrid.innerHTML = results.apps.map(app => `
                <div class="app-compact" onclick="marketplace.showAppDetail(${JSON.stringify(app).replace(/"/g, '&quot;')})">
                    <div class="app-compact-header">
                        <span>${app.category}</span>
                        <span>★ ${app.rating}/5</span>
                    </div>
                    <div class="app-compact-title">${app.name}</div>
                    <div class="app-compact-desc">${app.description}</div>
                </div>
            `).join('');
        }

        // Update articles with search results
        if (results.articles && results.articles.length) {
            const articlesList = document.getElementById('articles-list');
            articlesList.innerHTML = results.articles.map(article => `
                <div class="article-compact" onclick="marketplace.showArticle('${article.id}')">
                    <div class="article-meta">
                        <span>${article.category}</span> · <span>${new Date(article.published_at).toLocaleDateString()}</span>
                    </div>
                    <div class="article-title">${article.title}</div>
                    <div class="article-author">by ${article.author}</div>
                </div>
            `).join('');
        }
    }

    async loadMoreApps() {
        this.loadedApps += 12;
        const moreApps = await this.api.getApps({ offset: this.loadedApps, limit: 12 });
        if (moreApps && moreApps.length) {
            const moreGrid = document.getElementById('more-apps-grid');
            moreApps.forEach(app => {
                const card = document.createElement('div');
                card.className = 'app-compact';
                card.innerHTML = `
                    <div class="app-compact-header">
                        <span>${app.category}</span>
                        <span>${app.type}</span>
                    </div>
                    <div class="app-compact-title">${app.name}</div>
                `;
                card.onclick = () => this.showAppDetail(app);
                moreGrid.appendChild(card);
            });
        }
    }

    showAppDetail(app) {
        // Navigate to detail page instead of showing modal
        const slug = app.slug || app.name.toLowerCase().replace(/\s+/g, '-');
        window.location.href = `app-detail.html?app=${slug}`;
    }

    showArticle(articleId) {
        // Could create article detail page similarly
        console.log('Show article:', articleId);
    }
}

// Initialize marketplace
let marketplace;
document.addEventListener('DOMContentLoaded', () => {
    marketplace = new MarketplaceUI();
});