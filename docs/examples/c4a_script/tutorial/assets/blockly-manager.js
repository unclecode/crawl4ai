// Blockly Manager for C4A-Script
// Handles Blockly workspace, code generation, and synchronization with text editor

class BlocklyManager {
    constructor(tutorialApp) {
        this.app = tutorialApp;
        this.workspace = null;
        this.isUpdating = false; // Prevent circular updates
        this.blocklyVisible = false;
        this.toolboxXml = this.generateToolbox();
        
        this.init();
    }
    
    init() {
        this.setupBlocklyContainer();
        this.initializeWorkspace();
        this.setupEventHandlers();
        this.setupSynchronization();
    }
    
    setupBlocklyContainer() {
        // Create blockly container div
        const editorContainer = document.querySelector('.editor-container');
        const blocklyDiv = document.createElement('div');
        blocklyDiv.id = 'blockly-view';
        blocklyDiv.className = 'blockly-workspace hidden';
        blocklyDiv.style.height = '100%';
        blocklyDiv.style.width = '100%';
        editorContainer.appendChild(blocklyDiv);
    }
    
    generateToolbox() {
        return `
        <xml id="toolbox" style="display: none">
            <category name="Navigation" colour="${BlockColors.NAVIGATION}">
                <block type="c4a_go"></block>
                <block type="c4a_reload"></block>
                <block type="c4a_back"></block>
                <block type="c4a_forward"></block>
            </category>
            
            <category name="Wait" colour="${BlockColors.WAIT}">
                <block type="c4a_wait_time">
                    <field name="SECONDS">3</field>
                </block>
                <block type="c4a_wait_selector">
                    <field name="SELECTOR">#content</field>
                    <field name="TIMEOUT">10</field>
                </block>
                <block type="c4a_wait_text">
                    <field name="TEXT">Loading complete</field>
                    <field name="TIMEOUT">5</field>
                </block>
            </category>
            
            <category name="Mouse Actions" colour="${BlockColors.ACTIONS}">
                <block type="c4a_click">
                    <field name="SELECTOR">button.submit</field>
                </block>
                <block type="c4a_click_xy"></block>
                <block type="c4a_double_click"></block>
                <block type="c4a_right_click"></block>
                <block type="c4a_move"></block>
                <block type="c4a_drag"></block>
                <block type="c4a_scroll">
                    <field name="DIRECTION">DOWN</field>
                    <field name="AMOUNT">500</field>
                </block>
            </category>
            
            <category name="Keyboard" colour="${BlockColors.KEYBOARD}">
                <block type="c4a_type">
                    <field name="TEXT">hello@example.com</field>
                </block>
                <block type="c4a_type_var">
                    <field name="VAR">email</field>
                </block>
                <block type="c4a_clear"></block>
                <block type="c4a_set">
                    <field name="SELECTOR">#email</field>
                    <field name="VALUE">user@example.com</field>
                </block>
                <block type="c4a_press">
                    <field name="KEY">Tab</field>
                </block>
                <block type="c4a_key_down">
                    <field name="KEY">Shift</field>
                </block>
                <block type="c4a_key_up">
                    <field name="KEY">Shift</field>
                </block>
            </category>
            
            <category name="Control Flow" colour="${BlockColors.CONTROL}">
                <block type="c4a_if_exists">
                    <field name="SELECTOR">.cookie-banner</field>
                </block>
                <block type="c4a_if_exists_else">
                    <field name="SELECTOR">#user</field>
                </block>
                <block type="c4a_if_not_exists">
                    <field name="SELECTOR">.modal</field>
                </block>
                <block type="c4a_if_js">
                    <field name="CONDITION">window.innerWidth < 768</field>
                </block>
                <block type="c4a_repeat_times">
                    <field name="TIMES">5</field>
                </block>
                <block type="c4a_repeat_while">
                    <field name="CONDITION">document.querySelector('.load-more')</field>
                </block>
            </category>
            
            <category name="Variables" colour="${BlockColors.VARIABLES}">
                <block type="c4a_setvar">
                    <field name="NAME">username</field>
                    <field name="VALUE">john@example.com</field>
                </block>
                <block type="c4a_eval">
                    <field name="CODE">console.log('Hello')</field>
                </block>
            </category>
            
            <category name="Procedures" colour="${BlockColors.PROCEDURES}">
                <block type="c4a_proc_def">
                    <field name="NAME">login</field>
                </block>
                <block type="c4a_proc_call">
                    <field name="NAME">login</field>
                </block>
            </category>
            
            <category name="Comments" colour="#9E9E9E">
                <block type="c4a_comment">
                    <field name="TEXT">Add comment here</field>
                </block>
            </category>
        </xml>`;
    }
    
