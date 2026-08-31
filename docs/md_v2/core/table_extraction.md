# Table Extraction Strategies

## Overview

**New in v0.7.3+**: Table extraction now follows the **Strategy Design Pattern**, providing unprecedented flexibility and power for handling different table structures. Don't worry - **your existing code still works!** We maintain full backward compatibility while offering new capabilities.

### What's Changed?
- **Architecture**: Table extraction now uses pluggable strategies
- **Backward Compatible**: Your existing code with `table_score_threshold` continues to work
- **More Power**: Choose from multiple strategies or create your own
- **Same Default Behavior**: By default, uses `DefaultTableExtraction` (same as before)

### Key Points
✅ **Old code still works** - No breaking changes  
✅ **Same default behavior** - Uses the proven extraction algorithm  
✅ **New capabilities** - Add LLM extraction or custom strategies when needed  
✅ **Strategy pattern** - Clean, extensible architecture

## Quick Start

### The Simplest Way (Works Like Before)

If you're already using Crawl4AI, nothing changes:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def extract_tables():
    async with AsyncWebCrawler() as crawler:
        # This works exactly like before - uses DefaultTableExtraction internally
        result = await crawler.arun("https://example.com/data")
        
        # Tables are automatically extracted and available in result.tables
        for table in result.tables:
            print(f"Table with {len(table['rows'])} rows and {len(table['headers'])} columns")
            print(f"Headers: {table['headers']}")
            print(f"First row: {table['rows'][0] if table['rows'] else 'No data'}")

asyncio.run(extract_tables())
```

### Using the Old Configuration (Still Supported)

Your existing code with `table_score_threshold` continues to work:

```python
# This old approach STILL WORKS - we maintain backward compatibility
config = CrawlerRunConfig(
    table_score_threshold=7  # Internally creates DefaultTableExtraction(table_score_threshold=7)
)
result = await crawler.arun(url, config)
```

## Table Extraction Strategies

### Understanding the Strategy Pattern

The strategy pattern allows you to choose different table extraction algorithms at runtime. Think of it as having different tools in a toolbox - you pick the right one for the job:

- **No explicit strategy?** → Uses `DefaultTableExtraction` automatically (same as v0.7.2 and earlier)
- **Need complex table handling?** → Choose `LLMTableExtraction` (costs money, use sparingly)
- **Want to disable tables?** → Use `NoTableExtraction`
- **Have special requirements?** → Create a custom strategy

### Available Strategies

| Strategy | Description | Use Case | Cost | When to Use |
|----------|-------------|----------|------|-------------|
| `DefaultTableExtraction` | **RECOMMENDED**: Same algorithm as before v0.7.3 | General purpose (default) | Free | **Use this first - handles 95% of cases** |
| `LLMTableExtraction` | AI-powered extraction for complex tables | Tables with complex rowspan/colspan | **$$$ Per API call** | Only when DefaultTableExtraction fails |
| `NoTableExtraction` | Disables table extraction | When tables aren't needed | Free | For text-only extraction |
| Custom strategies | User-defined extraction logic | Specialized requirements | Free | Domain-specific needs |

> **⚠️ CRITICAL COST WARNING for LLMTableExtraction**: 
> 
> **DO NOT USE `LLMTableExtraction` UNLESS ABSOLUTELY NECESSARY!**
> 
> - **Always try `DefaultTableExtraction` first** - It's free and handles most tables perfectly
> - LLM extraction **costs money** with every API call
> - For large tables (100+ rows), LLM extraction can be **very slow**
> - **For large tables**: If you must use LLM, choose fast providers:
>   - ✅ **Groq** (fastest inference)
>   - ✅ **Cerebras** (optimized for speed)
>   - ⚠️ Avoid: OpenAI, Anthropic for large tables (slower)
> 
> **🚧 WORK IN PROGRESS**: 
> We are actively developing an **advanced non-LLM algorithm** that will handle complex table structures (rowspan, colspan, nested tables) for **FREE**. This will replace the need for costly LLM extraction in most cases. Coming soon!

### DefaultTableExtraction

The default strategy uses a sophisticated scoring system to identify data tables:

```python
from crawl4ai import DefaultTableExtraction, CrawlerRunConfig

