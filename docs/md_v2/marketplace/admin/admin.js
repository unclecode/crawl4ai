// Admin Dashboard - Smart & Powerful
const { API_BASE, API_ORIGIN } = (() => {
    const cleanOrigin = (value) => value ? value.replace(/\/$/, '') : '';
    const params = new URLSearchParams(window.location.search);
    const overrideParam = cleanOrigin(params.get('api_origin'));

    let storedOverride = '';
    try {
        storedOverride = cleanOrigin(localStorage.getItem('marketplace_api_origin'));
    } catch (error) {
        storedOverride = '';
    }

    let origin = overrideParam || storedOverride;

    if (overrideParam && overrideParam !== storedOverride) {
        try {
            localStorage.setItem('marketplace_api_origin', overrideParam);
        } catch (error) {
            // ignore storage errors (private mode, etc.)
        }
    }

    const { protocol, hostname, port } = window.location;
    const isLocalHost = ['localhost', '127.0.0.1', '0.0.0.0'].includes(hostname);

    if (!origin && isLocalHost && port !== '8100') {
        origin = `${protocol}//127.0.0.1:8100`;
    }

    if (origin) {
        const normalized = cleanOrigin(origin);
        return { API_BASE: `${normalized}/marketplace/api`, API_ORIGIN: normalized };
    }

    return { API_BASE: '/marketplace/api', API_ORIGIN: '' };
})();