    initializeWorkspace() {
        const blocklyDiv = document.getElementById('blockly-view');
        
        // Dark theme configuration
        const theme = Blockly.Theme.defineTheme('c4a-dark', {
            'base': Blockly.Themes.Classic,
            'componentStyles': {
                'workspaceBackgroundColour': '#0e0e10',
                'toolboxBackgroundColour': '#1a1a1b',
                'toolboxForegroundColour': '#e0e0e0',
                'flyoutBackgroundColour': '#1a1a1b',
                'flyoutForegroundColour': '#e0e0e0',
                'flyoutOpacity': 0.9,
                'scrollbarColour': '#2a2a2c',
                'scrollbarOpacity': 0.5,
                'insertionMarkerColour': '#0fbbaa',
                'insertionMarkerOpacity': 0.3,
                'markerColour': '#0fbbaa',
                'cursorColour': '#0fbbaa',
                'selectedGlowColour': '#0fbbaa',
                'selectedGlowOpacity': 0.4,
                'replacementGlowColour': '#0fbbaa',
                'replacementGlowOpacity': 0.5
            },
            'fontStyle': {
                'family': 'Dank Mono, Monaco, Consolas, monospace',
                'weight': 'normal',
                'size': 13
            }
        });
        
        this.workspace = Blockly.inject(blocklyDiv, {
            toolbox: this.toolboxXml,
            theme: theme,
            grid: {
                spacing: 20,
                length: 3,
                colour: '#2a2a2c',
                snap: true
            },
            zoom: {
                controls: true,
                wheel: true,
                startScale: 1.0,
                maxScale: 3,
                minScale: 0.3,
                scaleSpeed: 1.2
            },
            trashcan: true,
            sounds: false,
            media: 'https://unpkg.com/blockly/media/'
        });
        
        // Add workspace change listener
        this.workspace.addChangeListener((event) => {
            if (!this.isUpdating && event.type !== Blockly.Events.UI) {
                this.syncBlocksToCode();
            }
        });
    }
    
    setupEventHandlers() {
        // Add blockly toggle button
        const headerActions = document.querySelector('.editor-panel .header-actions');
        const blocklyBtn = document.createElement('button');
        blocklyBtn.id = 'blockly-btn';
        blocklyBtn.className = 'action-btn';
        blocklyBtn.title = 'Toggle Blockly Mode';
        blocklyBtn.innerHTML = '<span class="icon">🧩</span>';
        
        // Insert before the Run button
        const runBtn = document.getElementById('run-btn');
        headerActions.insertBefore(blocklyBtn, runBtn);
        
        blocklyBtn.addEventListener('click', () => this.toggleBlocklyView());
    }
    
    setupSynchronization() {
        // Listen to CodeMirror changes
        this.app.editor.on('change', (instance, changeObj) => {
            if (!this.isUpdating && this.blocklyVisible && changeObj.origin !== 'setValue') {
                this.syncCodeToBlocks();
            }
        });
    }
    
    toggleBlocklyView() {
        const editorView = document.getElementById('editor-view');
        const blocklyView = document.getElementById('blockly-view');
        const timelineView = document.getElementById('timeline-view');
        const blocklyBtn = document.getElementById('blockly-btn');
        
        this.blocklyVisible = !this.blocklyVisible;
        
        if (this.blocklyVisible) {
            // Show Blockly
            editorView.classList.add('hidden');
            timelineView.classList.add('hidden');
            blocklyView.classList.remove('hidden');
            blocklyBtn.classList.add('active');
            
            // Resize workspace
            Blockly.svgResize(this.workspace);
            
            // Sync current code to blocks
            this.syncCodeToBlocks();
        } else {
            // Show editor
            blocklyView.classList.add('hidden');
            editorView.classList.remove('hidden');
            blocklyBtn.classList.remove('active');
            
            // Refresh CodeMirror
            setTimeout(() => this.app.editor.refresh(), 100);
        }
    }
    
