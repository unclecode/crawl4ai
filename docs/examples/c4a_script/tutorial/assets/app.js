// C4A-Script Tutorial App Controller
class TutorialApp {
    constructor() {
        this.editor = null;
        this.currentScript = '';
        this.currentJS = [];
        this.isEditingJS = false;
        this.tutorialMode = false;
        this.currentStep = 0;
        this.tutorialSteps = [];
        this.recordingManager = null;
        this.blocklyManager = null;
        
        this.init();
    }

    init() {
        this.setupEditors();
        this.setupButtons();
        this.setupTabs();
        this.setupTutorial();
        this.checkFirstVisit();
        
        // Initialize recording manager
        this.recordingManager = new RecordingManager(this);
        
        // Initialize Blockly manager
        this.blocklyManager = new BlocklyManager(this);
    }

    setupEditors() {
        // C4A Script Editor
        const c4aTextarea = document.getElementById('c4a-editor');
        this.editor = CodeMirror.fromTextArea(c4aTextarea, {
            mode: 'javascript', // Use JS mode for now
            theme: 'material-darker',
            lineNumbers: true,
            lineWrapping: true,
            autoCloseBrackets: true,
            matchBrackets: true,
            readOnly: false,
            cursorBlinkRate: 530,
            inputStyle: 'contenteditable' // Changed from 'textarea' to prevent cursor issues
        });

        // Save script on change
        this.editor.on('change', () => {
            this.currentScript = this.editor.getValue();
            localStorage.setItem('c4a-script', this.currentScript);
        });

        // Load saved script
        const saved = localStorage.getItem('c4a-script');
        if (saved && !this.tutorialMode) {
            this.editor.setValue(saved);
        }
        
        // Ensure editor is properly sized and interactive
        setTimeout(() => {
            this.editor.refresh();
            // Set cursor position instead of just focusing
            const doc = this.editor.getDoc();
            doc.setCursor(doc.lineCount() - 1, 0);
            this.editor.focus();
        }, 100);
        
        // Single unified click handler for focus
        const editorElement = this.editor.getWrapperElement();
        editorElement.addEventListener('mousedown', (e) => {
            // Use mousedown instead of click for immediate response
            e.stopPropagation();
            // Ensure editor gets focus on next tick
            setTimeout(() => {
                if (!this.editor.hasFocus()) {
                    this.editor.focus();
                }
            }, 0);
        });
    }

    setupButtons() {
        // Run button
        document.getElementById('run-btn').addEventListener('click', () => {
            this.runScript();
        });

        // Clear button
        document.getElementById('clear-btn').addEventListener('click', () => {
            this.editor.setValue('');
            this.clearConsole();
        });

        // Examples button
        document.getElementById('examples-btn').addEventListener('click', () => {
            this.showExamples();
        });

        // Tutorial button
        document.getElementById('tutorial-btn').addEventListener('click', () => {
            this.showIntroModal();
        });

        // Copy JS button
        document.getElementById('copy-js-btn').addEventListener('click', () => {
            this.copyJS();
        });

        // Edit JS button
        document.getElementById('edit-js-btn').addEventListener('click', () => {
            this.toggleJSEdit();
        });

        // Reset playground
        document.getElementById('reset-playground').addEventListener('click', () => {
            this.resetPlayground();
        });

        // Fullscreen
        document.getElementById('fullscreen-btn').addEventListener('click', () => {
            this.toggleFullscreen();
        });

        // Intro modal buttons
        document.getElementById('start-tutorial-btn').addEventListener('click', () => {
            this.hideIntroModal();
            this.startTutorial();
        });

        document.getElementById('skip-tutorial-btn').addEventListener('click', () => {
            this.hideIntroModal();
        });

        // Tutorial navigation
        document.getElementById('tutorial-prev').addEventListener('click', () => {
            this.prevStep();
        });

        document.getElementById('tutorial-next').addEventListener('click', () => {
            this.nextStep();
        });

        document.getElementById('tutorial-exit').addEventListener('click', () => {
            this.exitTutorial();
        });
    }