# Customize the default extraction
table_strategy = DefaultTableExtraction(
    table_score_threshold=7,  # Scoring threshold (default: 7)
    min_rows=2,               # Minimum rows required
    min_cols=2,               # Minimum columns required
    verbose=True              # Enable detailed logging
)

config = CrawlerRunConfig(
    table_extraction=table_strategy
)
```

#### Scoring System

The scoring system evaluates multiple factors:

| Factor | Score Impact | Description |
|--------|--------------|-------------|
| Has `<thead>` | +2 | Semantic table structure |
| Has `<tbody>` | +1 | Organized table body |
| Has `<th>` elements | +2 | Header cells present |
| Headers in correct position | +1 | Proper semantic structure |
| Consistent column count | +2 | Regular data structure |
| Has caption | +2 | Descriptive caption |
| Has summary | +1 | Summary attribute |
| High text density | +2 to +3 | Content-rich cells |
| Data attributes | +0.5 each | Data-* attributes |
| Nested tables | -3 | Often indicates layout |
| Role="presentation" | -3 | Explicitly non-data |
| Too few rows | -2 | Insufficient data |

### LLMTableExtraction (Use Sparingly!)

**⚠️ WARNING**: Only use this when `DefaultTableExtraction` fails with complex tables!

LLMTableExtraction uses AI to understand complex table structures that traditional parsers struggle with. It automatically handles large tables through intelligent chunking and parallel processing:

```python
from crawl4ai import LLMTableExtraction, LLMConfig, CrawlerRunConfig

# Configure LLM (costs money per call!)
llm_config = LLMConfig(
    provider="groq/llama-3.3-70b-versatile",  # Fast provider for large tables
    api_token="your_api_key",
    temperature=0.1
)

# Create LLM extraction strategy with smart chunking
table_strategy = LLMTableExtraction(
    llm_config=llm_config,
    max_tries=3,                      # Retry up to 3 times if extraction fails
    css_selector="table",             # Optional: focus on specific tables
    enable_chunking=True,             # Automatically chunk large tables (default: True)
    chunk_token_threshold=3000,       # Split tables larger than this (default: 3000 tokens)
    min_rows_per_chunk=10,            # Minimum rows per chunk (default: 10)
    max_parallel_chunks=5,            # Process up to 5 chunks in parallel (default: 5)
    verbose=True
)

config = CrawlerRunConfig(
    table_extraction=table_strategy
)

result = await crawler.arun(url, config)
```

#### When to Use LLMTableExtraction

✅ **Use ONLY when**:
- Tables have complex merged cells (rowspan/colspan) that break DefaultTableExtraction
- Nested tables that need semantic understanding
- Tables with irregular structures
- You've tried DefaultTableExtraction and it failed

❌ **Never use when**:
- DefaultTableExtraction works (99% of cases)
- Tables are simple or well-structured
- You're processing many pages (costs add up!)
- Tables have 100+ rows (very slow)

#### How Smart Chunking Works

LLMTableExtraction automatically handles large tables through intelligent chunking:

1. **Automatic Detection**: Tables exceeding the token threshold are automatically split
2. **Smart Splitting**: Chunks are created at row boundaries, preserving table structure
3. **Header Preservation**: Each chunk includes the original headers for context
4. **Parallel Processing**: Multiple chunks are processed simultaneously for speed
5. **Intelligent Merging**: Results are merged back into a single, complete table

**Chunking Parameters**:
- `enable_chunking` (default: `True`): Automatically handle large tables
- `chunk_token_threshold` (default: `3000`): When to split tables
- `min_rows_per_chunk` (default: `10`): Ensures meaningful chunk sizes
- `max_parallel_chunks` (default: `5`): Concurrent processing for speed

The chunking is completely transparent - you get the same output format whether the table was processed in one piece or multiple chunks.

#### Performance Optimization for LLMTableExtraction

**Provider Recommendations by Table Size**:

| Table Size | Recommended Providers | Why |
|------------|----------------------|-----|
| Small (<50 rows) | Any provider | Fast enough |
| Medium (50-200 rows) | Groq, Cerebras | Optimized inference |
| Large (200+ rows) | **Groq** (best), Cerebras | Fastest inference + automatic chunking |
| Very Large (500+ rows) | Groq with chunking | Parallel processing keeps it fast |

### NoTableExtraction

Disable table extraction for better performance when tables aren't needed:

```python
from crawl4ai import NoTableExtraction, CrawlerRunConfig

