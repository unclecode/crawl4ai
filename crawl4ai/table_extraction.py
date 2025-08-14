"""
Table extraction strategies for Crawl4AI.

This module provides various strategies for detecting and extracting tables from HTML content.
The strategy pattern allows for flexible table extraction methods while maintaining a consistent interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from lxml import etree
import re
import json
from .types import LLMConfig, create_llm_config
from .utils import perform_completion_with_backoff, sanitize_html
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import tiktoken


class TableExtractionStrategy(ABC):
    """
    Abstract base class for all table extraction strategies.
    
    This class defines the interface that all table extraction strategies must implement.
    It provides a consistent way to detect and extract tables from HTML content.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the table extraction strategy.
        
        Args:
            **kwargs: Additional keyword arguments for specific strategies
        """
        self.verbose = kwargs.get("verbose", False)
        self.logger = kwargs.get("logger", None)
    
    @abstractmethod
    def extract_tables(self, element: etree.Element, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract tables from the given HTML element.
        
        Args:
            element: The HTML element (typically the body or a container element)
            **kwargs: Additional parameters for extraction
            
        Returns:
            List of dictionaries containing table data, each with:
                - headers: List of column headers
                - rows: List of row data (each row is a list)
                - caption: Table caption if present
                - summary: Table summary attribute if present
                - metadata: Additional metadata about the table
        """
        pass
    
    def _log(self, level: str, message: str, tag: str = "TABLE", **kwargs):
        """Helper method to safely use logger."""
        if self.logger:
            log_method = getattr(self.logger, level, None)
            if log_method:
                log_method(message=message, tag=tag, **kwargs)