    setupTabs() {
        const tabs = document.querySelectorAll('.tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const tabName = tab.getAttribute('data-tab');
                this.switchTab(tabName);
            });
        });
        
        // Remove execution tab since we're removing it
        const progressTab = document.querySelector('[data-tab="progress"]');
        if (progressTab) progressTab.remove();
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update tab panes
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    checkFirstVisit() {
        const hasVisited = localStorage.getItem('c4a-tutorial-visited');
        if (!hasVisited) {
            setTimeout(() => this.showIntroModal(), 500);
        }
    }

    showIntroModal() {
        document.getElementById('tutorial-intro').classList.remove('hidden');
    }

    hideIntroModal() {
        document.getElementById('tutorial-intro').classList.add('hidden');
        localStorage.setItem('c4a-tutorial-visited', 'true');
    }

    setupTutorial() {
        this.tutorialSteps = [
            {
                title: "Welcome to C4A-Script!",
                description: "C4A-Script is a simple language for web automation. Let's start by handling popups that appear on websites.",
                script: "# Welcome to C4A-Script Tutorial!\n# Let's start by waiting for the page to load\n\nWAIT `body` 2",
                validate: () => true
            },
            {
                title: "Handle Cookie Banner",
                description: "Check if cookie banner exists and accept it.",
                script: "# Wait for page and handle cookie banner\nWAIT `body` 2\n\n# Check if cookie banner exists, then click accept\nIF (EXISTS `.cookie-banner`) THEN CLICK `.accept`",
                validate: () => {
                    const iframe = document.getElementById('playground-frame');
                    return !iframe.contentDocument?.querySelector('.cookie-banner');
                }
            },
            {
                title: "Handle Newsletter Popup",
                description: "Now let's handle the newsletter popup that appears after 3 seconds.",
                script: "# Wait for newsletter popup to appear\nWAIT 3\n\n# Close the newsletter popup\nIF (EXISTS `#newsletter-popup`) THEN CLICK `.close`",
                validate: () => {
                    const iframe = document.getElementById('playground-frame');
                    return !iframe.contentDocument?.querySelector('#newsletter-popup');
                }
            },
            {
                title: "Start Interactive Elements",
                description: "Click the start button to reveal more interactive elements.",
                script: "# Click the start tutorial button\nCLICK `#start-tutorial`",
                validate: () => true
            },
            {
                title: "Login Process",
                description: "Now let's complete the login form with email and password using the new SET command.",
                script: "# Login process\nCLICK `#login-btn`\nWAIT `.login-form` 2\n\n# Fill form fields using SET\nSET `#email` \"demo@example.com\"\nSET `#password` \"demo123\"\n\n# Submit the form\nCLICK `button[type=\"submit\"]`\nWAIT `.success` 2",
                validate: () => {
                    const iframe = document.getElementById('playground-frame');
                    return iframe.contentDocument?.querySelector('.user-info')?.style.display === 'flex';
                }
            },
            {
                title: "Navigate and Scroll",
                description: "Navigate to the catalog and use scrolling to load more products.",
                script: "# Navigate to catalog\nCLICK `#catalog-link`\nWAIT `.product-grid` 3\n\n# Scroll to load more products\nSCROLL DOWN 500\nWAIT 1\nSCROLL DOWN 500\nWAIT 1\n\n# Apply a filter\nCLICK `.filter-group input[type=\"checkbox\"]`",
                validate: () => true
            },
            {
                title: "Advanced - Procedures",
                description: "Create reusable command groups with PROC for common tasks.",
                script: "# Define a procedure to check login status\nPROC check_login\n  IF (NOT EXISTS `.user-info`) THEN CLICK `#login-btn`\n  IF (NOT EXISTS `.user-info`) THEN WAIT `.login-form` 2\n  IF (NOT EXISTS `.user-info`) THEN SET `#email` \"demo@example.com\"\n  IF (NOT EXISTS `.user-info`) THEN SET `#password` \"demo123\"\n  IF (NOT EXISTS `.user-info`) THEN CLICK `button[type=\"submit\"]`\nENDPROC\n\n# Example: Navigate between sections\nCLICK `a[href=\"#tabs\"]`\nWAIT 1\nCLICK `a[href=\"#forms\"]`\nWAIT 1\n\n# If we get logged out, use our procedure\ncheck_login",
                validate: () => true
            },
            {
                title: "More Commands",
                description: "Explore additional C4A commands with the Forms section.",
                script: "# First, let's fill the contact form with variables\n\n# Set variables\nSETVAR name = \"Alice Smith\"\nSETVAR msg = \"I'd like to know more about your Premium plan!\"\n\n# Fill contact form\nSET `#contact-name` $name\nSET `#contact-email` \"alice@example.com\"\nSET `#contact-message` $msg\n\n# Select dropdown option\nCLICK `#contact-subject`\nCLICK `option[value=\"support\"]`\nWAIT 0.5\n\n# Submit contact form\nCLICK `.btn-primary`\nWAIT 1\n\n# Now let's do the multi-step survey\nSCROLL DOWN 400\nWAIT 0.5\n\n# Step 1: Personal info\nSET `#full-name` \"Bob Johnson\"\nSET `#survey-email` \"bob@example.com\"\nCLICK `.next-step`\nWAIT 0.5\n\n# Step 2: Select interests (multi-select)\nCLICK `#interests`\nCLICK `option[value=\"technology\"]`\nCLICK `option[value=\"science\"]`\nCLICK `.next-step`\nWAIT 0.5\n\n# Step 3: Submit survey\nCLICK `#submit-survey`\n\n# Check results with JavaScript\nEVAL `console.log('Forms completed successfully!')`",
                validate: () => true
            },
            {
                title: "Congratulations!",
                description: "You've mastered C4A-Script basics! You can now automate complex web interactions. Try the examples or create your own scripts.",
                script: "# 🎉 You've completed the tutorial!\n\n# You learned:\n# ✓ WAIT - Wait for elements or time\n# ✓ IF/THEN - Conditional actions\n# ✓ NOT - Negate conditions\n# ✓ CLICK - Click elements\n# ✓ SET - Set input field values\n# ✓ SETVAR - Create variables\n# ✓ SCROLL - Scroll the page\n# ✓ PROC - Create procedures\n# ✓ And much more!\n\n# Try the Examples button for more scripts\n# Happy automating with C4A-Script!",
                validate: () => true
            }
        ];
    }

    startTutorial() {
        this.tutorialMode = true;
        this.currentStep = 0;
        document.getElementById('tutorial-nav').classList.remove('hidden');
        document.querySelector('.app-container').classList.add('tutorial-active');
        this.showStep(0);
    }

    exitTutorial() {
        this.tutorialMode = false;
        document.getElementById('tutorial-nav').classList.add('hidden');
        document.querySelector('.app-container').classList.remove('tutorial-active');
    }

    showStep(index) {
        const step = this.tutorialSteps[index];
        if (!step) return;

        // Update navigation UI
        document.getElementById('tutorial-step-info').textContent = `Step ${index + 1} of ${this.tutorialSteps.length}`;
        document.getElementById('tutorial-title').textContent = step.title;
        
        // Update progress bar
        const progress = ((index + 1) / this.tutorialSteps.length) * 100;
        document.getElementById('tutorial-progress-fill').style.width = `${progress}%`;

        // Update buttons
        document.getElementById('tutorial-prev').disabled = index === 0;
        const nextBtn = document.getElementById('tutorial-next');
        if (index === this.tutorialSteps.length - 1) {
            nextBtn.textContent = 'Finish';
        } else {
            nextBtn.textContent = 'Next →';
        }

        // Set script
        this.editor.setValue(step.script);
        
        // Update description in nav bar
        document.getElementById('tutorial-description').textContent = step.description;
        
        // Focus editor after setting content and ensure it's editable
        // Use requestAnimationFrame for better timing
        requestAnimationFrame(() => {
            this.editor.setOption('readOnly', false);
            this.editor.refresh();
            // Place cursor at end first, then focus
            const doc = this.editor.getDoc();
            const lastLine = doc.lineCount() - 1;
            const lastCh = doc.getLine(lastLine).length;
            doc.setCursor(lastLine, lastCh);
            this.editor.focus();
        });
    }

    // Removed showTooltip method - no longer needed

    nextStep() {
        if (this.currentStep < this.tutorialSteps.length - 1) {
            this.currentStep++;
            this.showStep(this.currentStep);
        } else {
            this.exitTutorial();
        }
    }

    prevStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep(this.currentStep);
        }
    }

    async runScript() {
        const script = this.editor.getValue();
        if (!script.trim()) {
            this.addConsoleMessage('No script to run', 'error');
            return;
        }

        this.clearConsole();
        this.switchTab('console');
        this.addConsoleMessage('Compiling C4A script...');

        try {
            // If in JS edit mode, use the edited JS directly
            if (this.isEditingJS) {
                const jsCode = document.getElementById('js-output').textContent.split('\n').filter(line => line.trim());
                await this.executeJS(jsCode);
                return;
            }

            // Compile C4A to JS
            const compiled = await this.compileScript(script);
            
            if (compiled.success) {
                this.currentJS = compiled.jsCode;
                this.displayJS(compiled.jsCode);
                this.addConsoleMessage(`✓ Compiled successfully (${compiled.jsCode.length} statements)`, 'success');
                
                // Execute the JS
                await this.executeJS(compiled.jsCode);
            } else {
                // Show compilation error
                const error = compiled.error;
                this.addConsoleMessage(`✗ Compilation error at line ${error.line}:${error.column}`, 'error');
                this.addConsoleMessage(`  ${error.message}`, 'error');
                if (error.suggestion) {
                    this.addConsoleMessage(`  💡 ${error.suggestion}`, 'warning');
                }
            }
        } catch (error) {
            this.addConsoleMessage(`Error: ${error.message}`, 'error');
        }
    }

    async compileScript(script) {
        try {
            const response = await fetch('/api/compile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ script })
            });
            
            if (!response.ok) {
                throw new Error('Compilation service unavailable');
            }
            
            return await response.json();
        } catch (error) {
            // Return error if compilation service is unavailable
            return {
                success: false,
                error: {
                    line: 1,
                    column: 1,
                    message: "C4A compilation service unavailable. Please ensure the server is running.",
                    suggestion: "Start the C4A server or check your connection"
                }
            };
        }
    }

    displayJS(jsCode) {
        const formatted = jsCode.map((line, i) => 
            `${(i + 1).toString().padStart(2, ' ')}. ${line}`
        ).join('\n');
        
        document.getElementById('js-output').textContent = formatted;
    }

    async executeJS(jsCode) {
        this.addConsoleMessage('Executing JavaScript...');
        
        // Send all code to iframe to execute at once
        await this.executeInIframe(jsCode);
    }

    async executeInIframe(jsCode) {
        const iframe = document.getElementById('playground-frame');
        const iframeWindow = iframe.contentWindow;
        
        // Create a unique ID for this execution
        const executionId = 'exec_' + Date.now();
        
        // Create the full script to execute in iframe
        const fullScript = `
            (async () => {
                const results = [];
                try {
                    ${jsCode.map((code, i) => `
                    try {
                        ${code}
                        results.push({ index: ${i}, success: true, code: ${JSON.stringify(code)} });
                    } catch (error) {
                        results.push({ index: ${i}, success: false, error: error.message, code: ${JSON.stringify(code)} });
                        throw error; // Stop execution on first error
                    }
                    `).join('\n')}
                    
                    // Send success message
                    window.parent.postMessage({
                        type: 'c4a-execution-complete',
                        id: '${executionId}',
                        success: true,
                        results: results
                    }, '*');
                } catch (error) {
                    // Send error message
                    window.parent.postMessage({
                        type: 'c4a-execution-complete',
                        id: '${executionId}',
                        success: false,
                        error: error.message,
                        results: results
                    }, '*');
                }
            })();
        `;
        
        // Wait for execution result
        return new Promise((resolve, reject) => {
            const messageHandler = (event) => {
                if (event.data.type === 'c4a-execution-complete' && event.data.id === executionId) {
                    window.removeEventListener('message', messageHandler);
                    
                    // Log results
                    if (event.data.results) {
                        event.data.results.forEach(result => {
                            if (result.success) {
                                this.addConsoleMessage(`✓ ${result.code}`, 'success');
                            } else {
                                this.addConsoleMessage(`✗ ${result.code}`, 'error');
                                this.addConsoleMessage(`  Error: ${result.error}`, 'error');
                            }
                        });
                    }
                    
                    if (event.data.success) {
                        this.addConsoleMessage('Execution completed successfully', 'success');
                        resolve();
                    } else {
                        this.addConsoleMessage('Execution stopped due to error', 'error');
                        resolve(); // Still resolve to not break the flow
                    }
                }
            };
            
            window.addEventListener('message', messageHandler);
            
            // Inject and execute the script
            const script = iframe.contentDocument.createElement('script');
            script.textContent = fullScript;
            iframe.contentDocument.body.appendChild(script);
            script.remove();
            
            // Timeout after 10 seconds
            setTimeout(() => {
                window.removeEventListener('message', messageHandler);
                this.addConsoleMessage('Execution timeout', 'warning');
                resolve();
            }, 10000);
        });
    }

    highlightElement(element) {
        const originalBorder = element.style.border;
        const originalBackground = element.style.backgroundColor;
        
        element.style.border = '2px solid #0fbbaa';
        element.style.backgroundColor = 'rgba(15, 187, 170, 0.1)';
        
        setTimeout(() => {
            element.style.border = originalBorder;
            element.style.backgroundColor = originalBackground;
        }, 1000);
    }

    // Removed progress methods - everything goes to console now

    addConsoleMessage(message, type = 'text') {
        const consoleEl = document.getElementById('console-output');
        const line = document.createElement('div');
        line.className = 'console-line';
        line.innerHTML = `
            <span class="console-prompt">$</span>
            <span class="console-${type}">${message}</span>
        `;
        consoleEl.appendChild(line);
        
        // Scroll the console container (parent of console-output)
        const consoleContainer = consoleEl.parentElement;
        if (consoleContainer) {
            // Use requestAnimationFrame to ensure DOM has updated
            requestAnimationFrame(() => {
                consoleContainer.scrollTop = consoleContainer.scrollHeight;
            });
        }
    }

    clearConsole() {
        document.getElementById('console-output').innerHTML = `
            <div class="console-line">
                <span class="console-prompt">$</span>
                <span class="console-text">Ready to run C4A scripts...</span>
            </div>
        `;
    }

    copyJS() {
        const text = this.currentJS.join('\n');
        navigator.clipboard.writeText(text).then(() => {
            this.addConsoleMessage('JavaScript copied to clipboard', 'success');
        });
    }

    toggleJSEdit() {
        this.isEditingJS = !this.isEditingJS;
        const editBtn = document.getElementById('edit-js-btn');
        const jsOutput = document.getElementById('js-output');
        
        if (this.isEditingJS) {
            editBtn.innerHTML = '<span>💾</span>';
            jsOutput.contentEditable = true;
            jsOutput.style.outline = '1px solid #0fbbaa';
            this.addConsoleMessage('JS edit mode enabled - modify and run', 'warning');
        } else {
            editBtn.innerHTML = '<span>✏️</span>';
            jsOutput.contentEditable = false;
            jsOutput.style.outline = 'none';
            this.addConsoleMessage('JS edit mode disabled', 'text');
        }
    }

    resetPlayground() {
        const iframe = document.getElementById('playground-frame');
        iframe.src = iframe.src;
        this.addConsoleMessage('Playground reset', 'success');
    }

    toggleFullscreen() {
        const playgroundPanel = document.querySelector('.playground-panel');
        playgroundPanel.classList.toggle('fullscreen');
    }

    showExamples() {
        const examples = [
            {
                name: 'Quick Start - Handle Popups',
                script: `# Handle popups quickly\nWAIT \`body\` 2\nIF (EXISTS \`.cookie-banner\`) THEN CLICK \`.accept\`\nWAIT 3\nIF (EXISTS \`#newsletter-popup\`) THEN CLICK \`.close\``
            },
            {
                name: 'Complete Login Flow',
                script: `# Full login process\nCLICK \`#login-btn\`\nWAIT \`.login-form\` 2\n\n# Set credentials using the new SET command\nSET \`#email\` "demo@example.com"\nSET \`#password\` "demo123"\n\n# Submit\nCLICK \`button[type="submit"]\`\nWAIT \`.success\` 2`
            },
            {
                name: 'Product Browsing',
                script: `# Browse products with filters\nCLICK \`#catalog-link\`\nWAIT \`.product-grid\` 3\n\n# Apply filters\nCLICK \`.filter-button\`\nWAIT 0.5\nCLICK \`input[value="electronics"]\`\n\n# Load more products\nREPEAT (SCROLL DOWN 800, 3)\nWAIT 1`
            },
            {
                name: 'Advanced Form Wizard',
                script: `# Multi-step form with validation\nCLICK \`a[href="#forms"]\`\nWAIT \`#survey-form\` 2\n\n# Step 1: Personal Info\nSET \`#full-name\` "John Doe"\nSET \`#survey-email\` "john@example.com"\nCLICK \`.next-step\`\nWAIT 1\n\n# Step 2: Preferences\nCLICK \`#interests\`\nCLICK \`option[value="tech"]\`\nCLICK \`option[value="music"]\`\nCLICK \`.next-step\`\nWAIT 1\n\n# Step 3: Submit\nIF (EXISTS \`#comments\`) THEN SET \`#comments\` "Great experience!"\nCLICK \`#submit-survey\`\nWAIT \`.success-message\` 3`
            }
        ];

        const currentIndex = parseInt(localStorage.getItem('exampleIndex') || '0');
        const example = examples[currentIndex % examples.length];
        
        this.editor.setValue(example.script);
        this.addConsoleMessage(`Loaded example: ${example.name}`, 'success');
        
        localStorage.setItem('exampleIndex', ((currentIndex + 1) % examples.length).toString());
    }

    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Add animations CSS