config = CrawlerRunConfig(
    table_extraction=NoTableExtraction()
)

# Tables won't be extracted, improving performance
result = await crawler.arun(url, config)
assert len(result.tables) == 0
```

## Extracted Table Structure

Each extracted table contains:

```python
{
    "headers": ["Column 1", "Column 2", ...],  # Column headers
    "rows": [                                   # Data rows
        ["Row 1 Col 1", "Row 1 Col 2", ...],
        ["Row 2 Col 1", "Row 2 Col 2", ...],
    ],
    "caption": "Table Caption",                # If present
    "summary": "Table Summary",                # If present
    "metadata": {
        "row_count": 10,                       # Number of rows
        "column_count": 3,                      # Number of columns
        "has_headers": True,                    # Headers detected
        "has_caption": True,                    # Caption exists
        "has_summary": False,                   # Summary exists
        "id": "data-table-1",                   # Table ID if present
        "class": "financial-data"               # Table class if present
    }
}
```

## Configuration Options

### Basic Configuration

```python
config = CrawlerRunConfig(
    # Table extraction settings
    table_score_threshold=7,      # Default threshold (backward compatible)
    table_extraction=strategy,     # Optional: custom strategy
    
    # Filter what to process
    css_selector="main",          # Focus on specific area
    excluded_tags=["nav", "aside"] # Exclude page sections
)
```

### Advanced Configuration

```python
from crawl4ai import DefaultTableExtraction, CrawlerRunConfig

# Fine-tuned extraction
strategy = DefaultTableExtraction(
    table_score_threshold=5,      # Lower = more permissive
    min_rows=3,                   # Require at least 3 rows
    min_cols=2,                   # Require at least 2 columns
    verbose=True                  # Detailed logging
)

config = CrawlerRunConfig(
    table_extraction=strategy,
    css_selector="article.content", # Target specific content
    exclude_domains=["ads.com"],   # Exclude ad domains
    cache_mode=CacheMode.BYPASS    # Fresh extraction
)
```

## Working with Extracted Tables

### Convert to Pandas DataFrame

```python
import pandas as pd

async def tables_to_dataframes(url):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)
        
        dataframes = []
        for table_data in result.tables:
            # Create DataFrame
            if table_data['headers']:
                df = pd.DataFrame(
                    table_data['rows'],
                    columns=table_data['headers']
                )
            else:
                df = pd.DataFrame(table_data['rows'])
            
            # Add metadata as DataFrame attributes
            df.attrs['caption'] = table_data.get('caption', '')
            df.attrs['metadata'] = table_data.get('metadata', {})
            
            dataframes.append(df)
        
        return dataframes
```

### Filter Tables by Criteria

```python
async def extract_large_tables(url):
    async with AsyncWebCrawler() as crawler:
        # Configure minimum size requirements
        strategy = DefaultTableExtraction(
            min_rows=10,
            min_cols=3,
            table_score_threshold=6
        )
        
        config = CrawlerRunConfig(
            table_extraction=strategy
        )
        
        result = await crawler.arun(url, config)
        
        # Further filter results
        large_tables = [
            table for table in result.tables
            if table['metadata']['row_count'] > 10
            and table['metadata']['column_count'] > 3
        ]
        
        return large_tables
```

### Export Tables to Different Formats

```python
import json
import csv

