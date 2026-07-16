// Playground App JavaScript
class PlaygroundApp {
    constructor() {
        this.isLoggedIn = false;
        this.currentSection = 'home';
        this.productsLoaded = 0;
        this.maxProducts = 100;
        this.tableRowsLoaded = 10;
        this.inspectorMode = false;
        this.tooltip = null;
        
        this.init();
    }

    init() {
        this.setupCookieBanner();
        this.setupNewsletterPopup();
        this.setupNavigation();
        this.setupAuth();
        this.setupProductCatalog();
        this.setupForms();
        this.setupTabs();
        this.setupDataTable();
        this.setupInspector();
        this.loadInitialData();
    }

    // Cookie Banner
    setupCookieBanner() {
        const banner = document.getElementById('cookie-banner');
        const acceptBtn = banner.querySelector('.accept');
        const declineBtn = banner.querySelector('.decline');

        acceptBtn.addEventListener('click', () => {
            banner.style.display = 'none';
            console.log('✅ Cookies accepted');
        });

        declineBtn.addEventListener('click', () => {
            banner.style.display = 'none';
            console.log('❌ Cookies declined');
        });
    }

    // Newsletter Popup
    setupNewsletterPopup() {
        const popup = document.getElementById('newsletter-popup');
        const closeBtn = popup.querySelector('.close');
        const subscribeBtn = popup.querySelector('.subscribe');

        // Show popup after 3 seconds
        setTimeout(() => {
            popup.style.display = 'flex';
        }, 3000);

        closeBtn.addEventListener('click', () => {
            popup.style.display = 'none';
        });

        subscribeBtn.addEventListener('click', () => {
            const email = popup.querySelector('input').value;
            if (email) {
                console.log(`📧 Subscribed: ${email}`);
                popup.style.display = 'none';
            }
        });

        // Close on outside click
        popup.addEventListener('click', (e) => {
            if (e.target === popup) {
                popup.style.display = 'none';
            }
        });
    }

    // Navigation
    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        const sections = document.querySelectorAll('.section');

        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                
                // Update active states
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
                
