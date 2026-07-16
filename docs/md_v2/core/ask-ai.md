<div class="ask-ai-container">
<iframe id="ask-ai-frame" src="../../ask_ai/index.html" width="100%" style="border:none; display: block;" title="Crawl4AI Assistant"></iframe>
</div>

<script>
// Iframe height adjustment
function resizeAskAiIframe() {
  const iframe = document.getElementById('ask-ai-frame');
  if (iframe) {
    const headerHeight = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header-height') || '55');
    // Footer is removed by JS below, so calculate height based on header + small buffer
    const topOffset = headerHeight + 20; // Header + buffer/margin

    const availableHeight = window.innerHeight - topOffset;
    iframe.style.height = Math.max(600, availableHeight) + 'px'; // Min height 600px
  }
}

// Run immediately and on resize/load
resizeAskAiIframe(); // Initial call
let resizeTimer;
window.addEventListener('load', resizeAskAiIframe);
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(resizeAskAiIframe, 150);
});

// Remove Footer & HR from parent page (DOM Ready might be safer)
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => { // Add slight delay just in case elements render slowly
        const footer = window.parent.document.querySelector('footer'); // Target parent document
        if (footer) {
            const hrBeforeFooter = footer.previousElementSibling;
            if (hrBeforeFooter && hrBeforeFooter.tagName === 'HR') {
                hrBeforeFooter.remove();
            }
            footer.remove();
            // Trigger resize again after removing footer
            resizeAskAiIframe();
        } else {
             console.warn("Ask AI Page: Could not find footer in parent document to remove.");
        }
    }, 100); // Shorter delay
});
</script>

<style>
#terminal-mkdocs-main-content {
    padding: 0 !important;
    margin: 0;
    width: 100%;
    height: 100%;
    overflow: hidden; /* Prevent body scrollbars, panels handle scroll */
}

/* Ensure iframe container takes full space */
#terminal-mkdocs-main-content .ask-ai-container {
    /* Remove negative margins if footer removal handles space */
     margin: 0;
    padding: 0;
    max-width: none;
    /* Let the JS set the height */
    /* height: 600px; Initial fallback height */
    overflow: hidden; /* Hide potential overflow before JS resize */
}

/* Hide title/paragraph if they were part of the markdown */
/* Alternatively, just remove them from the .md file directly */
/* #terminal-mkdocs-main-content > h1,
#terminal-mkdocs-main-content > p:first-of-type {
    display: none;
} */

</style>