    syncBlocksToCode() {
        if (this.isUpdating) return;
        
        try {
            this.isUpdating = true;
            
            // Generate C4A-Script from blocks using our custom generator
            if (typeof c4aGenerator !== 'undefined') {
                const code = c4aGenerator.workspaceToCode(this.workspace);
                
                // Process the code to maintain proper formatting
                const lines = code.split('\n');
                const formattedLines = [];
                let lastWasComment = false;
                
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i].trim();
                    if (!line) continue;
                    
                    const isComment = line.startsWith('#');
                    
                    // Add blank line when transitioning between comments and commands
                    if (formattedLines.length > 0 && lastWasComment !== isComment) {
                        formattedLines.push('');
                    }
                    
                    formattedLines.push(line);
                    lastWasComment = isComment;
                }
                
                const cleanCode = formattedLines.join('\n');
                
                // Update CodeMirror
                this.app.editor.setValue(cleanCode);
            }
            
        } catch (error) {
            console.error('Error syncing blocks to code:', error);
        } finally {
            this.isUpdating = false;
        }
    }
    
    syncCodeToBlocks() {
        if (this.isUpdating) return;
        
        try {
            this.isUpdating = true;
            
            // Clear workspace
            this.workspace.clear();
            
            // Parse C4A-Script and generate blocks
            const code = this.app.editor.getValue();
            const blocks = this.parseC4AToBlocks(code);
            
            if (blocks) {
                Blockly.Xml.domToWorkspace(blocks, this.workspace);
            }
            
        } catch (error) {
            console.error('Error syncing code to blocks:', error);
            // Show error in console
            this.app.addConsoleMessage(`Blockly sync error: ${error.message}`, 'warning');
        } finally {
            this.isUpdating = false;
        }
    }
    
    parseC4AToBlocks(code) {
        const lines = code.split('\n');
        const xml = document.createElement('xml');
        let yPos = 20;
        let previousBlock = null;
        let rootBlock = null;
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            // Skip empty lines
            if (!line) continue;
            
            // Handle comments
            if (line.startsWith('#')) {
                const commentBlock = this.parseLineToBlock(line, i, lines);
                if (commentBlock) {
                    if (previousBlock) {
                        // Connect to previous block
                        const next = document.createElement('next');
                        next.appendChild(commentBlock);
                        previousBlock.appendChild(next);
                    } else {
                        // First block - set position
                        commentBlock.setAttribute('x', 20);
                        commentBlock.setAttribute('y', yPos);
                        xml.appendChild(commentBlock);
                        rootBlock = commentBlock;
                        yPos += 60;
                    }
                    previousBlock = commentBlock;
                }
                continue;
            }
            
            const block = this.parseLineToBlock(line, i, lines);
            
            if (block) {
                if (previousBlock) {
                    // Connect to previous block using <next>
                    const next = document.createElement('next');
                    next.appendChild(block);
                    previousBlock.appendChild(next);
                } else {
                    // First block - set position
                    block.setAttribute('x', 20);
                    block.setAttribute('y', yPos);
                    xml.appendChild(block);
                    rootBlock = block;
                    yPos += 60;
                }
                previousBlock = block;
            }
        }
        
        return xml;
    }
    
    parseLineToBlock(line, index, allLines) {
        // Navigation commands
        if (line.startsWith('GO ')) {
            const url = line.substring(3).trim();
            return this.createBlock('c4a_go', { 'URL': url });
        }
        if (line === 'RELOAD') {
            return this.createBlock('c4a_reload');
        }
        if (line === 'BACK') {
            return this.createBlock('c4a_back');
        }
        if (line === 'FORWARD') {
            return this.createBlock('c4a_forward');
        }
        
        // Wait commands
        if (line.startsWith('WAIT ')) {
            const parts = line.substring(5).trim();
            
            // Check if it's just a number (wait time)
            if (/^\d+(\.\d+)?$/.test(parts)) {
                return this.createBlock('c4a_wait_time', { 'SECONDS': parts });
            }
            
            // Check for selector wait
            const selectorMatch = parts.match(/^`([^`]+)`\s+(\d+)$/);
            if (selectorMatch) {
                return this.createBlock('c4a_wait_selector', {
                    'SELECTOR': selectorMatch[1],
                    'TIMEOUT': selectorMatch[2]
                });
            }
            
            // Check for text wait
            const textMatch = parts.match(/^"([^"]+)"\s+(\d+)$/);
            if (textMatch) {
                return this.createBlock('c4a_wait_text', {
                    'TEXT': textMatch[1],
                    'TIMEOUT': textMatch[2]
                });
            }
        }
        
        // Click commands
        if (line.startsWith('CLICK ')) {
            const target = line.substring(6).trim();
            
            // Check for coordinates
            const coordMatch = target.match(/^(\d+)\s+(\d+)$/);
            if (coordMatch) {
                return this.createBlock('c4a_click_xy', {
                    'X': coordMatch[1],
                    'Y': coordMatch[2]
                });
            }
            
            // Selector click
            const selectorMatch = target.match(/^`([^`]+)`$/);
            if (selectorMatch) {
                return this.createBlock('c4a_click', {
                    'SELECTOR': selectorMatch[1]
                });
            }
        }
        
        // Other mouse actions
        if (line.startsWith('DOUBLE_CLICK ')) {
            const selector = line.substring(13).trim().match(/^`([^`]+)`$/);
            if (selector) {
                return this.createBlock('c4a_double_click', {
                    'SELECTOR': selector[1]
                });
            }
        }
        
        if (line.startsWith('RIGHT_CLICK ')) {
            const selector = line.substring(12).trim().match(/^`([^`]+)`$/);
            if (selector) {
                return this.createBlock('c4a_right_click', {
                    'SELECTOR': selector[1]
                });
            }
        }
        
        // Scroll
        if (line.startsWith('SCROLL ')) {
            const match = line.match(/^SCROLL\s+(UP|DOWN|LEFT|RIGHT)(?:\s+(\d+))?$/);
            if (match) {
                return this.createBlock('c4a_scroll', {
                    'DIRECTION': match[1],
                    'AMOUNT': match[2] || '500'
                });
            }
        }
        
        // Type commands
        if (line.startsWith('TYPE ')) {
            const content = line.substring(5).trim();
            
            // Variable type
            if (content.startsWith('$')) {
                return this.createBlock('c4a_type_var', {
                    'VAR': content.substring(1)
                });
            }
            
            // Text type
            const textMatch = content.match(/^"([^"]*)"$/);
            if (textMatch) {
                return this.createBlock('c4a_type', {
                    'TEXT': textMatch[1]
                });
            }
        }
        
        // SET command
        if (line.startsWith('SET ')) {
            const match = line.match(/^SET\s+`([^`]+)`\s+"([^"]*)"$/);
            if (match) {
                return this.createBlock('c4a_set', {
                    'SELECTOR': match[1],
                    'VALUE': match[2]
                });
            }
        }
        
        // CLEAR command
        if (line.startsWith('CLEAR ')) {
            const match = line.match(/^CLEAR\s+`([^`]+)`$/);
            if (match) {
                return this.createBlock('c4a_clear', {
                    'SELECTOR': match[1]
                });
            }
        }
        
        // SETVAR command
        if (line.startsWith('SETVAR ')) {
            const match = line.match(/^SETVAR\s+(\w+)\s*=\s*"([^"]*)"$/);
            if (match) {
                return this.createBlock('c4a_setvar', {
                    'NAME': match[1],
                    'VALUE': match[2]
                });
            }
        }
        
        // IF commands (simplified - only single line)
        if (line.startsWith('IF ')) {
            // IF EXISTS
            const existsMatch = line.match(/^IF\s+\(EXISTS\s+`([^`]+)`\)\s+THEN\s+(.+?)(?:\s+ELSE\s+(.+))?$/);
            if (existsMatch) {
                if (existsMatch[3]) {
                    // Has ELSE
                    const block = this.createBlock('c4a_if_exists_else', {
                        'SELECTOR': existsMatch[1]
                    });
                    // Parse then and else commands - simplified for now
                    return block;
                } else {
                    // No ELSE
                    const block = this.createBlock('c4a_if_exists', {
                        'SELECTOR': existsMatch[1]
                    });
                    return block;
                }
            }
            
            // IF NOT EXISTS
            const notExistsMatch = line.match(/^IF\s+\(NOT\s+EXISTS\s+`([^`]+)`\)\s+THEN\s+(.+)$/);
            if (notExistsMatch) {
                const block = this.createBlock('c4a_if_not_exists', {
                    'SELECTOR': notExistsMatch[1]
                });
                return block;
            }
        }
        
        // Comments
        if (line.startsWith('#')) {
            return this.createBlock('c4a_comment', {
                'TEXT': line.substring(1).trim()
            });
        }
        
        // If we can't parse it, return null
        return null;
    }
    
    createBlock(type, fields = {}) {
        const block = document.createElement('block');
        block.setAttribute('type', type);
        
        // Add fields
        for (const [name, value] of Object.entries(fields)) {
            const field = document.createElement('field');
            field.setAttribute('name', name);
            field.textContent = value;
            block.appendChild(field);
        }
        
        return block;
    }
}