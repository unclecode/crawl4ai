class ScriptBuilder {
  constructor() {
    this.mode = 'recording';
    this.isRecording = false;
    this.isPaused = false;
    this.rawEvents = [];
    this.groupedEvents = [];
    this.startTime = 0;
    this.lastEventTime = 0;
    this.toolbar = null;
    this.keyBuffer = [];
    this.keyBufferTimeout = null;
    this.scrollAccumulator = { direction: null, amount: 0, startTime: 0 };
    this.processedEventIndices = new Set();
    this.outputFormat = 'js'; // 'js' or 'c4a'
    this.timelineModal = null;
    this.recordingIndicator = null;
  }

  start() {
    // Don't start recording immediately, just show the toolbar
    this.createToolbar();
    this.showStartScreen();
  }
  
  showStartScreen() {
    const toolbarContent = this.toolbar.querySelector('.c4ai-toolbar-content');
    toolbarContent.innerHTML = `
      <div class="c4ai-toolbar-status">
        <div class="c4ai-status-item">
          <span class="c4ai-status-label">Script Builder</span>
          <span class="c4ai-status-value">Ready</span>
        </div>
      </div>
      <div class="c4ai-toolbar-hint" id="c4ai-script-hint">
        Click "Start Recording" to begin capturing your actions. <span style="color: #ff3c74; font-size: 11px;">(Alpha - May contain bugs)</span>
      </div>
      <div class="c4ai-toolbar-actions c4ai-start-actions">
        <button id="c4ai-start-recording" class="c4ai-action-btn c4ai-primary-btn">
          <span>🔴</span> Start Recording
        </button>
        <button id="c4ai-saved-flows" class="c4ai-action-btn c4ai-secondary-btn">
          <span>📂</span> Saved Flows
        </button>
      </div>
    `;
    
    // Add event listeners
    document.getElementById('c4ai-start-recording').addEventListener('click', () => this.startRecording());
    document.getElementById('c4ai-saved-flows').addEventListener('click', () => this.showSavedFlows());
  }
  
  startRecording() {
    this.isRecording = true;
    this.startTime = Date.now();
    this.lastEventTime = this.startTime;
    this.createRecordingIndicator();
    this.injectEventCapture();
    
    // Update toolbar to show recording controls
    const toolbarContent = this.toolbar.querySelector('.c4ai-toolbar-content');
    toolbarContent.innerHTML = `
      <div class="c4ai-toolbar-status">
        <div class="c4ai-status-item">
          <span class="c4ai-status-label">Actions:</span>
          <span class="c4ai-status-value" id="c4ai-action-count">0</span>
        </div>
        <div class="c4ai-status-item">
          <span class="c4ai-status-label">Format:</span>
          <select id="c4ai-output-format" class="c4ai-format-select">
            <option value="js">JavaScript</option>
            <option value="c4a">C4A Script</option>
          </select>
        </div>
      </div>
      <div class="c4ai-toolbar-hint" id="c4ai-script-hint">
        Recording your actions... Click, type, and scroll to build your script.
      </div>
      <div class="c4ai-toolbar-actions c4ai-recording-actions">
        <button id="c4ai-add-wait" class="c4ai-action-btn c4ai-secondary-btn">
          <span class="c4ai-wait-icon">⏱</span> Add Wait
        </button>
        <button id="c4ai-pause-recording" class="c4ai-action-btn c4ai-secondary-btn">
          <span class="c4ai-pause-icon">⏸</span> Pause
        </button>
        <button id="c4ai-stop-generate" class="c4ai-action-btn c4ai-primary-btn">
          <span class="c4ai-generate-icon">⚡</span> Stop & Generate
        </button>
        <button id="c4ai-saved-flows" class="c4ai-action-btn c4ai-secondary-btn">
          <span>📂</span> Saved Flows
        </button>
      </div>
    `;
    
    // Re-add event listeners
    document.getElementById('c4ai-pause-recording').addEventListener('click', () => this.togglePause());
    document.getElementById('c4ai-stop-generate').addEventListener('click', () => this.stopAndGenerate());
    document.getElementById('c4ai-add-wait').addEventListener('click', () => this.showWaitDialog());
    document.getElementById('c4ai-saved-flows').addEventListener('click', () => this.showSavedFlows());
    document.getElementById('c4ai-output-format').addEventListener('change', (e) => {
      this.outputFormat = e.target.value;
    });
    
    this.updateToolbar();
  }

  stop() {
    this.isRecording = false;
    this.removeEventCapture();
    this.toolbar?.remove();
    this.recordingIndicator?.remove();
    this.timelineModal?.remove();
    this.rawEvents = [];
    this.groupedEvents = [];
    this.processedEventIndices.clear();
  }

  createRecordingIndicator() {
    this.recordingIndicator = document.createElement('div');
    this.recordingIndicator.className = 'c4ai-recording-indicator';
    this.recordingIndicator.innerHTML = `
      <div class="c4ai-recording-dot"></div>
      <span>Recording</span>
    `;
    document.body.appendChild(this.recordingIndicator);
  }

  createToolbar() {
    this.toolbar = document.createElement('div');
    this.toolbar.className = 'c4ai-script-toolbar';
    this.toolbar.innerHTML = `
      <div class="c4ai-toolbar-titlebar">
        <div class="c4ai-titlebar-dots">
          <button class="c4ai-dot c4ai-dot-close" id="c4ai-script-close"></button>
          <button class="c4ai-dot c4ai-dot-minimize"></button>
          <button class="c4ai-dot c4ai-dot-maximize"></button>
        </div>
        <img src="${chrome.runtime.getURL('icons/icon-16.png')}" class="c4ai-titlebar-icon" alt="Crawl4AI">
        <div class="c4ai-titlebar-title">Crawl4AI Script Builder <span style="color: #ff3c74; font-size: 10px; margin-left: 8px;">(ALPHA)</span></div>
      </div>
      <div class="c4ai-toolbar-content" id="c4ai-toolbar-content">
        <!-- Content will be dynamically updated -->
      </div>
    `;
    document.body.appendChild(this.toolbar);

    // Add close button listener
    document.getElementById('c4ai-script-close').addEventListener('click', () => this.stop());

    // Make toolbar draggable
    window.C4AI_Utils.makeDraggable(this.toolbar);
  }

  showStartScreen() {
    const content = document.getElementById('c4ai-toolbar-content');
    content.innerHTML = `
      <div class="c4ai-start-screen">
        <div class="c4ai-welcome-message">
          <h3>Welcome to Script Builder</h3>
          <p>Record your actions to create automation scripts. <span style="color: #ff3c74;">Alpha version - may contain bugs</span></p>
        </div>
        <div class="c4ai-start-actions">
          <button id="c4ai-start-recording" class="c4ai-action-btn c4ai-primary-btn">
            <span>🔴</span> Start Recording
          </button>
          <button id="c4ai-saved-flows" class="c4ai-action-btn c4ai-secondary-btn">
            <span>📂</span> Saved Flows
          </button>
        </div>
      </div>
    `;
    
    // Add event listeners
    document.getElementById('c4ai-start-recording').addEventListener('click', () => this.startRecording());
    document.getElementById('c4ai-saved-flows').addEventListener('click', () => this.showSavedFlows());
  }

  showRecordingUI() {
    const content = document.getElementById('c4ai-toolbar-content');
    content.innerHTML = `
      <div class="c4ai-toolbar-status">
        <div class="c4ai-status-item">
          <span class="c4ai-status-label">Actions:</span>
          <span class="c4ai-status-value" id="c4ai-action-count">0</span>
        </div>
        <div class="c4ai-status-item">
          <span class="c4ai-status-label">Format:</span>
          <select id="c4ai-output-format" class="c4ai-format-select">
            <option value="js">JavaScript</option>
            <option value="c4a">C4A Script</option>
          </select>
        </div>
      </div>
      <div class="c4ai-toolbar-hint" id="c4ai-script-hint">
        Recording your actions... Click, type, and scroll to build your script.
      </div>
      <div class="c4ai-toolbar-actions">
        <button id="c4ai-saved-flows" class="c4ai-action-btn c4ai-secondary-btn">
          <span>📂</span> Saved Flows
        </button>
        <button id="c4ai-add-wait" class="c4ai-action-btn c4ai-secondary-btn">
          <span class="c4ai-wait-icon">⏱</span> Add Wait
        </button>
        <button id="c4ai-pause-recording" class="c4ai-action-btn c4ai-pause-btn">
          <span class="c4ai-pause-icon">⏸</span> Pause
        </button>
        <button id="c4ai-stop-generate" class="c4ai-action-btn c4ai-primary-btn">
          <span class="c4ai-generate-icon">⚡</span> Stop & Generate
        </button>
      </div>
    `;
    
    // Re-add event listeners
    document.getElementById('c4ai-pause-recording').addEventListener('click', () => this.togglePause());
    document.getElementById('c4ai-stop-generate').addEventListener('click', () => this.stopAndGenerate());
    document.getElementById('c4ai-add-wait').addEventListener('click', () => this.showWaitDialog());
    document.getElementById('c4ai-saved-flows').addEventListener('click', () => this.showSavedFlows());
    document.getElementById('c4ai-output-format').addEventListener('change', (e) => {
      this.outputFormat = e.target.value;
    });
  }


  togglePause() {
    this.isPaused = !this.isPaused;
    const pauseBtn = document.getElementById('c4ai-pause-recording');
    const recordingIndicator = document.querySelector('.c4ai-recording-indicator');
    
    if (this.isPaused) {
      pauseBtn.innerHTML = '<span class="c4ai-play-icon">▶</span> Resume';
      pauseBtn.classList.add('c4ai-paused');
      recordingIndicator.classList.add('c4ai-paused');
      document.getElementById('c4ai-script-hint').textContent = 'Recording paused. Click Resume to continue.';
    } else {
      pauseBtn.innerHTML = '<span class="c4ai-pause-icon">⏸</span> Pause';
      pauseBtn.classList.remove('c4ai-paused');
      recordingIndicator.classList.remove('c4ai-paused');
      document.getElementById('c4ai-script-hint').textContent = 'Recording your actions... Click, type, and scroll to build your script.';
    }
  }

  showWaitDialog() {
    const dialog = document.createElement('div');
    dialog.className = 'c4ai-wait-dialog';
    dialog.innerHTML = `
      <div class="c4ai-wait-dialog-content">
        <h4>Add Wait Command</h4>
        <div class="c4ai-wait-options">
          <label class="c4ai-wait-option">
            <input type="radio" name="wait-type" value="time" checked>
            <span>Wait for time (seconds)</span>
          </label>
          <label class="c4ai-wait-option">
            <input type="radio" name="wait-type" value="selector">
            <span>Wait for element</span>
          </label>
        </div>
        <div class="c4ai-wait-input" id="c4ai-wait-time-input">
          <input type="number" id="c4ai-wait-seconds" min="0.5" step="0.5" value="2" placeholder="Seconds">
        </div>
        <div class="c4ai-wait-input c4ai-hidden" id="c4ai-wait-selector-input">
          <p>Click on an element to wait for</p>
        </div>
        <div class="c4ai-wait-actions">
          <button id="c4ai-wait-cancel" class="c4ai-action-btn">Cancel</button>
          <button id="c4ai-wait-add" class="c4ai-action-btn c4ai-primary">Add Wait</button>
        </div>
      </div>
    `;
    document.body.appendChild(dialog);

    // Handle radio button changes
    dialog.querySelectorAll('input[name="wait-type"]').forEach(radio => {
      radio.addEventListener('change', (e) => {
        const timeInput = document.getElementById('c4ai-wait-time-input');
        const selectorInput = document.getElementById('c4ai-wait-selector-input');
        
        if (e.target.value === 'time') {
          timeInput.classList.remove('c4ai-hidden');
          selectorInput.classList.add('c4ai-hidden');
        } else {
          timeInput.classList.add('c4ai-hidden');
          selectorInput.classList.remove('c4ai-hidden');
          this.waitForElementSelection(dialog);
        }
      });
    });

    // Handle buttons
    document.getElementById('c4ai-wait-cancel').addEventListener('click', () => {
      dialog.remove();
    });

    document.getElementById('c4ai-wait-add').addEventListener('click', () => {
      const waitType = dialog.querySelector('input[name="wait-type"]:checked').value;
      
      if (waitType === 'time') {
        const seconds = parseFloat(document.getElementById('c4ai-wait-seconds').value) || 2;
        this.addWaitCommand('time', seconds);
        dialog.remove();
      }
    });
  }

  waitForElementSelection(dialog) {
    this.isPaused = true; // Pause recording during element selection
    
    const highlightBox = document.createElement('div');
    highlightBox.className = 'c4ai-highlight-box c4ai-wait-mode';
    document.body.appendChild(highlightBox);

    const handleMouseMove = (e) => {
      const element = document.elementFromPoint(e.clientX, e.clientY);
      if (element && !this.isOurElement(element)) {
        this.highlightElement(element, highlightBox);
      }
    };

    const handleClick = (e) => {
      const element = e.target;
      if (this.isOurElement(element)) return;

      e.preventDefault();
      e.stopPropagation();

      const selector = this.getElementSelector(element);
      this.addWaitCommand('selector', selector);

      // Cleanup
      document.removeEventListener('mousemove', handleMouseMove, true);
      document.removeEventListener('click', handleClick, true);
      highlightBox.remove();
      dialog.remove();
      this.isPaused = false;
    };

    document.addEventListener('mousemove', handleMouseMove, true);
    document.addEventListener('click', handleClick, true);
  }

  addWaitCommand(type, value) {
    const waitEvent = {
      type: 'WAIT',
      waitType: type,
      value: value,
      time: (Date.now() - this.startTime) / 1000
    };

    this.groupedEvents.push(waitEvent);
    this.updateToolbar();
  }

  highlightElement(element, highlightBox) {
    if (!highlightBox) {
      highlightBox = document.querySelector('.c4ai-highlight-box');
    }
    
    const rect = element.getBoundingClientRect();
    highlightBox.style.display = 'block';
    highlightBox.style.top = `${rect.top + window.scrollY}px`;
    highlightBox.style.left = `${rect.left + window.scrollX}px`;
    highlightBox.style.width = `${rect.width}px`;
    highlightBox.style.height = `${rect.height}px`;
  }

  isOurElement(element) {
    return window.C4AI_Utils.isOurElement(element);
  }

  getElementSelector(element) {
    return window.C4AI_Utils.getElementSelector(element);
  }

  injectEventCapture() {
    // Use content script context instead of injecting inline script
    if (window.__c4aiScriptRecordingActive) return;
    window.__c4aiScriptRecordingActive = true;
    
    const captureEvent = (type, event) => {
      // Skip events from our own UI
      if (event.target.classList && 
          (event.target.classList.contains('c4ai-script-toolbar') ||
           event.target.closest('.c4ai-script-toolbar') ||
           event.target.classList.contains('c4ai-wait-dialog') ||
           event.target.closest('.c4ai-wait-dialog') ||
           event.target.classList.contains('c4ai-timeline-modal') ||
           event.target.closest('.c4ai-timeline-modal'))) {
        return;
      }
      
      const data = {
        type: type,
        timestamp: Date.now(),
        targetTag: event.target.tagName,
        targetId: event.target.id,
        targetClass: event.target.className,
        targetSelector: this.getElementSelector(event.target),
        targetType: event.target.type
      };
      
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
          data.metaKey = event.metaKey; // Add meta key support
          break;
        case 'input':
        case 'change':
          // Check if it's a contenteditable element
          if (event.target.contentEditable === 'true' || 
              event.target.getAttribute('contenteditable') === 'true') {
            data.value = event.target.textContent || event.target.innerText;
            data.isContentEditable = true;
          } else {
            data.value = event.target.value;
          }
          data.inputType = event.inputType;
          if (event.target.type === 'checkbox' || event.target.type === 'radio') {
            data.checked = event.target.checked;
          }
          if (event.target.tagName === 'SELECT') {
            data.selectedText = event.target.options[event.target.selectedIndex]?.text || '';
          }
          break;
        case 'scroll':
          // Capture which element was scrolled
          if (event.target === window || event.target === document || event.target === document.body) {
            data.isWindowScroll = true;
            data.scrollTop = window.scrollY;
            data.scrollLeft = window.scrollX;
          } else {
            data.isWindowScroll = false;
            data.scrollTop = event.target.scrollTop;
            data.scrollLeft = event.target.scrollLeft;
            data.scrollHeight = event.target.scrollHeight;
            data.scrollWidth = event.target.scrollWidth;
          }
          break;
        case 'wheel':
          data.deltaY = event.deltaY || 0;
          data.deltaX = event.deltaX || 0;
          // Check if the target element is scrollable
          const isScrollable = (el) => {
            const hasScrollableContent = el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth;
            const overflowY = window.getComputedStyle(el).overflowY;
            const overflowX = window.getComputedStyle(el).overflowX;
            const canScroll = (overflowY !== 'visible' && overflowY !== 'hidden') || 
                              (overflowX !== 'visible' && overflowX !== 'hidden');
            return hasScrollableContent && canScroll;
          };
          
          // Find the actual scrollable element
          let scrollTarget = event.target;
          while (scrollTarget && scrollTarget !== document.body) {
            if (isScrollable(scrollTarget)) {
              break;
            }
            scrollTarget = scrollTarget.parentElement;
          }
          
          if (scrollTarget && scrollTarget !== document.body && isScrollable(scrollTarget)) {
            data.isWindowScroll = false;
            data.scrollTop = scrollTarget.scrollTop;
            data.scrollLeft = scrollTarget.scrollLeft;
            data.targetSelector = this.getElementSelector(scrollTarget);
          } else {
            data.isWindowScroll = true;
            data.scrollTop = window.scrollY;
            data.scrollLeft = window.scrollX;
          }
          break;
      }
      
      // Handle the event directly instead of using postMessage
      if (this.isRecording && !this.isPaused) {
        this.handleRecordedEvent(data);
      }
    };
    
    // Store bound event handlers for later removal
    this.eventHandlers = {
      click: (e) => captureEvent('click', e),
      dblclick: (e) => captureEvent('dblclick', e),
      contextmenu: (e) => captureEvent('contextmenu', e),
      keydown: (e) => captureEvent('keydown', e),
      input: (e) => captureEvent('input', e),
      change: (e) => captureEvent('change', e),
      scroll: (e) => captureEvent('scroll', e)
    };
    
    // Add event listeners
    Object.entries(this.eventHandlers).forEach(([eventType, handler]) => {
      document.addEventListener(eventType, handler, true);
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
      this.removeEventCapture();
    });
  }

  removeEventCapture() {
    window.__c4aiScriptRecordingActive = false;
    
    // Remove event listeners if they exist
    if (this.eventHandlers) {
      Object.entries(this.eventHandlers).forEach(([eventType, handler]) => {
        document.removeEventListener(eventType, handler, true);
      });
      this.eventHandlers = null;
    }
  }

  handleRecordedEvent(event) {
    // Skip events from our own UI
    if (event.targetClass && typeof event.targetClass === 'string' && event.targetClass.includes('c4ai-')) return;

    // Add time since start
    event.timeSinceStart = (event.timestamp - this.startTime) / 1000;
    
    // Store raw event
    this.rawEvents.push(event);

    // Process event based on type
    if (event.type === 'keydown') {
      // Handle keyboard shortcuts (with modifier keys)
      if (event.metaKey || event.ctrlKey || event.altKey) {
        // Flush any pending keystrokes
        if (this.keyBuffer.length > 0) {
          this.flushKeyBuffer();
        }
        
        // Create keyboard shortcut command
        const command = this.eventToCommand(event);
        if (command) {
          this.groupedEvents.push(command);
          this.updateToolbar();
        }
      } else if (this.shouldGroupKeystrokes(event)) {
        // Regular typing
        this.keyBuffer.push(event);
        
        if (this.keyBufferTimeout) {
          clearTimeout(this.keyBufferTimeout);
        }
        
        this.keyBufferTimeout = setTimeout(() => {
          this.flushKeyBuffer();
          this.updateToolbar();
        }, 500);
      } else if (event.key === 'Delete' || event.key === 'Backspace') {
        // Handle Delete and Backspace as individual commands when not part of typing
        if (this.keyBuffer.length > 0) {
          this.flushKeyBuffer();
        }
        
        const command = this.eventToCommand(event);
        if (command) {
          this.groupedEvents.push(command);
          this.updateToolbar();
        }
      }
    } else if (event.type === 'scroll' || event.type === 'wheel') {
      this.handleScrollEvent(event);
    } else if (event.type === 'click' || event.type === 'dblclick' || event.type === 'contextmenu') {
      // Flush any pending keystrokes before click
      if (this.keyBuffer.length > 0) {
        this.flushKeyBuffer();
      }
      
      const command = this.eventToCommand(event);
      if (command) {
        this.groupedEvents.push(command);
        this.updateToolbar();
      }
    } else if (event.type === 'change') {
      // Handle select, checkbox, radio changes
      const tagName = event.targetTag?.toLowerCase();
      if (tagName === 'select' || 
          (tagName === 'input' && (event.targetType === 'checkbox' || event.targetType === 'radio'))) {
        const command = this.eventToCommand(event);
        if (command) {
          this.groupedEvents.push(command);
          this.updateToolbar();
        }
      }
    }
  }

  shouldGroupKeystrokes(event) {
    // Don't group if modifier keys are pressed (except shift for capitals)
    if (event.metaKey || event.ctrlKey || event.altKey) {
      return false;
    }
    
    return event.key && (
      event.key.length === 1 ||
      event.key === ' ' ||
      event.key === 'Enter' ||
      event.key === 'Tab' ||
      event.key === 'Backspace' ||
      event.key === 'Delete'
    );
  }

  flushKeyBuffer() {
    if (this.keyBuffer.length === 0) return;
    
    const text = this.keyBuffer.map(e => {
      switch(e.key) {
        case ' ': return ' ';
        case 'Enter': return '\\n';
        case 'Tab': return '\\t';
        case 'Backspace': return '';
        case 'Delete': return '';
        default: return e.key;
      }
    }).join('');
    
    if (text.length === 0) {
      this.keyBuffer = [];
      return;
    }
    
    const firstEvent = this.keyBuffer[0];
    const lastEvent = this.keyBuffer[this.keyBuffer.length - 1];
    
    // Check if this is a SET command pattern
    const firstKeystrokeIndex = this.rawEvents.indexOf(firstEvent);
    let commandType = 'TYPE';
    
    if (firstKeystrokeIndex > 0) {
      const prevEvent = this.rawEvents[firstKeystrokeIndex - 1];
      
      // Check for click before typing
      if (prevEvent && prevEvent.type === 'click' && 
          prevEvent.targetSelector === firstEvent.targetSelector) {
        commandType = 'SET';
      }
      
      // Check for Cmd+A or Ctrl+A (select all) before typing
      if (prevEvent && prevEvent.type === 'keydown' && 
          prevEvent.key === 'a' && (prevEvent.metaKey || prevEvent.ctrlKey) &&
          prevEvent.targetSelector === firstEvent.targetSelector) {
        commandType = 'SET';
      }
    }
    
    // Also check within the last few events for select-all pattern
    if (commandType === 'TYPE' && firstKeystrokeIndex > 1) {
      // Look back up to 3 events for select-all
      for (let i = Math.max(0, firstKeystrokeIndex - 3); i < firstKeystrokeIndex; i++) {
        const event = this.rawEvents[i];
        if (event && event.type === 'keydown' && 
            event.key === 'a' && (event.metaKey || event.ctrlKey) &&
            event.targetSelector === firstEvent.targetSelector) {
          commandType = 'SET';
          break;
        }
      }
    }
    
    this.groupedEvents.push({
      type: commandType,
      selector: firstEvent.targetSelector,
      value: text,
      time: firstEvent.timeSinceStart
    });
    
    this.keyBuffer = [];
  }

  handleScrollEvent(event) {
    const direction = event.deltaY > 0 ? 'DOWN' : 'UP';
    const amount = Math.abs(event.deltaY);
    
    // Remove previous scroll in same direction within 0.5s for the same element
    this.groupedEvents = this.groupedEvents.filter(e => 
      !(e.type === 'SCROLL' && 
        e.direction === direction && 
        e.selector === (event.targetSelector || 'window') &&
        parseFloat(e.time) > parseFloat(event.timeSinceStart) - 0.5)
    );
    
    this.groupedEvents.push({
      type: 'SCROLL',
      direction: direction,
      amount: amount,
      selector: event.targetSelector || 'window',
      isWindowScroll: event.isWindowScroll !== false,
      time: event.timeSinceStart
    });
    
    this.updateToolbar();
  }

  eventToCommand(event) {
    switch (event.type) {
      case 'click':
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
      case 'keydown':
        // Handle keyboard shortcuts
        if (event.metaKey || event.ctrlKey || event.altKey) {
          return {
            type: 'KEYBOARD_SHORTCUT',
            key: event.key,
            code: event.code,
            metaKey: event.metaKey,
            ctrlKey: event.ctrlKey,
            altKey: event.altKey,
            shiftKey: event.shiftKey,
            time: event.timeSinceStart
          };
        } else if (event.key === 'Delete' || event.key === 'Backspace') {
          // Handle Delete/Backspace as special keys
          return {
            type: 'KEY_PRESS',
            key: event.key,
            time: event.timeSinceStart
          };
        }
        break;
      case 'change':
        if (event.targetTag === 'SELECT') {
          return {
            type: 'SET',
            selector: event.targetSelector,
            value: event.value,
            time: event.timeSinceStart
          };
        } else if (event.targetType === 'checkbox' || event.targetType === 'radio') {
          return {
            type: 'CLICK',
            selector: event.targetSelector,
            time: event.timeSinceStart
          };
        }
        break;
    }
    return null;
  }

  updateToolbar() {
    const actionCount = document.getElementById('c4ai-action-count');
    if (actionCount) {
      actionCount.textContent = this.groupedEvents.length;
    }
  }

  stopAndGenerate() {
    // Flush any pending events
    if (this.keyBufferTimeout) {
      clearTimeout(this.keyBufferTimeout);
      this.flushKeyBuffer();
    }

    this.isRecording = false;
    this.recordingIndicator?.remove();
    this.showRecordingSummary();
  }

  showRecordingSummary() {
    // Update toolbar to show summary
    const toolbarContent = this.toolbar.querySelector('.c4ai-toolbar-content');
    
    toolbarContent.innerHTML = `
      <div class="c4ai-toolbar-status">
        <div class="c4ai-status-item">
          <span class="c4ai-status-label">Recording Complete</span>
          <span class="c4ai-status-value">${this.groupedEvents.length} actions</span>
        </div>
      </div>
      <div class="c4ai-toolbar-hint" id="c4ai-script-hint">
        Recording stopped. You can replay, save, or generate code.
      </div>
      <div class="c4ai-toolbar-actions c4ai-summary-actions">
        <button id="c4ai-replay" class="c4ai-action-btn c4ai-replay-btn">
          <span>▶</span> Replay
        </button>
        <button id="c4ai-save-flow" class="c4ai-action-btn c4ai-save-btn">
          <span>💾</span> Save Flow
        </button>
        <button id="c4ai-show-timeline" class="c4ai-action-btn c4ai-timeline-btn">
          <span>📋</span> Review & Generate
        </button>
        <button id="c4ai-record-again" class="c4ai-action-btn c4ai-record-btn">
          <span>🔄</span> Record Again
        </button>
      </div>
    `;

    // Add event listeners
    document.getElementById('c4ai-replay')?.addEventListener('click', () => this.replayRecording());
    document.getElementById('c4ai-save-flow')?.addEventListener('click', () => this.saveFlow());
    document.getElementById('c4ai-show-timeline')?.addEventListener('click', () => this.showTimeline());
    document.getElementById('c4ai-record-again')?.addEventListener('click', () => this.recordAgain());
  }

  showTimeline() {
    this.timelineModal = document.createElement('div');
    this.timelineModal.className = 'c4ai-timeline-modal';
    this.timelineModal.innerHTML = `
      <div class="c4ai-timeline-content">
        <div class="c4ai-timeline-header">
          <h2>Review Your Actions</h2>
          <button class="c4ai-close-modal" id="c4ai-close-timeline">✕</button>
        </div>
        <div class="c4ai-timeline-body">
          <div class="c4ai-timeline-controls">
            <button class="c4ai-action-btn" id="c4ai-select-all">Select All</button>
            <button class="c4ai-action-btn" id="c4ai-clear-all">Clear All</button>
          </div>
          <div class="c4ai-timeline-events" id="c4ai-timeline-events">
            ${this.renderTimelineEvents()}
          </div>
        </div>
        <div class="c4ai-timeline-footer">
          <select id="c4ai-final-format" class="c4ai-format-select">
            <option value="js" ${this.outputFormat === 'js' ? 'selected' : ''}>JavaScript</option>
            <option value="c4a" ${this.outputFormat === 'c4a' ? 'selected' : ''}>C4A Script</option>
          </select>
          <button class="c4ai-action-btn c4ai-download-btn" id="c4ai-download-script">
            <span>⬇</span> Generate & Download
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(this.timelineModal);

    // Event listeners
    document.getElementById('c4ai-close-timeline').addEventListener('click', () => {
      this.timelineModal.remove();
      // Don't stop the toolbar, just close the modal
    });

    document.getElementById('c4ai-select-all').addEventListener('click', () => {
      document.querySelectorAll('.c4ai-event-checkbox').forEach(cb => cb.checked = true);
    });

    document.getElementById('c4ai-clear-all').addEventListener('click', () => {
      document.querySelectorAll('.c4ai-event-checkbox').forEach(cb => cb.checked = false);
    });

    document.getElementById('c4ai-download-script').addEventListener('click', () => {
      this.generateAndDownload();
    });
  }

  renderTimelineEvents() {
    return this.groupedEvents.map((event, index) => {
      const detail = this.getEventDetail(event);
      return `
        <div class="c4ai-timeline-event">
          <input type="checkbox" class="c4ai-event-checkbox" id="event-${index}" checked>
          <label for="event-${index}" class="c4ai-event-label">
            <span class="c4ai-event-time">${event.time.toFixed(1)}s</span>
            <span class="c4ai-event-type">${event.type.replace(/_/g, ' ')}</span>
            <span class="c4ai-event-detail" title="${detail.replace(/"/g, '&quot;')}">${detail}</span>
          </label>
        </div>
      `;
    }).join('');
  }

  getEventDetail(event) {
    switch (event.type) {
      case 'CLICK':
      case 'DOUBLE_CLICK':
      case 'RIGHT_CLICK':
        return event.selector;
      case 'TYPE':
      case 'SET':
        return `${event.selector} = "${event.value.substring(0, 30)}${event.value.length > 30 ? '...' : ''}"`;
      case 'SCROLL':
        if (event.isWindowScroll || event.selector === 'window') {
          return `${event.direction} ${event.amount}px`;
        } else {
          return `${event.selector} ${event.direction} ${event.amount}px`;
        }
      case 'WAIT':
        return event.waitType === 'time' ? `${event.value}s` : event.value;
      case 'KEYBOARD_SHORTCUT':
        const keys = [];
        if (event.metaKey) keys.push('Cmd');
        if (event.ctrlKey) keys.push('Ctrl');
        if (event.altKey) keys.push('Alt');
        if (event.shiftKey) keys.push('Shift');
        keys.push(event.key.toUpperCase());
        return keys.join('+');
      case 'KEY_PRESS':
        return event.key;
      default:
        return '';
    }
  }

  generateAndDownload() {
    const format = document.getElementById('c4ai-final-format').value;
    const selectedEvents = [];
    
    document.querySelectorAll('.c4ai-event-checkbox').forEach((cb, index) => {
      if (cb.checked && this.groupedEvents[index]) {
        selectedEvents.push(this.groupedEvents[index]);
      }
    });

    if (selectedEvents.length === 0) {
      alert('Please select at least one action');
      return;
    }

    const code = this.generateCode(selectedEvents, format);
    
    chrome.runtime.sendMessage({
      action: 'downloadScript',
      code: code,
      format: format,
      filename: `crawl4ai_script_${Date.now()}.py`
    }, (response) => {
      if (response && response.success) {
        this.timelineModal.remove();
        // Don't stop the toolbar after download
        // Show success message in toolbar
        document.getElementById('c4ai-script-hint').textContent = '✅ Script downloaded successfully!';
      }
    });
  }

  generateCode(events, format) {
    let scriptCode;
    
    if (format === 'js') {
      scriptCode = this.generateJavaScript(events);
    } else {
      scriptCode = this.generateC4AScript(events);
    }

    return this.generatePythonTemplate(scriptCode, format);
  }

  generateJavaScript(events) {
    const commands = events.map(event => {
      switch (event.type) {
        case 'CLICK':
          return `document.querySelector('${event.selector}').click();`;
        case 'DOUBLE_CLICK':
          return `const el = document.querySelector('${event.selector}');\nconst evt = new MouseEvent('dblclick', {bubbles: true});\nel.dispatchEvent(evt);`;
        case 'RIGHT_CLICK':
          return `const el = document.querySelector('${event.selector}');\nconst evt = new MouseEvent('contextmenu', {bubbles: true});\nel.dispatchEvent(evt);`;
        case 'TYPE':
          return this.generateTypeCode(event, 'append');
        case 'SET':
          return this.generateTypeCode(event, 'set');
        case 'SCROLL':
          if (event.isWindowScroll || event.selector === 'window') {
            return `window.scrollBy(0, ${event.direction === 'DOWN' ? event.amount : -event.amount});`;
          } else {
            const scrollAmount = event.direction === 'DOWN' ? event.amount : -event.amount;
            return `// Scroll element
