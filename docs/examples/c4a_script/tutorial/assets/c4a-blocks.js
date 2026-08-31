// C4A-Script Blockly Block Definitions
// This file defines all custom blocks for C4A-Script commands

// Color scheme for different block categories
const BlockColors = {
    NAVIGATION: '#1E88E5',    // Blue
    ACTIONS: '#43A047',       // Green  
    CONTROL: '#FB8C00',       // Orange
    VARIABLES: '#8E24AA',     // Purple
    WAIT: '#E53935',          // Red
    KEYBOARD: '#00ACC1',      // Cyan
    PROCEDURES: '#6A1B9A'     // Deep Purple
};

// Helper to create selector input with backticks
Blockly.Blocks['c4a_selector_input'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("`")
            .appendField(new Blockly.FieldTextInput("selector"), "SELECTOR")
            .appendField("`");
        this.setOutput(true, "Selector");
        this.setColour(BlockColors.ACTIONS);
        this.setTooltip("CSS selector for element");
    }
};

// ============================================
// NAVIGATION BLOCKS
// ============================================

Blockly.Blocks['c4a_go'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("GO")
            .appendField(new Blockly.FieldTextInput("https://example.com"), "URL");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.NAVIGATION);
        this.setTooltip("Navigate to URL");
    }
};

Blockly.Blocks['c4a_reload'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("RELOAD");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.NAVIGATION);
        this.setTooltip("Reload current page");
    }
};

Blockly.Blocks['c4a_back'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("BACK");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.NAVIGATION);
        this.setTooltip("Go back in browser history");
    }
};

Blockly.Blocks['c4a_forward'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("FORWARD");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.NAVIGATION);
        this.setTooltip("Go forward in browser history");
    }
};

// ============================================
// WAIT BLOCKS
// ============================================

Blockly.Blocks['c4a_wait_time'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("WAIT")
            .appendField(new Blockly.FieldNumber(1, 0), "SECONDS")
            .appendField("seconds");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.WAIT);
        this.setTooltip("Wait for specified seconds");
    }
};

Blockly.Blocks['c4a_wait_selector'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("WAIT for")
            .appendField("`")
            .appendField(new Blockly.FieldTextInput("selector"), "SELECTOR")
            .appendField("`")
            .appendField("max")
            .appendField(new Blockly.FieldNumber(10, 1), "TIMEOUT")
            .appendField("sec");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.WAIT);
        this.setTooltip("Wait for element to appear");
    }
};

Blockly.Blocks['c4a_wait_text'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("WAIT for text")
            .appendField(new Blockly.FieldTextInput("Loading complete"), "TEXT")
            .appendField("max")
            .appendField(new Blockly.FieldNumber(5, 1), "TIMEOUT")
            .appendField("sec");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.WAIT);
        this.setTooltip("Wait for text to appear on page");
    }
};

// ============================================
// MOUSE ACTION BLOCKS
// ============================================

Blockly.Blocks['c4a_click'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("CLICK")
            .appendField("`")
            .appendField(new Blockly.FieldTextInput("button"), "SELECTOR")
            .appendField("`");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.ACTIONS);
        this.setTooltip("Click on element");
    }
};

Blockly.Blocks['c4a_click_xy'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("CLICK at")
            .appendField("X:")
            .appendField(new Blockly.FieldNumber(100, 0), "X")
            .appendField("Y:")
            .appendField(new Blockly.FieldNumber(100, 0), "Y");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.ACTIONS);
        this.setTooltip("Click at coordinates");
    }
};

Blockly.Blocks['c4a_double_click'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("DOUBLE_CLICK")
            .appendField("`")
            .appendField(new Blockly.FieldTextInput(".item"), "SELECTOR")
            .appendField("`");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.ACTIONS);
        this.setTooltip("Double click on element");
    }
};

Blockly.Blocks['c4a_right_click'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("RIGHT_CLICK")
            .appendField("`")
            .appendField(new Blockly.FieldTextInput("#menu"), "SELECTOR")
            .appendField("`");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.ACTIONS);
        this.setTooltip("Right click on element");
    }
};