async def export_tables(url):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)
        
        for i, table in enumerate(result.tables):
            # Export as JSON
            with open(f'table_{i}.json', 'w') as f:
                json.dump(table, f, indent=2)
            
            # Export as CSV
            with open(f'table_{i}.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                if table['headers']:
                    writer.writerow(table['headers'])
                writer.writerows(table['rows'])
            
            # Export as Markdown
            with open(f'table_{i}.md', 'w') as f:
                # Write headers
                if table['headers']:
                    f.write('| ' + ' | '.join(table['headers']) + ' |\n')
                    f.write('|' + '---|' * len(table['headers']) + '\n')
                
                # Write rows
                for row in table['rows']:
                    f.write('| ' + ' | '.join(str(cell) for cell in row) + ' |\n')
```

## Creating Custom Strategies

Extend `TableExtractionStrategy` to create custom extraction logic:

### Example: Financial Table Extractor

```python
from crawl4ai import TableExtractionStrategy
from typing import List, Dict, Any
import re

class FinancialTableExtractor(TableExtractionStrategy):
    """Extract tables containing financial data."""
    
    def __init__(self, currency_symbols=None, require_numbers=True, **kwargs):
        super().__init__(**kwargs)
        self.currency_symbols = currency_symbols or ['$', '€', '£', '¥']
        self.require_numbers = require_numbers
        self.number_pattern = re.compile(r'\d+[,.]?\d*')
    
    def extract_tables(self, element, **kwargs):
        tables_data = []
        
        for table in element.xpath(".//table"):
            # Check if table contains financial indicators
            table_text = ''.join(table.itertext())
            
            # Must contain currency symbols
            has_currency = any(sym in table_text for sym in self.currency_symbols)
            if not has_currency:
                continue
            
            # Must contain numbers if required
            if self.require_numbers:
                numbers = self.number_pattern.findall(table_text)
                if len(numbers) < 3:  # Arbitrary minimum
                    continue
            
            # Extract the table data
            table_data = self._extract_financial_data(table)
            if table_data:
                tables_data.append(table_data)
        
        return tables_data
    
    def _extract_financial_data(self, table):
        """Extract and clean financial data from table."""
        headers = []
        rows = []
        
        # Extract headers
        for th in table.xpath(".//thead//th | .//tr[1]//th"):
            headers.append(th.text_content().strip())
        
        # Extract and clean rows
        for tr in table.xpath(".//tbody//tr | .//tr[position()>1]"):
            row = []
            for td in tr.xpath(".//td"):
                text = td.text_content().strip()
                # Clean currency formatting
                text = re.sub(r'[$€£¥,]', '', text)
                row.append(text)
            if row:
                rows.append(row)
        
        return {
            "headers": headers,
            "rows": rows,
            "caption": self._get_caption(table),
            "summary": table.get("summary", ""),
            "metadata": {
                "type": "financial",
                "row_count": len(rows),
                "column_count": len(headers) or len(rows[0]) if rows else 0
            }
        }
    
    def _get_caption(self, table):
        caption = table.xpath(".//caption/text()")
        return caption[0].strip() if caption else ""

# Usage
strategy = FinancialTableExtractor(
    currency_symbols=['$', 'EUR'],
    require_numbers=True
)

config = CrawlerRunConfig(
    table_extraction=strategy
)
```

### Example: Specific Table Extractor

```python
class SpecificTableExtractor(TableExtractionStrategy):
    """Extract only tables matching specific criteria."""
    
    def __init__(self, 
                 required_headers=None, 
                 id_pattern=None,
                 class_pattern=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.required_headers = required_headers or []
        self.id_pattern = id_pattern
        self.class_pattern = class_pattern
    
    def extract_tables(self, element, **kwargs):
        tables_data = []
        
        for table in element.xpath(".//table"):
            # Check ID pattern
            if self.id_pattern:
                table_id = table.get('id', '')
                if not re.match(self.id_pattern, table_id):
                    continue
            
            # Check class pattern
            if self.class_pattern:
                table_class = table.get('class', '')
                if not re.match(self.class_pattern, table_class):
                    continue
            
            # Extract headers to check requirements
            headers = self._extract_headers(table)
            
            # Check if required headers are present
            if self.required_headers:
                if not all(req in headers for req in self.required_headers):
                    continue
            
            # Extract full table data
            table_data = self._extract_table_data(table, headers)
            tables_data.append(table_data)
        
        return tables_data
```

## Combining with Other Strategies

Table extraction works seamlessly with other Crawl4AI strategies:

```python
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    DefaultTableExtraction,
    LLMExtractionStrategy,
    JsonCssExtractionStrategy
)

async def combined_extraction(url):
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            # Table extraction
            table_extraction=DefaultTableExtraction(
                table_score_threshold=6,
                min_rows=2
            ),
            
            # CSS-based extraction for specific elements
            extraction_strategy=JsonCssExtractionStrategy({
                "title": "h1",
                "summary": "p.summary",
                "date": "time"
            }),
            
            # Focus on main content
            css_selector="main.content"
        )
        
        result = await crawler.arun(url, config)
        
        # Access different extraction results
        tables = result.tables  # Table data
        structured = json.loads(result.extracted_content)  # CSS extraction
        
        return {
            "tables": tables,
            "structured_data": structured,
            "markdown": result.markdown
        }
