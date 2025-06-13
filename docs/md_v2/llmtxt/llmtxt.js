// Crawl4AI LLM Context Builder JavaScript

// Component definitions
const components = [
    {
        id: 'all',
        name: 'All Components',
        description: 'All components with all context types',
        special: true
    },
    {
        id: 'core',
        name: 'Core Functionality',
        description: 'Basic crawling and scraping features'
    },
    {
        id: 'config_objects',
        name: 'Configuration Objects',
        description: 'Browser and crawler configuration'
    },
    {
        id: 'deep_crawling',
        name: 'Deep Crawling',
        description: 'Multi-page crawling strategies'
    },
    {
        id: 'deployment',
        name: 'Deployment',
        description: 'Installation and Docker setup'
    },
    {
        id: 'extraction',
        name: 'Data Extraction',
        description: 'Structured data extraction strategies'
    },
    {
        id: 'markdown',
        name: 'Markdown Generation',
        description: 'Content-to-markdown conversion'
    },
    {
        id: 'vibe',
        name: 'Vibe Coding',
        description: 'General-purpose AI context',
        special: false
    }
];

// Context types
const contextTypes = ['memory', 'reasoning', 'examples'];

// State management
const state = {
    preset: 'custom',
    selectedComponents: new Set(),
    selectedContextTypes: new Map()
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    setupPresetHandlers();
    renderComponents();
    renderReferenceTable();
    setupActionHandlers();
    setupColumnHeaderHandlers();
    
    // Initialize only core component as selected with all context types
    state.selectedComponents.add('core');
    state.selectedContextTypes.set('core', new Set(contextTypes));
    updateComponentUI();
});

// Setup preset radio button handlers
function setupPresetHandlers() {
    const presetRadios = document.querySelectorAll('input[name="preset"]');
    presetRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            state.preset = e.target.value;
            updatePresetSelection();
        });
    });
}

// Update UI based on preset selection
function updatePresetSelection() {
    const componentSelector = document.getElementById('component-selector');
    
    if (state.preset === 'custom') {
        componentSelector.style.display = 'block';
    } else {
        componentSelector.style.display = 'none';
    }
}

