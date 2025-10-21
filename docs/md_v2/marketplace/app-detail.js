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

        // Sidebar info
        document.getElementById('sidebar-downloads').textContent = this.formatNumber(this.appData.downloads || 0);
        document.getElementById('sidebar-rating').textContent = (this.appData.rating || 0).toFixed(1);
        document.getElementById('sidebar-category').textContent = this.appData.category || '-';
        document.getElementById('sidebar-type').textContent = this.appData.type || '-';
        document.getElementById('sidebar-status').textContent = this.appData.status || 'Active';
        document.getElementById('sidebar-pricing').textContent = this.appData.pricing || 'Free';
        document.getElementById('sidebar-contact').textContent = this.appData.contact_email || 'contact@example.com';

        // Render tab contents from database fields
        this.renderTabContents();
    }

    renderTabContents() {
        // Overview tab - use long_description from database
        const overviewDiv = document.getElementById('app-overview');
        if (overviewDiv) {
            if (this.appData.long_description) {
                overviewDiv.innerHTML = this.renderMarkdown(this.appData.long_description);
            } else {
                overviewDiv.innerHTML = `<p>${this.appData.description || 'No overview available.'}</p>`;
            }
        }

        // Documentation tab - use documentation field from database
        const docsDiv = document.getElementById('app-docs');
        if (docsDiv) {
            if (this.appData.documentation) {
                docsDiv.innerHTML = this.renderMarkdown(this.appData.documentation);
            } else {
                docsDiv.innerHTML = '<p>Documentation coming soon.</p>';
            }
        }

        // Integration tab - use integration_guide, installation_command, examples from database
        this.renderIntegrationTab();
    }

    renderIntegrationTab() {
        // Installation code - use installation_command from database
        const installCode = document.getElementById('install-code');
        if (installCode) {
            if (this.appData.installation_command) {
                installCode.textContent = this.appData.installation_command;
            } else {
                // Fallback to generic installation
                installCode.textContent = `# Installation instructions not yet available\n# Please check ${this.appData.website_url || 'the official website'} for details`;
            }
        }

        // Usage code - use examples field from database
        const usageCode = document.getElementById('usage-code');
        if (usageCode && this.appData.examples) {
            // Extract first code block from examples if it contains multiple
            const codeMatch = this.appData.examples.match(/```[\s\S]*?```/);
            if (codeMatch) {
                usageCode.textContent = codeMatch[0].replace(/```(\w+)?\n?/g, '').trim();
            } else {
                usageCode.textContent = this.appData.examples;
            }
        }

        // Complete integration - use integration_guide field from database
        const integrationCode = document.getElementById('integration-code');
        if (integrationCode) {
            if (this.appData.integration_guide) {
                integrationCode.textContent = this.appData.integration_guide;
            } else {
                // Fallback message
                integrationCode.textContent = `# Integration guide not yet available for ${this.appData.name}\n\n# Please visit the admin panel to add integration instructions\n# Or check ${this.appData.website_url || 'the official website'} for integration details`;
            }
        }
    }

    renderMarkdown(text) {
        if (!text) return '';

        // Simple markdown rendering (convert to HTML)
        return text
            // Headers
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            // Bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
            // Code blocks
            .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
            // Inline code
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // Line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            // Lists
            .replace(/^\* (.*)$/gim, '<li>$1</li>')
            .replace(/^- (.*)$/gim, '<li>$1</li>')
            // Wrap in paragraphs
            .replace(/^(?!<[h|p|pre|ul|ol|li])/gim, '<p>')
            .replace(/(?<![>])$/gim, '</p>');
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
        const tabs = document.querySelectorAll('.tab-btn');
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