```

## Performance Considerations

### Optimization Tips

1. **Disable when not needed**: Use `NoTableExtraction` if tables aren't required
2. **Target specific areas**: Use `css_selector` to limit processing scope
3. **Set minimum thresholds**: Filter out small/irrelevant tables early
4. **Cache results**: Use appropriate cache modes for repeated extractions

```python
# Optimized configuration for large pages
config = CrawlerRunConfig(
    # Only process main content area
    css_selector="article.main-content",
    
    # Exclude navigation and sidebars
    excluded_tags=["nav", "aside", "footer"],
    
    # Higher threshold for stricter filtering
    table_extraction=DefaultTableExtraction(
        table_score_threshold=8,
        min_rows=5,
        min_cols=3
    ),
    
    # Enable caching for repeated access
    cache_mode=CacheMode.ENABLED
)
```

## Migration Guide

### Important: Your Code Still Works!

**No changes required!** The transition to the strategy pattern is **fully backward compatible**.

### How It Works Internally

#### v0.7.2 and Earlier
```python
# Old way - directly passing table_score_threshold
config = CrawlerRunConfig(
    table_score_threshold=7
)
# Internally: No strategy pattern, direct implementation
```

#### v0.7.3+ (Current)
```python
# Old way STILL WORKS - we handle it internally
config = CrawlerRunConfig(
    table_score_threshold=7
)
# Internally: Automatically creates DefaultTableExtraction(table_score_threshold=7)
```

### Taking Advantage of New Features

While your old code works, you can now use the strategy pattern for more control:

```python
# Option 1: Keep using the old way (perfectly fine!)
config = CrawlerRunConfig(
    table_score_threshold=7  # Still supported
)

# Option 2: Use the new strategy pattern (more flexibility)
from crawl4ai import DefaultTableExtraction

strategy = DefaultTableExtraction(
    table_score_threshold=7,
    min_rows=2,  # New capability!
    min_cols=2   # New capability!
)

config = CrawlerRunConfig(
    table_extraction=strategy
)

# Option 3: Use advanced strategies when needed
from crawl4ai import LLMTableExtraction, LLMConfig

# Only for complex tables that DefaultTableExtraction can't handle
# Automatically handles large tables with smart chunking
llm_strategy = LLMTableExtraction(
    llm_config=LLMConfig(
        provider="groq/llama-3.3-70b-versatile",
        api_token="your_key"
    ),
    max_tries=3,
    enable_chunking=True,  # Automatically chunk large tables
    chunk_token_threshold=3000,  # Chunk when exceeding 3000 tokens
    max_parallel_chunks=5  # Process up to 5 chunks in parallel
)