const style = document.createElement('style');
style.textContent = `
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeOut {
    from { opacity: 1; transform: translateY(0); }
    to { opacity: 0; transform: translateY(-10px); }
}
`;
document.head.appendChild(style);

// Recording Manager Class
class RecordingManager {
    constructor(tutorialApp) {
        this.app = tutorialApp;
        this.isRecording = false;
        this.rawEvents = [];
        this.groupedEvents = [];
        this.startTime = 0;
        this.lastEventTime = 0;
        this.eventInjected = false;
        this.keyBuffer = [];
        this.keyBufferTimeout = null;
        this.scrollAccumulator = { direction: null, amount: 0, startTime: 0 };
        this.processedEventIndices = new Set(); // Track which raw events have been processed
        
        this.init();
    }
    
    init() {
        this.setupUI();
        this.setupMessageHandler();
    }
    
    setupUI() {
        // Record button
        const recordBtn = document.getElementById('record-btn');
        recordBtn.addEventListener('click', () => this.toggleRecording());
        
        // Timeline button
        const timelineBtn = document.getElementById('timeline-btn');
        timelineBtn?.addEventListener('click', () => this.showTimeline());
        
        // Back to editor button
        document.getElementById('back-to-editor')?.addEventListener('click', () => this.hideTimeline());
        
        // Timeline controls
        document.getElementById('select-all-events')?.addEventListener('click', () => this.selectAllEvents());
        document.getElementById('clear-events')?.addEventListener('click', () => this.clearEvents());
        document.getElementById('generate-script')?.addEventListener('click', () => this.generateScript());
    }
    
