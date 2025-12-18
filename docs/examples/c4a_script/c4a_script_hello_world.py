"""
C4A-Script Hello World
A concise example showing how to use the C4A-Script compiler
"""

from crawl4ai.script.c4a_compile import compile

# Define your C4A-Script
script = """
GO https://example.com
WAIT `#content` 5
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept`
CLICK `button.submit`
"""

# Compile the script
result = compile(script)

# Check if compilation was successful
if result.success:
    # Success! Use the generated JavaScript
    print("✅ Compilation successful!")
    print(f"Generated {len(result.js_code)} JavaScript statements:\n")
    
    for i, js in enumerate(result.js_code, 1):
        print(f"{i}. {js}\n")
    
    # In real usage, you'd pass result.js_code to Crawl4AI:
    # config = CrawlerRunConfig(js_code=result.js_code)
    
else:
    # Error! Handle the compilation error
    print("❌ Compilation failed!")
    
    # Get the first error (there might be multiple)
    error = result.first_error
    
    # Show error details
    print(f"Error at line {error.line}, column {error.column}")
    print(f"Message: {error.message}")
    
    # Show the problematic code
    print(f"\nCode: {error.source_line}")
    print(" " * (6 + error.column) + "^")
    
    # Show suggestions if available
    if error.suggestions:
        print("\n💡 How to fix:")
        for suggestion in error.suggestions:
            print(f"   {suggestion.message}")
    
    # For debugging or logging, you can also get JSON
    # error_json = result.to_json()