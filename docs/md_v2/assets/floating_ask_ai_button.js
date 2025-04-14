// ==== File: docs/assets/floating_ask_ai_button.js ====

document.addEventListener('DOMContentLoaded', () => {
    const askAiPagePath = '/core/ask-ai/'; // IMPORTANT: Adjust this path if needed!
    const currentPath = window.location.pathname;

    // Determine the base URL for constructing the link correctly,
    // especially if deployed in a sub-directory.
    // This assumes a simple structure; adjust if needed.
    const baseUrl = window.location.origin + (currentPath.startsWith('/core/') ? '../..' : '');


    // Check if the current page IS the Ask AI page
    // Use includes() for flexibility (handles trailing slash or .html)
    if (currentPath.includes(askAiPagePath.replace(/\/$/, ''))) { // Remove trailing slash for includes check
        console.log("Floating Ask AI Button: Not adding button on the Ask AI page itself.");
        return; // Don't add the button on the target page
    }

    // --- Create the button ---
    const fabLink = document.createElement('a');
    fabLink.className = 'floating-ask-ai-button';
    fabLink.href = askAiPagePath; // Construct the correct URL
    fabLink.title = 'Ask Crawl4AI Assistant';
    fabLink.setAttribute('aria-label', 'Ask Crawl4AI Assistant');

    // Add content (using SVG icon for better visuals)
    fabLink.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
        </svg>
        <span>Ask AI</span>
    `;

    // Append to body
    document.body.appendChild(fabLink);

    console.log("Floating Ask AI Button added.");
});