    setupMessageHandler() {
        window.addEventListener('message', (event) => {
            if (event.data.type === 'c4a-recording-event' && this.isRecording) {
                this.handleRecordedEvent(event.data.event);
            }
        });
    }
    
    toggleRecording() {
        const recordBtn = document.getElementById('record-btn');
        const timelineBtn = document.getElementById('timeline-btn');
        
        if (!this.isRecording) {
            // Start recording
            this.isRecording = true;
            this.startTime = Date.now();
            this.lastEventTime = this.startTime;
            this.rawEvents = [];
            this.groupedEvents = [];
            this.processedEventIndices = new Set();
            this.keyBuffer = [];
            this.scrollAccumulator = { direction: null, amount: 0, startTime: 0 };
            
            recordBtn.classList.add('recording');
            recordBtn.innerHTML = '<span class="icon">⏹</span>Stop';
            
            // Show timeline immediately when recording starts
            timelineBtn.classList.remove('hidden');
            this.showTimeline();
            
            this.injectEventCapture();
            this.app.addConsoleMessage('🔴 Recording started...', 'info');
        } else {
            // Stop recording
            this.isRecording = false;
            recordBtn.classList.remove('recording');
            recordBtn.innerHTML = '<span class="icon">⏺</span>Record';
            
            this.removeEventCapture();
            this.processEvents();
            
            this.app.addConsoleMessage('⏹️ Recording stopped', 'info');
        }
    }
    
