(async () => {
  const waitForElement = (selector, timeout = 10000) => new Promise((resolve, reject) => {
    const el = document.querySelector(selector);
    if (el) return resolve(el);
    const observer = new MutationObserver(() => {
      const el = document.querySelector(selector);
      if (el) {
        observer.disconnect();
        resolve(el);
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => {
      observer.disconnect();
      reject(new Error(`Timeout waiting for ${selector}`));
    }, timeout);
  });

  try {
    const searchInput = await waitForElement('#adv_code_search input[type="text"]');
    searchInput.value = 'crawl4AI';
    searchInput.dispatchEvent(new Event('input', { bubbles: true }));

    const languageSelect = await waitForElement('#search_language');
    languageSelect.value = 'Python';
    languageSelect.dispatchEvent(new Event('change', { bubbles: true }));

    const starsInput = await waitForElement('#search_stars');
    starsInput.value = '>10000';
    starsInput.dispatchEvent(new Event('input', { bubbles: true }));

    const searchButton = await waitForElement('#adv_code_search button[type="submit"]');
    searchButton.click();

    await waitForElement('.codesearch-results, #search-results');
  } catch (e) {
    console.error('Search script failed:', e.message);
  }
})();