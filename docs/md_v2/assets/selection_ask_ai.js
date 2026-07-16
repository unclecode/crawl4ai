// ==== File: docs/assets/selection_ask_ai.js ====

document.addEventListener('DOMContentLoaded', () => {
    let askAiButton = null;
    const askAiPageUrl = '/core/ask-ai/'; // Adjust if your Ask AI page path is different

    function createAskAiButton() {
        const button = document.createElement('button');
        button.id = 'ask-ai-selection-btn';
        button.className = 'ask-ai-selection-button';
        
        // Add icon and text for better visibility
        button.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="12" height="12" fill="currentColor" style="margin-right: 4px; vertical-align: middle;">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4V4c0-1.1-.9-2-2-2z"/>
            </svg>
            <span>Ask AI</span>
        `;
        
        // Common styles
        button.style.display = 'none'; // Initially hidden
        button.style.position = 'absolute';
        button.style.zIndex = '1500'; // Ensure it's on top
        button.style.boxShadow = '0 3px 8px rgba(0, 0, 0, 0.4)'; // More pronounced shadow
        button.style.transition = 'transform 0.15s ease, background-color 0.2s ease'; // Smooth hover effect
        
        // Add transform on hover
        button.addEventListener('mouseover', () => {
            button.style.transform = 'scale(1.05)';
        });
        
        button.addEventListener('mouseout', () => {
            button.style.transform = 'scale(1)';
        });
        
        document.body.appendChild(button);
        button.addEventListener('click', handleAskAiClick);
        return button;
    }

    function getSafeSelectedText() {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) {
            return null;
        }
        // Avoid selecting text within the button itself if it was somehow selected
        const container = selection.getRangeAt(0).commonAncestorContainer;
        if (askAiButton && askAiButton.contains(container)) {
             return null;
        }

        const text = selection.toString().trim();
        return text.length > 0 ? text : null;
    }

    function positionButton(event) {
         const selection = window.getSelection();
         if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
             hideButton();
             return;
         }

        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();

        // Get viewport dimensions
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Calculate position based on selection
        const scrollX = window.scrollX;
        const scrollY = window.scrollY;
        
        // Default position (top-right of selection)
        let buttonTop = rect.top + scrollY - askAiButton.offsetHeight - 5; // 5px above
        let buttonLeft = rect.right + scrollX + 5; // 5px to the right
        
        // Check if we're on mobile (which we define as less than 768px)
        const isMobile = viewportWidth <= 768;
        
        if (isMobile) {
            // On mobile, position centered above selection to avoid edge issues
            buttonTop = rect.top + scrollY - askAiButton.offsetHeight - 10; // 10px above on mobile
            buttonLeft = rect.left + scrollX + (rect.width / 2) - (askAiButton.offsetWidth / 2); // Centered
        } else {
            // For desktop, ensure the button doesn't go off screen
            // Check right edge
            if (buttonLeft + askAiButton.offsetWidth > scrollX + viewportWidth) {
                buttonLeft = scrollX + viewportWidth - askAiButton.offsetWidth - 10; // 10px from right edge
            }
        }
        
        // Check top edge (for all devices)
        if (buttonTop < scrollY) {
            // If would go above viewport, position below selection instead
            buttonTop = rect.bottom + scrollY + 5; // 5px below
        }

        askAiButton.style.top = `${buttonTop}px`;
        askAiButton.style.left = `${buttonLeft}px`;
        askAiButton.style.display = 'block'; // Show the button
    }

    function hideButton() {
        if (askAiButton) {
            askAiButton.style.display = 'none';
        }
    }

    function handleAskAiClick(event) {
        event.stopPropagation(); // Prevent mousedown from hiding button immediately
        const selectedText = getSafeSelectedText();
        if (selectedText) {
            console.log("Selected Text:", selectedText);
            // Base64 encode for URL safety (handles special chars, line breaks)
            // Use encodeURIComponent first for proper Unicode handling before btoa
            const encodedText = btoa(unescape(encodeURIComponent(selectedText)));
            const targetUrl = `${askAiPageUrl}?qq=${encodedText}`;
            console.log("Navigating to:", targetUrl);
            window.location.href = targetUrl; // Navigate to Ask AI page
        }
        hideButton(); // Hide after click
    }

    // --- Event Listeners ---

    // Function to handle selection events (both mouse and touch)
    function handleSelectionEvent(event) {
        // Slight delay to ensure selection is registered
        setTimeout(() => {
            const selectedText = getSafeSelectedText();
            if (selectedText) {
                if (!askAiButton) {
                    askAiButton = createAskAiButton();
                }
                // Don't position if the event was ON the button itself
                if (event.target !== askAiButton) {
                     positionButton(event);
                }
            } else {
                hideButton();
            }
        }, 10); // Small delay
    }

    // Mouse selection events (desktop)
    document.addEventListener('mouseup', handleSelectionEvent);

    // Touch selection events (mobile)
    document.addEventListener('touchend', handleSelectionEvent);
    document.addEventListener('selectionchange', () => {
        // This helps with mobile selection which can happen without mouseup/touchend
        setTimeout(() => {
            const selectedText = getSafeSelectedText();
            if (selectedText && askAiButton) {
                positionButton();
            }
        }, 300); // Longer delay for selection change
    });

    // Hide button on various events
    document.addEventListener('mousedown', (event) => {
        // Hide if clicking anywhere EXCEPT the button itself
        if (askAiButton && event.target !== askAiButton) {
            hideButton();
        }
    });
    
    document.addEventListener('touchstart', (event) => {
        // Same for touch events, but only hide if not on the button
        if (askAiButton && event.target !== askAiButton) {
            hideButton();
        }
    });
    
    document.addEventListener('scroll', hideButton, true); // Capture scroll events
    
    // Also hide when pressing Escape key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            hideButton();
        }
    });

    console.log("Selection Ask AI script loaded.");
});