    showTimeline() {
        const editorView = document.getElementById('editor-view');
        const timelineView = document.getElementById('timeline-view');
        
        editorView.classList.add('hidden');
        timelineView.classList.remove('hidden');
        
        // Refresh CodeMirror when switching back
        this.editorNeedsRefresh = true;
    }
    
    hideTimeline() {
        const editorView = document.getElementById('editor-view');
        const timelineView = document.getElementById('timeline-view');
        
        timelineView.classList.add('hidden');
        editorView.classList.remove('hidden');
        
        // Refresh CodeMirror after switching
        if (this.editorNeedsRefresh) {
            setTimeout(() => this.app.editor.refresh(), 100);
            this.editorNeedsRefresh = false;
        }
    }
    
    injectEventCapture() {
        const iframe = document.getElementById('playground-frame');
        const script = `
            (function() {
                if (window.__c4aRecordingActive) return;
                window.__c4aRecordingActive = true;
                
                const captureEvent = (type, event) => {
                    const data = {
                        type: type,
                        timestamp: Date.now(),
                        targetTag: event.target.tagName,
                        targetId: event.target.id,
                        targetClass: event.target.className,
                        targetSelector: generateSelector(event.target),
                        targetType: event.target.type // For input elements
                    };
                    
                    // Add type-specific data
                    switch(type) {
                        case 'click':
                        case 'dblclick':
                        case 'contextmenu':
                            data.x = event.clientX;
                            data.y = event.clientY;
                            break;
                        case 'keydown':
                        case 'keyup':
                            data.key = event.key;
                            data.code = event.code;
                            data.ctrlKey = event.ctrlKey;
                            data.shiftKey = event.shiftKey;
                            data.altKey = event.altKey;
                            break;
                        case 'input':
                        case 'change':
                            data.value = event.target.value;
                            data.inputType = event.inputType;
                            // For checkboxes and radio buttons, also capture checked state
                            if (event.target.type === 'checkbox' || event.target.type === 'radio') {
                                data.checked = event.target.checked;
                            }
                            // For select elements, capture selected text
                            if (event.target.tagName === 'SELECT') {
                                data.selectedText = event.target.options[event.target.selectedIndex]?.text || '';
                            }
                            break;
                        case 'scroll':
                        case 'wheel':
                            data.scrollTop = window.scrollY;
                            data.scrollLeft = window.scrollX;
                            data.deltaY = event.deltaY || 0;
                            data.deltaX = event.deltaX || 0;
                            break;
                        case 'focus':
                        case 'blur':
                            data.value = event.target.value || '';
                            break;
                    }
                    
                    window.parent.postMessage({
                        type: 'c4a-recording-event',
                        event: data
                    }, '*');
                };
                
                const generateSelector = (element) => {
                    try {
                        if (element.id) return '#' + element.id;
                        
                        if (element.className && typeof element.className === 'string') {
                            const classes = element.className.trim().split(/\\s+/);
                            if (classes.length > 0 && classes[0]) {
                                return '.' + classes[0];
                            }
                        }
                        
                        // Generate nth-child selector
                        let path = [];
                        let currentElement = element;
                        while (currentElement && currentElement.nodeType === Node.ELEMENT_NODE) {
                            let selector = currentElement.nodeName.toLowerCase();
                            if (currentElement.id) {
                                selector = '#' + currentElement.id;
                                path.unshift(selector);
                                break;
                            } else {
                                let sibling = currentElement;
                                let nth = 1;
                                while (sibling.previousElementSibling) {
                                    sibling = sibling.previousElementSibling;
                                    if (sibling.nodeName === currentElement.nodeName) nth++;
                                }
                                if (nth > 1) selector += ':nth-child(' + nth + ')';
                            }
                            path.unshift(selector);
                            currentElement = currentElement.parentNode;
                        }
                        return path.join(' > ') || element.nodeName.toLowerCase();
                    } catch (e) {
                        return element.nodeName.toLowerCase();
                    }
                };
                
                // Store event handlers for cleanup
                window.__c4aEventHandlers = {};
                
                // Attach event listeners
                const events = ['click', 'dblclick', 'contextmenu', 'keydown', 'keyup', 
                               'input', 'change', 'scroll', 'wheel', 'focus', 'blur'];
                
                events.forEach(eventType => {
                    const handler = (e) => captureEvent(eventType, e);
                    window.__c4aEventHandlers[eventType] = handler;
                    document.addEventListener(eventType, handler, true);
                });
                
                // Cleanup function
                window.__c4aCleanupRecording = () => {
                    events.forEach(eventType => {
                        const handler = window.__c4aEventHandlers[eventType];
                        if (handler) {
                            document.removeEventListener(eventType, handler, true);
                        }
                    });
                    delete window.__c4aRecordingActive;
                    delete window.__c4aCleanupRecording;
                    delete window.__c4aEventHandlers;
                };
            })();
        `;
        
        const scriptEl = iframe.contentDocument.createElement('script');
        scriptEl.textContent = script;
        iframe.contentDocument.body.appendChild(scriptEl);
        scriptEl.remove();
        this.eventInjected = true;
    }
    
    removeEventCapture() {
        if (!this.eventInjected) return;
        
        const iframe = document.getElementById('playground-frame');
        iframe.contentWindow.eval('if (window.__c4aCleanupRecording) window.__c4aCleanupRecording();');
        this.eventInjected = false;
    }
    
