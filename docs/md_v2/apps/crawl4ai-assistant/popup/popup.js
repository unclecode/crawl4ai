// Popup script for Crawl4AI Assistant
let activeMode = null;

document.addEventListener('DOMContentLoaded', () => {
  // Fetch GitHub stars
  fetchGitHubStars();
  
  // Check current state
  chrome.storage.local.get(['captureMode', 'captureStats'], (data) => {
    if (data.captureMode) {
      activeMode = data.captureMode;
      showActiveSession(data.captureStats || {});
    }
  });

  // Mode buttons
  document.getElementById('schema-mode').addEventListener('click', () => {
    startSchemaCapture();
  });

  document.getElementById('script-mode').addEventListener('click', () => {
    startScriptCapture();
  });

  document.getElementById('c2c-mode').addEventListener('click', () => {
    startClick2Crawl();
  });

  // Session actions
  document.getElementById('generate-code').addEventListener('click', () => {
    generateCode();
  });

  document.getElementById('stop-capture').addEventListener('click', () => {
    stopCapture();
  });
});

async function fetchGitHubStars() {
  try {
    const response = await fetch('https://api.github.com/repos/unclecode/crawl4ai');
    const data = await response.json();
    const stars = data.stargazers_count;
    
    // Format the number (e.g., 1.2k)
    let formattedStars;
    if (stars >= 1000) {
      formattedStars = (stars / 1000).toFixed(1) + 'k';
    } else {
      formattedStars = stars.toString();
    }
    
    document.getElementById('stars-count').textContent = `⭐ ${formattedStars}`;
  } catch (error) {
    console.error('Failed to fetch GitHub stars:', error);
    document.getElementById('stars-count').textContent = '⭐ 2k+';
  }
}

function startSchemaCapture() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, {
      action: 'startSchemaCapture'
    }, (response) => {
      if (response && response.success) {
        // Close the popup to let user interact with the page
        window.close();
      }
    });
  });
}

function startScriptCapture() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, {
      action: 'startScriptCapture'
    }, (response) => {
      if (response && response.success) {
        // Close the popup to let user interact with the page
        window.close();
      }
    });
  });
}

function startClick2Crawl() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, {
      action: 'startClick2Crawl'
    }, (response) => {
      if (response && response.success) {
        // Close the popup to let user interact with the page
        window.close();
      }
    });
  });
}

function showActiveSession(stats) {
  document.querySelector('.mode-selector').style.display = 'none';
  document.getElementById('active-session').classList.remove('hidden');
  
  updateSessionStats(stats);
}

function updateSessionStats(stats) {
  document.getElementById('container-status').textContent = 
    stats.container ? 'Selected ✓' : 'Not selected';
  document.getElementById('fields-count').textContent = stats.fields || 0;
  
  // Enable generate button if we have container and fields
  document.getElementById('generate-code').disabled = 
    !stats.container || stats.fields === 0;
}

function generateCode() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, {
      action: 'generateCode'
    });
  });
}

function stopCapture() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, {
      action: 'stopCapture'
    }, () => {
      // Reset UI
      document.querySelector('.mode-selector').style.display = 'flex';
      document.getElementById('active-session').classList.add('hidden');
      activeMode = null;
      
      // Clear storage
      chrome.storage.local.remove(['captureMode', 'captureStats']);
    });
  });
}

// Listen for stats updates from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'updateStats') {
    updateSessionStats(message.stats);
    chrome.storage.local.set({ captureStats: message.stats });
  }
});