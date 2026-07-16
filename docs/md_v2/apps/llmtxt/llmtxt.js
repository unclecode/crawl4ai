// Crawl4AI LLM Context Builder JavaScript

// Component definitions - order matters
const components = [
    {
        id: 'installation',
        name: 'Installation',
        description: 'Setup and installation options'
    },
    {
        id: 'simple_crawling',
        name: 'Simple Crawling',
        description: 'Basic web crawling operations'
    },
    {
        id: 'config_objects',
        name: 'Configuration Objects',
        description: 'Browser and crawler configuration'
    },
    {
        id: 'extraction-llm',
        name: 'Data Extraction Using LLM',
        description: 'Structured data extraction strategies using LLMs'
    },
    {
        id: 'extraction-no-llm',
        name: 'Data Extraction Without LLM',
        description: 'Structured data extraction strategies without LLMs'
    },
    {
        id: 'multi_urls_crawling',
        name: 'Multi URLs Crawling',
        description: 'Crawling multiple URLs efficiently'
    },
    {
        id: 'deep_crawling',
        name: 'Deep Crawling',
        description: 'Multi-page crawling strategies'
    },
    {
        id: 'docker',
        name: 'Docker',
        description: 'Docker deployment and configuration'
    },
    {
        id: 'cli',
        name: 'CLI',
        description: 'Command-line interface usage'
    },
    {
        id: 'http_based_crawler_strategy',
        name: 'HTTP-based Crawler',
        description: 'HTTP crawler strategy implementation'
    },
    {
        id: 'url_seeder',
        name: 'URL Seeder',
        description: 'URL seeding and discovery'
    },
    {
        id: 'deep_crawl_advanced_filters_scorers',
        name: 'Advanced Filters & Scorers',
        description: 'Deep crawl filtering and scoring'
    }
];

// Context types
const contextTypes = ['memory', 'reasoning', 'examples'];

// State management
const state = {
    selectedComponents: new Set(),
    selectedContextTypes: new Map(),
    tokenCounts: new Map() // Store token counts for each file
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    renderComponents();
    renderReferenceTable();
    setupActionHandlers();
    setupColumnHeaderHandlers();
    
    // Initialize first component as selected with available context types
    const firstComponent = components[0];
    state.selectedComponents.add(firstComponent.id);
    state.selectedContextTypes.set(firstComponent.id, new Set(['memory', 'reasoning']));
    updateComponentUI();
});

// Helper function to count tokens (words × 2.5)
function estimateTokens(text) {
    if (!text) return 0;
    const words = text.trim().split(/\s+/).length;
    return Math.round(words * 2.5);
}

// Update total token count display
function updateTotalTokenCount() {
    let totalTokens = 0;
    
    state.selectedComponents.forEach(compId => {
        const types = state.selectedContextTypes.get(compId);
        if (types) {
            types.forEach(type => {
                const key = `${compId}-${type}`;
                totalTokens += state.tokenCounts.get(key) || 0;
            });
        }
    });
    
    document.getElementById('total-tokens').textContent = totalTokens.toLocaleString();
}

// Render component selection table
function renderComponents() {
    const tbody = document.getElementById('components-tbody');
    tbody.innerHTML = '';
    
    components.forEach(component => {
        const row = createComponentRow(component);
        tbody.appendChild(row);
    });
    
    // Fetch token counts for all files
    fetchAllTokenCounts();
}

