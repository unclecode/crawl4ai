// ==== File: docs/assets/copy_code.js ====

document.addEventListener('DOMContentLoaded', () => {
    // Target specifically code blocks within the main content area
    const codeBlocks = document.querySelectorAll('#terminal-mkdocs-main-content pre > code');

    codeBlocks.forEach((codeElement) => {
        const preElement = codeElement.parentElement; // The <pre> tag

        // Ensure the <pre> tag can contain a positioned button
        if (window.getComputedStyle(preElement).position === 'static') {
            preElement.style.position = 'relative';
        }

        // Create the button
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-code-button';
        copyButton.type = 'button';
        copyButton.setAttribute('aria-label', 'Copy code to clipboard');
        copyButton.title = 'Copy code to clipboard';
        copyButton.innerHTML = 'Copy'; // Or use an icon like an SVG or FontAwesome class

        // Append the button to the <pre> element
        preElement.appendChild(copyButton);

        // Add click event listener
        copyButton.addEventListener('click', () => {
            copyCodeToClipboard(codeElement, copyButton);
        });
    });

    async function copyCodeToClipboard(codeElement, button) {
        // Use innerText to get the rendered text content, preserving line breaks
        const textToCopy = codeElement.innerText;

        try {
            await navigator.clipboard.writeText(textToCopy);

            // Visual feedback
            button.innerHTML = 'Copied!';
            button.classList.add('copied');
            button.disabled = true; // Temporarily disable

            // Revert button state after a short delay
            setTimeout(() => {
                button.innerHTML = 'Copy';
                button.classList.remove('copied');
                button.disabled = false;
            }, 2000); // Show "Copied!" for 2 seconds

        } catch (err) {
            console.error('Failed to copy code: ', err);
            // Optional: Provide error feedback on the button
            button.innerHTML = 'Error';
            setTimeout(() => {
                button.innerHTML = 'Copy';
            }, 2000);
        }
    }

    console.log("Copy Code Button script loaded.");
});