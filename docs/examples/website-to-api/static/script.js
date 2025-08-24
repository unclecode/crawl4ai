// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const navLinks = document.querySelectorAll('.nav-link');
const pages = document.querySelectorAll('.page');
const scrapeForm = document.getElementById('scrape-form');
const modelForm = document.getElementById('model-form');
const modelSelect = document.getElementById('model-select');
const modelsList = document.getElementById('models-list');
const resultsSection = document.getElementById('results-section');
const loadingSection = document.getElementById('loading');
const copyJsonBtn = document.getElementById('copy-json');

// Navigation
navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetPage = link.dataset.page;
        
        // Update active nav link
        navLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        
        // Show target page
        pages.forEach(page => page.classList.remove('active'));
        document.getElementById(`${targetPage}-page`).classList.add('active');
        
        // Load data for the page
        if (targetPage === 'models') {
            loadModels();
        } else if (targetPage === 'requests') {
            loadSavedRequests();
        }
    });
});

// Scrape Form Handler
document.getElementById('extract-btn').addEventListener('click', async (e) => {
    e.preventDefault();
    
    // Scroll to results section immediately when button is clicked
    document.getElementById('results-section').scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
    });
    
    const url = document.getElementById('url').value;
    const query = document.getElementById('query').value;
    const headless = true; // Always use headless mode
    const model_name = document.getElementById('model-select').value || null;
    const scraping_approach = document.getElementById('scraping-approach').value;
    
    if (!url || !query) {
        showToast('Please fill in both URL and query fields', 'error');
        return;
    }
    
    if (!model_name) {
        showToast('Please select a model from the dropdown or add one from the Models page', 'error');
        return;
    }
    
    const data = {
        url: url,
        query: query,
        headless: headless,
        model_name: model_name
    };
    
    // Show loading state
    showLoading(true);
    hideResults();
    
    try {
        // Choose endpoint based on scraping approach
        const endpoint = scraping_approach === 'llm' ? '/scrape-with-llm' : '/scrape';
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displayResults(result);
            showToast(`Data extracted successfully using ${scraping_approach === 'llm' ? 'LLM-based' : 'Schema-based'} approach!`, 'success');
        } else {
            throw new Error(result.detail || 'Failed to extract data');
        }
    } catch (error) {
        console.error('Scraping error:', error);
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
});

// Model Form Handler
modelForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(modelForm);
    const data = {
        model_name: formData.get('model_name'),
        provider: formData.get('provider'),
        api_token: formData.get('api_token')
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/models`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Model saved successfully!', 'success');
            modelForm.reset();
            loadModels();
            loadModelSelect();
        } else {
            throw new Error(result.detail || 'Failed to save model');
        }
    } catch (error) {
        console.error('Model save error:', error);
        showToast(`Error: ${error.message}`, 'error');
    }
});

// Copy JSON Button
copyJsonBtn.addEventListener('click', () => {
    const actualJsonOutput = document.getElementById('actual-json-output');
    const textToCopy = actualJsonOutput.textContent;
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        showToast('JSON copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy JSON', 'error');
    });
});

// Load Models
async function loadModels() {
    try {
        const response = await fetch(`${API_BASE_URL}/models`);
        const result = await response.json();
        
        if (response.ok) {
            displayModels(result.models);
        } else {
            throw new Error(result.detail || 'Failed to load models');
        }
    } catch (error) {
        console.error('Load models error:', error);
        showToast(`Error: ${error.message}`, 'error');
    }
}

// Display Models
function displayModels(models) {
    if (models.length === 0) {
        modelsList.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 2rem;">No models saved yet. Add your first model above!</p>';
        return;
    }
    
    modelsList.innerHTML = models.map(model => `
        <div class="model-card">
            <div class="model-info">
                <div class="model-name">${model}</div>
                <div class="model-provider">Model Configuration</div>
            </div>
            <div class="model-actions">
                <button class="btn btn-danger" onclick="deleteModel('${model}')">
                    <i class="fas fa-trash"></i>
                    Delete
                </button>
            </div>
        </div>
    `).join('');
}

// Delete Model
async function deleteModel(modelName) {
    if (!confirm(`Are you sure you want to delete the model "${modelName}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/models/${modelName}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Model deleted successfully!', 'success');
            loadModels();
            loadModelSelect();
        } else {
            throw new Error(result.detail || 'Failed to delete model');
        }
    } catch (error) {
        console.error('Delete model error:', error);
        showToast(`Error: ${error.message}`, 'error');
    }
}