// Create a component table row
function createComponentRow(component) {
    const tr = document.createElement('tr');
    tr.id = `component-${component.id}`;
    
    // Component checkbox cell
    const checkboxCell = document.createElement('td');
    checkboxCell.innerHTML = `
        <input type="checkbox" id="check-${component.id}" 
               data-component="${component.id}">
    `;
    tr.appendChild(checkboxCell);
    
    // Component name cell
    const nameCell = document.createElement('td');
    nameCell.innerHTML = `<span class="component-name">${component.name}</span>`;
    tr.appendChild(nameCell);
    
    // Context type cells
    contextTypes.forEach(type => {
        const td = document.createElement('td');
        const key = `${component.id}-${type}`;
        const tokenCount = state.tokenCounts.get(key) || 0;
        const isDisabled = type === 'examples' ? 'disabled' : '';
        
        td.innerHTML = `
            <input type="checkbox" id="check-${component.id}-${type}" 
                   data-component="${component.id}" data-type="${type}"
                   ${isDisabled}>
            <span class="token-info" id="tokens-${component.id}-${type}">
                ${tokenCount > 0 ? `${tokenCount.toLocaleString()} tokens` : ''}
            </span>
        `;
        tr.appendChild(td);
    });
    
    // Add event listeners
    const mainCheckbox = tr.querySelector(`#check-${component.id}`);
    mainCheckbox.addEventListener('change', (e) => {
        handleComponentToggle(component.id, e.target.checked);
    });
    
    // Add event listeners for context type checkboxes
    contextTypes.forEach(type => {
        const typeCheckbox = tr.querySelector(`#check-${component.id}-${type}`);
        if (!typeCheckbox.disabled) {
            typeCheckbox.addEventListener('change', (e) => {
                handleContextTypeToggle(component.id, type, e.target.checked);
            });
        }
    });
    
    return tr;
}

// Handle component checkbox toggle
function handleComponentToggle(componentId, checked) {
    if (checked) {
        state.selectedComponents.add(componentId);
        // Select only available context types when component is selected
        if (!state.selectedContextTypes.has(componentId)) {
            state.selectedContextTypes.set(componentId, new Set(['memory', 'reasoning']));
        } else {
            // If component was already partially selected, select all available
            state.selectedContextTypes.set(componentId, new Set(['memory', 'reasoning']));
        }
    } else {
        state.selectedComponents.delete(componentId);
        state.selectedContextTypes.delete(componentId);
    }
    updateComponentUI();
}

// Handle component selection based on context types
function updateComponentSelection(componentId) {
    const types = state.selectedContextTypes.get(componentId) || new Set();
    if (types.size > 0) {
        state.selectedComponents.add(componentId);
    } else {
        state.selectedComponents.delete(componentId);
    }
}

// Handle context type checkbox toggle
function handleContextTypeToggle(componentId, type, checked) {
    if (!state.selectedContextTypes.has(componentId)) {
        state.selectedContextTypes.set(componentId, new Set());
    }
    
    const types = state.selectedContextTypes.get(componentId);
    if (checked) {
        types.add(type);
    } else {
        types.delete(type);
    }
    
    updateComponentSelection(componentId);
    updateComponentUI();
}

// Update UI to reflect current state
function updateComponentUI() {
    components.forEach(component => {
        const row = document.getElementById(`component-${component.id}`);
        if (!row) return;
        
        const mainCheckbox = row.querySelector(`#check-${component.id}`);
        const hasSelection = state.selectedComponents.has(component.id);
        const selectedTypes = state.selectedContextTypes.get(component.id) || new Set();
        
        // Update main checkbox
        mainCheckbox.checked = hasSelection;
        
        // Update row disabled state
        row.classList.toggle('disabled', !hasSelection);
        
        // Update context type checkboxes
        contextTypes.forEach(type => {
            const typeCheckbox = row.querySelector(`#check-${component.id}-${type}`);
            typeCheckbox.checked = selectedTypes.has(type);
        });
    });
    
    updateTotalTokenCount();
}

// Fetch token counts for all files
async function fetchAllTokenCounts() {
    const promises = [];
    
    components.forEach(component => {
        contextTypes.forEach(type => {
            promises.push(fetchTokenCount(component.id, type));
        });
    });
    
    await Promise.all(promises);
    updateComponentUI();
    renderReferenceTable(); // Update reference table with token counts
}

// Fetch token count for a specific file
async function fetchTokenCount(componentId, type) {
    const key = `${componentId}-${type}`;
    
    try {
        const fileName = getFileName(componentId, type);
        const baseUrl = getBaseUrl(type);
        const response = await fetch(baseUrl + fileName);
        
        if (response.ok) {
            const content = await response.text();
            const tokens = estimateTokens(content);
            state.tokenCounts.set(key, tokens);
            
            // Update UI
            const tokenSpan = document.getElementById(`tokens-${componentId}-${type}`);
            if (tokenSpan) {
                tokenSpan.textContent = `${tokens.toLocaleString()} tokens`;
            }
        } else if (type === 'examples') {
            // Examples might not exist yet
            state.tokenCounts.set(key, 0);
            const tokenSpan = document.getElementById(`tokens-${componentId}-${type}`);
            if (tokenSpan) {
                tokenSpan.textContent = '';
            }
        }
    } catch (error) {
        console.warn(`Failed to fetch token count for ${componentId}-${type}`);
        if (type === 'examples') {
            const tokenSpan = document.getElementById(`tokens-${componentId}-${type}`);
            if (tokenSpan) {
                tokenSpan.textContent = '';
            }
        }
    }
}

