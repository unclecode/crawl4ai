// C4A-Script Code Generator for Blockly
// Compatible with latest Blockly API

// Create a custom code generator for C4A-Script
const c4aGenerator = new Blockly.Generator('C4A');

// Helper to get field value with proper escaping
c4aGenerator.getFieldValue = function(block, fieldName) {
    return block.getFieldValue(fieldName);
};

// Navigation generators
c4aGenerator.forBlock['c4a_go'] = function(block, generator) {
    const url = generator.getFieldValue(block, 'URL');
    return `GO ${url}\n`;
};

c4aGenerator.forBlock['c4a_reload'] = function(block, generator) {
    return 'RELOAD\n';
};

c4aGenerator.forBlock['c4a_back'] = function(block, generator) {
    return 'BACK\n';
};

c4aGenerator.forBlock['c4a_forward'] = function(block, generator) {
    return 'FORWARD\n';
};

// Wait generators
c4aGenerator.forBlock['c4a_wait_time'] = function(block, generator) {
    const seconds = generator.getFieldValue(block, 'SECONDS');
    return `WAIT ${seconds}\n`;
};

c4aGenerator.forBlock['c4a_wait_selector'] = function(block, generator) {
    const selector = generator.getFieldValue(block, 'SELECTOR');
    const timeout = generator.getFieldValue(block, 'TIMEOUT');
    return `WAIT \`${selector}\` ${timeout}\n`;
};

c4aGenerator.forBlock['c4a_wait_text'] = function(block, generator) {
    const text = generator.getFieldValue(block, 'TEXT');
    const timeout = generator.getFieldValue(block, 'TIMEOUT');
    return `WAIT "${text}" ${timeout}\n`;
};

// Mouse action generators
c4aGenerator.forBlock['c4a_click'] = function(block, generator) {
    const selector = generator.getFieldValue(block, 'SELECTOR');
    return `CLICK \`${selector}\`\n`;
};

c4aGenerator.forBlock['c4a_click_xy'] = function(block, generator) {
    const x = generator.getFieldValue(block, 'X');
    const y = generator.getFieldValue(block, 'Y');
    return `CLICK ${x} ${y}\n`;
};

c4aGenerator.forBlock['c4a_double_click'] = function(block, generator) {
    const selector = generator.getFieldValue(block, 'SELECTOR');
    return `DOUBLE_CLICK \`${selector}\`\n`;
};

c4aGenerator.forBlock['c4a_right_click'] = function(block, generator) {
    const selector = generator.getFieldValue(block, 'SELECTOR');
    return `RIGHT_CLICK \`${selector}\`\n`;
};

c4aGenerator.forBlock['c4a_move'] = function(block, generator) {
    const x = generator.getFieldValue(block, 'X');
    const y = generator.getFieldValue(block, 'Y');
    return `MOVE ${x} ${y}\n`;
};

c4aGenerator.forBlock['c4a_drag'] = function(block, generator) {
    const x1 = generator.getFieldValue(block, 'X1');
    const y1 = generator.getFieldValue(block, 'Y1');
    const x2 = generator.getFieldValue(block, 'X2');
    const y2 = generator.getFieldValue(block, 'Y2');
    return `DRAG ${x1} ${y1} ${x2} ${y2}\n`;
};

c4aGenerator.forBlock['c4a_scroll'] = function(block, generator) {
    const direction = generator.getFieldValue(block, 'DIRECTION');
    const amount = generator.getFieldValue(block, 'AMOUNT');
    return `SCROLL ${direction} ${amount}\n`;
};

// Keyboard generators
c4aGenerator.forBlock['c4a_type'] = function(block, generator) {
    const text = generator.getFieldValue(block, 'TEXT');
    return `TYPE "${text}"\n`;
};

c4aGenerator.forBlock['c4a_type_var'] = function(block, generator) {
    const varName = generator.getFieldValue(block, 'VAR');
    return `TYPE $${varName}\n`;
};

c4aGenerator.forBlock['c4a_clear'] = function(block, generator) {
    const selector = generator.getFieldValue(block, 'SELECTOR');
    return `CLEAR \`${selector}\`\n`;
};

c4aGenerator.forBlock['c4a_set'] = function(block, generator) {
    const selector = generator.getFieldValue(block, 'SELECTOR');
    const value = generator.getFieldValue(block, 'VALUE');
    return `SET \`${selector}\` "${value}"\n`;
};

c4aGenerator.forBlock['c4a_press'] = function(block, generator) {
    const key = generator.getFieldValue(block, 'KEY');
    return `PRESS ${key}\n`;
};

c4aGenerator.forBlock['c4a_key_down'] = function(block, generator) {
    const key = generator.getFieldValue(block, 'KEY');
    return `KEY_DOWN ${key}\n`;
};

c4aGenerator.forBlock['c4a_key_up'] = function(block, generator) {
    const key = generator.getFieldValue(block, 'KEY');
    return `KEY_UP ${key}\n`;
};