// Load Model Select Options
async function loadModelSelect() {
    try {
        const response = await fetch(`${API_BASE_URL}/models`);
        const result = await response.json();
        
        if (response.ok) {
            // Clear existing options
            modelSelect.innerHTML = '<option value="">Select a Model</option>';
            
            // Add model options
            result.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Load model select error:', error);
    }
}

// Display Results
function displayResults(result) {
    // Update result info
    document.getElementById('result-url').textContent = result.url;
    document.getElementById('result-query').textContent = result.query;
    document.getElementById('result-model').textContent = result.model_name || 'Default Model';
    
    // Display JSON in the actual results section
    const actualJsonOutput = document.getElementById('actual-json-output');
    actualJsonOutput.textContent = JSON.stringify(result.extracted_data, null, 2);
    
    // Don't update the sample JSON in the workflow demo - keep it as example
    
    // Update the cURL example based on the approach used
    const scraping_approach = document.getElementById('scraping-approach').value;
    const endpoint = scraping_approach === 'llm' ? '/scrape-with-llm' : '/scrape';
    const curlExample = document.getElementById('curl-example');
    curlExample.textContent = `curl -X POST http://localhost:8000${endpoint} -H "Content-Type: application/json" -d '{"url": "${result.url}", "query": "${result.query}"}'`;
    
    // Show results section
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Show/Hide Loading
function showLoading(show) {
    loadingSection.style.display = show ? 'block' : 'none';
}

// Hide Results
function hideResults() {
    resultsSection.style.display = 'none';
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'fas fa-check-circle' : 
                 type === 'error' ? 'fas fa-exclamation-circle' : 
                 'fas fa-info-circle';
    
    toast.innerHTML = `
        <i class="${icon}"></i>
        <span>${message}</span>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Load Saved Requests
async function loadSavedRequests() {
    try {
        const response = await fetch(`${API_BASE_URL}/saved-requests`);
        const result = await response.json();
        
        if (response.ok) {
            displaySavedRequests(result.requests);
        } else {
            throw new Error(result.detail || 'Failed to load saved requests');
        }
    } catch (error) {
        console.error('Load saved requests error:', error);
        showToast(`Error: ${error.message}`, 'error');
    }
}

// Display Saved Requests
function displaySavedRequests(requests) {
    const requestsList = document.getElementById('requests-list');
    
    if (requests.length === 0) {
        requestsList.innerHTML = '<p style="text-align: center; color: #CCCCCC; padding: 2rem;">No saved API requests yet. Make your first request from the Scrape page!</p>';
        return;
    }
    
    requestsList.innerHTML = requests.map(request => {
        const url = request.body.url;
        const query = request.body.query;
        const model = request.body.model_name || 'Default Model';
        const endpoint = request.endpoint;
        
        // Create curl command
        const curlCommand = `curl -X POST http://localhost:8000${endpoint} \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "${url}",
    "query": "${query}",
    "model_name": "${model}"
  }'`;
        
        return `
            <div class="request-card">
                <div class="request-header">
                    <div class="request-info">
                        <div class="request-url">${url}</div>
                        <div class="request-query">${query}</div>
                    </div>
                    <div class="request-actions">
                        <button class="btn-danger" onclick="deleteSavedRequest('${request.id}')">
                            <i class="fas fa-trash"></i>
                            Delete
                        </button>
                    </div>
                </div>
                
                <div class="request-curl">
                    <h4>cURL Command:</h4>
                    <pre>${curlCommand}</pre>
                </div>
            </div>
        `;
    }).join('');
}

// Delete Saved Request
async function deleteSavedRequest(requestId) {
    if (!confirm('Are you sure you want to delete this saved request?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/saved-requests/${requestId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Saved request deleted successfully!', 'success');
            loadSavedRequests();
        } else {
            throw new Error(result.detail || 'Failed to delete saved request');
        }
    } catch (error) {
        console.error('Delete saved request error:', error);
        showToast(`Error: ${error.message}`, 'error');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadModelSelect();
    
    // Check if API is available
    fetch(`${API_BASE_URL}/health`)
        .then(response => {
            if (!response.ok) {
                showToast('Warning: API server might not be running', 'error');
            }
        })
        .catch(() => {
            showToast('Warning: Cannot connect to API server. Make sure it\'s running on localhost:8000', 'error');
        });
}); 