Blockly.Blocks['c4a_move'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("MOVE to")
            .appendField("X:")
            .appendField(new Blockly.FieldNumber(500, 0), "X")
            .appendField("Y:")
            .appendField(new Blockly.FieldNumber(300, 0), "Y");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.ACTIONS);
        this.setTooltip("Move mouse to position");
    }
};

Blockly.Blocks['c4a_drag'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("DRAG from")
            .appendField("X:")
            .appendField(new Blockly.FieldNumber(100, 0), "X1")
            .appendField("Y:")
            .appendField(new Blockly.FieldNumber(100, 0), "Y1");
        this.appendDummyInput()
            .appendField("to")
            .appendField("X:")
            .appendField(new Blockly.FieldNumber(500, 0), "X2")
            .appendField("Y:")
            .appendField(new Blockly.FieldNumber(300, 0), "Y2");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.ACTIONS);
        this.setTooltip("Drag from one point to another");
    }
};

Blockly.Blocks['c4a_scroll'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("SCROLL")
            .appendField(new Blockly.FieldDropdown([
                ["DOWN", "DOWN"],
                ["UP", "UP"],
                ["LEFT", "LEFT"],
                ["RIGHT", "RIGHT"]
            ]), "DIRECTION")
            .appendField(new Blockly.FieldNumber(500, 0), "AMOUNT")
            .appendField("pixels");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.ACTIONS);
        this.setTooltip("Scroll in direction");
    }
};

// ============================================
// KEYBOARD BLOCKS
// ============================================

Blockly.Blocks['c4a_type'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("TYPE")
            .appendField(new Blockly.FieldTextInput("text to type"), "TEXT");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.KEYBOARD);
        this.setTooltip("Type text");
    }
};

Blockly.Blocks['c4a_type_var'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("TYPE")
            .appendField("$")
            .appendField(new Blockly.FieldTextInput("variable"), "VAR");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.KEYBOARD);
        this.setTooltip("Type variable value");
    }
};

Blockly.Blocks['c4a_clear'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("CLEAR")
            .appendField("`")
            .appendField(new Blockly.FieldTextInput("input"), "SELECTOR")
            .appendField("`");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.KEYBOARD);
        this.setTooltip("Clear input field");
    }
};

Blockly.Blocks['c4a_set'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("SET")
            .appendField("`")
            .appendField(new Blockly.FieldTextInput("#input"), "SELECTOR")
            .appendField("`")
            .appendField("to")
            .appendField(new Blockly.FieldTextInput("value"), "VALUE");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.KEYBOARD);
        this.setTooltip("Set input field value");
    }
};

Blockly.Blocks['c4a_press'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("PRESS")
            .appendField(new Blockly.FieldDropdown([
                ["Tab", "Tab"],
                ["Enter", "Enter"],
                ["Escape", "Escape"],
                ["Space", "Space"],
                ["ArrowUp", "ArrowUp"],
                ["ArrowDown", "ArrowDown"],
                ["ArrowLeft", "ArrowLeft"],
                ["ArrowRight", "ArrowRight"],
                ["Delete", "Delete"],
                ["Backspace", "Backspace"]
            ]), "KEY");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.KEYBOARD);
        this.setTooltip("Press and release key");
    }
};

Blockly.Blocks['c4a_key_down'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("KEY_DOWN")
            .appendField(new Blockly.FieldDropdown([
                ["Shift", "Shift"],
                ["Control", "Control"],
                ["Alt", "Alt"],
                ["Meta", "Meta"]
            ]), "KEY");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.KEYBOARD);
        this.setTooltip("Hold key down");
    }
};

Blockly.Blocks['c4a_key_up'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("KEY_UP")
            .appendField(new Blockly.FieldDropdown([
                ["Shift", "Shift"],
                ["Control", "Control"],
                ["Alt", "Alt"],
                ["Meta", "Meta"]
            ]), "KEY");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.KEYBOARD);
        this.setTooltip("Release key");
    }
};

// ============================================
// CONTROL FLOW BLOCKS
// ============================================

