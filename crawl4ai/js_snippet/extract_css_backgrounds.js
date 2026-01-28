/**
 * Extract CSS background images from all elements on the page.
 * This script is executed by crawl4ai to extract CSS background images.
 *
 * Returns a JSON object with css_images array containing:
 * - src: Image URL
 * - selector: CSS selector for the element
 * - element_tag: Tag name of the element
 * - element_class: Class names of the element
 * - element_id: ID of the element
 * - style_property: Which CSS property had the image
 * - computed_width: Element width in pixels
 * - computed_height: Element height in pixels
 * - is_repeated: Whether background repeats
 * - background_position: CSS background-position value
 * - background_size: CSS background-size value
 */

(function() {
    const results = [];
    const allElements = document.querySelectorAll('*');
    const processedUrls = new Set();

    /**
     * Generate a unique CSS selector for an element
     */
    function getElementSelector(element) {
        if (element.id) {
            return '#' + element.id;
        }

        let selector = element.tagName.toLowerCase();

        if (element.className && typeof element.className === 'string') {
            const classes = element.className.trim().split(/\s+/).filter(c => c);
            if (classes.length > 0) {
                selector += '.' + classes.join('.');
            }
        }

        // Add nth-child if needed for uniqueness
        const parent = element.parentElement;
        if (parent) {
            const siblings = Array.from(parent.children).filter(
                child => child.tagName === element.tagName
            );
            if (siblings.length > 1) {
                const index = siblings.indexOf(element) + 1;
                selector += `:nth-child(${index})`;
            }
        }

        return selector;
    }

    /**
     * Check if element is visible and has meaningful dimensions
     */
    function isElementVisible(element) {
        const rect = element.getBoundingClientRect();
        const style = window.getComputedStyle(element);

        // Check if element has display: none or visibility: hidden
        if (style.display === 'none' || style.visibility === 'hidden') {
            return false;
        }

        // Check if element has meaningful dimensions
        return rect.width > 0 && rect.height > 0;
    }

    allElements.forEach(element => {
        // Skip invisible elements
        if (!isElementVisible(element)) {
            return;
        }

        const style = window.getComputedStyle(element);
        const backgroundImage = style.backgroundImage;

        // Skip if no background image or if it's 'none'
        if (!backgroundImage || backgroundImage === 'none' || backgroundImage === 'initial') {
            return;
        }

        // Parse url() from background-image property
        // Handles: url(...), url("..."), url('...'), and multiple backgrounds
        const urlPattern = /url\(['"]?([^'")\s]+)['"]?\)/g;
        let match;
        const urls = [];

        while ((match = urlPattern.exec(backgroundImage)) !== null) {
            urls.push(match[1]);
        }

        if (urls.length === 0) {
            return;
        }

        // Process each URL
        urls.forEach(url => {
            // Skip data URLs
            if (url.startsWith('data:')) {
                return;
            }

            // Skip already processed URLs (deduplication)
            if (processedUrls.has(url)) {
                return;
            }
            processedUrls.add(url);

            // Get element dimensions
            const rect = element.getBoundingClientRect();

            // Create result object
            const result = {
                src: url,
                selector: getElementSelector(element),
                element_tag: element.tagName.toLowerCase(),
                element_class: element.className || '',
                element_id: element.id || '',
                style_property: 'background-image',
                computed_width: Math.round(rect.width),
                computed_height: Math.round(rect.height),
                is_repeated: style.backgroundRepeat !== 'no-repeat',
                background_position: style.backgroundPosition,
                background_size: style.backgroundSize
            };

            results.push(result);
        });
    });

    return {
        css_images: results
    };
})();