// Control flow generators
c4aGenerator.forBlock['c4a_if_exists'] = function(block, generator) {
    const selector = generator.getFieldValue(block, 'SELECTOR');
    const thenCode = generator.statementToCode(block, 'THEN').trim();
    
    if (thenCode.includes('\n')) {
        // Multi-line then block
        const lines = thenCode.split('\n').filter(line => line.trim());
        return lines.map(line => `IF (EXISTS \`${selector}\`) THEN ${line}`).join('\n') + '\n';
    } else if (thenCode) {
        // Single line
        return `IF (EXISTS \`${selector}\`) THEN ${thenCode}\n`;
    }
    return '';
};

c4aGenerator.forBlock['c4a_if_exists_else'] = function(block, generator) {
    const selector = generator.getFieldValue(block, 'SELECTOR');
    const thenCode = generator.statementToCode(block, 'THEN').trim();
    const elseCode = generator.statementToCode(block, 'ELSE').trim();
    
    // For simplicity, only handle single-line then/else
    const thenLine = thenCode.split('\n')[0];
    const elseLine = elseCode.split('\n')[0];
    
    if (thenLine && elseLine) {
        return `IF (EXISTS \`${selector}\`) THEN ${thenLine} ELSE ${elseLine}\n`;
    } else if (thenLine) {
        return `IF (EXISTS \`${selector}\`) THEN ${thenLine}\n`;
    }
    return '';
};

c4aGenerator.forBlock['c4a_if_not_exists'] = function(block, generator) {
    const selector = generator.getFieldValue(block, 'SELECTOR');
    const thenCode = generator.statementToCode(block, 'THEN').trim();
    
    if (thenCode.includes('\n')) {
        const lines = thenCode.split('\n').filter(line => line.trim());
        return lines.map(line => `IF (NOT EXISTS \`${selector}\`) THEN ${line}`).join('\n') + '\n';
    } else if (thenCode) {
        return `IF (NOT EXISTS \`${selector}\`) THEN ${thenCode}\n`;
    }
    return '';
};

c4aGenerator.forBlock['c4a_if_js'] = function(block, generator) {
    const condition = generator.getFieldValue(block, 'CONDITION');
    const thenCode = generator.statementToCode(block, 'THEN').trim();
    
    if (thenCode.includes('\n')) {
        const lines = thenCode.split('\n').filter(line => line.trim());
        return lines.map(line => `IF (\`${condition}\`) THEN ${line}`).join('\n') + '\n';
    } else if (thenCode) {
        return `IF (\`${condition}\`) THEN ${thenCode}\n`;
    }
    return '';
};

c4aGenerator.forBlock['c4a_repeat_times'] = function(block, generator) {
    const times = generator.getFieldValue(block, 'TIMES');
    const doCode = generator.statementToCode(block, 'DO').trim();
    
    if (doCode) {
        // Get first command for repeat
        const firstLine = doCode.split('\n')[0];
        return `REPEAT (${firstLine}, ${times})\n`;
    }
    return '';
};

c4aGenerator.forBlock['c4a_repeat_while'] = function(block, generator) {
    const condition = generator.getFieldValue(block, 'CONDITION');
    const doCode = generator.statementToCode(block, 'DO').trim();
    
    if (doCode) {
        // Get first command for repeat
        const firstLine = doCode.split('\n')[0];
        return `REPEAT (${firstLine}, \`${condition}\`)\n`;
    }
    return '';
};

// Variable generators
c4aGenerator.forBlock['c4a_setvar'] = function(block, generator) {
    const name = generator.getFieldValue(block, 'NAME');
    const value = generator.getFieldValue(block, 'VALUE');
    return `SETVAR ${name} = "${value}"\n`;
};

// Advanced generators
c4aGenerator.forBlock['c4a_eval'] = function(block, generator) {
    const code = generator.getFieldValue(block, 'CODE');
    return `EVAL \`${code}\`\n`;
};

c4aGenerator.forBlock['c4a_comment'] = function(block, generator) {
    const text = generator.getFieldValue(block, 'TEXT');
    return `# ${text}\n`;
};

// Procedure generators
c4aGenerator.forBlock['c4a_proc_def'] = function(block, generator) {
    const name = generator.getFieldValue(block, 'NAME');
    const body = generator.statementToCode(block, 'BODY');
    return `PROC ${name}\n${body}ENDPROC\n`;
};

c4aGenerator.forBlock['c4a_proc_call'] = function(block, generator) {
    const name = generator.getFieldValue(block, 'NAME');
    return `${name}\n`;
};

// Override scrub_ to handle our custom format
c4aGenerator.scrub_ = function(block, code, opt_thisOnly) {
    const nextBlock = block.nextConnection && block.nextConnection.targetBlock();
    let nextCode = '';
    
    if (nextBlock) {
        if (!opt_thisOnly) {
            nextCode = c4aGenerator.blockToCode(nextBlock);
            
            // Add blank line between comment and non-comment blocks
            const currentIsComment = block.type === 'c4a_comment';
            const nextIsComment = nextBlock.type === 'c4a_comment';
            
            // Add blank line when transitioning from command to comment or vice versa
            if (currentIsComment !== nextIsComment && code.trim() && nextCode.trim()) {
                nextCode = '\n' + nextCode;
            }
        }
    }
    
    return code + nextCode;
};