class DefaultTableExtraction(TableExtractionStrategy):
    """
    Default table extraction strategy that implements the current Crawl4AI table extraction logic.
    
    This strategy uses a scoring system to identify data tables (vs layout tables) and
    extracts structured data including headers, rows, captions, and summaries.
    It handles colspan and rowspan attributes to preserve table structure.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the default table extraction strategy.
        
        Args:
            table_score_threshold (int): Minimum score for a table to be considered a data table (default: 7)
            min_rows (int): Minimum number of rows for a valid table (default: 0)
            min_cols (int): Minimum number of columns for a valid table (default: 0)
            **kwargs: Additional parameters passed to parent class
        """
        super().__init__(**kwargs)
        self.table_score_threshold = kwargs.get("table_score_threshold", 7)
        self.min_rows = kwargs.get("min_rows", 0)
        self.min_cols = kwargs.get("min_cols", 0)
    
    def extract_tables(self, element: etree.Element, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract all data tables from the HTML element.
        
        Args:
            element: The HTML element to search for tables
            **kwargs: Additional parameters (can override instance settings)
            
        Returns:
            List of dictionaries containing extracted table data
        """
        tables_data = []
        
        # Allow kwargs to override instance settings
        score_threshold = kwargs.get("table_score_threshold", self.table_score_threshold)
        
        # Find all table elements
        tables = element.xpath(".//table")
        
        for table in tables:
            # Check if this is a data table (not a layout table)
            if self.is_data_table(table, table_score_threshold=score_threshold):
                try:
                    table_data = self.extract_table_data(table)
                    
                    # Apply minimum size filters if specified
                    if self.min_rows > 0 and len(table_data.get("rows", [])) < self.min_rows:
                        continue
                    if self.min_cols > 0:
                        col_count = len(table_data.get("headers", [])) or (
                            max(len(row) for row in table_data.get("rows", [])) if table_data.get("rows") else 0
                        )
                        if col_count < self.min_cols:
                            continue
                    
                    tables_data.append(table_data)
                except Exception as e:
                    self._log("error", f"Error extracting table data: {str(e)}", "TABLE_EXTRACT")
                    continue
        
        return tables_data
    
    def is_data_table(self, table: etree.Element, **kwargs) -> bool:
        """
        Determine if a table is a data table (vs. layout table) using a scoring system.
        
        Args:
            table: The table element to evaluate
            **kwargs: Additional parameters (e.g., table_score_threshold)
            
        Returns:
            True if the table scores above the threshold, False otherwise
        """
        score = 0
        
        # Check for thead and tbody
        has_thead = len(table.xpath(".//thead")) > 0
        has_tbody = len(table.xpath(".//tbody")) > 0
        if has_thead:
            score += 2
        if has_tbody:
            score += 1
        
        # Check for th elements
        th_count = len(table.xpath(".//th"))
        if th_count > 0:
            score += 2
            if has_thead or table.xpath(".//tr[1]/th"):
                score += 1
        
        # Check for nested tables (negative indicator)
        if len(table.xpath(".//table")) > 0:
            score -= 3
        
        # Role attribute check
        role = table.get("role", "").lower()
        if role in {"presentation", "none"}:
            score -= 3
        
        # Column consistency
        rows = table.xpath(".//tr")
        if not rows:
            return False
        
        col_counts = [len(row.xpath(".//td|.//th")) for row in rows]
        if col_counts:
            avg_cols = sum(col_counts) / len(col_counts)
            variance = sum((c - avg_cols)**2 for c in col_counts) / len(col_counts)
            if variance < 1:
                score += 2
        
        # Caption and summary
        if table.xpath(".//caption"):
            score += 2
        if table.get("summary"):
            score += 1
        
        # Text density
        total_text = sum(
            len(''.join(cell.itertext()).strip()) 
            for row in rows 
            for cell in row.xpath(".//td|.//th")
        )
        total_tags = sum(1 for _ in table.iterdescendants())
        text_ratio = total_text / (total_tags + 1e-5)
        if text_ratio > 20:
            score += 3
        elif text_ratio > 10:
            score += 2
        
        # Data attributes
        data_attrs = sum(1 for attr in table.attrib if attr.startswith('data-'))
        score += data_attrs * 0.5
        
        # Size check
        if col_counts and len(rows) >= 2:
            avg_cols = sum(col_counts) / len(col_counts)
            if avg_cols >= 2:
                score += 2
        
        threshold = kwargs.get("table_score_threshold", self.table_score_threshold)
        return score >= threshold
    
    def extract_table_data(self, table: etree.Element) -> Dict[str, Any]:
        """
        Extract structured data from a table element.
        
        Args:
            table: The table element to extract data from
            
        Returns:
            Dictionary containing:
                - headers: List of column headers
                - rows: List of row data (each row is a list)
                - caption: Table caption if present
                - summary: Table summary attribute if present
                - metadata: Additional metadata about the table
        """
        # Extract caption and summary
        caption = table.xpath(".//caption/text()")
        caption = caption[0].strip() if caption else ""
        summary = table.get("summary", "").strip()
        
        # Extract headers with colspan handling
        headers = []
        thead_rows = table.xpath(".//thead/tr")
        if thead_rows:
            header_cells = thead_rows[0].xpath(".//th")
            for cell in header_cells:
                text = cell.text_content().strip()
                colspan = int(cell.get("colspan", 1))
                headers.extend([text] * colspan)
        else:
            # Check first row for headers
            first_row = table.xpath(".//tr[1]")
            if first_row:
                for cell in first_row[0].xpath(".//th|.//td"):
                    text = cell.text_content().strip()
                    colspan = int(cell.get("colspan", 1))
                    headers.extend([text] * colspan)
        
        # Extract rows with colspan handling
        rows = []
        for row in table.xpath(".//tr[not(ancestor::thead)]"):
            row_data = []
            for cell in row.xpath(".//td"):
                text = cell.text_content().strip()
                colspan = int(cell.get("colspan", 1))
                row_data.extend([text] * colspan)
            if row_data:
                rows.append(row_data)
        
        # Align rows with headers
        max_columns = len(headers) if headers else (
            max(len(row) for row in rows) if rows else 0
        )
        aligned_rows = []
        for row in rows:
            aligned = row[:max_columns] + [''] * (max_columns - len(row))
            aligned_rows.append(aligned)
        
        # Generate default headers if none found
        if not headers and max_columns > 0:
            headers = [f"Column {i+1}" for i in range(max_columns)]
        
        # Build metadata
        metadata = {
            "row_count": len(aligned_rows),
            "column_count": max_columns,
            "has_headers": bool(thead_rows) or bool(table.xpath(".//tr[1]/th")),
            "has_caption": bool(caption),
            "has_summary": bool(summary)
        }
        
        # Add table attributes that might be useful
        if table.get("id"):
            metadata["id"] = table.get("id")
        if table.get("class"):
            metadata["class"] = table.get("class")
        
        return {
            "headers": headers,
            "rows": aligned_rows,
            "caption": caption,
            "summary": summary,
            "metadata": metadata
        }


class NoTableExtraction(TableExtractionStrategy):
    """
    A strategy that does not extract any tables.
    
    This can be used to explicitly disable table extraction when needed.
    """
    
    def extract_tables(self, element: etree.Element, **kwargs) -> List[Dict[str, Any]]:
        """
        Return an empty list (no tables extracted).
        
        Args:
            element: The HTML element (ignored)
            **kwargs: Additional parameters (ignored)
            
        Returns:
            Empty list
        """
        return []


class LLMTableExtraction(TableExtractionStrategy):
    """
    LLM-based table extraction strategy that uses language models to intelligently extract 
    and structure table data, handling complex cases like rowspan, colspan, and nested tables.
    
    This strategy uses an LLM to understand table structure semantically and convert it to 
    structured data that can be easily consumed by pandas DataFrames.
    """
    
    # System prompt for table extraction
    TABLE_EXTRACTION_PROMPT = """You are a specialized table extraction system that converts complex HTML tables into structured JSON data. Your primary goal is to handle difficult, irregular HTML tables that cannot be easily parsed by standard tools, transforming them into clean, tabulated data.

## Critical Requirements

**IMPORTANT**: You must extract **EVERY SINGLE ROW** from the table, regardless of size. Tables often contain hundreds of rows, and omitting data is unacceptable. The reason we use an LLM for this task is because these tables have complex structures that standard parsers cannot handle properly.

## Output Format

**Your response must be valid JSON**. The output must be properly formatted, parseable JSON with:
- Proper escaping of quotes in strings
- Valid JSON syntax (commas, brackets, etc.)
- No trailing commas
- Proper handling of special characters

## Table Structure

Every table should be extracted as a JSON object with this structure:

```json
{
    "headers": ["Column 1", "Column 2", ...],
    "rows": [
        ["Row 1 Col 1", "Row 1 Col 2", ...],
        ["Row 2 Col 1", "Row 2 Col 2", ...],
        // ... continue for ALL rows ...
    ],
    "caption": "Table caption if present",
    "summary": "Table summary attribute if present",
    "metadata": {
        "row_count": <actual_number_of_rows>,
        "column_count": <number>,
        "has_headers": <boolean>,
        "has_merged_cells": <boolean>,
        "nested_tables": <boolean>,
        "table_type": "data|pivot|matrix|nested"
    }
}
```

## Handling Complex Structures

### Why This Matters
Standard HTML parsers fail on tables with:
- Complex colspan/rowspan arrangements
- Nested tables
- Irregular structures
- Mixed header patterns

Your job is to intelligently interpret these structures and produce clean, regular data.

### Colspan (Merged Columns)
When a cell spans multiple columns, duplicate the value across all spanned columns to maintain rectangular data structure.

Example HTML:
```html
<tr>
    <td colspan="3">Quarterly Report</td>
    <td>Total</td>
</tr>
```
Becomes: ["Quarterly Report", "Quarterly Report", "Quarterly Report", "Total"]

### Rowspan (Merged Rows)
When a cell spans multiple rows, duplicate the value down all affected rows.

Example with many rows:
```html
<tr>
    <td rowspan="50">Category A</td>
    <td>Item 1</td>
    <td>$100</td>
</tr>
<tr>
    <td>Item 2</td>
    <td>$200</td>
</tr>
<!-- ... 48 more rows ... -->
```

Result structure (response must be valid JSON):
```json
{
    "headers": ["Category", "Item", "Price"],
    "rows": [
        ["Category A", "Item 1", "$100"],
        ["Category A", "Item 2", "$200"],
        ["Category A", "Item 3", "$300"],
        ["Category A", "Item 4", "$400"],
        ["Category A", "Item 5", "$500"],
        // ... ALL 50 rows must be included ...
        ["Category A", "Item 50", "$5000"]
    ],
    "metadata": {
        "row_count": 50,
        "column_count": 3,
        "has_headers": true,
        "has_merged_cells": true,
        "nested_tables": false,
        "table_type": "data"
    }
}
```

### Nested Tables
For tables containing other tables:
1. Extract the outer table structure
2. Represent nested tables as a JSON string or structured representation
3. Ensure the data remains usable

## Complete Examples

### Example 1: Large Table with Complex Structure

Input HTML (abbreviated for documentation):
```html
<table>
    <thead>
        <tr>
            <th rowspan="2">Department</th>
            <th colspan="4">2024 Performance</th>
        </tr>
        <tr>
            <th>Q1</th>
            <th>Q2</th>
            <th>Q3</th>
            <th>Q4</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="15">Sales</td>
            <td>Region North</td>
            <td>$1.2M</td>
            <td>$1.5M</td>
            <td>$1.8M</td>
        </tr>
        <tr>
            <td>Region South</td>
            <td>$0.9M</td>
            <td>$1.1M</td>
            <td>$1.3M</td>
        </tr>
        <!-- ... 13 more regions ... -->
        <tr>
            <td rowspan="20">Engineering</td>
            <td>Team Alpha</td>
            <td>85%</td>
            <td>88%</td>
            <td>92%</td>
        </tr>
        <!-- ... 19 more teams ... -->
        <!-- ... continue for 200+ total rows ... -->
    </tbody>
</table>
```

Output (showing structure with all rows) - must be valid JSON:
```json
{
    "headers": ["Department", "Team/Region", "Q1", "Q2", "Q3", "Q4"],
    "rows": [
        ["Sales", "Region North", "$1.2M", "$1.5M", "$1.8M"],
        ["Sales", "Region South", "$0.9M", "$1.1M", "$1.3M"],
        ["Sales", "Region East", "$1.1M", "$1.4M", "$1.6M"],
        ["Sales", "Region West", "$1.0M", "$1.2M", "$1.5M"],
        ["Sales", "Region Central", "$0.8M", "$1.0M", "$1.2M"],
        // ... ALL 15 Sales rows must be included ...
        ["Engineering", "Team Alpha", "85%", "88%", "92%"],
        ["Engineering", "Team Beta", "82%", "85%", "89%"],
        ["Engineering", "Team Gamma", "88%", "90%", "93%"],
        // ... ALL 20 Engineering rows must be included ...
        // ... Continue for EVERY row in the table ...
    ],
    "caption": "",
    "summary": "",
    "metadata": {
        "row_count": 235,
        "column_count": 6,
        "has_headers": true,
        "has_merged_cells": true,
        "nested_tables": false,
        "table_type": "data"
    }
}
```

### Example 2: Pivot Table with Hundreds of Rows

Input structure:
```html
<table>
    <tr>
        <th>Product ID</th>
        <th>Jan</th>
        <th>Feb</th>
        <!-- ... all 12 months ... -->
    </tr>
    <tr>
        <td>PROD-001</td>
        <td>1,234</td>
        <td>1,456</td>
        <!-- ... -->
    </tr>
    <!-- ... 500+ product rows ... -->
</table>
```

Output must include ALL rows and be valid JSON:
```json
{
    "headers": ["Product ID", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "rows": [
        ["PROD-001", "1,234", "1,456", "1,789", "2,012", "2,234", "2,456", "2,678", "2,890", "3,123", "3,345", "3,567", "3,789"],
        ["PROD-002", "2,345", "2,567", "2,789", "3,012", "3,234", "3,456", "3,678", "3,890", "4,123", "4,345", "4,567", "4,789"],
        ["PROD-003", "3,456", "3,678", "3,890", "4,123", "4,345", "4,567", "4,789", "5,012", "5,234", "5,456", "5,678", "5,890"],
        // ... ALL 500+ rows MUST be included ...
        ["PROD-547", "9,876", "10,098", "10,321", "10,543", "10,765", "10,987", "11,210", "11,432", "11,654", "11,876", "12,098", "12,321"]
    ],
    "metadata": {
        "row_count": 547,
        "column_count": 13,
        "has_headers": true,
        "has_merged_cells": false,
        "nested_tables": false,
        "table_type": "pivot"
    }
}
```

## Critical Data Integrity Rules

1. **COMPLETENESS**: Extract EVERY row, no matter how many (10, 100, 1000+)
2. **ACCURACY**: Preserve exact values, including formatting
3. **STRUCTURE**: Maintain consistent column count across all rows
4. **VALIDATION**: Ensure output is valid JSON that can be parsed
5. **ESCAPING**: Properly escape quotes and special characters in cell values

## Special Handling Instructions

### Large Tables
- Never abbreviate or summarize
- Never use "..." to indicate omitted rows
- Process every row even if it takes significant time
- The metadata row_count must match actual extracted rows

### Complex Merged Cells
- Track rowspan/colspan values carefully
- Ensure proper cell duplication
- Maintain data alignment across all rows

### Data Types
- Keep numbers as strings to preserve formatting
- Preserve currency symbols, percentages, etc.
- Handle empty cells as empty strings ""

### Error Prevention
- If a cell contains quotes, escape them properly
- Handle newlines within cells appropriately
- Ensure no JSON syntax errors

## Output Validation

Before returning results:
1. Verify JSON is valid and parseable
2. Confirm row count matches actual data
3. Check that all rows have same column count
4. Ensure all data is preserved without truncation

## JSON Schema Definition

Your output must conform to the following JSON schema (OpenAPI 3.0 format):

{
 "components": {
   "schemas": {
     "ExtractedTable": {
       "type": "object",
       "required": [
         "headers",
         "rows",
         "metadata"
       ],
       "properties": {
         "headers": {
           "type": "array",
           "description": "Column headers for the table",
           "items": {
             "type": "string"
           },
           "minItems": 1
         },
         "rows": {
           "type": "array",
           "description": "All table rows - must include every single row",
           "items": {
             "type": "array",
             "items": {
               "type": "string"
             },
             "minItems": 1
           }
         },
         "caption": {
           "type": "string",
           "description": "Table caption if present",
           "default": ""
         },
         "summary": {
           "type": "string",
           "description": "Table summary attribute if present",
           "default": ""
         },
         "metadata": {
           "type": "object",
           "required": [
             "row_count",
             "column_count",
             "has_headers",
             "has_merged_cells",
             "nested_tables",
             "table_type"
           ],
           "properties": {
             "row_count": {
               "type": "integer",
               "description": "Actual count of rows extracted",
               "minimum": 0
             },
             "column_count": {
               "type": "integer",
               "description": "Number of columns in the table",
               "minimum": 1
             },
             "has_headers": {
               "type": "boolean",
               "description": "Whether table has identified headers"
             },
             "has_merged_cells": {
               "type": "boolean",
               "description": "Whether table contains colspan or rowspan"
             },
             "nested_tables": {
               "type": "boolean",
               "description": "Whether table contains nested tables"
             },
             "table_type": {
               "type": "string",
               "enum": ["data", "pivot", "matrix", "nested"],
               "description": "Classification of table structure"
             }
           }
         }
       }
     }
   }
 }
}

**CRITICAL**: Your response must be a valid JSON object that conforms to this schema. The entire purpose of using an LLM for this task is to handle complex HTML tables that standard parsers cannot process correctly. Your value lies in intelligently interpreting complex structures and returning complete, clean, tabulated data in valid JSON format."""
    
    def __init__(self, 
                 llm_config: Optional[LLMConfig] = None,
                 css_selector: Optional[str] = None,
                 max_tries: int = 3,
                 enable_chunking: bool = True,
                 chunk_token_threshold: int = 3000,
                 min_rows_per_chunk: int = 10,
                 max_parallel_chunks: int = 5,
                 verbose: bool = False,
                 **kwargs):
        """
        Initialize the LLM-based table extraction strategy.
        
        Args:
            llm_config: LLM configuration for the extraction
            css_selector: Optional CSS selector to focus on specific page areas
            max_tries: Maximum number of retries if LLM fails to extract tables (default: 3)
            enable_chunking: Enable smart chunking for large tables (default: True)
            chunk_token_threshold: Token threshold for triggering chunking (default: 3000)
            min_rows_per_chunk: Minimum rows per chunk (default: 10)
            max_parallel_chunks: Maximum parallel chunk processing (default: 5)
            verbose: Enable verbose logging
            **kwargs: Additional parameters passed to parent class
        """
        super().__init__(verbose=verbose, **kwargs)
        
        # Set up LLM configuration
        self.llm_config = llm_config
        if not self.llm_config:
            # Use default configuration if not provided
            self.llm_config = create_llm_config(
                provider=os.getenv("DEFAULT_PROVIDER", "openai/gpt-4o-mini"),
                api_token=os.getenv("OPENAI_API_KEY"),
            )
        
        self.css_selector = css_selector
        self.max_tries = max(1, max_tries)  # Ensure at least 1 try
        self.enable_chunking = enable_chunking
        self.chunk_token_threshold = chunk_token_threshold
        self.min_rows_per_chunk = max(5, min_rows_per_chunk)  # At least 5 rows per chunk
        self.max_parallel_chunks = max(1, max_parallel_chunks)
        self.extra_args = kwargs.get("extra_args", {})
    
    def extract_tables(self, element: etree.Element, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract tables from HTML using LLM.
        
        Args:
            element: The HTML element to search for tables
            **kwargs: Additional parameters
            
        Returns:
            List of dictionaries containing extracted table data
        """
        # Allow CSS selector override via kwargs
        css_selector = kwargs.get("css_selector", self.css_selector)
        
        # Get the HTML content to process
        if css_selector:
            # Use XPath to convert CSS selector (basic conversion)
            # For more complex CSS selectors, we might need a proper CSS to XPath converter
            selected_elements = self._css_to_xpath_select(element, css_selector)
            if not selected_elements:
                self._log("warning", f"No elements found for CSS selector: {css_selector}")
                return []
            html_content = ''.join(etree.tostring(elem, encoding='unicode') for elem in selected_elements)
        else:
            # Process entire element
            html_content = etree.tostring(element, encoding='unicode')
        
        # Check if there are any tables in the content
        if '<table' not in html_content.lower():
            if self.verbose:
                self._log("info", f"No <table> tags found in HTML content")
            return []
        
        if self.verbose:
            self._log("info", f"Found table tags in HTML, content length: {len(html_content)}")
        
        # Check if chunking is needed
        if self.enable_chunking and self._needs_chunking(html_content):
            if self.verbose:
                self._log("info", "Content exceeds token threshold, using chunked extraction")
            return self._extract_with_chunking(html_content)
        
        # Single extraction for small content
        # Prepare the prompt
        user_prompt = f"""GENERATE THE TABULATED DATA from the following HTML content:

```html
{sanitize_html(html_content)}
```

Return only a JSON array of extracted tables following the specified format."""
        
        # Try extraction with retries
        for attempt in range(1, self.max_tries + 1):
            try:
                if self.verbose and attempt > 1:
                    self._log("info", f"Retry attempt {attempt}/{self.max_tries} for table extraction")
                
                # Call LLM with the extraction prompt
                response = perform_completion_with_backoff(
                    provider=self.llm_config.provider,
                    prompt_with_variables=self.TABLE_EXTRACTION_PROMPT + "\n\n" + user_prompt + "\n\n MAKE SURE TO EXTRACT ALL DATA, DO NOT LEAVE ANYTHING FOR BRAVITY, YOUR GOAL IS TO RETURN ALL, NO MATTER HOW LONG IS DATA",
                    api_token=self.llm_config.api_token,
                    base_url=self.llm_config.base_url,
                    json_response=True,
                    extra_args=self.extra_args
                )
                
                # Parse the response
                if response and response.choices:
                    content = response.choices[0].message.content
                    
                    if self.verbose:
                        self._log("debug", f"LLM response type: {type(content)}")
                        if isinstance(content, str):
                            self._log("debug", f"LLM response preview: {content[:200]}...")
                    
                    # Parse JSON response
                    if isinstance(content, str):
                        tables_data = json.loads(content)
                    else:
                        tables_data = content
                    
                    # Handle various response formats from LLM
                    # Sometimes LLM wraps response in "result" or other keys
                    if isinstance(tables_data, dict):
                        # Check for common wrapper keys
                        if 'result' in tables_data:
                            tables_data = tables_data['result']
                        elif 'tables' in tables_data:
                            tables_data = tables_data['tables']
                        elif 'data' in tables_data:
                            tables_data = tables_data['data']
                        else:
                            # If it's a single table dict, wrap in list
                            tables_data = [tables_data]
                    
                    # Flatten nested lists if needed
                    while isinstance(tables_data, list) and len(tables_data) == 1 and isinstance(tables_data[0], list):
                        tables_data = tables_data[0]
                    
                    # Ensure we have a list
                    if not isinstance(tables_data, list):
                        tables_data = [tables_data]
                    
                    if self.verbose:
                        self._log("debug", f"Parsed {len(tables_data)} table(s) from LLM response")
                    
                    # Validate and clean the extracted tables
                    validated_tables = []
                    for table in tables_data:
                        if self._validate_table_structure(table):
                            validated_tables.append(self._ensure_table_format(table))
                        elif self.verbose:
                            self._log("warning", f"Table failed validation: {table}")
                    
                    # Check if we got valid tables
                    if validated_tables:
                        if self.verbose:
                            self._log("info", f"Successfully extracted {len(validated_tables)} tables using LLM on attempt {attempt}")
                        return validated_tables
                    
                    # If no valid tables but we still have attempts left, retry
                    if attempt < self.max_tries:
                        if self.verbose:
                            self._log("warning", f"No valid tables extracted on attempt {attempt}, retrying...")
                        continue
                    else:
                        if self.verbose:
                            self._log("warning", f"No valid tables extracted after {self.max_tries} attempts")
                        return []
                    
            except json.JSONDecodeError as e:
                if self.verbose:
                    self._log("error", f"JSON parsing error on attempt {attempt}: {str(e)}")
                if attempt < self.max_tries:
                    continue
                else:
                    return []
                    
            except Exception as e:
                if self.verbose:
                    self._log("error", f"Error in LLM table extraction on attempt {attempt}: {str(e)}")
                    if attempt == self.max_tries:
                        import traceback
                        self._log("debug", f"Traceback: {traceback.format_exc()}")
                
                # For unexpected errors, retry if we have attempts left
                if attempt < self.max_tries:
                    # Add a small delay before retry for rate limiting
                    import time
                    time.sleep(1)
                    continue
                else:
                    return []
        
        # Should not reach here, but return empty list as fallback
        return []
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Uses tiktoken for OpenAI models, simple approximation for others.
        """
        try:
            # Try to use tiktoken for accurate counting
            if 'gpt' in self.llm_config.provider.lower():
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
                return len(encoding.encode(text))
        except:
            pass
        
        # Fallback: rough approximation (1 token ≈ 4 characters)
        return len(text) // 4
    
    def _needs_chunking(self, html_content: str) -> bool:
        """
        Check if table HTML needs chunking based on token count.
        """
        if not self.enable_chunking:
            return False
        
        token_count = self._estimate_tokens(html_content)
        needs_chunk = token_count > self.chunk_token_threshold
        
        if self.verbose and needs_chunk:
            self._log("info", f"Table needs chunking: {token_count} tokens > {self.chunk_token_threshold} threshold")
        
        return needs_chunk
    
    def _extract_table_structure(self, html_content: str) -> Tuple[List[etree.Element], List[etree.Element], List[etree.Element], bool]:
        """
        Extract headers, body rows, and footer from table HTML.
        
        Returns:
            Tuple of (header_rows, body_rows, footer_rows, has_headers)
        """
        parser = etree.HTMLParser()
        tree = etree.fromstring(html_content, parser)
        
        # Find all tables
        tables = tree.xpath('.//table')
        if not tables:
            return [], [], [], False
        
        table = tables[0]  # Process first table
        
        # Extract header rows (from thead or first rows with th)
        header_rows = []
        thead = table.xpath('.//thead')
        if thead:
            header_rows = thead[0].xpath('.//tr')
        else:
            # Look for rows with th elements
            for row in table.xpath('.//tr'):
                if row.xpath('.//th'):
                    header_rows.append(row)
                else:
                    break
        
        # Track if we found headers
        has_headers = len(header_rows) > 0
        
        # Extract footer rows
        footer_rows = []
        tfoot = table.xpath('.//tfoot')
        if tfoot:
            footer_rows = tfoot[0].xpath('.//tr')
        
        # Extract body rows
        body_rows = []
        tbody = table.xpath('.//tbody')
        if tbody:
            body_rows = tbody[0].xpath('.//tr')
        else:
            # Get all rows that aren't headers or footers
            all_rows = table.xpath('.//tr')
            header_count = len(header_rows)
            footer_count = len(footer_rows)
            
            if footer_count > 0:
                body_rows = all_rows[header_count:-footer_count]
            else:
                body_rows = all_rows[header_count:]
        
        # If no headers found and no tbody, all rows are body rows
        if not has_headers and not tbody:
            body_rows = tables[0].xpath('.//tr')
        
        return header_rows, body_rows, footer_rows, has_headers
    
    def _create_smart_chunks(self, html_content: str) -> Tuple[List[str], bool]:
        """
        Create smart chunks of table HTML, preserving headers in each chunk.
        
        Returns:
            Tuple of (chunks, has_headers)
        """
        if self.verbose:
            self._log("info", f"Creating smart chunks from {len(html_content)} characters of HTML")
        
        header_rows, body_rows, footer_rows, has_headers = self._extract_table_structure(html_content)
        
        if self.verbose:
            self._log("info", f"Table structure: {len(header_rows)} header rows, {len(body_rows)} body rows, {len(footer_rows)} footer rows")
        
        if not body_rows:
            if self.verbose:
                self._log("info", "No body rows to chunk, returning full content")
            return [html_content], has_headers  # No rows to chunk
        
        # Create header HTML (to be included in every chunk)
        header_html = ""
        if header_rows:
            thead_element = etree.Element("thead")
            for row in header_rows:
                thead_element.append(row)
            header_html = etree.tostring(thead_element, encoding='unicode')
        
        # Calculate rows per chunk based on token estimates
        chunks = []
        current_chunk_rows = []
        current_token_count = self._estimate_tokens(header_html)
        
        for row in body_rows:
            row_html = etree.tostring(row, encoding='unicode')
            row_tokens = self._estimate_tokens(row_html)
            
            # Check if adding this row would exceed threshold
            if current_chunk_rows and (current_token_count + row_tokens > self.chunk_token_threshold):
                # Create chunk with current rows
                chunk_html = self._create_chunk_html(header_html, current_chunk_rows, None)
                chunks.append(chunk_html)
                
                # Start new chunk
                current_chunk_rows = [row_html]
                current_token_count = self._estimate_tokens(header_html) + row_tokens
            else:
                current_chunk_rows.append(row_html)
                current_token_count += row_tokens
        
        # Add remaining rows
        if current_chunk_rows:
            # Include footer only in the last chunk
            footer_html = None
            if footer_rows:
                tfoot_element = etree.Element("tfoot")
                for row in footer_rows:
                    tfoot_element.append(row)
                footer_html = etree.tostring(tfoot_element, encoding='unicode')
            
            chunk_html = self._create_chunk_html(header_html, current_chunk_rows, footer_html)
            chunks.append(chunk_html)
        
        # Ensure minimum rows per chunk
        if len(chunks) > 1:
            chunks = self._rebalance_chunks(chunks, self.min_rows_per_chunk)
        
        if self.verbose:
            self._log("info", f"Created {len(chunks)} chunks for parallel processing")
        
        return chunks, has_headers
    
    def _create_chunk_html(self, header_html: str, body_rows: List[str], footer_html: Optional[str]) -> str:
        """
        Create a complete table HTML chunk with headers, body rows, and optional footer.
        """
        html_parts = ['<table>']
        
        if header_html:
            html_parts.append(header_html)
        
        html_parts.append('<tbody>')
        html_parts.extend(body_rows)
        html_parts.append('</tbody>')
        
        if footer_html:
            html_parts.append(footer_html)
        
        html_parts.append('</table>')
        
        return ''.join(html_parts)
    
    def _rebalance_chunks(self, chunks: List[str], min_rows: int) -> List[str]:
        """
        Rebalance chunks to ensure minimum rows per chunk.
        Merge small chunks if necessary.
        """
        # This is a simplified implementation
        # In production, you'd want more sophisticated rebalancing
        return chunks
    
    def _process_chunk(self, chunk_html: str, chunk_index: int, total_chunks: int, has_headers: bool = True) -> Dict[str, Any]:
        """
        Process a single chunk with the LLM.
        """
        if self.verbose:
            self._log("info", f"Processing chunk {chunk_index + 1}/{total_chunks}")
        
        # Build context about headers
        header_context = ""
        if not has_headers:
            header_context = "\nIMPORTANT: This table has NO headers. Return an empty array for 'headers' field and extract all rows as data rows."
        
        # Add context about this being part of a larger table
        chunk_prompt = f"""Extract table data from this HTML chunk.
This is part {chunk_index + 1} of {total_chunks} of a larger table.
Focus on extracting the data rows accurately.{header_context}

```html
{sanitize_html(chunk_html)}
```

Return only a JSON array of extracted tables following the specified format."""
        
        for attempt in range(1, self.max_tries + 1):
            try:
                if self.verbose and attempt > 1:
                    self._log("info", f"Retry attempt {attempt}/{self.max_tries} for chunk {chunk_index + 1}")
                
                response = perform_completion_with_backoff(
                    provider=self.llm_config.provider,
                    prompt_with_variables=self.TABLE_EXTRACTION_PROMPT + "\n\n" + chunk_prompt,
                    api_token=self.llm_config.api_token,
                    base_url=self.llm_config.base_url,
                    json_response=True,
                    extra_args=self.extra_args
                )
                
                if response and response.choices:
                    content = response.choices[0].message.content
                    
                    # Parse JSON response
                    if isinstance(content, str):
                        tables_data = json.loads(content)
                    else:
                        tables_data = content
                    
                    # Handle various response formats
                    if isinstance(tables_data, dict):
                        if 'result' in tables_data:
                            tables_data = tables_data['result']
                        elif 'tables' in tables_data:
                            tables_data = tables_data['tables']
                        elif 'data' in tables_data:
                            tables_data = tables_data['data']
                        else:
                            tables_data = [tables_data]
                    
                    # Flatten nested lists
                    while isinstance(tables_data, list) and len(tables_data) == 1 and isinstance(tables_data[0], list):
                        tables_data = tables_data[0]
                    
                    if not isinstance(tables_data, list):
                        tables_data = [tables_data]
                    
                    # Return first valid table (each chunk should have one table)
                    for table in tables_data:
                        if self._validate_table_structure(table):
                            return {
                                'chunk_index': chunk_index,
                                'table': self._ensure_table_format(table)
                            }
                    
                    # If no valid table, return empty result
                    return {'chunk_index': chunk_index, 'table': None}
                    
            except Exception as e:
                if self.verbose:
                    self._log("error", f"Error processing chunk {chunk_index + 1}: {str(e)}")
                
                if attempt < self.max_tries:
                    time.sleep(1)
                    continue
                else:
                    return {'chunk_index': chunk_index, 'table': None, 'error': str(e)}
        
        return {'chunk_index': chunk_index, 'table': None}
    
    def _merge_chunk_results(self, chunk_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge results from multiple chunks into a single table.
        """
        # Sort by chunk index to maintain order
        chunk_results.sort(key=lambda x: x.get('chunk_index', 0))
        
        # Filter out failed chunks
        valid_chunks = [r for r in chunk_results if r.get('table')]
        
        if not valid_chunks:
            return []
        
        # Start with the first chunk's structure
        merged_table = valid_chunks[0]['table'].copy()
        
        # Concatenate rows from all chunks
        all_rows = []
        for chunk_result in valid_chunks:
            table = chunk_result['table']
            # Skip headers from non-first chunks (they're duplicates)
            rows = table.get('rows', [])
            all_rows.extend(rows)
        
        merged_table['rows'] = all_rows
        
        # Update metadata
        merged_table['metadata']['row_count'] = len(all_rows)
        merged_table['metadata']['chunked'] = True
        merged_table['metadata']['chunk_count'] = len(valid_chunks)
        
        if self.verbose:
            self._log("info", f"Merged {len(valid_chunks)} chunks into table with {len(all_rows)} rows")
        
        return [merged_table]
    
    def _extract_with_chunking(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extract tables using chunking and parallel processing.
        """
        if self.verbose:
            self._log("info", f"Starting chunked extraction for content with {len(html_content)} characters")
        
        # Create smart chunks
        chunks, has_headers = self._create_smart_chunks(html_content)
        
        if self.verbose:
            self._log("info", f"Created {len(chunks)} chunk(s) for processing")
        
        if len(chunks) == 1:
            # No need for parallel processing
            if self.verbose:
                self._log("info", "Processing as single chunk (no parallelization needed)")
            result = self._process_chunk(chunks[0], 0, 1, has_headers)
            return [result['table']] if result.get('table') else []
        
        # Process chunks in parallel
        if self.verbose:
            self._log("info", f"Processing {len(chunks)} chunks in parallel (max workers: {self.max_parallel_chunks})")
        
        chunk_results = []
        with ThreadPoolExecutor(max_workers=self.max_parallel_chunks) as executor:
            # Submit all chunks for processing
            futures = {
                executor.submit(self._process_chunk, chunk, i, len(chunks), has_headers): i
                for i, chunk in enumerate(chunks)
            }
            
            # Collect results as they complete
            for future in as_completed(futures):
                chunk_index = futures[future]
                try:
                    result = future.result(timeout=60)  # 60 second timeout per chunk
                    if self.verbose:
                        self._log("info", f"Chunk {chunk_index + 1}/{len(chunks)} completed successfully")
                    chunk_results.append(result)
                except Exception as e:
                    if self.verbose:
                        self._log("error", f"Chunk {chunk_index + 1}/{len(chunks)} processing failed: {str(e)}")
                    chunk_results.append({'chunk_index': chunk_index, 'table': None, 'error': str(e)})
        
        if self.verbose:
            self._log("info", f"All chunks processed, merging results...")
        
        # Merge results
        return self._merge_chunk_results(chunk_results)
    
    def _css_to_xpath_select(self, element: etree.Element, css_selector: str) -> List[etree.Element]:
        """
        Convert CSS selector to XPath and select elements.
        This is a basic implementation - for complex CSS selectors, 
        consider using cssselect library.
        
        Args:
            element: Root element to search from
            css_selector: CSS selector string
            
        Returns:
            List of selected elements
        """
        # Basic CSS to XPath conversion
        # This handles simple cases like "div", ".class", "#id", "div.class"
        xpath = css_selector
        
        # Handle ID selector
        if css_selector.startswith('#'):
            xpath = f".//*[@id='{css_selector[1:]}']"
        # Handle class selector
        elif css_selector.startswith('.'):
            xpath = f".//*[contains(@class, '{css_selector[1:]}')]"
        # Handle element with class
        elif '.' in css_selector:
            parts = css_selector.split('.')
            element_name = parts[0]
            class_name = parts[1]
            xpath = f".//{element_name}[contains(@class, '{class_name}')]"
        # Handle element with ID
        elif '#' in css_selector:
            parts = css_selector.split('#')
            element_name = parts[0]
            id_value = parts[1]
            xpath = f".//{element_name}[@id='{id_value}']"
        # Handle simple element selector
        else:
            xpath = f".//{css_selector}"
        
        try:
            return element.xpath(xpath)
        except Exception as e:
            self._log("warning", f"XPath conversion failed for selector '{css_selector}': {str(e)}")
            return []
    
    def _validate_table_structure(self, table: Dict) -> bool:
        """
        Validate that the table has the required structure.
        
        Args:
            table: Table dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not isinstance(table, dict):
            return False
        
        # Must have at least headers and rows
        if 'headers' not in table or 'rows' not in table:
            return False
        
        # Headers should be a list (but might be nested)
        headers = table.get('headers')
        if not isinstance(headers, list):
            return False
        
        # Flatten headers if nested
        while isinstance(headers, list) and len(headers) == 1 and isinstance(headers[0], list):
            table['headers'] = headers[0]
            headers = table['headers']
        
        # Rows should be a list
        rows = table.get('rows')
        if not isinstance(rows, list):
            return False
        
        # Flatten rows if deeply nested
        cleaned_rows = []
        for row in rows:
            # Handle multiple levels of nesting
            while isinstance(row, list) and len(row) == 1 and isinstance(row[0], list):
                row = row[0]
            cleaned_rows.append(row)
        table['rows'] = cleaned_rows
        
        # Each row should be a list
        for row in table.get('rows', []):
            if not isinstance(row, list):
                return False
        
        return True
    
    def _ensure_table_format(self, table: Dict) -> Dict[str, Any]:
        """
        Ensure the table has all required fields with proper defaults.
        
        Args:
            table: Table dictionary to format
            
        Returns:
            Properly formatted table dictionary
        """
        # Ensure all required fields exist
        formatted_table = {
            'headers': table.get('headers', []),
            'rows': table.get('rows', []),
            'caption': table.get('caption', ''),
            'summary': table.get('summary', ''),
            'metadata': table.get('metadata', {})
        }
        
        # Ensure metadata has basic fields
        if not formatted_table['metadata']:
            formatted_table['metadata'] = {}
        
        # Calculate metadata if not provided
        metadata = formatted_table['metadata']
        if 'row_count' not in metadata:
            metadata['row_count'] = len(formatted_table['rows'])
        if 'column_count' not in metadata:
            metadata['column_count'] = len(formatted_table['headers'])
        if 'has_headers' not in metadata:
            metadata['has_headers'] = bool(formatted_table['headers'])
        
        # Ensure all rows have the same number of columns as headers
        col_count = len(formatted_table['headers'])
        if col_count > 0:
            for i, row in enumerate(formatted_table['rows']):
                if len(row) < col_count:
                    # Pad with empty strings
                    formatted_table['rows'][i] = row + [''] * (col_count - len(row))
                elif len(row) > col_count:
                    # Truncate extra columns
                    formatted_table['rows'][i] = row[:col_count]
        
        return formatted_table