Blockly.Blocks['c4a_if_exists'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("IF EXISTS")
            .appendField("`")
            .appendField(new Blockly.FieldTextInput(".element"), "SELECTOR")
            .appendField("`")
            .appendField("THEN");
        this.appendStatementInput("THEN")
            .setCheck(null);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.CONTROL);
        this.setTooltip("If element exists, then do something");
    }
};

Blockly.Blocks['c4a_if_exists_else'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("IF EXISTS")
            .appendField("`")
            .appendField(new Blockly.FieldTextInput(".element"), "SELECTOR")
            .appendField("`")
            .appendField("THEN");
        this.appendStatementInput("THEN")
            .setCheck(null);
        this.appendDummyInput()
            .appendField("ELSE");
        this.appendStatementInput("ELSE")
            .setCheck(null);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.CONTROL);
        this.setTooltip("If element exists, then do something, else do something else");
    }
};

Blockly.Blocks['c4a_if_not_exists'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("IF NOT EXISTS")
            .appendField("`")
            .appendField(new Blockly.FieldTextInput(".element"), "SELECTOR")
            .appendField("`")
            .appendField("THEN");
        this.appendStatementInput("THEN")
            .setCheck(null);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.CONTROL);
        this.setTooltip("If element does not exist, then do something");
    }
};

Blockly.Blocks['c4a_if_js'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("IF")
            .appendField("`")
            .appendField(new Blockly.FieldTextInput("window.innerWidth < 768"), "CONDITION")
            .appendField("`")
            .appendField("THEN");
        this.appendStatementInput("THEN")
            .setCheck(null);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.CONTROL);
        this.setTooltip("If JavaScript condition is true");
    }
};

Blockly.Blocks['c4a_repeat_times'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("REPEAT")
            .appendField(new Blockly.FieldNumber(5, 1), "TIMES")
            .appendField("times");
        this.appendStatementInput("DO")
            .setCheck(null);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.CONTROL);
        this.setTooltip("Repeat commands N times");
    }
};

Blockly.Blocks['c4a_repeat_while'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("REPEAT WHILE")
            .appendField("`")
            .appendField(new Blockly.FieldTextInput("document.querySelector('.load-more')"), "CONDITION")
            .appendField("`");
        this.appendStatementInput("DO")
            .setCheck(null);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.CONTROL);
        this.setTooltip("Repeat while condition is true");
    }
};

// ============================================
// VARIABLE BLOCKS
// ============================================

Blockly.Blocks['c4a_setvar'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("SETVAR")
            .appendField(new Blockly.FieldTextInput("username"), "NAME")
            .appendField("=")
            .appendField(new Blockly.FieldTextInput("value"), "VALUE");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.VARIABLES);
        this.setTooltip("Set variable value");
    }
};

// ============================================
// ADVANCED BLOCKS
// ============================================

Blockly.Blocks['c4a_eval'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("EVAL")
            .appendField("`")
            .appendField(new Blockly.FieldTextInput("console.log('Hello')"), "CODE")
            .appendField("`");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.VARIABLES);
        this.setTooltip("Execute JavaScript code");
    }
};

Blockly.Blocks['c4a_comment'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("#")
            .appendField(new Blockly.FieldTextInput("Comment", null, {
                spellcheck: false,
                class: 'blocklyCommentText'
            }), "TEXT");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour("#616161");
        this.setTooltip("Add a comment");
        this.setStyle('comment_blocks');
    }
};

// ============================================
// PROCEDURE BLOCKS
// ============================================

Blockly.Blocks['c4a_proc_def'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("PROC")
            .appendField(new Blockly.FieldTextInput("procedure_name"), "NAME");
        this.appendStatementInput("BODY")
            .setCheck(null);
        this.appendDummyInput()
            .appendField("ENDPROC");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.PROCEDURES);
        this.setTooltip("Define a procedure");
    }
};

Blockly.Blocks['c4a_proc_call'] = {
    init: function() {
        this.appendDummyInput()
            .appendField("Call")
            .appendField(new Blockly.FieldTextInput("procedure_name"), "NAME");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(BlockColors.PROCEDURES);
        this.setTooltip("Call a procedure");
    }
};

// Code generators have been moved to c4a-generator.js