// Get file name based on component and type
function getFileName(componentId, type) {
    // For new structure, all files are just [componentId].txt
    return `${componentId}.txt`;
}

// Get base URL based on context type
function getBaseUrl(type) {
    // For MkDocs, we need to go up to the root level
    const basePrefix = window.location.pathname.includes('/apps/') ? '../../' : '/';
    
    switch(type) {
        case 'memory':
            return basePrefix + 'assets/llm.txt/txt/';
        case 'reasoning':
            return basePrefix + 'assets/llm.txt/diagrams/';
        case 'examples':
            return basePrefix + 'assets/llm.txt/examples/'; // Will return 404 for now
        default:
            return basePrefix + 'assets/llm.txt/txt/';
    }
}

// Setup action button handlers
function setupActionHandlers() {
    // Select/Deselect all buttons
    document.getElementById('select-all').addEventListener('click', () => {
        components.forEach(comp => {
            state.selectedComponents.add(comp.id);
            state.selectedContextTypes.set(comp.id, new Set(['memory', 'reasoning']));
        });
        updateComponentUI();
    });
    
    document.getElementById('deselect-all').addEventListener('click', () => {
        state.selectedComponents.clear();
        state.selectedContextTypes.clear();
        updateComponentUI();
    });
    
    // Download button
    document.getElementById('download-btn').addEventListener('click', handleDownload);
}

// Setup column header click handlers
function setupColumnHeaderHandlers() {
    const headers = document.querySelectorAll('.clickable-header');
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const type = header.getAttribute('data-type');
            toggleColumnSelection(type);
        });
    });
}

// Toggle all checkboxes in a column
function toggleColumnSelection(type) {
    // Don't toggle examples column
    if (type === 'examples') return;
    
    // Check if all are currently selected
    let allSelected = true;
    components.forEach(comp => {
        const types = state.selectedContextTypes.get(comp.id);
        if (!types || !types.has(type)) {
            allSelected = false;
        }
    });
    
    // Toggle all
    components.forEach(comp => {
        if (!state.selectedContextTypes.has(comp.id)) {
            state.selectedContextTypes.set(comp.id, new Set());
        }
        
        const types = state.selectedContextTypes.get(comp.id);
        if (allSelected) {
            types.delete(type);
        } else {
            types.add(type);
        }
        
        updateComponentSelection(comp.id);
    });
    
    updateComponentUI();
}

// Handle download action
async function handleDownload() {
    const statusEl = document.getElementById('status');
    statusEl.textContent = 'Preparing context files...';
    statusEl.className = 'status loading';
    
    try {
        const files = getSelectedFiles();
        if (files.length === 0) {
            throw new Error('No files selected. Please select at least one component or preset.');
        }
        
        statusEl.textContent = `Fetching ${files.length} files...`;
        
        const contents = await fetchFiles(files);
        const combined = combineContents(contents);
        
        downloadFile(combined, 'crawl4ai_custom_context.md');
        
        statusEl.textContent = 'Download complete!';
        statusEl.className = 'status success';
        
        setTimeout(() => {
            statusEl.textContent = '';
            statusEl.className = 'status';
        }, 3000);
        
    } catch (error) {
        statusEl.textContent = `Error: ${error.message}`;
        statusEl.className = 'status error';
    }
}

// Get list of selected files based on current state
function getSelectedFiles() {
    const files = [];
    
    // Build list of selected files with their context info
    state.selectedComponents.forEach(compId => {
        const types = state.selectedContextTypes.get(compId);
        if (types) {
            types.forEach(type => {
                files.push({
                    componentId: compId,
                    type: type,
                    fileName: getFileName(compId, type),
                    baseUrl: getBaseUrl(type)
                });
            });
        }
    });
    
    return files;
}