                // Show target section
                sections.forEach(s => s.classList.remove('active'));
                const targetSection = document.getElementById(targetId);
                if (targetSection) {
                    targetSection.classList.add('active');
                    this.currentSection = targetId;
                    
                    // Load content for specific sections
                    this.loadSectionContent(targetId);
                }
            });
        });

        // Start tutorial button
        const startBtn = document.getElementById('start-tutorial');
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                console.log('🚀 Tutorial started!');
                alert('Tutorial started! Check the console for progress.');
            });
        }
    }

    // Authentication
    setupAuth() {
        const loginBtn = document.getElementById('login-btn');
        const logoutBtn = document.getElementById('logout-btn');
        const loginModal = document.getElementById('login-modal');
        const loginForm = document.getElementById('login-form');
        const closeBtn = loginModal.querySelector('.close');

        loginBtn.addEventListener('click', () => {
            loginModal.style.display = 'flex';
        });

        closeBtn.addEventListener('click', () => {
            loginModal.style.display = 'none';
        });

        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const rememberMe = document.getElementById('remember-me').checked;
            const messageEl = document.getElementById('login-message');

            // Simple validation
            if (email === 'demo@example.com' && password === 'demo123') {
                this.isLoggedIn = true;
                messageEl.textContent = '✅ Login successful!';
                messageEl.className = 'form-message success';
                
                setTimeout(() => {
                    loginModal.style.display = 'none';
                    document.getElementById('login-btn').style.display = 'none';
                    document.getElementById('user-info').style.display = 'flex';
                    document.getElementById('username-display').textContent = 'Demo User';
                    console.log(`✅ Logged in${rememberMe ? ' (remembered)' : ''}`);
                }, 1000);
            } else {
                messageEl.textContent = '❌ Invalid credentials. Try demo@example.com / demo123';
                messageEl.className = 'form-message error';
            }
        });

        logoutBtn.addEventListener('click', () => {
            this.isLoggedIn = false;
            document.getElementById('login-btn').style.display = 'block';
            document.getElementById('user-info').style.display = 'none';
            console.log('👋 Logged out');
        });

        // Close modal on outside click
        loginModal.addEventListener('click', (e) => {
            if (e.target === loginModal) {
                loginModal.style.display = 'none';
            }
        });
    }

    // Product Catalog
    setupProductCatalog() {
        // View toggle
        const infiniteBtn = document.getElementById('infinite-scroll-btn');
        const paginationBtn = document.getElementById('pagination-btn');
        const infiniteView = document.getElementById('infinite-scroll-view');
        const paginationView = document.getElementById('pagination-view');

        infiniteBtn.addEventListener('click', () => {
            infiniteBtn.classList.add('active');
            paginationBtn.classList.remove('active');
            infiniteView.style.display = 'block';
            paginationView.style.display = 'none';
            this.setupInfiniteScroll();
        });

        paginationBtn.addEventListener('click', () => {
            paginationBtn.classList.add('active');
            infiniteBtn.classList.remove('active');
            paginationView.style.display = 'block';
            infiniteView.style.display = 'none';
        });

        // Load more button
        const loadMoreBtn = paginationView.querySelector('.load-more');
        loadMoreBtn.addEventListener('click', () => {
            this.loadMoreProducts();
        });

        // Collapsible filters
        const collapsibles = document.querySelectorAll('.collapsible');
        collapsibles.forEach(header => {
            header.addEventListener('click', () => {
                const content = header.nextElementSibling;
                const toggle = header.querySelector('.toggle');
                content.style.display = content.style.display === 'none' ? 'block' : 'none';
                toggle.textContent = content.style.display === 'none' ? '▶' : '▼';
            });
        });
    }

    setupInfiniteScroll() {
        const container = document.querySelector('.products-container');
        const loadingIndicator = document.getElementById('loading-indicator');
        
        container.addEventListener('scroll', () => {
            if (container.scrollTop + container.clientHeight >= container.scrollHeight - 100) {
                if (this.productsLoaded < this.maxProducts) {
                    loadingIndicator.style.display = 'block';
                    setTimeout(() => {
                        this.loadMoreProducts();
                        loadingIndicator.style.display = 'none';
                    }, 1000);
                }
            }
        });
    }

    loadMoreProducts() {
        const grid = document.getElementById('product-grid');
        const batch = 10;
        
        for (let i = 0; i < batch && this.productsLoaded < this.maxProducts; i++) {
            const product = this.createProductCard(this.productsLoaded + 1);
            grid.appendChild(product);
            this.productsLoaded++;
        }
        
        console.log(`📦 Loaded ${batch} more products. Total: ${this.productsLoaded}`);
    }

    createProductCard(id) {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.innerHTML = `
            <div class="product-image">📦</div>
            <div class="product-name">Product ${id}</div>
            <div class="product-price">$${(Math.random() * 100 + 10).toFixed(2)}</div>
            <button class="btn btn-sm">Quick View</button>
        `;
        
        // Quick view functionality
        const quickViewBtn = card.querySelector('button');
        quickViewBtn.addEventListener('click', () => {
            alert(`Quick view for Product ${id}`);
        });
        
        return card;
    }

    // Forms
    setupForms() {
        // Contact Form
        const contactForm = document.getElementById('contact-form');
        const subjectSelect = document.getElementById('contact-subject');
        const departmentGroup = document.getElementById('department-group');
        const departmentSelect = document.getElementById('department');

        subjectSelect.addEventListener('change', () => {
            if (subjectSelect.value === 'support') {
                departmentGroup.style.display = 'block';
                departmentSelect.innerHTML = `
                    <option value="">Select department</option>
                    <option value="technical">Technical Support</option>
                    <option value="billing">Billing Support</option>
                    <option value="general">General Support</option>
                `;
            } else {
                departmentGroup.style.display = 'none';
            }
        });

        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const messageDisplay = document.getElementById('contact-message-display');
            messageDisplay.textContent = '✅ Message sent successfully!';
            messageDisplay.className = 'form-message success';
            console.log('📧 Contact form submitted');
        });

        // Multi-step Form
        const surveyForm = document.getElementById('survey-form');
        const steps = surveyForm.querySelectorAll('.form-step');
        const progressFill = document.getElementById('progress-fill');
        let currentStep = 1;

        surveyForm.addEventListener('click', (e) => {
            if (e.target.classList.contains('next-step')) {
                if (currentStep < 3) {
                    steps[currentStep - 1].style.display = 'none';
                    currentStep++;
                    steps[currentStep - 1].style.display = 'block';
                    progressFill.style.width = `${(currentStep / 3) * 100}%`;
                }
            } else if (e.target.classList.contains('prev-step')) {
                if (currentStep > 1) {
                    steps[currentStep - 1].style.display = 'none';
                    currentStep--;
                    steps[currentStep - 1].style.display = 'block';
                    progressFill.style.width = `${(currentStep / 3) * 100}%`;
                }
            }
        });

        surveyForm.addEventListener('submit', (e) => {
            e.preventDefault();
            document.getElementById('survey-success').style.display = 'block';
            console.log('📋 Survey submitted successfully!');
        });
    }

    // Tabs
    setupTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabPanes = document.querySelectorAll('.tab-pane');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.getAttribute('data-tab');
                
                // Update active states
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Show target pane
                tabPanes.forEach(pane => {
                    pane.style.display = pane.id === targetTab ? 'block' : 'none';
                });
            });
        });

        // Show more functionality
        const showMoreBtn = document.querySelector('.show-more');
        const hiddenText = document.querySelector('.hidden-text');
        
        if (showMoreBtn) {
            showMoreBtn.addEventListener('click', () => {
                if (hiddenText.style.display === 'none') {
                    hiddenText.style.display = 'block';
                    showMoreBtn.textContent = 'Show Less';
                } else {
                    hiddenText.style.display = 'none';
                    showMoreBtn.textContent = 'Show More';
                }
            });
        }

        // Load comments
        const loadCommentsBtn = document.querySelector('.load-comments');
        const commentsSection = document.querySelector('.comments-section');
        
        if (loadCommentsBtn) {
            loadCommentsBtn.addEventListener('click', () => {
                commentsSection.style.display = 'block';
                commentsSection.innerHTML = `
                    <div class="comment">
                        <div class="comment-author">John Doe</div>
                        <div class="comment-text">Great product! Highly recommended.</div>
                    </div>
                    <div class="comment">
                        <div class="comment-author">Jane Smith</div>
                        <div class="comment-text">Excellent quality and fast shipping.</div>
                    </div>
                `;
                loadCommentsBtn.style.display = 'none';
                console.log('💬 Comments loaded');
            });
        }
    }

    // Data Table
    setupDataTable() {
        const loadMoreBtn = document.querySelector('.load-more-rows');
        const searchInput = document.querySelector('.search-input');
        const exportBtn = document.getElementById('export-btn');
        const sortableHeaders = document.querySelectorAll('.sortable');

        // Load more rows
        loadMoreBtn.addEventListener('click', () => {
            this.loadMoreTableRows();
        });

        // Search functionality
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#table-body tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });

        // Export functionality
        exportBtn.addEventListener('click', () => {
            console.log('📊 Exporting table data...');
            alert('Table data exported! (Check console)');
        });

        // Sorting
        sortableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                console.log(`🔄 Sorting by ${header.getAttribute('data-sort')}`);
            });
        });
    }

    loadMoreTableRows() {
        const tbody = document.getElementById('table-body');
        const batch = 10;
        
        for (let i = 0; i < batch; i++) {
            const row = document.createElement('tr');
            const id = this.tableRowsLoaded + i + 1;
            row.innerHTML = `
                <td>User ${id}</td>
                <td>user${id}@example.com</td>
                <td>${new Date().toLocaleDateString()}</td>
                <td><button class="btn btn-sm">Edit</button></td>
            `;
            tbody.appendChild(row);
        }
        
        this.tableRowsLoaded += batch;
        console.log(`📄 Loaded ${batch} more rows. Total: ${this.tableRowsLoaded}`);
    }

    // Load initial data
    loadInitialData() {
        // Load initial products
        this.loadMoreProducts();
        
        // Load initial table rows
        this.loadMoreTableRows();
    }

    // Load content when navigating to sections
    loadSectionContent(sectionId) {
        switch(sectionId) {
            case 'catalog':
                // Ensure products are loaded in catalog
                if (this.productsLoaded === 0) {
                    this.loadMoreProducts();
                }
                break;
            case 'data-tables':
                // Ensure table rows are loaded
                if (this.tableRowsLoaded === 0) {
                    this.loadMoreTableRows();
                }
                break;
            case 'forms':
                // Forms are already set up
                break;
            case 'tabs':
                // Tabs content is static
                break;
        }
    }

    // Inspector Mode
    setupInspector() {
        const inspectorBtn = document.getElementById('inspector-btn');
        
        // Create tooltip element
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'inspector-tooltip';
        this.tooltip.style.cssText = `
            position: fixed;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-family: monospace;
            pointer-events: none;
            z-index: 10000;
            display: none;
            max-width: 300px;
        `;
        document.body.appendChild(this.tooltip);

        inspectorBtn.addEventListener('click', () => {
            this.toggleInspector();
        });

        // Add mouse event listeners
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseout', this.handleMouseOut.bind(this));
    }

    toggleInspector() {
        this.inspectorMode = !this.inspectorMode;
        const inspectorBtn = document.getElementById('inspector-btn');
        
        if (this.inspectorMode) {
            inspectorBtn.classList.add('active');
            inspectorBtn.style.background = '#0fbbaa';
            document.body.style.cursor = 'crosshair';
        } else {
            inspectorBtn.classList.remove('active');
            inspectorBtn.style.background = '';
            document.body.style.cursor = '';
            this.tooltip.style.display = 'none';
            this.removeHighlight();
        }
    }

    handleMouseMove(e) {
        if (!this.inspectorMode) return;
        
        const element = e.target;
        if (element === this.tooltip) return;
        
        // Highlight element
        this.highlightElement(element);
        
        // Show tooltip with element info
        const info = this.getElementInfo(element);
        this.tooltip.innerHTML = info;
        this.tooltip.style.display = 'block';
        
        // Position tooltip
        const x = e.clientX + 15;
        const y = e.clientY + 15;
        
        // Adjust position if tooltip would go off screen
        const rect = this.tooltip.getBoundingClientRect();
        const adjustedX = x + rect.width > window.innerWidth ? x - rect.width - 30 : x;
        const adjustedY = y + rect.height > window.innerHeight ? y - rect.height - 30 : y;
        
        this.tooltip.style.left = adjustedX + 'px';
        this.tooltip.style.top = adjustedY + 'px';
    }

    handleMouseOut(e) {
        if (!this.inspectorMode) return;
        if (e.target === document.body) {
            this.removeHighlight();
            this.tooltip.style.display = 'none';
        }
    }

    highlightElement(element) {
        this.removeHighlight();
        element.style.outline = '2px solid #0fbbaa';
        element.style.outlineOffset = '1px';
        element.setAttribute('data-inspector-highlighted', 'true');
    }

    removeHighlight() {
        const highlighted = document.querySelector('[data-inspector-highlighted]');
        if (highlighted) {
            highlighted.style.outline = '';
            highlighted.style.outlineOffset = '';
            highlighted.removeAttribute('data-inspector-highlighted');
        }
    }

    getElementInfo(element) {
        const tagName = element.tagName.toLowerCase();
        const id = element.id ? `#${element.id}` : '';
        const classes = element.className ? 
            `.${element.className.split(' ').filter(c => c).join('.')}` : '';
        
        let selector = tagName;
        if (id) {
            selector = id;
        } else if (classes) {
            selector = `${tagName}${classes}`;
        }
        
        // Build info HTML
        let info = `<strong>${selector}</strong>`;
        
        // Add additional attributes
        const attrs = [];
        if (element.name) attrs.push(`name="${element.name}"`);
        if (element.type) attrs.push(`type="${element.type}"`);
        if (element.href) attrs.push(`href="${element.href}"`);
        if (element.value && element.tagName === 'INPUT') attrs.push(`value="${element.value}"`);
        
        if (attrs.length > 0) {
            info += `<br><span style="color: #888;">${attrs.join(' ')}</span>`;
        }
        
        return info;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.playgroundApp = new PlaygroundApp();
    console.log('🎮 Playground app initialized!');
});