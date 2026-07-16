// ==== File: assets/page_actions.js ====
// Page Actions - Copy/View Markdown functionality

document.addEventListener('DOMContentLoaded', () => {
    // Configuration
    const config = {
        githubRepo: 'unclecode/crawl4ai',
        githubBranch: 'main',
        docsPath: 'docs/md_v2',
        excludePaths: ['/apps/c4a-script/', '/apps/llmtxt/', '/apps/crawl4ai-assistant/', '/core/ask-ai/'], // Don't show on app pages
    };

    let cachedMarkdown = null;
    let cachedMarkdownPath = null;

    // Check if we should show the button on this page
    function shouldShowButton() {
        const currentPath = window.location.pathname;

        // Don't show on homepage
        if (currentPath === '/' || currentPath === '/index.html') {
            return false;
        }

        // Don't show on 404 pages
        if (document.title && document.title.toLowerCase().includes('404')) {
            return false;
        }

        // Require mkdocs main content container
        const mainContent = document.getElementById('terminal-mkdocs-main-content');
        if (!mainContent) {
            return false;
        }

        // Don't show on excluded paths (apps)
        for (const excludePath of config.excludePaths) {
            if (currentPath.includes(excludePath)) {
                return false;
            }
        }

        // Only show on documentation pages
        return true;
    }

    if (!shouldShowButton()) {
        return;
    }

    // Get current page markdown path
    function getCurrentMarkdownPath() {
        let path = window.location.pathname;

        // Remove leading/trailing slashes
        path = path.replace(/^\/|\/$/g, '');

        // Remove .html extension if present
        path = path.replace(/\.html$/, '');

        // Handle root/index
        if (!path || path === 'index') {
            return 'index.md';
        }

        // Add .md extension
        return `${path}.md`;
    }

    async function loadMarkdownContent() {
        const mdPath = getCurrentMarkdownPath();

        if (!mdPath) {
            throw new Error('Invalid markdown path');
        }

        const rawUrl = getGithubRawUrl();
        const response = await fetch(rawUrl);

        if (!response.ok) {
            throw new Error(`Failed to fetch markdown: ${response.status}`);
        }

        const markdown = await response.text();
        cachedMarkdown = markdown;
        cachedMarkdownPath = mdPath;
        return markdown;
    }

    async function ensureMarkdownCached() {
        const mdPath = getCurrentMarkdownPath();

        if (!mdPath) {
            return false;
        }

        if (cachedMarkdown && cachedMarkdownPath === mdPath) {
            return true;
        }

        try {
            await loadMarkdownContent();
            return true;
        } catch (error) {
            console.warn('Page Actions: Markdown not available for this page.', error);
            cachedMarkdown = null;
            cachedMarkdownPath = null;
            return false;
        }
    }

    async function getMarkdownContent() {
        const available = await ensureMarkdownCached();
        if (!available) {
            throw new Error('Markdown not available for this page.');
        }
        return cachedMarkdown;
    }

    // Get GitHub raw URL for current page
    function getGithubRawUrl() {
        const mdPath = getCurrentMarkdownPath();
        return `https://raw.githubusercontent.com/${config.githubRepo}/${config.githubBranch}/${config.docsPath}/${mdPath}`;
    }

    // Get GitHub file URL for current page (for viewing)
    function getGithubFileUrl() {
        const mdPath = getCurrentMarkdownPath();
        return `https://github.com/${config.githubRepo}/blob/${config.githubBranch}/${config.docsPath}/${mdPath}`;
    }

    // Create the UI
    function createPageActionsUI() {
        // Find the main content area
        const mainContent = document.getElementById('terminal-mkdocs-main-content');
        if (!mainContent) {
            console.warn('Page Actions: Could not find #terminal-mkdocs-main-content');
            return null;
        }

        // Create button
        const button = document.createElement('button');
        button.className = 'page-actions-button';
        button.setAttribute('aria-label', 'Page copy');
        button.setAttribute('aria-expanded', 'false');
        button.innerHTML = '<span>Page Copy</span>';

        // Create overlay for mobile
        const overlay = document.createElement('div');
        overlay.className = 'page-actions-overlay';

        // Create dropdown
        const dropdown = document.createElement('div');
        dropdown.className = 'page-actions-dropdown';
        dropdown.setAttribute('role', 'menu');
        dropdown.innerHTML = `
            <div class="page-actions-header">Page Copy</div>
            <ul class="page-actions-menu">
                <li class="page-action-item">
                    <a href="#" class="page-action-link" id="action-copy-markdown" role="menuitem">
                        <span class="page-action-icon icon-copy"></span>
                        <span class="page-action-text">
                            <span class="page-action-label">Copy as Markdown</span>
                            <span class="page-action-description">Copy page for LLMs</span>
                        </span>
                    </a>
                </li>
                <li class="page-action-item">
                    <a href="#" class="page-action-link page-action-external" id="action-view-markdown" target="_blank" role="menuitem">
                        <span class="page-action-icon icon-view"></span>
                        <span class="page-action-text">
                            <span class="page-action-label">View as Markdown</span>
                            <span class="page-action-description">Open raw source</span>
                        </span>
                    </a>
                </li>
                <div class="page-actions-divider"></div>
                <li class="page-action-item">
                    <a href="#" class="page-action-link page-action-external" id="action-open-chatgpt" role="menuitem">
                        <span class="page-action-icon icon-ai"></span>
                        <span class="page-action-text">
                            <span class="page-action-label">Open in ChatGPT</span>
                            <span class="page-action-description">Ask questions about this page</span>
                        </span>
                    </a>
                </li>
            </ul>
            <div class="page-actions-footer">ESC to close</div>
        `;

        // Create a wrapper for button and dropdown
        const wrapper = document.createElement('div');
        wrapper.className = 'page-actions-wrapper';
        wrapper.appendChild(button);
        wrapper.appendChild(dropdown);

        // Inject into main content area
        mainContent.appendChild(wrapper);

        // Append overlay to body
        document.body.appendChild(overlay);

        return { button, dropdown, overlay, wrapper };
    }

    // Toggle dropdown
    function toggleDropdown(button, dropdown, overlay) {
        const isActive = dropdown.classList.contains('active');

        if (isActive) {
            closeDropdown(button, dropdown, overlay);
        } else {
            openDropdown(button, dropdown, overlay);
        }
    }

    function openDropdown(button, dropdown, overlay) {
        dropdown.classList.add('active');
        // Don't activate overlay - not needed
        button.classList.add('active');
        button.setAttribute('aria-expanded', 'true');
    }

    function closeDropdown(button, dropdown, overlay) {
        dropdown.classList.remove('active');
        // Don't deactivate overlay - not needed
        button.classList.remove('active');
        button.setAttribute('aria-expanded', 'false');
    }

    // Show notification
    function showNotification(message, duration = 2000) {
        const notification = document.createElement('div');
        notification.className = 'page-actions-notification';
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, duration);
    }

    // Copy markdown to clipboard
    async function copyMarkdownToClipboard(link) {
        // Add loading state
        link.classList.add('loading');

        try {
            const markdown = await getMarkdownContent();

            // Copy to clipboard
            await navigator.clipboard.writeText(markdown);

            // Visual feedback
            link.classList.remove('loading');
            link.classList.add('page-action-copied');

            showNotification('Markdown copied to clipboard!');

            // Reset after delay
            setTimeout(() => {
                link.classList.remove('page-action-copied');
            }, 2000);

        } catch (error) {
            console.error('Error copying markdown:', error);
            link.classList.remove('loading');
            showNotification('Error: Could not copy markdown');
        }
    }

    // View markdown in new tab
    function viewMarkdown() {
        const githubUrl = getGithubFileUrl();
        window.open(githubUrl, '_blank', 'noopener,noreferrer');
    }

    function getCurrentPageUrl() {
        const { href } = window.location;
        return href.split('#')[0];
    }

    function openChatGPT() {
        const pageUrl = getCurrentPageUrl();
        const prompt = encodeURIComponent(`Read ${pageUrl} so I can ask questions about it.`);
        const chatUrl = `https://chatgpt.com/?hint=search&prompt=${prompt}`;
        window.open(chatUrl, '_blank', 'noopener,noreferrer');
    }

    (async () => {
        if (!shouldShowButton()) {
            return;
        }

        const markdownAvailable = await ensureMarkdownCached();
        if (!markdownAvailable) {
            return;
        }

        const ui = createPageActionsUI();
        if (!ui) {
            return;
        }

        const { button, dropdown, overlay } = ui;

        // Event listeners
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDropdown(button, dropdown, overlay);
        });

        overlay.addEventListener('click', () => {
            closeDropdown(button, dropdown, overlay);
        });

        // Copy markdown action
        document.getElementById('action-copy-markdown').addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            await copyMarkdownToClipboard(e.currentTarget);
        });

        // View markdown action
        document.getElementById('action-view-markdown').addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            viewMarkdown();
            closeDropdown(button, dropdown, overlay);
        });

        // Open in ChatGPT action
        document.getElementById('action-open-chatgpt').addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            openChatGPT();
            closeDropdown(button, dropdown, overlay);
        });

        // Close on ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && dropdown.classList.contains('active')) {
                closeDropdown(button, dropdown, overlay);
            }
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target) && !button.contains(e.target)) {
                closeDropdown(button, dropdown, overlay);
            }
        });

        // Prevent dropdown from closing when clicking inside
        dropdown.addEventListener('click', (e) => {
            // Only stop propagation if not clicking on a link
            if (!e.target.closest('.page-action-link')) {
                e.stopPropagation();
            }
        });

        // Close dropdown on link click (except for copy which handles itself)
        dropdown.querySelectorAll('.page-action-link:not(#action-copy-markdown)').forEach(link => {
            link.addEventListener('click', () => {
                if (!link.classList.contains('disabled')) {
                    setTimeout(() => {
                        closeDropdown(button, dropdown, overlay);
                    }, 100);
                }
            });
        });

        // Handle window resize
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                // Close dropdown on resize to prevent positioning issues
                if (dropdown.classList.contains('active')) {
                    closeDropdown(button, dropdown, overlay);
                }
            }, 250);
        });

        // Accessibility: Focus management
        button.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleDropdown(button, dropdown, overlay);

                // Focus first menu item when opening
                if (dropdown.classList.contains('active')) {
                    const firstLink = dropdown.querySelector('.page-action-link:not(.disabled)');
                    if (firstLink) {
                        setTimeout(() => firstLink.focus(), 100);
                    }
                }
            }
        });

        // Arrow key navigation within menu
        dropdown.addEventListener('keydown', (e) => {
            if (!dropdown.classList.contains('active')) return;

            const links = Array.from(dropdown.querySelectorAll('.page-action-link:not(.disabled)'));
            const currentIndex = links.indexOf(document.activeElement);

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                const nextIndex = (currentIndex + 1) % links.length;
                links[nextIndex].focus();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                const prevIndex = (currentIndex - 1 + links.length) % links.length;
                links[prevIndex].focus();
            } else if (e.key === 'Home') {
                e.preventDefault();
                links[0].focus();
            } else if (e.key === 'End') {
                e.preventDefault();
                links[links.length - 1].focus();
            }
        });

        console.log('Page Actions initialized for:', getCurrentMarkdownPath());
    })();
});