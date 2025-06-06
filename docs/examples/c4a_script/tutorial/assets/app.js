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
        
        this.init();
    }

    init() {
        this.setupEditors();
        this.setupButtons();
        this.setupTabs();
        this.setupTutorial();
        this.checkFirstVisit();
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.tutorialApp = new TutorialApp();
    console.log('🎓 C4A-Script Tutorial initialized!');
});