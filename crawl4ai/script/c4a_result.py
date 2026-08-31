"""
Result classes for C4A-Script compilation
Clean API design with no exceptions
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
import json


class ErrorType(Enum):
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    RUNTIME = "runtime"
    

class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Suggestion:
    """A suggestion for fixing an error"""
    message: str
    fix: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "fix": self.fix
        }


@dataclass
class ErrorDetail:
    """Detailed information about a compilation error"""
    # Core info
    type: ErrorType
    code: str  # E001, E002, etc.
    severity: Severity
    message: str
    
    # Location
    line: int
    column: int
    
    # Context
    source_line: str
    
    # Optional fields with defaults
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    line_before: Optional[str] = None
    line_after: Optional[str] = None
    
    # Help
    suggestions: List[Suggestion] = field(default_factory=list)
    documentation_url: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": self.type.value,
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "location": {
                "line": self.line,
                "column": self.column,
                "endLine": self.end_line,
                "endColumn": self.end_column
            },
            "context": {
                "sourceLine": self.source_line,
                "lineBefore": self.line_before,
                "lineAfter": self.line_after,
                "marker": {
                    "start": self.column - 1,
                    "length": (self.end_column - self.column) if self.end_column else 1
                }
            },
            "suggestions": [s.to_dict() for s in self.suggestions],
            "documentationUrl": self.documentation_url
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @property
    def formatted_message(self) -> str:
        """Returns the nice text format for terminals"""
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"{self.type.value.title()} Error [{self.code}]")
        lines.append(f"{'='*60}")
        lines.append(f"Location: Line {self.line}, Column {self.column}")
        lines.append(f"Error: {self.message}")
        
        if self.source_line:
            marker = " " * (self.column - 1) + "^"
            if self.end_column:
                marker += "~" * (self.end_column - self.column - 1)
            lines.append(f"\nCode:")
            if self.line_before:
                lines.append(f"  {self.line - 1: >3} | {self.line_before}")
            lines.append(f"  {self.line: >3} | {self.source_line}")
            lines.append(f"      | {marker}")
            if self.line_after:
                lines.append(f"  {self.line + 1: >3} | {self.line_after}")
        
        if self.suggestions:
            lines.append("\nSuggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"  {i}. {suggestion.message}")
                if suggestion.fix:
                    lines.append(f"     Fix: {suggestion.fix}")
        
        lines.append("="*60)
        return "\n".join(lines)
    
    @property
    def simple_message(self) -> str:
        """Returns just the error message without formatting"""
        return f"Line {self.line}: {self.message}"


@dataclass
class WarningDetail:
    """Information about a compilation warning"""
    code: str
    message: str
    line: int
    column: int
    
    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "line": self.line,
            "column": self.column
        }


@dataclass
class CompilationResult:
    """Result of C4A-Script compilation"""
    success: bool
    js_code: Optional[List[str]] = None
    errors: List[ErrorDetail] = field(default_factory=list)
    warnings: List[WarningDetail] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "jsCode": self.js_code,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0
    
    @property
    def first_error(self) -> Optional[ErrorDetail]:
        """Get the first error if any"""
        return self.errors[0] if self.errors else None
    
    def __str__(self) -> str:
        """String representation for debugging"""
        if self.success:
            msg = f"✓ Compilation successful"
            if self.js_code:
                msg += f" - {len(self.js_code)} statements generated"
            if self.warnings:
                msg += f" ({len(self.warnings)} warnings)"
            return msg
        else:
            return f"✗ Compilation failed - {len(self.errors)} error(s)"


@dataclass
class ValidationResult:
    """Result of script validation"""
    valid: bool
    errors: List[ErrorDetail] = field(default_factory=list)
    warnings: List[WarningDetail] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings]
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @property
    def first_error(self) -> Optional[ErrorDetail]:
        return self.errors[0] if self.errors else None