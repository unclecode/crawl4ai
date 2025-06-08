// Service worker for Crawl4AI Assistant

// Handle messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'downloadCode' || message.action === 'downloadScript') {
    try {
      // Create a data URL for the Python code
      const dataUrl = 'data:text/plain;charset=utf-8,' + encodeURIComponent(message.code);
      
      // Download the file
      chrome.downloads.download({
        url: dataUrl,
        filename: message.filename || 'crawl4ai_schema.py',
        saveAs: true
      }, (downloadId) => {
        if (chrome.runtime.lastError) {
          console.error('Download failed:', chrome.runtime.lastError);
          sendResponse({ success: false, error: chrome.runtime.lastError.message });
        } else {
          console.log('Download started with ID:', downloadId);
          sendResponse({ success: true, downloadId: downloadId });
        }
      });
    } catch (error) {
      console.error('Error creating download:', error);
      sendResponse({ success: false, error: error.message });
    }
    
    return true; // Keep the message channel open for async response
  }
  
  return false;
});

// Clean up on extension install/update
chrome.runtime.onInstalled.addListener(() => {
  // Clear any stored state
  chrome.storage.local.clear();
});