// Render component selection table
function renderComponents() {
    const tbody = document.getElementById('components-tbody');
    tbody.innerHTML = '';
    
    components.filter(c => !c.special).forEach(component => {
        const row = createComponentRow(component);
        tbody.appendChild(row);
    });
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
        td.innerHTML = `
            <input type="checkbox" id="check-${component.id}-${type}" 
                   data-component="${component.id}" data-type="${type}">
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
        typeCheckbox.addEventListener('change', (e) => {
            handleContextTypeToggle(component.id, type, e.target.checked);
        });
    });
    
    return tr;
}

// Handle component checkbox toggle
function handleComponentToggle(componentId, checked) {
    if (checked) {
        state.selectedComponents.add(componentId);
        // Select all context types when component is selected
        if (!state.selectedContextTypes.has(componentId)) {
            state.selectedContextTypes.set(componentId, new Set(contextTypes));
        } else {
            // If component was already partially selected, select all
            state.selectedContextTypes.set(componentId, new Set(contextTypes));
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
    components.filter(c => !c.special).forEach(component => {
        const row = document.getElementById(`component-${component.id}`);
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
}

// Setup action button handlers
function setupActionHandlers() {
    // Select/Deselect all buttons
    document.getElementById('select-all').addEventListener('click', () => {
        components.filter(c => !c.special).forEach(comp => {
            state.selectedComponents.add(comp.id);
            state.selectedContextTypes.set(comp.id, new Set(contextTypes));
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
    // Check if all are currently selected
    let allSelected = true;
    components.filter(c => !c.special).forEach(comp => {
        const types = state.selectedContextTypes.get(comp.id);
        if (!types || !types.has(type)) {
            allSelected = false;
        }
    });
    
    // Toggle all
    components.filter(c => !c.special).forEach(comp => {
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
    
    if (state.preset === 'vibe') {
        files.push('crawl4ai_vibe.llm.full.md');
    } else if (state.preset === 'all') {
        // Use the dedicated aggregated files for all components
        files.push('crawl4ai_all_memory_content.llm.md');
        files.push('crawl4ai_all_reasoning_content.llm.md');
        files.push('crawl4ai_all_examples_content.llm.md');
    } else {
        // Custom selection
        state.selectedComponents.forEach(compId => {
            const types = state.selectedContextTypes.get(compId);
            if (types) {
                types.forEach(type => {
                    files.push(`crawl4ai_${compId}_${type}_content.llm.md`);
                });
            }
        });
    }
    
    return files;
}

// Fetch multiple files
async function fetchFiles(fileNames) {
    // Use /assets/llmtxt/ path with .txt extension
    const baseUrl = '/assets/llmtxt/';
    const promises = fileNames.map(async (fileName) => {
        // Convert .md to .txt for fetching
        const txtFileName = fileName.replace('.md', '.txt');
        try {
            const response = await fetch(baseUrl + txtFileName);
            if (!response.ok) {
                console.warn(`Failed to fetch ${txtFileName} from ${baseUrl + txtFileName}`);
                return { fileName, content: `<!-- Failed to load ${fileName} -->` };
            }
            const content = await response.text();
            return { fileName, content };
        } catch (error) {
            console.warn(`Error fetching ${txtFileName} from ${baseUrl + txtFileName}:`, error);
            return { fileName, content: `<!-- Error loading ${fileName} -->` };
        }
    });
    
    return Promise.all(promises);
}

// Combine file contents with headers
function combineContents(fileContents) {
    const header = `# Crawl4AI Custom LLM Context
Generated on: ${new Date().toISOString()}
Total files: ${fileContents.length}

---

`;
    
    const sections = fileContents.map(({ fileName, content }) => {
        const componentName = extractComponentName(fileName);
        const contextType = extractContextType(fileName);
        
        return `## ${componentName} - ${contextType}
Source: ${fileName}

${content}

---

`;
    });
    
    return header + sections.join('\n');
}

// Extract component name from filename
function extractComponentName(fileName) {
    // Pattern: crawl4ai_{component}_{type}_content.llm.md
    const match = fileName.match(/crawl4ai_(.+?)_(memory|reasoning|examples|llm\.full)/);
    if (match) {
        const compId = match[1];
        const component = components.find(c => c.id === compId);
        return component ? component.name : compId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    return 'Unknown Component';
}

// Extract context type from filename
function extractContextType(fileName) {
    if (fileName.includes('_memory_')) return 'Memory';
    if (fileName.includes('_reasoning_')) return 'Reasoning';
    if (fileName.includes('_examples_')) return 'Examples';
    if (fileName.includes('.llm.full')) return 'Complete Context';
    return 'Context';
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
    
    // Since vibe is no longer special, just show all components the same way
    components.forEach(component => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${component.name}</strong></td>
            <td><a href="/assets/llmtxt/crawl4ai_${component.id}_memory_content.llm.txt" class="file-link" target="_blank">Memory</a></td>
            <td><a href="/assets/llmtxt/crawl4ai_${component.id}_reasoning_content.llm.txt" class="file-link" target="_blank">Reasoning</a></td>
            <td><a href="/assets/llmtxt/crawl4ai_${component.id}_examples_content.llm.txt" class="file-link" target="_blank">Examples</a></td>
            <td><a href="/assets/llmtxt/crawl4ai_${component.id}.llm.full.txt" class="file-link" target="_blank">Full</a></td>
        `;
        tbody.appendChild(row);
    });
}

// Check if examples file exists (all components have examples)
function hasExamplesFile(componentId) {
    // All components have examples files
    return true;
}

// Check if full file exists (all components have full files)
function hasFullFile(componentId) {
    // All components have full files
    return true;
}

// Utility function to capitalize first letter
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}