const resolveAssetUrl = (path) => {
    if (!path) return '';
    if (/^https?:\/\//i.test(path)) return path;
    if (path.startsWith('/') && API_ORIGIN) {
        return `${API_ORIGIN}${path}`;
    }
    return path;
};

class AdminDashboard {
    constructor() {
        this.token = localStorage.getItem('admin_token');
        this.currentSection = 'stats';
        this.data = {
            apps: [],
            articles: [],
            categories: [],
            sponsors: []
        };
        this.editingItem = null;
        this.init();
    }

    async init() {
        // Check auth
        if (!this.token) {
            this.showLogin();
            return;
        }

        // Try to load stats to verify token
        try {
            await this.loadStats();
            this.showDashboard();
            this.setupEventListeners();
            await this.loadAllData();
        } catch (error) {
            if (error.status === 401) {
                this.showLogin();
            }
        }
    }

    showLogin() {
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('admin-dashboard').classList.add('hidden');

        // Set up login button click handler
        const loginBtn = document.getElementById('login-btn');
        if (loginBtn) {
            loginBtn.onclick = async () => {
                const password = document.getElementById('password').value;
                await this.login(password);
            };
        }
    }

    async login(password) {
        try {
            const response = await fetch(`${API_BASE}/admin/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password })
            });

            if (!response.ok) throw new Error('Invalid password');

            const data = await response.json();
            this.token = data.token;
            localStorage.setItem('admin_token', this.token);

            document.getElementById('login-screen').classList.add('hidden');
            this.showDashboard();
            this.setupEventListeners();
            await this.loadAllData();
        } catch (error) {
            document.getElementById('login-error').textContent = 'Invalid password';
            document.getElementById('password').value = '';
        }
    }

    showDashboard() {
        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('admin-dashboard').classList.remove('hidden');
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.onclick = () => this.switchSection(btn.dataset.section);
        });

        // Logout
        document.getElementById('logout-btn').onclick = () => this.logout();

        // Export/Backup
        document.getElementById('export-btn').onclick = () => this.exportData();
        document.getElementById('backup-btn').onclick = () => this.backupDatabase();

        // Search
        ['apps', 'articles'].forEach(type => {
            const searchInput = document.getElementById(`${type}-search`);
            if (searchInput) {
                searchInput.oninput = (e) => this.filterTable(type, e.target.value);
            }
        });

        // Category filter
        const categoryFilter = document.getElementById('apps-filter');
        if (categoryFilter) {
            categoryFilter.onchange = (e) => this.filterByCategory(e.target.value);
        }

        // Save button in modal
        document.getElementById('save-btn').onclick = () => this.saveItem();
    }

    async loadAllData() {
        try {
            await this.loadStats();
        } catch (e) {
            console.error('Failed to load stats:', e);
        }

        try {
            await this.loadApps();
        } catch (e) {
            console.error('Failed to load apps:', e);
        }

        try {
            await this.loadArticles();
        } catch (e) {
            console.error('Failed to load articles:', e);
        }

        try {
            await this.loadCategories();
        } catch (e) {
            console.error('Failed to load categories:', e);
        }

        try {
            await this.loadSponsors();
        } catch (e) {
            console.error('Failed to load sponsors:', e);
        }

        this.populateCategoryFilter();
    }

    async apiCall(endpoint, options = {}) {
        const isFormData = options.body instanceof FormData;
        const headers = {
            'Authorization': `Bearer ${this.token}`,
            ...options.headers
        };

        if (!isFormData && !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            this.logout();
            throw { status: 401 };
        }

        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return response.json();
    }

    async loadStats() {
        const stats = await this.apiCall(`/admin/stats?_=${Date.now()}`, {
            cache: 'no-store'
        });

        document.getElementById('stat-apps').textContent = stats.apps.total;
        document.getElementById('stat-featured').textContent = stats.apps.featured;
        document.getElementById('stat-sponsored').textContent = stats.apps.sponsored;
        document.getElementById('stat-articles').textContent = stats.articles;
        document.getElementById('stat-sponsors').textContent = stats.sponsors.active;
        document.getElementById('stat-views').textContent = this.formatNumber(stats.total_views);
    }

    async loadApps() {
        this.data.apps = await this.apiCall(`/apps?limit=100&_=${Date.now()}`, {
            cache: 'no-store'
        });
        this.renderAppsTable(this.data.apps);
    }

    async loadArticles() {
        this.data.articles = await this.apiCall(`/articles?limit=100&_=${Date.now()}`, {
            cache: 'no-store'
        });
        this.renderArticlesTable(this.data.articles);
    }

    async loadCategories() {
        const cacheBuster = Date.now();
        this.data.categories = await this.apiCall(`/categories?_=${cacheBuster}`, {
            cache: 'no-store'
        });
        this.renderCategoriesTable(this.data.categories);
    }

    async loadSponsors() {
        const cacheBuster = Date.now();
        this.data.sponsors = await this.apiCall(`/sponsors?limit=100&_=${cacheBuster}`, {
            cache: 'no-store'
        });
        this.renderSponsorsTable(this.data.sponsors);
    }

    renderAppsTable(apps) {
        const table = document.getElementById('apps-table');
        table.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Category</th>
                        <th>Type</th>
                        <th>Rating</th>
                        <th>Downloads</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${apps.map(app => `
                        <tr>
                            <td>${app.id}</td>
                            <td>${app.name}</td>
                            <td>${app.category}</td>
                            <td>${app.type}</td>
                            <td>◆ ${app.rating}/5</td>
                            <td>${this.formatNumber(app.downloads)}</td>
                            <td>
                                ${app.featured ? '<span class="badge featured">Featured</span>' : ''}
                                ${app.sponsored ? '<span class="badge sponsored">Sponsored</span>' : ''}
                            </td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn-edit" onclick="admin.editItem('apps', ${app.id})">Edit</button>
                                    <button class="btn-duplicate" onclick="admin.duplicateItem('apps', ${app.id})">Duplicate</button>
                                    <button class="btn-delete" onclick="admin.deleteItem('apps', ${app.id})">Delete</button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    renderArticlesTable(articles) {
        const table = document.getElementById('articles-table');
        table.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Category</th>
                        <th>Author</th>
                        <th>Published</th>
                        <th>Views</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${articles.map(article => `
                        <tr>
                            <td>${article.id}</td>
                            <td>${article.title}</td>
                            <td>${article.category}</td>
                            <td>${article.author}</td>
                            <td>${new Date(article.published_date).toLocaleDateString()}</td>
                            <td>${this.formatNumber(article.views)}</td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn-edit" onclick="admin.editItem('articles', ${article.id})">Edit</button>
                                    <button class="btn-duplicate" onclick="admin.duplicateItem('articles', ${article.id})">Duplicate</button>
                                    <button class="btn-delete" onclick="admin.deleteItem('articles', ${article.id})">Delete</button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    renderCategoriesTable(categories) {
        const table = document.getElementById('categories-table');
        table.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Order</th>
                        <th>Icon</th>
                        <th>Name</th>
                        <th>Description</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${categories.map(cat => `
                        <tr>
                            <td>${cat.order_index}</td>
                            <td>${cat.icon}</td>
                            <td>${cat.name}</td>
                            <td>${cat.description}</td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn-edit" onclick="admin.editItem('categories', ${cat.id})">Edit</button>
                                    <button class="btn-delete" onclick="admin.deleteCategory(${cat.id})">Delete</button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    renderSponsorsTable(sponsors) {
        const table = document.getElementById('sponsors-table');
        table.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Logo</th>
                        <th>Company</th>
                        <th>Tier</th>
                        <th>Start</th>
                        <th>End</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${sponsors.map(sponsor => `
                        <tr>
                            <td>${sponsor.id}</td>
                            <td>${sponsor.logo_url ? `<img class="table-logo" src="${resolveAssetUrl(sponsor.logo_url)}" alt="${sponsor.company_name} logo">` : '-'}</td>
                            <td>${sponsor.company_name}</td>
                            <td>${sponsor.tier}</td>
                            <td>${new Date(sponsor.start_date).toLocaleDateString()}</td>
                            <td>${new Date(sponsor.end_date).toLocaleDateString()}</td>
                            <td>${sponsor.active ? '<span class="badge active">Active</span>' : 'Inactive'}</td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn-edit" onclick="admin.editItem('sponsors', ${sponsor.id})">Edit</button>
                                    <button class="btn-delete" onclick="admin.deleteItem('sponsors', ${sponsor.id})">Delete</button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    showAddForm(type) {
        this.editingItem = null;
        this.showModal(type, null);
    }

    async editItem(type, id) {
        const item = this.data[type].find(i => i.id === id);
        if (item) {
            this.editingItem = item;
            this.showModal(type, item);
        }
    }

    async duplicateItem(type, id) {
        const item = this.data[type].find(i => i.id === id);
        if (item) {
            const newItem = { ...item };
            delete newItem.id;
            newItem.name = `${newItem.name || newItem.title} (Copy)`;
            if (newItem.slug) newItem.slug = `${newItem.slug}-copy-${Date.now()}`;

            this.editingItem = null;
            this.showModal(type, newItem);
        }
    }

    showModal(type, item) {
        const modal = document.getElementById('form-modal');
        const title = document.getElementById('modal-title');
        const body = document.getElementById('modal-body');

        title.textContent = item ? `Edit ${type.slice(0, -1)}` : `Add New ${type.slice(0, -1)}`;

        if (type === 'apps') {
            body.innerHTML = this.getAppForm(item);
        } else if (type === 'articles') {
            body.innerHTML = this.getArticleForm(item);
        } else if (type === 'categories') {
            body.innerHTML = this.getCategoryForm(item);
        } else if (type === 'sponsors') {
            body.innerHTML = this.getSponsorForm(item);
        }

        modal.classList.remove('hidden');
        modal.dataset.type = type;

        if (type === 'sponsors') {
            this.setupLogoUploadHandlers();
        }
    }

    getAppForm(app) {
        return `
            <div class="form-grid">
                <div class="form-group">
                    <label>Name *</label>
                    <input type="text" id="form-name" value="${app?.name || ''}" required>
                </div>
                <div class="form-group">
                    <label>Slug</label>
                    <input type="text" id="form-slug" value="${app?.slug || ''}" placeholder="auto-generated">
                </div>
                <div class="form-group">
                    <label>Category</label>
                    <select id="form-category">
                        ${this.data.categories.map(cat =>
                            `<option value="${cat.name}" ${app?.category === cat.name ? 'selected' : ''}>${cat.name}</option>`
                        ).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Type</label>
                    <select id="form-type">
                        <option value="Open Source" ${app?.type === 'Open Source' ? 'selected' : ''}>Open Source</option>
                        <option value="Paid" ${app?.type === 'Paid' ? 'selected' : ''}>Paid</option>
                        <option value="Freemium" ${app?.type === 'Freemium' ? 'selected' : ''}>Freemium</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Rating</label>
                    <input type="number" id="form-rating" value="${app?.rating || 4.5}" min="0" max="5" step="0.1">
                </div>
                <div class="form-group">
                    <label>Downloads</label>
                    <input type="number" id="form-downloads" value="${app?.downloads || 0}">
                </div>
                <div class="form-group full-width">
                    <label>Description</label>
                    <textarea id="form-description" rows="3">${app?.description || ''}</textarea>
                </div>
                <div class="form-group full-width">
                    <label>Image URL</label>
                    <input type="text" id="form-image" value="${app?.image || ''}" placeholder="https://...">
                </div>
                <div class="form-group">
                    <label>Website URL</label>
                    <input type="text" id="form-website" value="${app?.website_url || ''}">
                </div>
                <div class="form-group">
                    <label>GitHub URL</label>
                    <input type="text" id="form-github" value="${app?.github_url || ''}">
                </div>
                <div class="form-group">
                    <label>Pricing</label>
                    <input type="text" id="form-pricing" value="${app?.pricing || 'Free'}">
                </div>
                <div class="form-group">
                    <label>Contact Email</label>
                    <input type="email" id="form-email" value="${app?.contact_email || ''}">
                </div>
                <div class="form-group full-width checkbox-group">
                    <label class="checkbox-label">
                        <input type="checkbox" id="form-featured" ${app?.featured ? 'checked' : ''}>
                        Featured
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" id="form-sponsored" ${app?.sponsored ? 'checked' : ''}>
                        Sponsored
                    </label>
                </div>
                <div class="form-group full-width">
                    <label>Long Description (Markdown - Overview tab)</label>
                    <textarea id="form-long-description" rows="10" placeholder="Enter detailed description with markdown formatting...">${app?.long_description || ''}</textarea>
                    <small>Markdown support: **bold**, *italic*, [links](url), # headers, code blocks, lists</small>
                </div>
                <div class="form-group full-width">
                    <label>Integration Guide (Markdown - Integration tab)</label>
                    <textarea id="form-integration" rows="20" placeholder="Enter integration guide with installation, examples, and code snippets using markdown...">${app?.integration_guide || ''}</textarea>
                    <small>Single markdown field with installation, examples, and complete guide. Code blocks get auto copy buttons.</small>
                </div>
                <div class="form-group full-width">
                    <label>Documentation (Markdown - Documentation tab)</label>
                    <textarea id="form-documentation" rows="20" placeholder="Enter documentation with API reference, examples, and best practices using markdown...">${app?.documentation || ''}</textarea>
                    <small>Full documentation with API reference, examples, best practices, etc.</small>
                </div>
            </div>
        `;
    }

    getArticleForm(article) {
        return `
            <div class="form-grid">
                <div class="form-group full-width">
                    <label>Title *</label>
                    <input type="text" id="form-title" value="${article?.title || ''}" required>
                </div>
                <div class="form-group">
                    <label>Author</label>
                    <input type="text" id="form-author" value="${article?.author || 'Crawl4AI Team'}">
                </div>
                <div class="form-group">
                    <label>Category</label>
                    <select id="form-category">
                        <option value="News" ${article?.category === 'News' ? 'selected' : ''}>News</option>
                        <option value="Tutorial" ${article?.category === 'Tutorial' ? 'selected' : ''}>Tutorial</option>
                        <option value="Review" ${article?.category === 'Review' ? 'selected' : ''}>Review</option>
                        <option value="Comparison" ${article?.category === 'Comparison' ? 'selected' : ''}>Comparison</option>
                    </select>
                </div>
                <div class="form-group full-width">
                    <label>Featured Image URL</label>
                    <input type="text" id="form-image" value="${article?.featured_image || ''}">
                </div>
                <div class="form-group full-width">
                    <label>Content</label>
                    <textarea id="form-content" rows="20">${article?.content || ''}</textarea>
                </div>
            </div>
        `;
    }

    getCategoryForm(category) {
        return `
            <div class="form-grid">
                <div class="form-group">
                    <label>Name *</label>
                    <input type="text" id="form-name" value="${category?.name || ''}" required>
                </div>
                <div class="form-group">
                    <label>Icon</label>
                    <input type="text" id="form-icon" value="${category?.icon || '📁'}" maxlength="2">
                </div>
                <div class="form-group">
                    <label>Order</label>
                    <input type="number" id="form-order" value="${category?.order_index || 0}">
                </div>
                <div class="form-group full-width">
                    <label>Description</label>
                    <textarea id="form-description" rows="3">${category?.description || ''}</textarea>
                </div>
            </div>
        `;
    }

    getSponsorForm(sponsor) {
        const existingFile = sponsor?.logo_url ? sponsor.logo_url.split('/').pop().split('?')[0] : '';
        return `
            <div class="form-grid sponsor-form">
                <div class="form-group sponsor-logo-group">
                    <label>Logo</label>
                    <input type="hidden" id="form-logo-url" value="${sponsor?.logo_url || ''}">
                    <div class="logo-upload">
                        <div class="image-preview ${sponsor?.logo_url ? '' : 'empty'}" id="form-logo-preview">
                            ${sponsor?.logo_url ? `<img src="${resolveAssetUrl(sponsor.logo_url)}" alt="Logo preview">` : '<span>No logo uploaded</span>'}
                        </div>
                        <button type="button" class="upload-btn" id="form-logo-button">Upload Logo</button>
                        <input type="file" id="form-logo-file" accept="image/png,image/jpeg,image/webp,image/svg+xml" hidden>
                    </div>
                    <p class="upload-hint" id="form-logo-filename">${existingFile ? `Current: ${existingFile}` : 'No file selected'}</p>
                </div>
                <div class="form-group span-two">
                    <label>Company Name *</label>
                    <input type="text" id="form-name" value="${sponsor?.company_name || ''}" required>
                </div>
                <div class="form-group">
                    <label>Tier</label>
                    <select id="form-tier">
                        <option value="Bronze" ${sponsor?.tier === 'Bronze' ? 'selected' : ''}>Bronze</option>
                        <option value="Silver" ${sponsor?.tier === 'Silver' ? 'selected' : ''}>Silver</option>
                        <option value="Gold" ${sponsor?.tier === 'Gold' ? 'selected' : ''}>Gold</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Landing URL</label>
                    <input type="text" id="form-landing" value="${sponsor?.landing_url || ''}">
                </div>
                <div class="form-group">
                    <label>Banner URL</label>
                    <input type="text" id="form-banner" value="${sponsor?.banner_url || ''}">
                </div>
                <div class="form-group">
                    <label>Start Date</label>
                    <input type="date" id="form-start" value="${sponsor?.start_date?.split('T')[0] || ''}">
                </div>
                <div class="form-group">
                    <label>End Date</label>
                    <input type="date" id="form-end" value="${sponsor?.end_date?.split('T')[0] || ''}">
                </div>
                <div class="form-group">
                    <label class="checkbox-label">
                        <input type="checkbox" id="form-active" ${sponsor?.active ? 'checked' : ''}>
                        Active
                    </label>
                </div>
            </div>
        `;
    }

    async saveItem() {
        const modal = document.getElementById('form-modal');
        const type = modal.dataset.type;

        try {
            if (type === 'sponsors') {
                const fileInput = document.getElementById('form-logo-file');
                if (fileInput && fileInput.files && fileInput.files[0]) {
                    const formData = new FormData();
                    formData.append('file', fileInput.files[0]);
                    formData.append('folder', 'sponsors');

                    const uploadResponse = await this.apiCall('/admin/upload-image', {
                        method: 'POST',
                        body: formData
                    });

                    if (!uploadResponse.url) {
                        throw new Error('Image upload failed');
                    }

                    document.getElementById('form-logo-url').value = uploadResponse.url;
                }
            }

            const data = this.collectFormData(type);

            if (this.editingItem) {
                await this.apiCall(`/admin/${type}/${this.editingItem.id}`, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
            } else {
                await this.apiCall(`/admin/${type}`, {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            }

            this.closeModal();
            await this[`load${type.charAt(0).toUpperCase() + type.slice(1)}`]();
            await this.loadStats();
        } catch (error) {
            alert('Error saving item: ' + error.message);
        }
    }

    collectFormData(type) {
        const data = {};

        if (type === 'apps') {
            data.name = document.getElementById('form-name').value;
            data.slug = document.getElementById('form-slug').value || this.generateSlug(data.name);
            data.description = document.getElementById('form-description').value;
            data.category = document.getElementById('form-category').value;
            data.type = document.getElementById('form-type').value;
            const rating = parseFloat(document.getElementById('form-rating').value);
            const downloads = parseInt(document.getElementById('form-downloads').value, 10);
            data.rating = Number.isFinite(rating) ? rating : 0;
            data.downloads = Number.isFinite(downloads) ? downloads : 0;
            data.image = document.getElementById('form-image').value;
            data.website_url = document.getElementById('form-website').value;
            data.github_url = document.getElementById('form-github').value;
            data.pricing = document.getElementById('form-pricing').value;
            data.contact_email = document.getElementById('form-email').value;
            data.featured = document.getElementById('form-featured').checked ? 1 : 0;
            data.sponsored = document.getElementById('form-sponsored').checked ? 1 : 0;
            data.long_description = document.getElementById('form-long-description').value;
            data.integration_guide = document.getElementById('form-integration').value;
            data.documentation = document.getElementById('form-documentation').value;
        } else if (type === 'articles') {
            data.title = document.getElementById('form-title').value;
            data.slug = this.generateSlug(data.title);
            data.author = document.getElementById('form-author').value;
            data.category = document.getElementById('form-category').value;
            data.featured_image = document.getElementById('form-image').value;
            data.content = document.getElementById('form-content').value;
        } else if (type === 'categories') {
            data.name = document.getElementById('form-name').value;
            data.slug = this.generateSlug(data.name);
            data.icon = document.getElementById('form-icon').value;
            data.description = document.getElementById('form-description').value;
            const orderIndex = parseInt(document.getElementById('form-order').value, 10);
            data.order_index = Number.isFinite(orderIndex) ? orderIndex : 0;
        } else if (type === 'sponsors') {
            data.company_name = document.getElementById('form-name').value;
            data.logo_url = document.getElementById('form-logo-url').value;
            data.tier = document.getElementById('form-tier').value;
            data.landing_url = document.getElementById('form-landing').value;
            data.banner_url = document.getElementById('form-banner').value;
            data.start_date = document.getElementById('form-start').value;
            data.end_date = document.getElementById('form-end').value;
            data.active = document.getElementById('form-active').checked ? 1 : 0;
        }

        return data;
    }

    setupLogoUploadHandlers() {
        const fileInput = document.getElementById('form-logo-file');
        const preview = document.getElementById('form-logo-preview');
        const logoUrlInput = document.getElementById('form-logo-url');
        const trigger = document.getElementById('form-logo-button');
        const fileNameEl = document.getElementById('form-logo-filename');

        if (!fileInput || !preview || !logoUrlInput) return;

        const setFileName = (text) => {
            if (fileNameEl) {
                fileNameEl.textContent = text;
            }
        };

        const setEmptyState = () => {
            preview.innerHTML = '<span>No logo uploaded</span>';
            preview.classList.add('empty');
            setFileName('No file selected');
        };

        const setExistingState = () => {
            if (logoUrlInput.value) {
                const existingFile = logoUrlInput.value.split('/').pop().split('?')[0];
                preview.innerHTML = `<img src="${resolveAssetUrl(logoUrlInput.value)}" alt="Logo preview">`;
                preview.classList.remove('empty');
                setFileName(existingFile ? `Current: ${existingFile}` : 'Current logo');
            } else {
                setEmptyState();
            }
        };

        setExistingState();

        if (trigger) {
            trigger.onclick = () => fileInput.click();
        }

        fileInput.addEventListener('change', (event) => {
            const file = event.target.files && event.target.files[0];

            if (!file) {
                setExistingState();
                return;
            }

            setFileName(file.name);

            const reader = new FileReader();
            reader.onload = () => {
                preview.innerHTML = `<img src="${reader.result}" alt="Logo preview">`;
                preview.classList.remove('empty');
            };
            reader.readAsDataURL(file);
        });
    }

    async deleteItem(type, id) {
        if (!confirm(`Are you sure you want to delete this ${type.slice(0, -1)}?`)) return;

        try {
            await this.apiCall(`/admin/${type}/${id}`, { method: 'DELETE' });
            await this[`load${type.charAt(0).toUpperCase() + type.slice(1)}`]();
            await this.loadStats();
        } catch (error) {
            alert('Error deleting item: ' + error.message);
        }
    }

    async deleteCategory(id) {
        const hasApps = this.data.apps.some(app =>
            app.category === this.data.categories.find(c => c.id === id)?.name
        );

        if (hasApps) {
            alert('Cannot delete category with existing apps');
            return;
        }

        await this.deleteItem('categories', id);
    }

    closeModal() {
        document.getElementById('form-modal').classList.add('hidden');
        this.editingItem = null;
    }

    switchSection(section) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.section === section);
        });

        // Show section
        document.querySelectorAll('.content-section').forEach(sec => {
            sec.classList.remove('active');
        });
        document.getElementById(`${section}-section`).classList.add('active');

        this.currentSection = section;
    }

    filterTable(type, query) {
        const items = this.data[type].filter(item => {
            const searchText = Object.values(item).join(' ').toLowerCase();
            return searchText.includes(query.toLowerCase());
        });

        if (type === 'apps') {
            this.renderAppsTable(items);
        } else if (type === 'articles') {
            this.renderArticlesTable(items);
        }
    }

    filterByCategory(category) {
        const apps = category
            ? this.data.apps.filter(app => app.category === category)
            : this.data.apps;
        this.renderAppsTable(apps);
    }

    populateCategoryFilter() {
        const filter = document.getElementById('apps-filter');
        if (!filter) return;

        filter.innerHTML = '<option value="">All Categories</option>';
        this.data.categories.forEach(cat => {
            filter.innerHTML += `<option value="${cat.name}">${cat.name}</option>`;
        });
    }

    async exportData() {
        const data = {
            apps: this.data.apps,
            articles: this.data.articles,
            categories: this.data.categories,
            sponsors: this.data.sponsors,
            exported: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `marketplace-export-${Date.now()}.json`;
        a.click();
    }

    async backupDatabase() {
        // In production, this would download the SQLite file
        alert('Database backup would be implemented on the server side');
    }

    generateSlug(text) {
        return text.toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-')
            .trim();
    }

    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    logout() {
        localStorage.removeItem('admin_token');
        this.token = null;
        this.showLogin();
    }
}

// Initialize
const admin = new AdminDashboard();