    handleRecordedEvent(event) {
        const now = Date.now();
        const timeSinceStart = ((now - this.startTime) / 1000).toFixed(1);
        
        // Add time since last event
        event.timeSinceStart = timeSinceStart;
        event.timeSinceLast = now - this.lastEventTime;
        this.lastEventTime = now;
        
        this.rawEvents.push(event);
        
        // Real-time processing for immediate feedback
        if (event.type === 'keydown' && this.shouldGroupKeystrokes(event)) {
            this.keyBuffer.push(event);
            
            // Clear existing timeout
            if (this.keyBufferTimeout) {
                clearTimeout(this.keyBufferTimeout);
            }
            
            // Set timeout to flush buffer after 500ms of no typing
            this.keyBufferTimeout = setTimeout(() => {
                this.flushKeyBuffer();
                this.updateTimeline();
            }, 500);
        } else {
            // Handle change events for select, checkbox, radio
            if (event.type === 'change') {
                const tagName = event.targetTag?.toLowerCase();
                
                // Only skip change events for text inputs (they're part of typing)
                if (tagName === 'input' && 
                    event.targetType !== 'checkbox' && 
                    event.targetType !== 'radio') {
                    return; // Skip text input change events
                }
                
                // For select, checkbox, radio - process the change event
                if (tagName === 'select' || 
                    (tagName === 'input' && (event.targetType === 'checkbox' || event.targetType === 'radio'))) {
                    
                    // Flush any pending keystrokes first
                    if (this.keyBuffer.length > 0) {
                        this.flushKeyBuffer();
                        this.updateTimeline();
                    }
                    
                    // Create SET command for the value change
                    const command = this.eventToCommand(event, this.rawEvents.length - 1);
                    if (command) {
                        this.groupedEvents.push(command);
                        this.updateTimeline();
                    }
                    return;
                }
            }
            
            // Skip input events - they're part of typing
            if (event.type === 'input') {
                return;
            }
            
            // Clear timeout if exists
            if (this.keyBufferTimeout) {
                clearTimeout(this.keyBufferTimeout);
                this.keyBufferTimeout = null;
            }
            
            // Flush key buffer only for significant events
            const shouldFlushBuffer = event.type === 'click' || 
                                    event.type === 'dblclick' || 
                                    event.type === 'contextmenu' ||
                                    event.type === 'scroll' ||
                                    event.type === 'wheel';
            
            const hadKeyBuffer = this.keyBuffer.length > 0;
            
            if (shouldFlushBuffer && hadKeyBuffer) {
                this.flushKeyBuffer();
                this.updateTimeline();
            }
            
            // Process this event immediately if it's not a typing-related event
            if (event.type !== 'keydown' && event.type !== 'keyup' && 
                event.type !== 'input' && event.type !== 'change' &&
                event.type !== 'focus' && event.type !== 'blur') {
                const command = this.eventToCommand(event, this.rawEvents.length - 1);
                if (command) {
                    // Check if it's a scroll event that should be accumulated
                    if (command.type === 'SCROLL') {
                        // Remove previous scroll events in the same direction
                        this.groupedEvents = this.groupedEvents.filter(e => 
                            !(e.type === 'SCROLL' && e.direction === command.direction && 
                              parseFloat(e.time) > parseFloat(command.time) - 0.5)
                        );
                    }
                    this.groupedEvents.push(command);
                    this.updateTimeline();
                }
            }
        }
    }
    
    shouldGroupKeystrokes(event) {
        // Skip if no key
        if (!event.key) return false;
        
        // Group printable characters, space, and common typing keys
        return (
            event.key.length === 1 || // Single characters
            event.key === ' ' || // Space
            event.key === 'Enter' || // Enter key
            event.key === 'Tab' || // Tab key
            event.key === 'Backspace' || // Backspace
            event.key === 'Delete' // Delete
        );
    }
    
    flushKeyBuffer() {
        if (this.keyBuffer.length === 0) return;
        
        // Build the text, handling special keys
        const text = this.keyBuffer.map(e => {
            switch(e.key) {
                case ' ': return ' ';
                case 'Enter': return '\n';
                case 'Tab': return '\t';
                case 'Backspace': return ''; // Skip backspace in final text
                case 'Delete': return ''; // Skip delete in final text
                default: return e.key;
            }
        }).join('');
        
        // Don't create empty TYPE commands
        if (text.length === 0) {
            this.keyBuffer = [];
            return;
        }
        
        const firstEvent = this.keyBuffer[0];
        const lastEvent = this.keyBuffer[this.keyBuffer.length - 1];
        
        // Mark all keystroke events as processed
        this.keyBuffer.forEach(event => {
            const index = this.rawEvents.indexOf(event);
            if (index !== -1) {
                this.processedEventIndices.add(index);
            }
        });
        
        // Check if this should be a SET command instead of TYPE
        // Look for a click event just before the first keystroke
        const firstKeystrokeIndex = this.rawEvents.indexOf(firstEvent);
        let commandType = 'TYPE';
        
        if (firstKeystrokeIndex > 0) {
            const prevEvent = this.rawEvents[firstKeystrokeIndex - 1];
            if (prevEvent && prevEvent.type === 'click' && 
                prevEvent.targetSelector === firstEvent.targetSelector) {
                // This looks like a SET pattern
                commandType = 'SET';
                // Mark the click event as processed too
                this.processedEventIndices.add(firstKeystrokeIndex - 1);
            }
        }
        
        // Check if we already have a TYPE command for this exact text at this time
        // This prevents duplicates when the buffer is flushed multiple times
        const existingCommand = this.groupedEvents.find(cmd => 
            cmd.type === commandType && 
            cmd.value === text && 
            cmd.time === firstEvent.timeSinceStart
        );
        
        if (!existingCommand) {
            this.groupedEvents.push({
                type: commandType,
                selector: firstEvent.targetSelector,
                value: text,
                time: firstEvent.timeSinceStart,
                duration: lastEvent.timestamp - firstEvent.timestamp,
                raw: [...this.keyBuffer]  // Make a copy to avoid reference issues
            });
        }
        
        this.keyBuffer = [];
    }
    
    processEvents() {
        // Clear any pending timeouts
        if (this.keyBufferTimeout) {
            clearTimeout(this.keyBufferTimeout);
            this.keyBufferTimeout = null;
        }
        
        // Flush any remaining buffers
        this.flushKeyBuffer();
        
        // Don't reprocess events that were already grouped during recording
        // Just apply final optimizations
        this.optimizeEvents();
        this.updateTimeline();
    }
    