config = CrawlerRunConfig(
    table_extraction=llm_strategy  # Advanced extraction with automatic chunking
)
```

### Summary

- ✅ **No breaking changes** - Old code works as-is
- ✅ **Same defaults** - DefaultTableExtraction is automatically used
- ✅ **Gradual adoption** - Use new features when you need them
- ✅ **Full compatibility** - result.tables structure unchanged

## Best Practices

### 1. Choose the Right Strategy (Cost-Conscious Approach)

**Decision Flow**:
```
1. Do you need tables? 
   → No: Use NoTableExtraction
   → Yes: Continue to #2

2. Try DefaultTableExtraction first (FREE)
   → Works? Done! ✅
   → Fails? Continue to #3

3. Is the table critical and complex?
   → No: Accept DefaultTableExtraction results
   → Yes: Continue to #4

4. Use LLMTableExtraction (COSTS MONEY)
   → Small table (<50 rows): Any LLM provider
   → Large table (50+ rows): Use Groq or Cerebras
   → Very large (500+ rows): Reconsider - maybe chunk the page
```

**Strategy Selection Guide**:
- **DefaultTableExtraction**: Use for 99% of cases - it's free and effective
- **LLMTableExtraction**: Only for complex tables with merged cells that break DefaultTableExtraction
- **NoTableExtraction**: When you only need text/markdown content
- **Custom Strategy**: For specialized requirements (financial, scientific, etc.)

### 2. Validate Extracted Data

```python
def validate_table(table):
    """Validate table data quality."""
    # Check structure
    if not table.get('rows'):
        return False
    
    # Check consistency
    if table.get('headers'):
        expected_cols = len(table['headers'])
        for row in table['rows']:
            if len(row) != expected_cols:
                return False
    
    # Check minimum content
    total_cells = sum(len(row) for row in table['rows'])
    non_empty = sum(1 for row in table['rows'] 
                    for cell in row if cell.strip())
    
    if non_empty / total_cells < 0.5:  # Less than 50% non-empty
        return False
    
    return True

# Filter valid tables
valid_tables = [t for t in result.tables if validate_table(t)]
```

### 3. Handle Edge Cases

```python
async def robust_table_extraction(url):
    """Extract tables with error handling."""
    async with AsyncWebCrawler() as crawler:
        try:
            config = CrawlerRunConfig(
                table_extraction=DefaultTableExtraction(
                    table_score_threshold=6,
                    verbose=True
                )
            )
            
            result = await crawler.arun(url, config)
            
            if not result.success:
                print(f"Crawl failed: {result.error}")
                return []
            
            # Process tables safely
            processed_tables = []
            for table in result.tables:
                try:
                    # Validate and process
                    if validate_table(table):
                        processed_tables.append(table)
                except Exception as e:
                    print(f"Error processing table: {e}")
                    continue
            
            return processed_tables
            
        except Exception as e:
            print(f"Extraction error: {e}")
            return []
```

## Troubleshooting

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| No tables extracted | Score too high | Lower `table_score_threshold` |
| Layout tables included | Score too low | Increase `table_score_threshold` |
| Missing tables | CSS selector too specific | Broaden or remove `css_selector` |
| Incomplete data | Complex table structure | Create custom strategy |
| Performance issues | Processing entire page | Use `css_selector` to limit scope |

### Debug Logging

Enable verbose logging to understand extraction decisions:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Enable verbose mode in strategy
strategy = DefaultTableExtraction(
    table_score_threshold=7,
    verbose=True  # Detailed extraction logs
)

config = CrawlerRunConfig(
    table_extraction=strategy,
    verbose=True  # General crawler logs
)
```

## See Also

- [Extraction Strategies](extraction-strategies.md) - Overview of all extraction strategies
- [Content Selection](content-selection.md) - Using CSS selectors and filters
- [Performance Optimization](../optimization/performance-tuning.md) - Speed up extraction
- [Examples](../examples/table_extraction_example.py) - Complete working examples