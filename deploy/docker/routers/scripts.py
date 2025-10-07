from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from schemas import C4AScriptPayload

from crawl4ai.script import (
    CompilationResult,
    ValidationResult,
    # ErrorDetail
)

# Import all necessary components from the crawl4ai library
# C4A Script Language Support
from crawl4ai.script import (
    compile as c4a_compile,
)
from crawl4ai.script import (
    validate as c4a_validate,
)

# --- APIRouter for c4a Scripts Endpoints ---
router = APIRouter(
    prefix="/c4a",
    tags=["c4a Scripts"],
)

# --- Background Worker Function ---


@router.post("/validate",
    summary="Validate C4A-Script",
    description="Validate the syntax of a C4A-Script without compiling it.",
    response_description="Validation result with errors if any",
    response_model=ValidationResult
)
async def validate_c4a_script_endpoint(payload: C4AScriptPayload):
    """
    Validate the syntax of a C4A-Script.
    
    Checks the script syntax without compiling to executable JavaScript.
    Returns detailed error information if validation fails.
    
    **Request Body:**
    ```json
    {
        "script": "NAVIGATE https://example.com\\nWAIT 2\\nCLICK button.submit"
    }
    ```
    
    **Response (Valid):**
    ```json
    {
        "success": true,
        "errors": []
    }
    ```
    
    **Response (Invalid):**
    ```json
    {
        "success": false,
        "errors": [
            {
                "line": 3,
                "message": "Unknown command: CLCK",
                "type": "SyntaxError"
            }
        ]
    }
    ```
    
    **Usage:**
    ```python
    response = requests.post(
        "http://localhost:11235/c4a/validate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "script": "NAVIGATE https://example.com\\nWAIT 2"
        }
    )
    result = response.json()
    if result["success"]:
        print("Script is valid!")
    else:
        for error in result["errors"]:
            print(f"Line {error['line']}: {error['message']}")
    ```
    
    **Notes:**
    - Validates syntax only, doesn't execute
    - Returns detailed error locations
    - Use before compiling to check for issues
    """
    # The validate function is designed not to raise exceptions
    validation_result = c4a_validate(payload.script)
    return validation_result


@router.post("/compile",
    summary="Compile C4A-Script",
    description="Compile a C4A-Script into executable JavaScript code.",
    response_description="Compiled JavaScript code or compilation errors",
    response_model=CompilationResult
)
async def compile_c4a_script_endpoint(payload: C4AScriptPayload):
    """
    Compile a C4A-Script into executable JavaScript.
    
    Transforms high-level C4A-Script commands into JavaScript that can be
    executed in a browser context.
    
    **Request Body:**
    ```json
    {
        "script": "NAVIGATE https://example.com\\nWAIT 2\\nCLICK button.submit"
    }
    ```
    
    **Response (Success):**
    ```json
    {
        "success": true,
        "javascript": "await page.goto('https://example.com');\\nawait page.waitForTimeout(2000);\\nawait page.click('button.submit');",
        "errors": []
    }
    ```
    
    **Response (Error):**
    ```json
    {
        "success": false,
        "javascript": null,
        "errors": [
            {
                "line": 2,
                "message": "Invalid WAIT duration",
                "type": "CompilationError"
            }
        ]
    }
    ```
    
    **Usage:**
    ```python
    response = requests.post(
        "http://localhost:11235/c4a/compile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "script": "NAVIGATE https://example.com\\nCLICK .login-button"
        }
    )
    result = response.json()
    if result["success"]:
        print("Compiled JavaScript:")
        print(result["javascript"])
    else:
        print("Compilation failed:", result["errors"])
    ```
    
    **C4A-Script Commands:**
    - `NAVIGATE <url>` - Navigate to URL
    - `WAIT <seconds>` - Wait for specified time
    - `CLICK <selector>` - Click element
    - `TYPE <selector> <text>` - Type text into element
    - `SCROLL <direction>` - Scroll page
    - And many more...
    
    **Notes:**
    - Returns HTTP 400 if compilation fails
    - JavaScript can be used with /execute_js endpoint
    - Simplifies browser automation scripting
    """
    # The compile function also returns a result object instead of raising
    compilation_result = c4a_compile(payload.script)

    if not compilation_result.success:
        # You can optionally raise an HTTP exception for failed compilations
        # This makes it clearer on the client-side that it was a bad request
        raise HTTPException(
            status_code=400,
            detail=compilation_result.to_dict(),  # FastAPI will serialize this
        )

    return compilation_result


@router.post("/compile-file",
    summary="Compile C4A-Script from File",
    description="Compile a C4A-Script from an uploaded file or form string.",
    response_description="Compiled JavaScript code or compilation errors",
    response_model=CompilationResult
)
async def compile_c4a_script_file_endpoint(
    file: Optional[UploadFile] = File(None), script: Optional[str] = Form(None)
):
    """
    Compile a C4A-Script from file upload or form data.
    
    Accepts either a file upload or a string parameter. Useful for uploading
    C4A-Script files or sending multipart form data.
    
    **Parameters:**
    - `file`: C4A-Script file upload (multipart/form-data)
    - `script`: C4A-Script content as string (form field)
    
    **Note:** Provide either file OR script, not both.
    
    **Request (File Upload):**
    ```bash
    curl -X POST "http://localhost:11235/c4a/compile-file" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -F "file=@myscript.c4a"
    ```
    
    **Request (Form String):**
    ```bash
    curl -X POST "http://localhost:11235/c4a/compile-file" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -F "script=NAVIGATE https://example.com"
    ```
    
    **Response:**
    ```json
    {
        "success": true,
        "javascript": "await page.goto('https://example.com');",
        "errors": []
    }
    ```
    
    **Usage (Python with file):**
    ```python
    with open('script.c4a', 'rb') as f:
        response = requests.post(
            "http://localhost:11235/c4a/compile-file",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": f}
        )
    result = response.json()
    print(result["javascript"])
    ```
    
    **Usage (Python with string):**
    ```python
    response = requests.post(
        "http://localhost:11235/c4a/compile-file",
        headers={"Authorization": f"Bearer {token}"},
        data={"script": "NAVIGATE https://example.com"}
    )
    result = response.json()
    print(result["javascript"])
    ```
    
    **Notes:**
    - File must be UTF-8 encoded text
    - Use for batch script compilation
    - Returns HTTP 400 if both or neither parameter provided
    - Returns HTTP 400 if compilation fails
    """
    script_content = None

    # Validate that at least one input is provided
    if not file and not script:
        raise HTTPException(
            status_code=400,
            detail={"error": "Either 'file' or 'script' parameter must be provided"},
        )

    # If both are provided, prioritize the file
    if file and script:
        raise HTTPException(
            status_code=400,
            detail={"error": "Please provide either 'file' or 'script', not both"},
        )

    # Handle file upload
    if file:
        try:
            file_content = await file.read()
            script_content = file_content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "File must be a valid UTF-8 text file"},
            ) from exc
        except Exception as e:
            raise HTTPException(
                status_code=400, detail={"error": f"Error reading file: {str(e)}"}
            ) from e

    # Handle string content
    elif script:
        script_content = script

    # Compile the script content
    compilation_result = c4a_compile(script_content)

    if not compilation_result.success:
        # You can optionally raise an HTTP exception for failed compilations
        # This makes it clearer on the client-side that it was a bad request
        raise HTTPException(
            status_code=400,
            detail=compilation_result.to_dict(),  # FastAPI will serialize this
        )

    return compilation_result