    eventToCommand(event, index) {
        // Skip already processed events
        if (this.processedEventIndices.has(index)) {
            return null;
        }
        
        // Skip events that should only be processed as grouped commands
        if (event.type === 'keydown' || event.type === 'keyup' || 
            event.type === 'input' || event.type === 'focus' || event.type === 'blur') {
            return null;
        }
        
        // Allow change events for select, checkbox, radio
        if (event.type === 'change') {
            const tagName = event.targetTag?.toLowerCase();
            if (tagName === 'select' || 
                (tagName === 'input' && (event.targetType === 'checkbox' || event.targetType === 'radio'))) {
                // Process as SET command
            } else {
                return null; // Skip change events for text inputs
            }
        }
        
        switch (event.type) {
            case 'click':
                // Check if followed by input focus or change event
                const nextEvent = this.rawEvents[index + 1];
                if (nextEvent && nextEvent.targetSelector === event.targetSelector) {
                    if (nextEvent.type === 'focus' || nextEvent.type === 'change') {
                        return null; // Skip, will be handled by SET or change event
                    }
                }
                
                // Also check if this is a click on a select element
                if (event.targetTag?.toLowerCase() === 'select') {
                    // Look ahead for a change event
                    for (let i = index + 1; i < Math.min(index + 5, this.rawEvents.length); i++) {
                        if (this.rawEvents[i].type === 'change' && 
                            this.rawEvents[i].targetSelector === event.targetSelector) {
                            return null; // Skip click, change event will handle it
                        }
                    }
                }
                
                return {
                    type: 'CLICK',
                    selector: event.targetSelector,
                    time: event.timeSinceStart
                };
                
            case 'dblclick':
                return {
                    type: 'DOUBLE_CLICK',
                    selector: event.targetSelector,
                    time: event.timeSinceStart
                };
                
            case 'contextmenu':
                return {
                    type: 'RIGHT_CLICK',
                    selector: event.targetSelector,
                    time: event.timeSinceStart
                };
                
            case 'scroll':
            case 'wheel':
                // Accumulate scroll events
                if (event.deltaY !== 0) {
                    const direction = event.deltaY > 0 ? 'DOWN' : 'UP';
                    const amount = Math.abs(event.deltaY);
                    
                    if (this.scrollAccumulator.direction === direction && 
                        event.timestamp - this.scrollAccumulator.startTime < 500) {
                        this.scrollAccumulator.amount += amount;
                    } else {
                        this.scrollAccumulator = { direction, amount, startTime: event.timestamp };
                    }
                    
                    // Return accumulated scroll at end of sequence
                    const nextEvent = this.rawEvents[index + 1];
                    if (!nextEvent || nextEvent.type !== 'scroll' || 
                        nextEvent.timestamp - event.timestamp > 500) {
                        return {
                            type: 'SCROLL',
                            direction: this.scrollAccumulator.direction,
                            amount: Math.round(this.scrollAccumulator.amount),
                            time: event.timeSinceStart
                        };
                    }
                }
                return null;
                
            // Input events are handled through keystroke grouping
            case 'input':
                return null;
                
            case 'change':
                // Handle select, checkbox, radio changes
                const tagName = event.targetTag?.toLowerCase();
                
                if (tagName === 'select') {
                    return {
                        type: 'SET',
                        selector: event.targetSelector,
                        value: event.value,
                        displayValue: event.selectedText || event.value,
                        time: event.timeSinceStart
                    };
                } else if (tagName === 'input' && event.targetType === 'checkbox') {
                    return {
                        type: 'SET',
                        selector: event.targetSelector,
                        value: event.checked ? 'checked' : 'unchecked',
                        time: event.timeSinceStart
                    };
                } else if (tagName === 'input' && event.targetType === 'radio') {
                    return {
                        type: 'SET',
                        selector: event.targetSelector,
                        value: 'checked',
                        time: event.timeSinceStart
                    };
                }
                return null;
        }
        
        return null;
    }
    
    optimizeEvents() {
        const optimized = [];
        let lastTime = 0;
        
        this.groupedEvents.forEach((event, index) => {
            // Insert WAIT if pause > 1 second
            const currentTime = parseFloat(event.time);
            if (currentTime - lastTime > 1) {
                optimized.push({
                    type: 'WAIT',
                    value: Math.round(currentTime - lastTime),
                    time: lastTime.toFixed(1)
                });
            }
            
            optimized.push(event);
            lastTime = currentTime;
        });
        
        this.groupedEvents = optimized;
    }
    
    updateTimeline() {
        const timeline = document.getElementById('timeline-events');
        timeline.innerHTML = '';
        
        this.groupedEvents.forEach((event, index) => {
            const eventEl = this.createEventElement(event, index);
            timeline.appendChild(eventEl);
        });
    }
    
    createEventElement(event, index) {
        const div = document.createElement('div');
        div.className = 'timeline-event';
        div.dataset.index = index;
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'event-checkbox';
        checkbox.checked = true;
        checkbox.addEventListener('change', () => {
            div.classList.toggle('selected', checkbox.checked);
        });
        
        const time = document.createElement('span');
        time.className = 'event-time';
        time.textContent = event.time + 's';
        
        const command = document.createElement('span');
        command.className = 'event-command';
        command.innerHTML = this.formatCommand(event);
        
        const editBtn = document.createElement('button');
        editBtn.className = 'event-edit';
        editBtn.textContent = 'Edit';
        editBtn.addEventListener('click', () => this.editEvent(index));
        
        div.appendChild(checkbox);
        div.appendChild(time);
        div.appendChild(command);
        div.appendChild(editBtn);
        
        // Initially selected
        div.classList.add('selected');
        
        return div;
    }
    
