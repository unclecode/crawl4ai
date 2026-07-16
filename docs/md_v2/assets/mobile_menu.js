// mobile_menu.js - Hamburger menu for mobile view
document.addEventListener('DOMContentLoaded', () => {
    // Get references to key elements
    const sidePanel = document.getElementById('terminal-mkdocs-side-panel');
    const mainHeader = document.querySelector('.terminal .container:first-child');
    
    if (!sidePanel || !mainHeader) {
        console.warn('Mobile menu: Required elements not found');
        return;
    }
    
    // Force hide sidebar on mobile
    const checkMobile = () => {
        if (window.innerWidth <= 768) {
            // Force with !important-like priority
            sidePanel.style.setProperty('left', '-100%', 'important');
            // Also hide terminal-menu from the theme
            const terminalMenu = document.querySelector('.terminal-menu');
            if (terminalMenu) {
                terminalMenu.style.setProperty('display', 'none', 'important');
            }
        } else {
            sidePanel.style.removeProperty('left');
            // Restore terminal-menu if it exists
            const terminalMenu = document.querySelector('.terminal-menu');
            if (terminalMenu) {
                terminalMenu.style.removeProperty('display');
            }
        }
    };
    
    // Run on initial load
    checkMobile();
    
    // Also run on resize
    window.addEventListener('resize', checkMobile);
    
    // Create hamburger button
    const hamburgerBtn = document.createElement('button');
    hamburgerBtn.className = 'mobile-menu-toggle';
    hamburgerBtn.setAttribute('aria-label', 'Toggle navigation menu');
    hamburgerBtn.innerHTML = `
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
    `;
    
    // Create backdrop overlay
    const menuBackdrop = document.createElement('div');
    menuBackdrop.className = 'mobile-menu-backdrop';
    menuBackdrop.style.display = 'none';
    document.body.appendChild(menuBackdrop);
    
    // Make sure it's properly hidden on page load
    if (window.innerWidth <= 768) {
        menuBackdrop.style.display = 'none';
    }
    
    // Insert hamburger button into header
    mainHeader.insertBefore(hamburgerBtn, mainHeader.firstChild);
    
    // Add menu close button to side panel
    const closeBtn = document.createElement('button');
    closeBtn.className = 'mobile-menu-close';
    closeBtn.setAttribute('aria-label', 'Close navigation menu');
    closeBtn.innerHTML = `&times;`;
    sidePanel.insertBefore(closeBtn, sidePanel.firstChild);
    
    // Toggle function
    function toggleMobileMenu() {
        const isOpen = sidePanel.classList.toggle('sidebar-visible');
        
        // Toggle backdrop
        menuBackdrop.style.display = isOpen ? 'block' : 'none';
        
        // Toggle aria-expanded
        hamburgerBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        
        // Toggle hamburger animation class
        hamburgerBtn.classList.toggle('is-active');
        
        // Force sidebar visibility setting
        if (isOpen) {
            sidePanel.style.setProperty('left', '0', 'important');
        } else {
            sidePanel.style.setProperty('left', '-100%', 'important');
        }
        
        // Prevent body scrolling when menu is open
        document.body.style.overflow = isOpen ? 'hidden' : '';
    }
    
    // Event listeners
    hamburgerBtn.addEventListener('click', toggleMobileMenu);
    closeBtn.addEventListener('click', toggleMobileMenu);
    menuBackdrop.addEventListener('click', toggleMobileMenu);
    
    // Close menu on window resize to desktop
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768 && sidePanel.classList.contains('sidebar-visible')) {
            toggleMobileMenu();
        }
    });
    
    console.log('Mobile menu initialized');
});