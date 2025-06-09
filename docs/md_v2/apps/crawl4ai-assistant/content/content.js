// Main content script for Crawl4AI Assistant
// Coordinates between SchemaBuilder and ScriptBuilder

let activeBuilder = null;

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'startCapture') {
    if (activeBuilder) {
      console.log('Stopping existing capture session');
      activeBuilder.stop();
      activeBuilder = null;
    }

    if (request.mode === 'schema') {
      console.log('Starting Schema Builder');
      activeBuilder = new SchemaBuilder();
      activeBuilder.start();
    } else if (request.mode === 'script') {
      console.log('Starting Script Builder');
      activeBuilder = new ScriptBuilder();
      activeBuilder.start();
    }
    
    sendResponse({ success: true });
  } else if (request.action === 'stopCapture') {
    if (activeBuilder) {
      activeBuilder.stop();
      activeBuilder = null;
    }
    sendResponse({ success: true });
  } else if (request.action === 'startSchemaCapture') {
    if (activeBuilder) {
      activeBuilder.deactivate?.();
      activeBuilder = null;
    }
    console.log('Starting Schema Builder');
    activeBuilder = new SchemaBuilder();
    activeBuilder.start();
    sendResponse({ success: true });
  } else if (request.action === 'startScriptCapture') {
    if (activeBuilder) {
      activeBuilder.deactivate?.();
      activeBuilder = null;
    }
    console.log('Starting Script Builder');
    activeBuilder = new ScriptBuilder();
    activeBuilder.start();
    sendResponse({ success: true });
  } else if (request.action === 'startClick2Crawl') {
    if (activeBuilder) {
      activeBuilder.deactivate?.();
      activeBuilder = null;
    }
    console.log('Starting Click2Crawl');
    activeBuilder = new Click2CrawlBuilder();
    sendResponse({ success: true });
  } else if (request.action === 'generateCode') {
    if (activeBuilder && activeBuilder.generateCode) {
      activeBuilder.generateCode();
    }
    sendResponse({ success: true });
  }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (activeBuilder) {
    if (activeBuilder.deactivate) {
      activeBuilder.deactivate();
    } else if (activeBuilder.stop) {
      activeBuilder.stop();
    }
    activeBuilder = null;
  }
});

console.log('Crawl4AI Assistant content script loaded');