    formatCommand(event) {
        switch (event.type) {
            case 'CLICK':
                return `<span class="cmd-name">CLICK</span> <span class="cmd-selector">\`${event.selector}\`</span>`;
            case 'DOUBLE_CLICK':
                return `<span class="cmd-name">DOUBLE_CLICK</span> <span class="cmd-selector">\`${event.selector}\`</span>`;
            case 'RIGHT_CLICK':
                return `<span class="cmd-name">RIGHT_CLICK</span> <span class="cmd-selector">\`${event.selector}\`</span>`;
            case 'TYPE':
                return `<span class="cmd-name">TYPE</span> <span class="cmd-value">"${event.value}"</span> <span class="cmd-detail">(${event.value.length} chars)</span>`;
            case 'SET':
                // Use displayValue if available (for select elements)
                const displayText = event.displayValue || event.value;
                return `<span class="cmd-name">SET</span> <span class="cmd-selector">\`${event.selector}\`</span> <span class="cmd-value">"${displayText}"</span>`;
            case 'SCROLL':
                return `<span class="cmd-name">SCROLL</span> <span class="cmd-value">${event.direction} ${event.amount}</span>`;
            case 'WAIT':
                return `<span class="cmd-name">WAIT</span> <span class="cmd-value">${event.value}</span>`;
            default:
                return `<span class="cmd-name">${event.type}</span>`;
        }
    }
    
    editEvent(index) {
        const event = this.groupedEvents[index];
        this.currentEditIndex = index;
        
        // Show modal
        const overlay = document.getElementById('event-editor-overlay');
        const modal = document.getElementById('event-editor-modal');
        overlay.classList.remove('hidden');
        modal.classList.remove('hidden');
        
        // Populate fields
        document.getElementById('edit-command-type').value = event.type;
        
        // Show/hide fields based on command type
        const selectorField = document.getElementById('edit-selector-field');
        const valueField = document.getElementById('edit-value-field');
        const directionField = document.getElementById('edit-direction-field');
        
        selectorField.classList.add('hidden');
        valueField.classList.add('hidden');
        directionField.classList.add('hidden');
        
        switch (event.type) {
            case 'CLICK':
            case 'DOUBLE_CLICK':
            case 'RIGHT_CLICK':
                selectorField.classList.remove('hidden');
                document.getElementById('edit-selector').value = event.selector;
                break;
            case 'TYPE':
                valueField.classList.remove('hidden');
                document.getElementById('edit-value').value = event.value;
                break;
            case 'SET':
                selectorField.classList.remove('hidden');
                valueField.classList.remove('hidden');
                document.getElementById('edit-selector').value = event.selector;
                document.getElementById('edit-value').value = event.value;
                break;
            case 'SCROLL':
                directionField.classList.remove('hidden');
                valueField.classList.remove('hidden');
                document.getElementById('edit-direction').value = event.direction;
                document.getElementById('edit-value').value = event.amount;
                break;
            case 'WAIT':
                valueField.classList.remove('hidden');
                document.getElementById('edit-value').value = event.value;
                break;
        }
        
        // Setup event handlers
        this.setupEditModalHandlers();
    }
    
    setupEditModalHandlers() {
        const overlay = document.getElementById('event-editor-overlay');
        const modal = document.getElementById('event-editor-modal');
        const cancelBtn = document.getElementById('edit-cancel');
        const saveBtn = document.getElementById('edit-save');
        
        const closeModal = () => {
            overlay.classList.add('hidden');
            modal.classList.add('hidden');
        };
        
        const saveHandler = () => {
            const event = this.groupedEvents[this.currentEditIndex];
            
            // Update event based on type
            switch (event.type) {
                case 'CLICK':
                case 'DOUBLE_CLICK':
                case 'RIGHT_CLICK':
                    event.selector = document.getElementById('edit-selector').value;
                    break;
                case 'TYPE':
                    event.value = document.getElementById('edit-value').value;
                    break;
                case 'SET':
                    event.selector = document.getElementById('edit-selector').value;
                    event.value = document.getElementById('edit-value').value;
                    break;
                case 'SCROLL':
                    event.direction = document.getElementById('edit-direction').value;
                    event.amount = parseInt(document.getElementById('edit-value').value) || 0;
                    break;
                case 'WAIT':
                    event.value = parseInt(document.getElementById('edit-value').value) || 0;
                    break;
            }
            
            // Update timeline
            this.updateTimeline();
            closeModal();
        };
        
        // Clean up old handlers
        cancelBtn.replaceWith(cancelBtn.cloneNode(true));
        saveBtn.replaceWith(saveBtn.cloneNode(true));
        overlay.replaceWith(overlay.cloneNode(true));
        
        // Add new handlers
        document.getElementById('edit-cancel').addEventListener('click', closeModal);
        document.getElementById('edit-save').addEventListener('click', saveHandler);
        document.getElementById('event-editor-overlay').addEventListener('click', closeModal);
    }
    
    selectAllEvents() {
        const checkboxes = document.querySelectorAll('.event-checkbox');
        const events = document.querySelectorAll('.timeline-event');
        checkboxes.forEach((cb, i) => {
            cb.checked = true;
            events[i].classList.add('selected');
        });
    }
    
    clearEvents() {
        this.groupedEvents = [];
        this.updateTimeline();
    }
    
    generateScript() {
        const selectedEvents = [];
        const checkboxes = document.querySelectorAll('.event-checkbox');
        
        checkboxes.forEach((cb, index) => {
            if (cb.checked && this.groupedEvents[index]) {
                selectedEvents.push(this.groupedEvents[index]);
            }
        });
        
        if (selectedEvents.length === 0) {
            this.app.addConsoleMessage('No events selected', 'warning');
            return;
        }
        
        const script = selectedEvents.map(event => this.eventToC4A(event)).join('\n');
        
        // Set the script in the editor
        this.app.editor.setValue(script);
        this.app.addConsoleMessage(`Generated ${selectedEvents.length} commands`, 'success');
        
        // Switch back to editor view
        this.hideTimeline();
    }
    
    eventToC4A(event) {
        switch (event.type) {
            case 'CLICK':
                return `CLICK \`${event.selector}\``;
            case 'DOUBLE_CLICK':
                return `DOUBLE_CLICK \`${event.selector}\``;
            case 'RIGHT_CLICK':
                return `RIGHT_CLICK \`${event.selector}\``;
            case 'TYPE':
                return `TYPE "${event.value}"`;
            case 'SET':
                return `SET \`${event.selector}\` "${event.value}"`;
            case 'SCROLL':
                return `SCROLL ${event.direction} ${event.amount}`;
            case 'WAIT':
                return `WAIT ${event.value}`;
            default:
                return `# Unknown: ${event.type}`;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.tutorialApp = new TutorialApp();
    console.log('🎓 C4A-Script Tutorial initialized!');
});