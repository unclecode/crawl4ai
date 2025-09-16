#!/usr/bin/env python3
"""
C4A-Script Tutorial Server
Serves the tutorial app and provides C4A compilation API
"""

import sys
import os
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_cors import CORS

# Add parent directories to path to import crawl4ai
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

try:
    from crawl4ai.script import compile as c4a_compile
    C4A_AVAILABLE = True
except ImportError:
    print("⚠️  C4A compiler not available. Using mock compiler.")
    C4A_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Serve static files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory('assets', path)

@app.route('/playground/')
def playground():
    return send_from_directory('playground', 'index.html')

@app.route('/playground/<path:path>')
def serve_playground(path):
    return send_from_directory('playground', path)

# API endpoint for C4A compilation
@app.route('/api/compile', methods=['POST'])
def compile_endpoint():
    try:
        data = request.get_json()
        script = data.get('script', '')
        
        if not script:
            return jsonify({
                'success': False,
                'error': {
                    'line': 1,
                    'column': 1,
                    'message': 'No script provided',
                    'suggestion': 'Write some C4A commands'
                }
            })
        
        if C4A_AVAILABLE:
            # Use real C4A compiler
            result = c4a_compile(script)
            
            if result.success:
                return jsonify({
                    'success': True,
                    'jsCode': result.js_code,
                    'metadata': {
                        'lineCount': len(result.js_code),
                        'sourceLines': len(script.split('\n'))
                    }
                })
            else:
                error = result.first_error
                return jsonify({
                    'success': False,
                    'error': {
                        'line': error.line,
                        'column': error.column,
                        'message': error.message,
                        'suggestion': error.suggestions[0].message if error.suggestions else None,
                        'code': error.code,
                        'sourceLine': error.source_line
                    }
                })
        else:
            # Use mock compiler for demo
            result = mock_compile(script)
            return jsonify(result)
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'line': 1,
                'column': 1,
                'message': f'Server error: {str(e)}',
                'suggestion': 'Check server logs'
            }
        }), 500

def mock_compile(script):
    """Simple mock compiler for demo when C4A is not available"""
    lines = [line for line in script.split('\n') if line.strip() and not line.strip().startswith('#')]
    js_code = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        try:
            if line.startswith('GO '):
                url = line[3:].strip()
                # Handle relative URLs
                if not url.startswith(('http://', 'https://')):
                    url = '/' + url.lstrip('/')
                js_code.append(f"await page.goto('{url}');")
                
            elif line.startswith('WAIT '):
                parts = line[5:].strip().split(' ')
                if parts[0].startswith('`'):
                    selector = parts[0].strip('`')
                    timeout = parts[1] if len(parts) > 1 else '5'
                    js_code.append(f"await page.waitForSelector('{selector}', {{ timeout: {timeout}000 }});")
                else:
                    seconds = parts[0]
                    js_code.append(f"await page.waitForTimeout({seconds}000);")
                    
            elif line.startswith('CLICK '):
                selector = line[6:].strip().strip('`')
                js_code.append(f"await page.click('{selector}');")
                
            elif line.startswith('TYPE '):
                text = line[5:].strip().strip('"')
                js_code.append(f"await page.keyboard.type('{text}');")
                
            elif line.startswith('SCROLL '):
                parts = line[7:].strip().split(' ')
                direction = parts[0]
                amount = parts[1] if len(parts) > 1 else '500'
                if direction == 'DOWN':
                    js_code.append(f"await page.evaluate(() => window.scrollBy(0, {amount}));")
                elif direction == 'UP':
                    js_code.append(f"await page.evaluate(() => window.scrollBy(0, -{amount}));")
                    
            elif line.startswith('IF '):
                if 'THEN' not in line:
                    return {
                        'success': False,
                        'error': {
                            'line': i + 1,
                            'column': len(line),
                            'message': "Missing 'THEN' keyword after IF condition",
                            'suggestion': "Add 'THEN' after the condition",
                            'sourceLine': line
                        }
                    }
                    
                condition = line[3:line.index('THEN')].strip()
                action = line[line.index('THEN') + 4:].strip()
                
                if 'EXISTS' in condition:
                    selector_match = condition.split('`')
                    if len(selector_match) >= 2:
                        selector = selector_match[1]
                        action_selector = action.split('`')[1] if '`' in action else ''
                        js_code.append(
                            f"if (await page.$$('{selector}').length > 0) {{ "
                            f"await page.click('{action_selector}'); }}"
                        )
                        
            elif line.startswith('PRESS '):
                key = line[6:].strip()
                js_code.append(f"await page.keyboard.press('{key}');")
                
            else:
                # Unknown command
                return {
                    'success': False,
                    'error': {
                        'line': i + 1,
                        'column': 1,
                        'message': f"Unknown command: {line.split()[0]}",
                        'suggestion': "Check command syntax",
                        'sourceLine': line
                    }
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': {
                    'line': i + 1,
                    'column': 1,
                    'message': f"Failed to parse: {str(e)}",
                    'suggestion': "Check syntax",
                    'sourceLine': line
                }
            }
    
    return {
        'success': True,
        'jsCode': js_code,
        'metadata': {
            'lineCount': len(js_code),
            'sourceLines': len(lines)
        }
    }