const scrollEl = document.querySelector('${event.selector}');
if (scrollEl) {
  scrollEl.scrollTop += ${scrollAmount};
}`;
          }
        case 'WAIT':
          if (event.waitType === 'time') {
            return `await new Promise(resolve => setTimeout(resolve, ${event.value * 1000}));`;
          } else {
            return `// Wait for element: ${event.value}\nawait new Promise((resolve) => {\n  const checkElement = setInterval(() => {\n    if (document.querySelector('${event.value}')) {\n      clearInterval(checkElement);\n      resolve();\n    }\n  }, 100);\n  setTimeout(() => { clearInterval(checkElement); resolve(); }, 5000);\n});`;
          }
        case 'KEYBOARD_SHORTCUT':
          const modifiers = [];
          if (event.metaKey) modifiers.push('metaKey: true');
          if (event.ctrlKey) modifiers.push('ctrlKey: true');
          if (event.altKey) modifiers.push('altKey: true');
          if (event.shiftKey) modifiers.push('shiftKey: true');
          return `// Keyboard shortcut: ${this.getEventDetail(event)}\ndocument.dispatchEvent(new KeyboardEvent('keydown', {key: '${event.key}', ${modifiers.join(', ')}}));`;
        case 'KEY_PRESS':
          return `// Press ${event.key} key\ndocument.dispatchEvent(new KeyboardEvent('keydown', {key: '${event.key}'}));`;
        default:
          return `// Unknown action: ${event.type}`;
      }
    });

    return commands.join('\\n');
  }

  generateTypeCode(event, mode) {
    const value = event.value.replace(/'/g, "\\'").replace(/\n/g, '\\n');
    
    return `// ${mode === 'set' ? 'Set' : 'Type'} text
const el = document.querySelector('${event.selector}');
el.focus();
el.click();

// Check if contenteditable
if (el.contentEditable === 'true' || el.getAttribute('contenteditable') === 'true') {
  // Handle contenteditable element
  ${mode === 'set' ? 'el.textContent = "";' : ''}
  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(el);
  range.collapse(${mode === 'set' ? 'true' : 'false'});
  selection.removeAllRanges();
  selection.addRange(range);
  
  // Type each character
  '${value}'.split('').forEach(char => {
    document.execCommand('insertText', false, char);
    el.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: 'insertText', data: char}));
  });
} else if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
  // Handle input/textarea
  ${mode === 'set' ? `el.value = '${value}';` : `el.value += '${value}';`}
  el.dispatchEvent(new Event('input', {bubbles: true}));
  el.dispatchEvent(new Event('change', {bubbles: true}));
}
el.dispatchEvent(new Event('blur', {bubbles: true}));`;
    }

  generateC4AScript(events) {
    const commands = events.map(event => {
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
          if (event.isWindowScroll || event.selector === 'window') {
            return `SCROLL ${event.direction} ${event.amount}`;
          } else {
            return `SCROLL \`${event.selector}\` ${event.direction} ${event.amount}`;
          }
        case 'WAIT':
          if (event.waitType === 'time') {
            return `WAIT ${event.value}`;
          } else {
            return `WAIT \`${event.value}\` 5`;
          }
        case 'KEYBOARD_SHORTCUT':
          return `# Keyboard shortcut: ${this.getEventDetail(event)}\nKEY "${this.getEventDetail(event)}"`;
        case 'KEY_PRESS':
          return `KEY "${event.key}"`;
        default:
          return `# Unknown: ${event.type}`;
      }
    });

    return commands.join('\\n');
  }

  async replayRecording() {
    if (this.groupedEvents.length === 0) {
      alert('No actions to replay');
      return;
    }

    // Create debugger window instead of simple overlay
    this.createDebuggerWindow();
  }

  createReplayOverlay() {
    // Create visual indicator for current action
    this.replayIndicator = document.createElement('div');
    this.replayIndicator.className = 'c4ai-replay-indicator';
    this.replayIndicator.innerHTML = `
      <div class="c4ai-replay-content">
        <div class="c4ai-replay-header">
          <span class="c4ai-replay-icon">▶️</span>
          <span class="c4ai-replay-title">Replaying Actions</span>
        </div>
        <div class="c4ai-replay-progress">
          <div class="c4ai-replay-progress-bar" id="c4ai-replay-progress"></div>
        </div>
        <div class="c4ai-replay-status" id="c4ai-replay-status">
          Preparing...
        </div>
        <button class="c4ai-replay-stop" id="c4ai-replay-stop">Stop Replay</button>
      </div>
    `;
    document.body.appendChild(this.replayIndicator);
    
    // Create highlight overlay for showing where actions happen
    this.replayHighlight = document.createElement('div');
    this.replayHighlight.className = 'c4ai-replay-highlight';
    document.body.appendChild(this.replayHighlight);
    
    // Add stop button listener
    document.getElementById('c4ai-replay-stop').addEventListener('click', () => {
      this.stopReplay();
    });
  }

  async executeReplaySequence() {
    const events = this.groupedEvents;
    const totalEvents = events.length;
    
    for (let i = 0; i < totalEvents; i++) {
      if (!this.isReplaying) break;
      
      this.replayIndex = i;
      const event = events[i];
      const progress = ((i + 1) / totalEvents) * 100;
      
      // Update progress
      document.getElementById('c4ai-replay-progress').style.width = `${progress}%`;
      document.getElementById('c4ai-replay-status').textContent = 
        `Action ${i + 1}/${totalEvents}: ${this.getReplayActionDescription(event)}`;
      
      // Execute the action with visual feedback
      await this.executeReplayAction(event);
      
      // Wait between actions (except for the last one)
      if (i < totalEvents - 1) {
        const nextEvent = events[i + 1];
        const waitTime = this.calculateWaitTime(event, nextEvent);
        await this.wait(waitTime);
      }
    }
    
    // Replay complete
    this.stopReplay(true);
  }

  async executeReplayAction(event) {
    switch (event.type) {
      case 'CLICK':
      case 'DOUBLE_CLICK':
      case 'RIGHT_CLICK':
        await this.replayClickAction(event);
        break;
      case 'TYPE':
      case 'SET':
        await this.replayTypeAction(event);
        break;
      case 'SCROLL':
        await this.replayScrollAction(event);
        break;
      case 'WAIT':
        await this.replayWaitAction(event);
        break;
      case 'KEYBOARD_SHORTCUT':
        await this.replayKeyboardShortcut(event);
        break;
      case 'KEY_PRESS':
        await this.replayKeyPress(event);
        break;
    }
  }

  async replayClickAction(event) {
    const element = document.querySelector(event.selector);
    if (element) {
      // Highlight the element
      this.highlightReplayElement(element);
      
      // Show click animation
      this.showClickAnimation(element);
      
      // Wait a bit for visual effect
      await this.wait(300);
    } else {
      console.warn(`Element not found for selector: ${event.selector}`);
    }
  }

  async replayTypeAction(event) {
    const element = document.querySelector(event.selector);
    if (element) {
      // Highlight the input field
      this.highlightReplayElement(element);
      
      // Show typing animation
      const originalValue = element.value || '';
      
      if (event.type === 'SET') {
        // Clear and set new value with animation
        element.value = '';
        await this.wait(200);
        
        // Type character by character
        for (let i = 0; i < event.value.length; i++) {
          element.value = event.value.substring(0, i + 1);
          await this.wait(50); // Typing speed
        }
      } else {
        // Append text with typing animation
        const startLength = originalValue.length;
        for (let i = 0; i < event.value.length; i++) {
          element.value = originalValue + event.value.substring(0, i + 1);
          await this.wait(50);
        }
      }
    }
  }

  async replayScrollAction(event) {
    const scrollAmount = event.direction === 'DOWN' ? event.amount : -event.amount;
    
    // Animate scroll
    const startY = window.scrollY;
    const targetY = startY + scrollAmount;
    const duration = 500; // ms
    const startTime = Date.now();
    
    const animateScroll = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeProgress = this.easeInOut(progress);
      
      window.scrollTo(0, startY + (targetY - startY) * easeProgress);
      
      if (progress < 1 && this.isReplaying) {
        requestAnimationFrame(animateScroll);
      }
    };
    
    animateScroll();
    await this.wait(duration);
  }

  async replayWaitAction(event) {
    if (event.waitType === 'time') {
      document.getElementById('c4ai-replay-status').textContent = 
        `Waiting ${event.value} seconds...`;
      await this.wait(event.value * 1000);
    } else {
      // Wait for element
      document.getElementById('c4ai-replay-status').textContent = 
        `Waiting for element: ${event.value}`;
      await this.waitForElement(event.value, 5000); // 5 second timeout
    }
  }

  async replayKeyboardShortcut(event) {
    const keys = [];
    if (event.metaKey) keys.push('Cmd');
    if (event.ctrlKey) keys.push('Ctrl');
    if (event.altKey) keys.push('Alt');
    if (event.shiftKey) keys.push('Shift');
    keys.push(event.key.toUpperCase());
    
    // Show keyboard shortcut overlay
    this.showKeyboardOverlay(keys.join('+'));
    await this.wait(1000);
  }

  async replayKeyPress(event) {
    this.showKeyboardOverlay(event.key);
    await this.wait(500);
  }

  highlightReplayElement(element) {
    const rect = element.getBoundingClientRect();
    this.replayHighlight.style.display = 'block';
    this.replayHighlight.style.top = `${rect.top + window.scrollY}px`;
    this.replayHighlight.style.left = `${rect.left + window.scrollX}px`;
    this.replayHighlight.style.width = `${rect.width}px`;
    this.replayHighlight.style.height = `${rect.height}px`;
    
    // Fade out after a moment
    setTimeout(() => {
      this.replayHighlight.style.display = 'none';
    }, 800);
  }

  showClickAnimation(element) {
    const rect = element.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    const clickIndicator = document.createElement('div');
    clickIndicator.className = 'c4ai-click-indicator';
    clickIndicator.style.left = `${centerX}px`;
    clickIndicator.style.top = `${centerY}px`;
    document.body.appendChild(clickIndicator);
    
    // Remove after animation
    setTimeout(() => clickIndicator.remove(), 600);
  }

  showKeyboardOverlay(keys) {
    const overlay = document.createElement('div');
    overlay.className = 'c4ai-keyboard-overlay';
    overlay.textContent = keys;
    document.body.appendChild(overlay);
    
    // Fade in
    setTimeout(() => overlay.classList.add('visible'), 10);
    
    // Fade out and remove
    setTimeout(() => {
      overlay.classList.remove('visible');
      setTimeout(() => overlay.remove(), 300);
    }, 700);
  }

  getReplayActionDescription(event) {
    switch (event.type) {
      case 'CLICK': return `Click on ${event.selector}`;
      case 'DOUBLE_CLICK': return `Double-click on ${event.selector}`;
      case 'RIGHT_CLICK': return `Right-click on ${event.selector}`;
      case 'TYPE': return `Type "${event.value.substring(0, 20)}..."`;
      case 'SET': return `Set value in ${event.selector}`;
      case 'SCROLL': 
        if (event.isWindowScroll || event.selector === 'window') {
          return `Scroll ${event.direction} ${event.amount}px`;
        } else {
          return `Scroll ${event.selector} ${event.direction} ${event.amount}px`;
        }
      case 'WAIT': return event.waitType === 'time' ? 
        `Wait ${event.value}s` : `Wait for ${event.value}`;
      case 'KEYBOARD_SHORTCUT': return `Press ${this.getEventDetail(event)}`;
      case 'KEY_PRESS': return `Press ${event.key}`;
      default: return event.type;
    }
  }

  calculateWaitTime(currentEvent, nextEvent) {
    // Use timing from recording if available
    if (nextEvent.time && currentEvent.time) {
      const timeDiff = (nextEvent.time - currentEvent.time) * 1000; // Convert to ms
      // Cap wait time between 100ms and 2000ms for better replay experience
      return Math.min(Math.max(timeDiff, 100), 2000);
    }
    return 500; // Default wait time
  }

  async wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async waitForElement(selector, timeout = 5000) {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      const element = document.querySelector(selector);
      if (element) return element;
      await this.wait(100);
    }
    return null;
  }

  easeInOut(t) {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
  }

  stopReplay(completed = false) {
    this.isReplaying = false;
    
    // Remove replay UI
    this.replayIndicator?.remove();
    this.replayHighlight?.remove();
    
    // Update toolbar
    if (completed) {
      document.getElementById('c4ai-script-hint').textContent = '✅ Replay completed!';
    } else {
      document.getElementById('c4ai-script-hint').textContent = '⏹️ Replay stopped';
    }
    
    // Re-enable replay button
    const replayBtn = document.getElementById('c4ai-replay');
    if (replayBtn) {
      replayBtn.disabled = false;
      replayBtn.innerHTML = '<span>▶</span> Replay';
    }
  }

  createDebuggerWindow() {
    // Create debugger modal
    this.debuggerModal = document.createElement('div');
    this.debuggerModal.className = 'c4ai-debugger-modal';
    
    // Set initial position for dragging
    this.debuggerModal.style.position = 'fixed';
    this.debuggerModal.style.top = '50px';
    this.debuggerModal.style.right = '20px';
    
    this.debuggerModal.innerHTML = `
      <div class="c4ai-debugger-content">
        <div class="c4ai-debugger-header">
          <h2>Action Debugger <span style="color: #ff3c74; font-size: 12px;">(ALPHA)</span></h2>
          <button class="c4ai-close-modal" id="c4ai-close-debugger">✕</button>
        </div>
        <div class="c4ai-debugger-body">
          <div class="c4ai-debugger-controls">
            <button class="c4ai-debug-btn c4ai-run-btn" id="c4ai-debug-run" title="Run to end or next breakpoint">
              <span>▶</span> Run
            </button>
            <button class="c4ai-debug-btn c4ai-step-btn" id="c4ai-debug-step" title="Execute next action">
              <span>⏭</span> Step
            </button>
            <button class="c4ai-debug-btn c4ai-pause-btn" id="c4ai-debug-pause" disabled title="Pause execution">
              <span>⏸</span> Pause
            </button>
            <button class="c4ai-debug-btn c4ai-stop-btn" id="c4ai-debug-stop" title="Stop debugging">
              <span>⏹</span> Stop
            </button>
            <button class="c4ai-debug-btn c4ai-restart-btn" id="c4ai-debug-restart" title="Restart from beginning">
              <span>🔄</span> Restart
            </button>
          </div>
          <div class="c4ai-debugger-status">
            <span class="c4ai-debug-label">Status:</span>
            <span class="c4ai-debug-value" id="c4ai-debug-status">Ready</span>
          </div>
          <div class="c4ai-debugger-actions" id="c4ai-debugger-actions">
            ${this.renderDebuggerActions()}
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(this.debuggerModal);
    
    // Initialize debugger state
    this.debuggerState = {
      currentIndex: 0,
      isRunning: false,
      isPaused: false,
      breakpoints: new Set(),
      editedEvents: [...this.groupedEvents] // Copy for editing
    };
    
    // Create replay highlight element
    this.replayHighlight = document.createElement('div');
    this.replayHighlight.className = 'c4ai-replay-highlight';
    document.body.appendChild(this.replayHighlight);
    
    // Add event listeners
    this.attachDebuggerListeners();
    
    // Make debugger draggable by the header
    makeDraggableByHeader(this.debuggerModal);
  }

  renderDebuggerActions() {
    const events = this.debuggerState ? this.debuggerState.editedEvents : this.groupedEvents;
    return events.map((event, index) => {
      const detail = this.getEventDetail(event);
      return `
        <div class="c4ai-debug-action ${index === 0 ? 'c4ai-current' : ''}" data-index="${index}">
          <div class="c4ai-debug-action-left">
            <input type="checkbox" class="c4ai-breakpoint-checkbox" data-index="${index}" title="Toggle breakpoint">
            <span class="c4ai-action-number">${index + 1}</span>
            <span class="c4ai-action-indicator">➤</span>
          </div>
          <div class="c4ai-debug-action-content">
            <div class="c4ai-action-type">${event.type.replace(/_/g, ' ')}</div>
            <div class="c4ai-action-detail" contenteditable="true" data-index="${index}" data-field="detail">
              ${detail}
            </div>
          </div>
          <div class="c4ai-debug-action-right">
            <button class="c4ai-action-play" data-index="${index}" title="Execute this action">▶</button>
            <button class="c4ai-action-edit" data-index="${index}" title="Edit action">✏️</button>
            <button class="c4ai-action-delete" data-index="${index}" title="Delete action">🗑</button>
          </div>
        </div>
      `;
    }).join('');
  }

  attachDebuggerListeners() {
    // Control buttons
    document.getElementById('c4ai-debug-run').addEventListener('click', () => this.debugRun());
    document.getElementById('c4ai-debug-step').addEventListener('click', () => this.debugStep());
    document.getElementById('c4ai-debug-pause').addEventListener('click', () => this.debugPause());
    document.getElementById('c4ai-debug-stop').addEventListener('click', () => this.debugStop());
    document.getElementById('c4ai-debug-restart').addEventListener('click', () => this.debugRestart());
    document.getElementById('c4ai-close-debugger').addEventListener('click', () => this.closeDebugger());
    
    // Breakpoint checkboxes
    document.querySelectorAll('.c4ai-breakpoint-checkbox').forEach(cb => {
      cb.addEventListener('change', (e) => {
        const index = parseInt(e.target.dataset.index);
        if (e.target.checked) {
          this.debuggerState.breakpoints.add(index);
        } else {
          this.debuggerState.breakpoints.delete(index);
        }
        this.updateBreakpointVisual(index, e.target.checked);
      });
    });
    
    // Play buttons
    document.querySelectorAll('.c4ai-action-play').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const index = parseInt(e.target.dataset.index);
        this.executeActionOnPage(this.debuggerState.editedEvents[index], index);
      });
    });
    
    // Delete buttons
    document.querySelectorAll('.c4ai-action-delete').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const index = parseInt(e.target.dataset.index);
        this.deleteDebugAction(index);
      });
    });
    
    // Edit buttons
    document.querySelectorAll('.c4ai-action-edit').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const index = parseInt(e.target.dataset.index);
        this.editDebugAction(index);
      });
    });
    
    // Inline editing
    document.querySelectorAll('.c4ai-action-detail[contenteditable]').forEach(elem => {
      elem.addEventListener('blur', (e) => {
        const index = parseInt(e.target.dataset.index);
        this.updateActionDetail(index, e.target.textContent);
      });
    });
  }

  async debugRun() {
    this.debuggerState.isRunning = true;
    this.debuggerState.isPaused = false;
    this.updateDebugControls();
    this.updateDebugStatus('Running...');
    
    const startIndex = this.debuggerState.currentIndex;
    const events = this.debuggerState.editedEvents;
    
    for (let i = startIndex; i < events.length; i++) {
      if (!this.debuggerState.isRunning || this.debuggerState.isPaused) break;
      
      // Update current action
      this.setCurrentAction(i);
      
      // Execute the action
      await this.executeDebugAction(events[i], i);
      
      // Check for breakpoint on next action
      if (i < events.length - 1 && this.debuggerState.breakpoints.has(i + 1)) {
        this.debuggerState.currentIndex = i + 1;
        this.debugPause();
        this.updateDebugStatus(`Stopped at breakpoint ${i + 2}`);
        break;
      }
      
      this.debuggerState.currentIndex = i + 1;
    }
    
    if (this.debuggerState.currentIndex >= events.length) {
      this.debugStop(true);
    }
  }

  async debugStep() {
    if (this.debuggerState.currentIndex >= this.debuggerState.editedEvents.length) {
      this.updateDebugStatus('End of actions');
      return;
    }
    
    this.updateDebugStatus('Stepping...');
    this.setCurrentAction(this.debuggerState.currentIndex);
    
    await this.executeDebugAction(
      this.debuggerState.editedEvents[this.debuggerState.currentIndex],
      this.debuggerState.currentIndex
    );
    
    this.debuggerState.currentIndex++;
    
    if (this.debuggerState.currentIndex >= this.debuggerState.editedEvents.length) {
      this.updateDebugStatus('Completed');
    } else {
      this.updateDebugStatus('Ready');
    }
  }

  debugPause() {
    this.debuggerState.isPaused = true;
    this.debuggerState.isRunning = false;
    this.updateDebugControls();
    this.updateDebugStatus('Paused');
  }

  debugStop(completed = false) {
    this.debuggerState.isRunning = false;
    this.debuggerState.isPaused = false;
    this.updateDebugControls();
    
    if (completed) {
      this.updateDebugStatus('Completed');
    } else {
      this.updateDebugStatus('Stopped');
    }
  }

  debugRestart() {
    this.debuggerState.currentIndex = 0;
    this.debuggerState.isRunning = false;
    this.debuggerState.isPaused = false;
    this.setCurrentAction(0);
    this.updateDebugControls();
    this.updateDebugStatus('Ready');
  }

  closeDebugger() {
    this.debuggerModal?.remove();
    this.replayHighlight?.remove();
    this.debuggerState = null;
  }

  setCurrentAction(index) {
    // Remove previous current marker
    document.querySelectorAll('.c4ai-debug-action').forEach(elem => {
      elem.classList.remove('c4ai-current');
    });
    
    // Add current marker
    const currentElem = document.querySelector(`.c4ai-debug-action[data-index="${index}"]`);
    if (currentElem) {
      currentElem.classList.add('c4ai-current');
      
      // Better scrolling into view
      const scrollContainer = document.querySelector('.c4ai-debugger-actions');
      if (scrollContainer) {
        const containerRect = scrollContainer.getBoundingClientRect();
        const elemRect = currentElem.getBoundingClientRect();
        
        // Check if element is out of view
        if (elemRect.top < containerRect.top || elemRect.bottom > containerRect.bottom) {
          // Scroll to center the element
          const scrollTop = currentElem.offsetTop - scrollContainer.offsetTop - (scrollContainer.clientHeight / 2) + (currentElem.clientHeight / 2);
          scrollContainer.scrollTo({
            top: scrollTop,
            behavior: 'smooth'
          });
        }
      }
    }
    
    this.debuggerState.currentIndex = index;
  }

  updateDebugControls() {
    const runBtn = document.getElementById('c4ai-debug-run');
    const stepBtn = document.getElementById('c4ai-debug-step');
    const pauseBtn = document.getElementById('c4ai-debug-pause');
    
    if (this.debuggerState.isRunning) {
      runBtn.disabled = true;
      stepBtn.disabled = true;
      pauseBtn.disabled = false;
    } else {
      runBtn.disabled = false;
      stepBtn.disabled = false;
      pauseBtn.disabled = true;
    }
  }

  updateDebugStatus(status) {
    document.getElementById('c4ai-debug-status').textContent = status;
  }

  updateBreakpointVisual(index, hasBreakpoint) {
    const actionElem = document.querySelector(`.c4ai-debug-action[data-index="${index}"]`);
    if (actionElem) {
      if (hasBreakpoint) {
        actionElem.classList.add('has-breakpoint');
      } else {
        actionElem.classList.remove('has-breakpoint');
      }
    }
  }

  deleteDebugAction(index) {
    if (confirm('Delete this action?')) {
      this.debuggerState.editedEvents.splice(index, 1);
      this.debuggerState.breakpoints = new Set(
        [...this.debuggerState.breakpoints]
          .filter(bp => bp !== index)
          .map(bp => bp > index ? bp - 1 : bp)
      );
      
      // Re-render actions
      document.getElementById('c4ai-debugger-actions').innerHTML = this.renderDebuggerActions();
      this.attachDebuggerListeners();
      
      // Adjust current index if needed
      if (this.debuggerState.currentIndex > index) {
        this.debuggerState.currentIndex--;
      }
      this.setCurrentAction(Math.min(this.debuggerState.currentIndex, this.debuggerState.editedEvents.length - 1));
    }
  }

  editDebugAction(index) {
    const event = this.debuggerState.editedEvents[index];
    const dialog = document.createElement('div');
    dialog.className = 'c4ai-edit-dialog';
    dialog.innerHTML = `
      <div class="c4ai-edit-content">
        <h3>Edit Action</h3>
        <div class="c4ai-edit-field">
          <label>Type:</label>
          <select id="c4ai-edit-type">
            <option value="CLICK" ${event.type === 'CLICK' ? 'selected' : ''}>Click</option>
            <option value="TYPE" ${event.type === 'TYPE' ? 'selected' : ''}>Type</option>
            <option value="SET" ${event.type === 'SET' ? 'selected' : ''}>Set</option>
            <option value="SCROLL" ${event.type === 'SCROLL' ? 'selected' : ''}>Scroll</option>
            <option value="WAIT" ${event.type === 'WAIT' ? 'selected' : ''}>Wait</option>
          </select>
        </div>
        <div class="c4ai-edit-field">
          <label>Selector/Value:</label>
          <input type="text" id="c4ai-edit-value" value="${event.selector || event.value || ''}">
        </div>
        <div class="c4ai-edit-actions">
          <button id="c4ai-edit-save">Save</button>
          <button id="c4ai-edit-cancel">Cancel</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(dialog);
    
    document.getElementById('c4ai-edit-save').addEventListener('click', () => {
      const newType = document.getElementById('c4ai-edit-type').value;
      const newValue = document.getElementById('c4ai-edit-value').value;
      
      // Update event based on type
      this.debuggerState.editedEvents[index] = {
        ...event,
        type: newType,
        selector: ['CLICK', 'TYPE', 'SET'].includes(newType) ? newValue : event.selector,
        value: ['TYPE', 'SET', 'WAIT'].includes(newType) ? newValue : event.value
      };
      
      // Re-render
      document.getElementById('c4ai-debugger-actions').innerHTML = this.renderDebuggerActions();
      this.attachDebuggerListeners();
      dialog.remove();
    });
    
    document.getElementById('c4ai-edit-cancel').addEventListener('click', () => {
      dialog.remove();
    });
  }

  async executeDebugAction(event, index) {
    this.updateDebugStatus(`Executing: ${this.getEventDetail(event)}`);
    
    // Execute the action on the page
    await this.executeActionOnPage(event, index);
    
    // Add small delay between actions for visibility
    await this.wait(300);
  }

  async executeActionOnPage(event, index) {
    try {
      // Set current action for visual feedback
      this.setCurrentAction(index);
      
      switch (event.type) {
        case 'CLICK':
        case 'DOUBLE_CLICK':
        case 'RIGHT_CLICK':
          await this.executeClick(event);
          break;
        case 'TYPE':
        case 'SET':
          await this.executeType(event);
          break;
        case 'SCROLL':
          await this.executeScroll(event);
          break;
        case 'WAIT':
          await this.executeWait(event);
          break;
        case 'KEYBOARD_SHORTCUT':
          await this.executeKeyboardShortcut(event);
          break;
        case 'KEY_PRESS':
          await this.executeKeyPress(event);
          break;
      }
      
      this.updateDebugStatus(`Executed: ${this.getEventDetail(event)}`);
    } catch (error) {
      console.error('Error executing action:', error);
      this.updateDebugStatus(`Error: ${error.message}`);
    }
  }

  async executeClick(event) {
    const element = document.querySelector(event.selector);
    if (!element) {
      throw new Error(`Element not found: ${event.selector}`);
    }
    
    // Highlight element briefly
    this.highlightReplayElement(element);
    
    // Create and dispatch the appropriate mouse event
    const eventType = {
      'CLICK': 'click',
      'DOUBLE_CLICK': 'dblclick',
      'RIGHT_CLICK': 'contextmenu'
    }[event.type];
    
    const mouseEvent = new MouseEvent(eventType, {
      view: window,
      bubbles: true,
      cancelable: true,
      buttons: event.type === 'RIGHT_CLICK' ? 2 : 1
    });
    
    element.dispatchEvent(mouseEvent);
    
    // Also try clicking for better compatibility
    if (event.type === 'CLICK' && typeof element.click === 'function') {
      element.click();
    }
  }

  async executeType(event) {
    const element = document.querySelector(event.selector);
    if (!element) {
      throw new Error(`Element not found: ${event.selector}`);
    }
    
    // Highlight element
    this.highlightReplayElement(element);
    
    // Make sure element is visible and focused
    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    await this.wait(100);
    
    // Focus the element
    element.focus();
    element.click(); // Some inputs need a click to properly focus
    
    // Check if it's a contenteditable element
    const isContentEditable = element.contentEditable === 'true' || 
                             element.getAttribute('contenteditable') === 'true' ||
                             element.closest('[contenteditable="true"]');
    
    if (isContentEditable) {
      // Handle contenteditable elements
      await this.typeInContentEditable(element, event);
    } else if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
      // Handle regular input/textarea elements
      await this.typeInInput(element, event);
    } else {
      // Try contenteditable approach for other elements
      await this.typeInContentEditable(element, event);
    }
  }

  async typeInInput(element, event) {
    if (event.type === 'SET') {
      // Clear and set value
      element.value = '';
      
      // Dispatch events
      element.dispatchEvent(new Event('focus', { bubbles: true }));
      element.dispatchEvent(new Event('input', { bubbles: true }));
      
      // Type character by character for realism
      for (let i = 0; i < event.value.length; i++) {
        element.value = event.value.substring(0, i + 1);
        
        // Dispatch multiple events for better compatibility
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new InputEvent('input', { 
          bubbles: true,
          cancelable: true,
          inputType: 'insertText',
          data: event.value[i]
        }));
        
        await this.wait(30);
      }
    } else {
      // TYPE - append to existing value
      const startValue = element.value || '';
      for (let i = 0; i < event.value.length; i++) {
        element.value = startValue + event.value.substring(0, i + 1);
        
        // Dispatch multiple events
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new InputEvent('input', { 
          bubbles: true,
          cancelable: true,
          inputType: 'insertText',
          data: event.value[i]
        }));
        
        await this.wait(30);
      }
    }
    
    // Dispatch change and blur events
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dispatchEvent(new Event('blur', { bubbles: true }));
  }

  async typeInContentEditable(element, event) {
    // Focus and prepare the element
    element.focus();
    
    // Create a range and selection
    const selection = window.getSelection();
    const range = document.createRange();
    
    if (event.type === 'SET') {
      // Clear existing content
      element.textContent = '';
      
      // Set cursor at the beginning
      range.selectNodeContents(element);
      range.collapse(true);
      selection.removeAllRanges();
      selection.addRange(range);
    } else {
      // Move cursor to the end for TYPE
      range.selectNodeContents(element);
      range.collapse(false);
      selection.removeAllRanges();
      selection.addRange(range);
    }
    
    // Type each character using keyboard events
    for (let i = 0; i < event.value.length; i++) {
      const char = event.value[i];
      
      // Dispatch keydown
      const keydownEvent = new KeyboardEvent('keydown', {
        key: char,
        char: char,
        keyCode: char.charCodeAt(0),
        which: char.charCodeAt(0),
        bubbles: true,
        cancelable: true
      });
      element.dispatchEvent(keydownEvent);
      
      // Insert the character
      if (!keydownEvent.defaultPrevented) {
        document.execCommand('insertText', false, char);
      }
      
      // Dispatch keyup
      const keyupEvent = new KeyboardEvent('keyup', {
        key: char,
        char: char,
        keyCode: char.charCodeAt(0),
        which: char.charCodeAt(0),
        bubbles: true,
        cancelable: true
      });
      element.dispatchEvent(keyupEvent);
      
      // Dispatch input event
      element.dispatchEvent(new InputEvent('input', {
        bubbles: true,
        cancelable: true,
        inputType: 'insertText',
        data: char
      }));
      
      await this.wait(30);
    }
    
    // Dispatch blur event
    element.dispatchEvent(new Event('blur', { bubbles: true }));
  }

  async executeScroll(event) {
    const scrollAmount = event.direction === 'DOWN' ? event.amount : -event.amount;
    const duration = 300;
    const startTime = Date.now();
    
    if (event.isWindowScroll || event.selector === 'window') {
      // Window scroll
      const startY = window.scrollY;
      const targetY = startY + scrollAmount;
      
      const animateScroll = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = this.easeInOut(progress);
        
        window.scrollTo(0, startY + (targetY - startY) * easeProgress);
        
        if (progress < 1) {
          requestAnimationFrame(animateScroll);
        }
      };
      
      animateScroll();
    } else {
      // Element scroll
      const element = document.querySelector(event.selector);
      if (!element) {
        throw new Error(`Scrollable element not found: ${event.selector}`);
      }
      
      // Highlight the scrollable element
      this.highlightReplayElement(element);
      
      const startY = element.scrollTop;
      const targetY = startY + scrollAmount;
      
      const animateScroll = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = this.easeInOut(progress);
        
        element.scrollTop = startY + (targetY - startY) * easeProgress;
        
        if (progress < 1) {
          requestAnimationFrame(animateScroll);
        }
      };
      
      animateScroll();
    }
    
    await this.wait(duration);
  }

  async executeWait(event) {
    if (event.waitType === 'time') {
      await this.wait(event.value * 1000);
    } else {
      // Wait for element to appear
      const timeout = 5000;
      const startTime = Date.now();
      
      while (Date.now() - startTime < timeout) {
        const element = document.querySelector(event.value);
        if (element) {
          this.highlightReplayElement(element);
          return;
        }
        await this.wait(100);
      }
      
      throw new Error(`Element not found after ${timeout}ms: ${event.value}`);
    }
  }

  async executeKeyboardShortcut(event) {
    // Show keyboard overlay
    this.showKeyboardOverlay(this.getEventDetail(event));
    
    // Create and dispatch keyboard event
    const keyEvent = new KeyboardEvent('keydown', {
      key: event.key,
      code: event.code,
      ctrlKey: event.ctrlKey,
      metaKey: event.metaKey,
      altKey: event.altKey,
      shiftKey: event.shiftKey,
      bubbles: true,
      cancelable: true
    });
    
    document.activeElement.dispatchEvent(keyEvent);
    
    // Some shortcuts need keyup as well
    const keyUpEvent = new KeyboardEvent('keyup', {
      key: event.key,
      code: event.code,
      ctrlKey: event.ctrlKey,
      metaKey: event.metaKey,
      altKey: event.altKey,
      shiftKey: event.shiftKey,
      bubbles: true,
      cancelable: true
    });
    
    document.activeElement.dispatchEvent(keyUpEvent);
    
    await this.wait(500);
  }

  async executeKeyPress(event) {
    this.showKeyboardOverlay(event.key);
    
    const activeElement = document.activeElement;
    
    if (event.key === 'Delete' || event.key === 'Backspace') {
      // Handle delete/backspace on input elements
      if (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA') {
        const start = activeElement.selectionStart;
        const end = activeElement.selectionEnd;
        
        if (start !== end) {
          // Delete selection
          activeElement.value = activeElement.value.substring(0, start) + activeElement.value.substring(end);
          activeElement.selectionStart = activeElement.selectionEnd = start;
        } else if (event.key === 'Backspace' && start > 0) {
          // Delete character before cursor
          activeElement.value = activeElement.value.substring(0, start - 1) + activeElement.value.substring(start);
          activeElement.selectionStart = activeElement.selectionEnd = start - 1;
        } else if (event.key === 'Delete' && start < activeElement.value.length) {
          // Delete character after cursor
          activeElement.value = activeElement.value.substring(0, start) + activeElement.value.substring(start + 1);
        }
        
        activeElement.dispatchEvent(new Event('input', { bubbles: true }));
      }
    } else {
      // Regular key press
      const keyEvent = new KeyboardEvent('keydown', {
        key: event.key,
        bubbles: true,
        cancelable: true
      });
      
      activeElement.dispatchEvent(keyEvent);
    }
    
    await this.wait(300);
  }

  async saveFlow() {
    // Get flow name from user
    const flowName = prompt('Enter a name for this flow:');
    if (!flowName || !flowName.trim()) {
      return;
    }

    // Get current domain
    const domain = window.location.hostname;
    
    // Create flow object
    const flow = {
      id: Date.now().toString(),
      name: flowName.trim(),
      domain: domain,
      url: window.location.href,
      events: this.groupedEvents,
      createdAt: new Date().toISOString(),
      outputFormat: this.outputFormat
    };

    // Get existing flows for this domain
    const storageKey = `c4ai_flows_${domain}`;
    chrome.storage.local.get(storageKey, (result) => {
      const flows = result[storageKey] || [];
      flows.push(flow);
      
      // Save updated flows
      chrome.storage.local.set({ [storageKey]: flows }, () => {
        if (chrome.runtime.lastError) {
          alert('Failed to save flow: ' + chrome.runtime.lastError.message);
        } else {
          alert(`Flow "${flowName}" saved successfully!`);
          // Update hint text
          document.getElementById('c4ai-script-hint').textContent = `✅ Flow "${flowName}" saved!`;
        }
      });
    });
  }

  showSavedFlows() {
    const domain = window.location.hostname;
    const storageKey = `c4ai_flows_${domain}`;
    
    chrome.storage.local.get(storageKey, (result) => {
      const flows = result[storageKey] || [];
      
      // Create modal
      const modal = document.createElement('div');
      modal.className = 'c4ai-saved-flows-modal';
      modal.innerHTML = `
        <div class="c4ai-saved-flows-content">
          <div class="c4ai-saved-flows-header">
            <h2>Saved Flows for ${domain}</h2>
            <button class="c4ai-close-modal" id="c4ai-close-flows">✕</button>
          </div>
          <div class="c4ai-saved-flows-body">
            ${flows.length === 0 ? 
              '<p class="c4ai-no-flows">No saved flows for this domain yet. Record and save your first flow!</p>' :
              `<div class="c4ai-flows-list">
                ${flows.map(flow => `
                  <div class="c4ai-flow-item" data-flow-id="${flow.id}">
                    <div class="c4ai-flow-info">
                      <h3>${flow.name}</h3>
                      <p class="c4ai-flow-meta">
                        <span>${flow.events.length} actions</span>
                        <span>•</span>
                        <span>${new Date(flow.createdAt).toLocaleDateString()}</span>
                      </p>
                    </div>
                    <div class="c4ai-flow-actions">
                      <button class="c4ai-action-btn c4ai-load-flow-btn" data-flow-id="${flow.id}">
                        <span>▶</span> Load
                      </button>
                      <button class="c4ai-action-btn c4ai-delete-flow-btn" data-flow-id="${flow.id}">
                        <span>🗑</span>
                      </button>
                    </div>
                  </div>
                `).join('')}
              </div>`
            }
          </div>
        </div>
      `;
      
      document.body.appendChild(modal);
      
      // Add event listeners
      document.getElementById('c4ai-close-flows').addEventListener('click', () => {
        modal.remove();
      });
      
      // Load flow buttons
      modal.querySelectorAll('.c4ai-load-flow-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const flowId = e.target.closest('button').dataset.flowId;
          const flow = flows.find(f => f.id === flowId);
          if (flow) {
            this.loadFlow(flow);
            modal.remove();
          }
        });
      });
      
      // Delete flow buttons
      modal.querySelectorAll('.c4ai-delete-flow-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const flowId = e.target.closest('button').dataset.flowId;
          if (confirm('Are you sure you want to delete this flow?')) {
            this.deleteFlow(flowId);
            modal.remove();
            this.showSavedFlows(); // Refresh the modal
          }
        });
      });
    });
  }

  loadFlow(flow) {
    // Stop any current recording
    this.isRecording = false;
    this.removeEventCapture();
    
    // Load the flow's events
    this.groupedEvents = [...flow.events];
    this.outputFormat = flow.outputFormat || 'js';
    
    // Show the recording summary UI
    this.showRecordingSummary();
    
    // Update hint
    document.getElementById('c4ai-script-hint').textContent = `Loaded flow: "${flow.name}"`;
  }

  deleteFlow(flowId) {
    const domain = window.location.hostname;
    const storageKey = `c4ai_flows_${domain}`;
    
    chrome.storage.local.get(storageKey, (result) => {
      const flows = result[storageKey] || [];
      const updatedFlows = flows.filter(f => f.id !== flowId);
      
      chrome.storage.local.set({ [storageKey]: updatedFlows }, () => {
        if (chrome.runtime.lastError) {
          alert('Failed to delete flow: ' + chrome.runtime.lastError.message);
        }
      });
    });
  }

  recordAgain() {
    // Show confirmation dialog
    if (!confirm('Are you sure you want to start a new recording? This will clear the current recording.')) {
      return;
    }
    
    // Clear current recording and start fresh
    this.groupedEvents = [];
    this.rawEvents = [];
    this.processedEventIndices.clear();
    this.keyBuffer = [];
    
    // Don't create a new toolbar, just update the existing one
    this.isRecording = true;
    this.startTime = Date.now();
    this.lastEventTime = this.startTime;
    
    // Reset toolbar content to recording state
    const toolbarContent = this.toolbar.querySelector('.c4ai-toolbar-content');
    toolbarContent.innerHTML = `
      <div class="c4ai-toolbar-status">
        <div class="c4ai-status-item">
          <span class="c4ai-status-label">Actions:</span>
          <span class="c4ai-status-value" id="c4ai-action-count">0</span>
        </div>
        <div class="c4ai-status-item">
          <span class="c4ai-status-label">Format:</span>
          <select id="c4ai-output-format" class="c4ai-format-select">
            <option value="js">JavaScript</option>
            <option value="c4a">C4A Script</option>
          </select>
        </div>
      </div>
      <div class="c4ai-toolbar-hint" id="c4ai-script-hint">
        Recording your actions... Click, type, and scroll to build your script.
      </div>
      <div class="c4ai-toolbar-actions">
        <button id="c4ai-saved-flows" class="c4ai-action-btn c4ai-flows-btn">
          <span>📂</span> Saved Flows
        </button>
        <button id="c4ai-add-wait" class="c4ai-action-btn c4ai-wait-btn">
          <span class="c4ai-wait-icon">⏱</span> Add Wait
        </button>
        <button id="c4ai-pause-recording" class="c4ai-action-btn c4ai-pause-btn">
          <span class="c4ai-pause-icon">⏸</span> Pause
        </button>
        <button id="c4ai-stop-generate" class="c4ai-action-btn c4ai-generate-btn">
          <span class="c4ai-generate-icon">⚡</span> Stop & Generate
        </button>
      </div>
    `;
    
    // Re-add event listeners
    document.getElementById('c4ai-pause-recording').addEventListener('click', () => this.togglePause());
    document.getElementById('c4ai-stop-generate').addEventListener('click', () => this.stopAndGenerate());
    document.getElementById('c4ai-add-wait').addEventListener('click', () => this.showWaitDialog());
    document.getElementById('c4ai-saved-flows').addEventListener('click', () => this.showSavedFlows());
    document.getElementById('c4ai-output-format').addEventListener('change', (e) => {
      this.outputFormat = e.target.value;
    });
    
    this.createRecordingIndicator();
    this.updateToolbar();
  }

  generatePythonTemplate(scriptCode, format) {
    const currentUrl = window.location.href;
    const timestamp = new Date().toISOString();
    
    if (format === 'js') {
      return `#!/usr/bin/env python3
"""
Generated by Crawl4AI Chrome Extension - Script Builder (ALPHA)
URL: ${currentUrl}
Generated: ${timestamp}
"""

import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# JavaScript code to execute
JS_SCRIPT = """
${scriptCode}
"""

async def run_automation():
    """Run the recorded automation script"""
    
    # Configure browser
    browser_config = BrowserConfig(
        headless=False,  # Set to True for headless mode
        verbose=True
    )
    
    # Configure crawler with JavaScript execution
    crawler_config = CrawlerRunConfig(
        js_code=JS_SCRIPT,
        wait_for="js:() => document.readyState === 'complete'",
        page_timeout=30000  # 30 seconds timeout
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="${currentUrl}",
            config=crawler_config
        )
        
        if result.success:
            print("✅ Automation completed successfully!")
            print(f"Final URL: {result.url}")
            # You can access the final HTML with result.html
            # Or extracted content with result.cleaned_html
        else:
            print("❌ Automation failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(run_automation())
`;
    } else {
      // C4A Script format
      return `#!/usr/bin/env python3
"""
Generated by Crawl4AI Chrome Extension - Script Builder (ALPHA)
URL: ${currentUrl}
Generated: ${timestamp}
"""

import asyncio
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai import JsonCssExtractionStrategy

# C4A Script commands
C4A_SCRIPT = """
${scriptCode}
"""

# Save the C4A script for reference
script_path = Path('automation_script.c4a')
with open(script_path, 'w') as f:
    f.write(C4A_SCRIPT)

print(f"💾 C4A Script saved to: {script_path}")
print("\\n📜 Generated C4A Script:")
print(C4A_SCRIPT)

# Note: To execute C4A scripts, you'll need to use the C4A Script compiler
# Example:
# from crawl4ai.script import C4ACompiler
# compiler = C4ACompiler()
# js_code = compiler.compile(C4A_SCRIPT)
# 
# Then use js_code in CrawlerRunConfig as shown in the JavaScript example above

print("\\n💡 To execute this C4A script, compile it to JavaScript first!")
`;
    }
  }
}

// Initialize
let schemaBuilder = null;
let scriptBuilder = null;

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.action) {
    case 'startSchemaCapture':
      if (!schemaBuilder) {
        schemaBuilder = new SchemaBuilder();
      }
      schemaBuilder.start();
      sendResponse({ success: true });
      break;

    case 'startScriptCapture':
      if (!scriptBuilder) {
        scriptBuilder = new ScriptBuilder();
      }
      scriptBuilder.start();
      sendResponse({ success: true });
      break;
      
    case 'stopCapture':
      if (schemaBuilder) {
        schemaBuilder.stop();
        schemaBuilder = null;
      }
      if (scriptBuilder) {
        scriptBuilder.stop();
        scriptBuilder = null;
      }
      sendResponse({ success: true });
      break;
      
    case 'generateCode':
      if (schemaBuilder) {
        const code = schemaBuilder.generateCode();
        schemaBuilder.showCodeModal(code);
      }
      sendResponse({ success: true });
      break;
  }
  
  return true;
});
