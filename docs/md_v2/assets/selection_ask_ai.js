// ==== File: docs/assets/selection_ask_ai.js ====

document.addEventListener('DOMContentLoaded', () => {
    let askAiButton = null;
    const askAiPageUrl = '/core/ask-ai/'; // Adjust if your Ask AI page path is different

    function createAskAiButton() {
        const button = document.createElement('button');
        button.id = 'ask-ai-selection-btn';
        button.className = 'ask-ai-selection-button';
        button.textContent = 'Ask AI'; // Or use an icon
        button.style.display = 'none'; // Initially hidden
        button.style.position = 'absolute';
        button.style.zIndex = '1500'; // Ensure it's on top
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

        // Calculate position: top-right of the selection
        const scrollX = window.scrollX;
        const scrollY = window.scrollY;
        const buttonTop = rect.top + scrollY - askAiButton.offsetHeight - 5; // 5px above
        const buttonLeft = rect.right + scrollX + 5; // 5px to the right

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

    // Show button on mouse up after selection
    document.addEventListener('mouseup', (event) => {
        // Slight delay to ensure selection is registered
        setTimeout(() => {
            const selectedText = getSafeSelectedText();
            if (selectedText) {
                if (!askAiButton) {
                    askAiButton = createAskAiButton();
                }
                // Don't position if the click was ON the button itself
                if (event.target !== askAiButton) {
                     positionButton(event);
                }
            } else {
                hideButton();
            }
        }, 10); // Small delay
    });

    // Hide button on scroll or click elsewhere
    document.addEventListener('mousedown', (event) => {
        // Hide if clicking anywhere EXCEPT the button itself
        if (askAiButton && event.target !== askAiButton) {
            hideButton();
        }
    });
    document.addEventListener('scroll', hideButton, true); // Capture scroll events

    console.log("Selection Ask AI script loaded.");
});