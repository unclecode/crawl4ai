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


@router.post(
    "/validate", response_model=ValidationResult, summary="Validate a C4A-Script"
)
async def validate_c4a_script_endpoint(payload: C4AScriptPayload):
    """
    Validates the syntax of a C4A-Script without compiling it.

    Returns a `ValidationResult` object indicating whether the script is
    valid and providing detailed error information if it's not.
    """
    # The validate function is designed not to raise exceptions
    validation_result = c4a_validate(payload.script)
    return validation_result


@router.post(
    "/compile", response_model=CompilationResult, summary="Compile a C4A-Script"
)
async def compile_c4a_script_endpoint(payload: C4AScriptPayload):
    """
    Compiles a C4A-Script into executable JavaScript.

    If successful, returns the compiled JavaScript code. If there are syntax
    errors, it returns a detailed error report.
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


@router.post(
    "/compile-file",
    response_model=CompilationResult,
    summary="Compile a C4A-Script from file or string",
)
async def compile_c4a_script_file_endpoint(
    file: Optional[UploadFile] = File(None), script: Optional[str] = Form(None)
):
    """
    Compiles a C4A-Script into executable JavaScript from either an uploaded file or string content.

    Accepts either:
    - A file upload containing the C4A-Script
    - A string containing the C4A-Script content

    At least one of the parameters must be provided.

    If successful, returns the compiled JavaScript code. If there are syntax
    errors, it returns a detailed error report.
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
