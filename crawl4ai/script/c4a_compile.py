"""
Clean C4A-Script API with Result pattern
No exceptions - always returns results
"""

from __future__ import annotations
import pathlib
import re
from typing import Union, List, Optional

# JSON_SCHEMA_BUILDER is still used elsewhere,
# but we now also need the new script-builder prompt.
from ..prompts import GENERATE_JS_SCRIPT_PROMPT, GENERATE_SCRIPT_PROMPT
import logging
import re

from .c4a_result import (
    CompilationResult, ValidationResult, ErrorDetail, WarningDetail,
    ErrorType, Severity, Suggestion
)
from .c4ai_script import Compiler
from lark.exceptions import UnexpectedToken, UnexpectedCharacters, VisitError
from ..async_configs import LLMConfig
from ..utils import perform_completion_with_backoff


class C4ACompiler:
    """Main compiler with result-based API"""
    
    # Error code mapping
    ERROR_CODES = {
        "missing_then": "E001",
        "missing_paren": "E002",
        "missing_comma": "E003",
        "missing_endproc": "E004",
        "undefined_proc": "E005",
        "missing_backticks": "E006",
        "invalid_command": "E007",
        "syntax_error": "E999"
    }
    
    @classmethod
    def compile(cls, script: Union[str, List[str]], root: Optional[pathlib.Path] = None) -> CompilationResult:
        """
        Compile C4A-Script to JavaScript
        
        Args:
            script: C4A-Script as string or list of lines
            root: Root directory for includes
            
        Returns:
            CompilationResult with success status and JS code or errors
        """
        # Normalize input
        if isinstance(script, list):
            script_text = '\n'.join(script)
            script_lines = script
        else:
            script_text = script
            script_lines = script.split('\n')
        
        try:
            # Try compilation
            compiler = Compiler(root)
            js_code = compiler.compile(script_text)
            
            # Success!
            result = CompilationResult(
                success=True,
                js_code=js_code,
                metadata={
                    "lineCount": len(script_lines),
                    "statementCount": len(js_code)
                }
            )
            
            # Add any warnings (future feature)
            # result.warnings = cls._check_warnings(script_text)
            
            return result
            
        except Exception as e:
            # Convert exception to ErrorDetail
            error = cls._exception_to_error(e, script_lines)
            return CompilationResult(
                success=False,
                errors=[error],
                metadata={
                    "lineCount": len(script_lines)
                }
            )
    
    @classmethod
    def validate(cls, script: Union[str, List[str]]) -> ValidationResult:
        """
        Validate script syntax without generating code
        
        Args:
            script: C4A-Script to validate
            
        Returns:
            ValidationResult with validity status and any errors
        """
        result = cls.compile(script)
        
        return ValidationResult(
            valid=result.success,
            errors=result.errors,
            warnings=result.warnings
        )
    
    @classmethod
    def compile_file(cls, path: Union[str, pathlib.Path]) -> CompilationResult:
        """
        Compile a C4A-Script file
        
        Args:
            path: Path to the file
            
        Returns:
            CompilationResult
        """
        path = pathlib.Path(path)
        
        if not path.exists():
            error = ErrorDetail(
                type=ErrorType.RUNTIME,
                code="E100",
                severity=Severity.ERROR,
                message=f"File not found: {path}",
                line=0,
                column=0,
                source_line=""
            )
            return CompilationResult(success=False, errors=[error])
        
        try:
            script = path.read_text()
            return cls.compile(script, root=path.parent)
        except Exception as e:
            error = ErrorDetail(
                type=ErrorType.RUNTIME,
                code="E101",
                severity=Severity.ERROR,
                message=f"Error reading file: {str(e)}",
                line=0,
                column=0,
                source_line=""
            )
            return CompilationResult(success=False, errors=[error])
    
    @classmethod
    def _exception_to_error(cls, exc: Exception, script_lines: List[str]) -> ErrorDetail:
        """Convert an exception to ErrorDetail"""
        
        if isinstance(exc, UnexpectedToken):
            return cls._handle_unexpected_token(exc, script_lines)
        elif isinstance(exc, UnexpectedCharacters):
            return cls._handle_unexpected_chars(exc, script_lines)
        elif isinstance(exc, ValueError):
            return cls._handle_value_error(exc, script_lines)
        else:
            # Generic error
            return ErrorDetail(
                type=ErrorType.SYNTAX,
                code=cls.ERROR_CODES["syntax_error"],
                severity=Severity.ERROR,
                message=str(exc),
                line=1,
                column=1,
                source_line=script_lines[0] if script_lines else ""
            )
    
    @classmethod
    def _handle_unexpected_token(cls, exc: UnexpectedToken, script_lines: List[str]) -> ErrorDetail:
        """Handle UnexpectedToken errors"""
        line = exc.line
        column = exc.column
        
        # Get context lines
        source_line = script_lines[line - 1] if 0 < line <= len(script_lines) else ""
        line_before = script_lines[line - 2] if line > 1 and line <= len(script_lines) + 1 else None
        line_after = script_lines[line] if 0 < line < len(script_lines) else None
        
        # Determine error type and suggestions
        if exc.token.type == 'CLICK' and 'THEN' in str(exc.expected):
            code = cls.ERROR_CODES["missing_then"]
            message = "Missing 'THEN' keyword after IF condition"
            suggestions = [
                Suggestion(
                    "Add 'THEN' after the condition",
                    source_line.replace("CLICK", "THEN CLICK") if source_line else None
                )
            ]
        elif exc.token.type == '$END':
            code = cls.ERROR_CODES["missing_endproc"]
            message = "Unexpected end of script"
            suggestions = [
                Suggestion("Check for missing ENDPROC"),
                Suggestion("Ensure all procedures are properly closed")
            ]
        elif 'RPAR' in str(exc.expected):
            code = cls.ERROR_CODES["missing_paren"]
            message = "Missing closing parenthesis ')'"
            suggestions = [
                Suggestion("Add closing parenthesis at the end of the condition")
            ]
        elif 'COMMA' in str(exc.expected):
            code = cls.ERROR_CODES["missing_comma"]
            message = "Missing comma ',' in command"
            suggestions = [
                Suggestion("Add comma between arguments")
            ]
        else:
            # Check if this might be missing backticks
            if exc.token.type == 'NAME' and 'BACKTICK_STRING' in str(exc.expected):
                code = cls.ERROR_CODES["missing_backticks"]
                message = "Selector must be wrapped in backticks"
                suggestions = [
                    Suggestion(
                        "Wrap the selector in backticks",
                        f"`{exc.token.value}`"
                    )
                ]
            else:
                code = cls.ERROR_CODES["syntax_error"]
                message = f"Unexpected '{exc.token.value}'"
                if exc.expected:
                    expected_list = [str(e) for e in exc.expected if not str(e).startswith('_')][:3]
                    if expected_list:
                        message += f". Expected: {', '.join(expected_list)}"
                suggestions = []
        
        return ErrorDetail(
            type=ErrorType.SYNTAX,
            code=code,
            severity=Severity.ERROR,
            message=message,
            line=line,
            column=column,
            source_line=source_line,
            line_before=line_before,
            line_after=line_after,
            suggestions=suggestions
        )
    
    @classmethod
    def _handle_unexpected_chars(cls, exc: UnexpectedCharacters, script_lines: List[str]) -> ErrorDetail:
        """Handle UnexpectedCharacters errors"""
        line = exc.line
        column = exc.column
        
        source_line = script_lines[line - 1] if 0 < line <= len(script_lines) else ""
        
        # Check for missing backticks
        if "CLICK" in source_line and column > source_line.find("CLICK"):
            code = cls.ERROR_CODES["missing_backticks"]
            message = "Selector must be wrapped in backticks"
            suggestions = [
                Suggestion(
                    "Wrap the selector in backticks",
                    re.sub(r'CLICK\s+([^\s]+)', r'CLICK `\1`', source_line)
                )
            ]
        else:
            code = cls.ERROR_CODES["syntax_error"]
            message = f"Invalid character at position {column}"
            suggestions = []
        
        return ErrorDetail(
            type=ErrorType.SYNTAX,
            code=code,
            severity=Severity.ERROR,
            message=message,
            line=line,
            column=column,
            source_line=source_line,
            suggestions=suggestions
        )
    
    @classmethod
    def _handle_value_error(cls, exc: ValueError, script_lines: List[str]) -> ErrorDetail:
        """Handle ValueError (runtime errors)"""
        message = str(exc)
        
        # Check for undefined procedure
        if "Unknown procedure" in message:
            proc_match = re.search(r"'([^']+)'", message)
            if proc_match:
                proc_name = proc_match.group(1)
                
                # Find the line with the procedure call
                for i, line in enumerate(script_lines):
                    if proc_name in line and not line.strip().startswith('PROC'):
                        return ErrorDetail(
                            type=ErrorType.RUNTIME,
                            code=cls.ERROR_CODES["undefined_proc"],
                            severity=Severity.ERROR,
                            message=f"Undefined procedure '{proc_name}'",
                            line=i + 1,
                            column=line.find(proc_name) + 1,
                            source_line=line,
                            suggestions=[
                                Suggestion(
                                    f"Define the procedure before using it",
                                    f"PROC {proc_name}\n  # commands here\nENDPROC"
                                )
                            ]
                        )
        
        # Generic runtime error
        return ErrorDetail(
            type=ErrorType.RUNTIME,
            code="E999",
            severity=Severity.ERROR,
            message=message,
            line=1,
            column=1,
            source_line=script_lines[0] if script_lines else ""
        )

    @staticmethod
    def generate_script(
        html: str,
        query: str | None = None,
        mode: str = "c4a",
        llm_config: LLMConfig | None = None,
        **completion_kwargs,
    ) -> str:
        """
        One-shot helper that calls the LLM exactly once to convert a
        natural-language goal + HTML snippet into either:

        1. raw JavaScript (`mode="js"`)
        2. Crawl4ai DSL (`mode="c4a"`)

        The returned string is guaranteed to be free of markdown wrappers
        or explanatory text, ready for direct execution.
        """
        if llm_config is None:
            llm_config = LLMConfig()  # falls back to env vars / defaults

        # Build the user chunk
        user_prompt = "\n".join(
            [
                "## GOAL",
                "<<goael>>",
                (query or "Prepare the page for crawling."),
                "<</goal>>",
                "",
                "## HTML",
                "<<html>>",
                html[:100000],  # guardrail against token blast
                "<</html>>",
                "",
                "## MODE",
                mode,
            ]
        )

        # Call the LLM with retry/back-off logic
        full_prompt =  f"{GENERATE_SCRIPT_PROMPT}\n\n{user_prompt}" if mode == "c4a" else f"{GENERATE_JS_SCRIPT_PROMPT}\n\n{user_prompt}"
        
        response = perform_completion_with_backoff(
            provider=llm_config.provider,
            prompt_with_variables=full_prompt,
            api_token=llm_config.api_token,
            json_response=False,
            base_url=getattr(llm_config, 'base_url', None),
            **completion_kwargs,
        )
        
        # Extract content from the response
        raw_response = response.choices[0].message.content.strip()

        # Strip accidental markdown fences (```js … ```)
        clean = re.sub(r"^```(?:[a-zA-Z0-9_-]+)?\s*|```$", "", raw_response, flags=re.MULTILINE).strip()

        if not clean:
            raise RuntimeError("LLM returned empty script.")

        return clean


# Convenience functions for direct use
def compile(script: Union[str, List[str]], root: Optional[pathlib.Path] = None) -> CompilationResult:
    """Compile C4A-Script to JavaScript"""
    return C4ACompiler.compile(script, root)


def validate(script: Union[str, List[str]]) -> ValidationResult:
    """Validate C4A-Script syntax"""
    return C4ACompiler.validate(script)


def compile_file(path: Union[str, pathlib.Path]) -> CompilationResult:
    """Compile C4A-Script file"""
    return C4ACompiler.compile_file(path)