async () => {
    // Function to check if element is visible
    const isVisible = (elem) => {
        const style = window.getComputedStyle(elem);
        return style.display !== "none" && style.visibility !== "hidden" && style.opacity !== "0";
    };

    // Common selectors for popups and overlays
    const commonSelectors = [
        // Close buttons first
        'button[class*="close" i]',
        'button[class*="dismiss" i]',
        'button[aria-label*="close" i]',
        'button[title*="close" i]',
        'a[class*="close" i]',
        'span[class*="close" i]',

        // Cookie notices
        '[class*="cookie-banner" i]',
        '[id*="cookie-banner" i]',
        '[class*="cookie-consent" i]',
        '[id*="cookie-consent" i]',

        // Newsletter/subscription dialogs
        '[class*="newsletter" i]',
        '[class*="subscribe" i]',

        // Generic popups/modals
        '[class*="popup" i]',
        '[class*="modal" i]',
        '[class*="overlay" i]',
        '[class*="dialog" i]',
        '[role="dialog"]',
        '[role="alertdialog"]',
    ];

    // Try to click close buttons first
    for (const selector of commonSelectors.slice(0, 6)) {
        const closeButtons = document.querySelectorAll(selector);
        for (const button of closeButtons) {
            if (isVisible(button)) {
                try {
                    button.click();
                    await new Promise((resolve) => setTimeout(resolve, 100));
                } catch (e) {
                    console.log("Error clicking button:", e);
                }
            }
        }
    }

    // Remove remaining overlay elements
    const removeOverlays = () => {
        // Find elements with high z-index
        const allElements = document.querySelectorAll("*");
        for (const elem of allElements) {
            const style = window.getComputedStyle(elem);
            const zIndex = parseInt(style.zIndex);
            const position = style.position;

            if (
                isVisible(elem) &&
                (zIndex > 999 || position === "fixed" || position === "absolute") &&
                (elem.offsetWidth > window.innerWidth * 0.5 ||
                    elem.offsetHeight > window.innerHeight * 0.5 ||
                    style.backgroundColor.includes("rgba") ||
                    parseFloat(style.opacity) < 1)
            ) {
                elem.remove();
            }
        }

        // Remove elements matching common selectors
        for (const selector of commonSelectors) {
            const elements = document.querySelectorAll(selector);
            elements.forEach((elem) => {
                if (isVisible(elem)) {
                    elem.remove();
                }
            });
        }
    };

    // Remove overlay elements
    removeOverlays();

    // Remove any fixed/sticky position elements at the top/bottom
    const removeFixedElements = () => {
        const elements = document.querySelectorAll("*");
        elements.forEach((elem) => {
            const style = window.getComputedStyle(elem);
            if ((style.position === "fixed" || style.position === "sticky") && isVisible(elem)) {
                elem.remove();
            }
        });
    };

    removeFixedElements();

    // Remove empty block elements as: div, p, span, etc.
    const removeEmptyBlockElements = () => {
        const blockElements = document.querySelectorAll(
            "div, p, span, section, article, header, footer, aside, nav, main, ul, ol, li, dl, dt, dd, h1, h2, h3, h4, h5, h6"
        );
        blockElements.forEach((elem) => {
            if (elem.innerText.trim() === "") {
                elem.remove();
            }
        });
    };

    // Remove margin-right and padding-right from body (often added by modal scripts)
    document.body.style.marginRight = "0px";
    document.body.style.paddingRight = "0px";
    document.body.style.overflow = "auto";

    // Wait a bit for any animations to complete
    document.body.scrollIntoView(false);
    await new Promise((resolve) => setTimeout(resolve, 50));
};
