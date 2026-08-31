// ==== File: assets/github_stats.js ====

document.addEventListener('DOMContentLoaded', async () => {
    // --- Configuration ---
    const targetHeaderSelector = '.terminal .container:first-child'; // Selector for your header container
    const insertBeforeSelector = '.terminal-nav'; // Selector for the element to insert the badge BEFORE (e.g., the main nav)
                                                  // Or set to null to append at the end of the header.

    // --- Find elements ---
    const headerContainer = document.querySelector(targetHeaderSelector);
    if (!headerContainer) {
        console.warn('GitHub Stats: Header container not found with selector:', targetHeaderSelector);
        return;
    }

    const repoLinkElement = headerContainer.querySelector('a[href*="github.com/"]'); // Find the existing GitHub link
    let repoUrl = 'https://github.com/unclecode/crawl4ai';
    // if (repoLinkElement) {
    //     repoUrl = repoLinkElement.href;
    // } else {
    //     // Fallback: Try finding from config (requires template injection - harder)
    //     // Or hardcode if necessary, but reading from the link is better.
    //      console.warn('GitHub Stats: GitHub repo link not found in header.');
    //      // Try to get repo_url from mkdocs config if available globally (less likely)
    //      // repoUrl = window.mkdocs_config?.repo_url; // Requires setting this variable
    //      // if (!repoUrl) return; // Exit if still no URL
    //      return; // Exit for now if link isn't found
    // }


    // --- Extract Repo Owner/Name ---
    let owner = '';
    let repo = '';
    try {
        const url = new URL(repoUrl);
        const pathParts = url.pathname.split('/').filter(part => part.length > 0);
        if (pathParts.length >= 2) {
            owner = pathParts[0];
            repo = pathParts[1];
        }
    } catch (e) {
        console.error('GitHub Stats: Could not parse repository URL:', repoUrl, e);
        return;
    }

    if (!owner || !repo) {
        console.warn('GitHub Stats: Could not extract owner/repo from URL:', repoUrl);
        return;
    }

    // --- Get Version (Attempt to extract from site title) ---
    let version = '';
    const siteTitleElement = headerContainer.querySelector('.terminal-title, .site-title'); // Adjust selector based on theme's title element
    // Example title: "Crawl4AI Documentation (v0.5.x)"
    if (siteTitleElement) {
         const match = siteTitleElement.textContent.match(/\((v?[^)]+)\)/); // Look for text in parentheses starting with 'v' (optional)
         if (match && match[1]) {
             version = match[1].trim();
         }
    }
     if (!version) {
        console.info('GitHub Stats: Could not extract version from title. You might need to adjust the selector or regex.');
        // You could fallback to config.extra.version if injected into JS
        // version = window.mkdocs_config?.extra?.version || 'N/A';
     }


    // --- Fetch GitHub API Data ---
    let stars = '...';
    let forks = '...';
    try {
        const apiUrl = `https://api.github.com/repos/${owner}/${repo}`;
        const response = await fetch(apiUrl);

        if (response.ok) {
            const data = await response.json();
            // Format large numbers (optional)
            stars = data.stargazers_count > 1000 ? `${(data.stargazers_count / 1000).toFixed(1)}k` : data.stargazers_count;
            forks = data.forks_count > 1000 ? `${(data.forks_count / 1000).toFixed(1)}k` : data.forks_count;
        } else {
            console.warn(`GitHub Stats: API request failed with status ${response.status}. Rate limit exceeded?`);
            stars = 'N/A';
            forks = 'N/A';
        }
    } catch (error) {
        console.error('GitHub Stats: Error fetching repository data:', error);
        stars = 'N/A';
        forks = 'N/A';
    }

    // --- Create Badge HTML ---
    const badgeContainer = document.createElement('div');
    badgeContainer.className = 'github-stats-badge';

    // Use innerHTML for simplicity, including potential icons (requires FontAwesome or similar)
    // Ensure your theme loads FontAwesome or add it yourself if you want icons.
    badgeContainer.innerHTML = `
        <a href="${repoUrl}" target="_blank" rel="noopener">
            <!-- Optional Icon (FontAwesome example) -->
            <!-- <i class="fab fa-github"></i> -->
             <span class="repo-name">${owner}/${repo}</span>
             ${version ? `<span class="stat version"><i class="fas fa-tag"></i> ${version}</span>` : ''}
            <span class="stat stars"><i class="fas fa-star"></i> ${stars}</span>
            <span class="stat forks"><i class="fas fa-code-branch"></i> ${forks}</span>
        </a>
    `;

    // --- Inject Badge into Header ---
    const insertBeforeElement = insertBeforeSelector ? headerContainer.querySelector(insertBeforeSelector) : null;
    if (insertBeforeElement) {
        // headerContainer.insertBefore(badgeContainer, insertBeforeElement);
        headerContainer.querySelector(insertBeforeSelector).appendChild(badgeContainer); 
    } else {
        headerContainer.appendChild(badgeContainer); 
    }

     console.info('GitHub Stats: Badge added to header.');

});