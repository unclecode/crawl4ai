// ==== File: assets/toc.js ====

document.addEventListener('DOMContentLoaded', () => {
    const mainContent = document.getElementById('terminal-mkdocs-main-content');
    const tocContainer = document.getElementById('toc-sidebar');
    const mainGrid = document.querySelector('.terminal-mkdocs-main-grid'); // Get the flex container

    if (!mainContent) {
        console.warn("TOC Generator: Main content area '#terminal-mkdocs-main-content' not found.");
        return;
    }

    // --- Create ToC container if it doesn't exist ---
    let tocElement = tocContainer;
    if (!tocElement) {
        if (!mainGrid) {
            console.warn("TOC Generator: Flex container '.terminal-mkdocs-main-grid' not found to append ToC.");
            return;
        }
        tocElement = document.createElement('aside');
        tocElement.id = 'toc-sidebar';
        tocElement.style.display = 'none'; // Keep hidden initially
        // Append it as the last child of the flex grid
        mainGrid.appendChild(tocElement);
        console.info("TOC Generator: Created '#toc-sidebar' element.");
    }

    // --- Find Headings (h2, h3, h4 are common for ToC) ---
    const headings = mainContent.querySelectorAll('h2, h3, h4');
    if (headings.length === 0) {
        console.info("TOC Generator: No headings found on this page. ToC not generated.");
        tocElement.style.display = 'none'; // Ensure it's hidden
        return;
    }

    // --- Generate ToC List ---
    const tocList = document.createElement('ul');
    const observerTargets = []; // Store headings for IntersectionObserver

    headings.forEach((heading, index) => {
        // Ensure heading has an ID for linking
        if (!heading.id) {
            // Create a simple slug-like ID
            heading.id = `toc-heading-${index}-${heading.textContent.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')}`;
        }

        const listItem = document.createElement('li');
        const link = document.createElement('a');

        link.href = `#${heading.id}`;
        link.textContent = heading.textContent;

        // Add class for styling based on heading level
        const level = parseInt(heading.tagName.substring(1), 10); // Get 2, 3, or 4
        listItem.classList.add(`toc-level-${level}`);

        listItem.appendChild(link);
        tocList.appendChild(listItem);
        observerTargets.push(heading); // Add to observer list
    });

    // --- Populate and Show ToC ---
    // Optional: Add a title
    const tocTitle = document.createElement('h4');
    tocTitle.textContent = 'On this page'; // Customize title if needed

    tocElement.innerHTML = ''; // Clear previous content if any
    tocElement.appendChild(tocTitle);
    tocElement.appendChild(tocList);
    tocElement.style.display = ''; // Show the ToC container

    console.info(`TOC Generator: Generated ToC with ${headings.length} items.`);

    // --- Scroll Spy using Intersection Observer ---
    const tocLinks = tocElement.querySelectorAll('a');
    let activeLink = null; // Keep track of the current active link

    const observerOptions = {
        // Observe changes relative to the viewport, offset by the header height
        // Negative top margin pushes the intersection trigger point down
        // Negative bottom margin ensures elements low on the screen can trigger before they exit
        rootMargin: `-${getComputedStyle(document.documentElement).getPropertyValue('--header-height').trim()} 0px -60% 0px`,
        threshold: 0 // Trigger as soon as any part enters/exits the boundary
    };

    const observerCallback = (entries) => {
        let topmostVisibleHeading = null;

        entries.forEach(entry => {
            const link = tocElement.querySelector(`a[href="#${entry.target.id}"]`);
            if (!link) return;

            // Check if the heading is intersecting (partially or fully visible within rootMargin)
            if (entry.isIntersecting) {
                 // Among visible headings, find the one closest to the top edge (within the rootMargin)
                if (!topmostVisibleHeading || entry.boundingClientRect.top < topmostVisibleHeading.boundingClientRect.top) {
                    topmostVisibleHeading = entry.target;
                 }
            }
        });

        // If we found a topmost visible heading, activate its link
        if (topmostVisibleHeading) {
            const newActiveLink = tocElement.querySelector(`a[href="#${topmostVisibleHeading.id}"]`);
            if (newActiveLink && newActiveLink !== activeLink) {
                 // Remove active class from previous link
                 if (activeLink) {
                     activeLink.classList.remove('active');
                     activeLink.parentElement.classList.remove('active-parent'); // Optional parent styling
                 }
                 // Add active class to the new link
                 newActiveLink.classList.add('active');
                 newActiveLink.parentElement.classList.add('active-parent'); // Optional parent styling
                 activeLink = newActiveLink;

                 // Optional: Scroll the ToC sidebar to keep the active link visible
                 // newActiveLink.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
        // If no headings are intersecting (scrolled past the last one?), maybe deactivate all
        // Or keep the last one active - depends on desired behavior. Current logic keeps last active.
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);

    // Observe all target headings
    observerTargets.forEach(heading => observer.observe(heading));

    // Initial check in case a heading is already in view on load
    // (Requires slight delay for accurate layout calculation)
    setTimeout(() => {
        observerCallback(observer.takeRecords()); // Process initial state
    }, 100);

    // move footer and the hr before footer to the end of the main content
    const footer = document.querySelector('footer');
    const hr = footer.previousElementSibling;
    if (hr && hr.tagName === 'HR') {
        mainContent.appendChild(hr);
    }
    mainContent.appendChild(footer);
    console.info("TOC Generator: Footer moved to the end of the main content.");

});