# Example scripts endpoint
@app.route('/api/examples')
def get_examples():
    examples = [
        {
            'id': 'cookie-banner',
            'name': 'Handle Cookie Banner',
            'description': 'Accept cookies and close newsletter popup',
            'script': '''# Handle cookie banner and newsletter
GO http://127.0.0.1:8080/playground/
WAIT `body` 2
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept`
IF (EXISTS `.newsletter-popup`) THEN CLICK `.close`'''
        },
        {
            'id': 'login',
            'name': 'Login Flow',
            'description': 'Complete login with credentials',
            'script': '''# Login to the site
CLICK `#login-btn`
WAIT `.login-form` 2
CLICK `#email`
TYPE "demo@example.com"
CLICK `#password`
TYPE "demo123"
IF (EXISTS `#remember-me`) THEN CLICK `#remember-me`
CLICK `button[type="submit"]`
WAIT `.welcome-message` 5'''
        },
        {
            'id': 'infinite-scroll',
            'name': 'Infinite Scroll',
            'description': 'Load products with scrolling',
            'script': '''# Navigate to catalog and scroll
CLICK `#catalog-link`
WAIT `.product-grid` 3

# Scroll multiple times to load products
SCROLL DOWN 1000
WAIT 1
SCROLL DOWN 1000
WAIT 1
SCROLL DOWN 1000'''
        },
        {
            'id': 'form-wizard',
            'name': 'Multi-step Form',
            'description': 'Complete a multi-step survey',
            'script': '''# Navigate to forms
CLICK `a[href="#forms"]`
WAIT `#survey-form` 2

# Step 1: Basic info
CLICK `#full-name`
TYPE "John Doe"
CLICK `#survey-email`
TYPE "john@example.com"
CLICK `.next-step`
WAIT 1

# Step 2: Preferences
CLICK `#interests`
CLICK `option[value="tech"]`
CLICK `option[value="music"]`
CLICK `.next-step`
WAIT 1

# Step 3: Submit
CLICK `#submit-survey`
WAIT `.success-message` 5'''
        }
    ]
    
    return jsonify(examples)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"""
╔══════════════════════════════════════════════════════════╗
║          C4A-Script Interactive Tutorial Server          ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Server running at: http://localhost:{port:<6}            ║
║                                                          ║
║  Features:                                               ║
║  • C4A-Script compilation API                            ║
║  • Interactive playground                                ║
║  • Real-time execution visualization                     ║
║                                                          ║
║  C4A Compiler: {'✓ Available' if C4A_AVAILABLE else '✗ Using mock compiler':<30} ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=True)