// Fetch multiple files
async function fetchFiles(fileInfos) {
    const promises = fileInfos.map(async (fileInfo) => {
        try {
            const response = await fetch(fileInfo.baseUrl + fileInfo.fileName);
            if (!response.ok) {
                if (fileInfo.type === 'examples') {
                    return { 
                        fileInfo, 
                        content: `<!-- Examples for ${fileInfo.componentId} coming soon -->\n\nExamples are currently being developed for this component.` 
                    };
                }
                console.warn(`Failed to fetch ${fileInfo.fileName} from ${fileInfo.baseUrl + fileInfo.fileName}`);
                return { fileInfo, content: `<!-- Failed to load ${fileInfo.fileName} -->` };
            }
            const content = await response.text();
            return { fileInfo, content };
        } catch (error) {
            if (fileInfo.type === 'examples') {
                return { 
                    fileInfo, 
                    content: `<!-- Examples for ${fileInfo.componentId} coming soon -->\n\nExamples are currently being developed for this component.` 
                };
            }
            console.warn(`Error fetching ${fileInfo.fileName}:`, error);
            return { fileInfo, content: `<!-- Error loading ${fileInfo.fileName} -->` };
        }
    });
    
    return Promise.all(promises);
}

// Combine file contents with headers
function combineContents(fileContents) {
    // Calculate total tokens
    let totalTokens = 0;
    fileContents.forEach(({ content }) => {
        totalTokens += estimateTokens(content);
    });
    
    const header = `# Crawl4AI Custom LLM Context
Generated on: ${new Date().toISOString()}
Total files: ${fileContents.length}
Estimated tokens: ${totalTokens.toLocaleString()}

---

`;
    
    const sections = fileContents.map(({ fileInfo, content }) => {
        const component = components.find(c => c.id === fileInfo.componentId);
        const componentName = component ? component.name : fileInfo.componentId;
        const contextType = getContextTypeName(fileInfo.type);
        const tokens = estimateTokens(content);
        
        return `## ${componentName} - ${contextType}
Component ID: ${fileInfo.componentId}
Context Type: ${fileInfo.type}
Estimated tokens: ${tokens.toLocaleString()}

${content}

---

`;
    });
    
    return header + sections.join('\n');
}

// Get display name for context type
function getContextTypeName(type) {
    switch(type) {
        case 'memory': return 'Full Content';
        case 'reasoning': return 'Diagrams & Workflows';
        case 'examples': return 'Code Examples';
        default: return type;
    }
}

// Download file to user's computer
function downloadFile(content, fileName) {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Render reference table
function renderReferenceTable() {
    const tbody = document.getElementById('reference-table-body');
    tbody.innerHTML = '';
    
    // Get base path for links
    const basePrefix = window.location.pathname.includes('/apps/') ? '../../' : '/';
    
    components.forEach(component => {
        const row = document.createElement('tr');
        const memoryTokens = state.tokenCounts.get(`${component.id}-memory`) || 0;
        const reasoningTokens = state.tokenCounts.get(`${component.id}-reasoning`) || 0;
        const examplesTokens = state.tokenCounts.get(`${component.id}-examples`) || 0;
        
        row.innerHTML = `
            <td><strong>${component.name}</strong></td>
            <td>
                <a href="${basePrefix}assets/llm.txt/txt/${component.id}.txt" class="file-link" target="_blank">Memory</a>
                ${memoryTokens > 0 ? `<span class="file-size">${memoryTokens.toLocaleString()} tokens</span>` : ''}
            </td>
            <td>
                <a href="${basePrefix}assets/llm.txt/diagrams/${component.id}.txt" class="file-link" target="_blank">Reasoning</a>
                ${reasoningTokens > 0 ? `<span class="file-size">${reasoningTokens.toLocaleString()} tokens</span>` : ''}
            </td>
            <td>
                ${examplesTokens > 0 
                    ? `<a href="${basePrefix}assets/llm.txt/examples/${component.id}.txt" class="file-link" target="_blank">Examples</a>
                       <span class="file-size">${examplesTokens.toLocaleString()} tokens</span>`
                    : '-'
                }
            </td>
            <td>-</td>
        `;
        tbody.appendChild(row);
    });
}

