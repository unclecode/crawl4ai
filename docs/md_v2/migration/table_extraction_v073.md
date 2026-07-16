# Migration Guide: Table Extraction v0.7.3

## Overview

Version 0.7.3 introduces the **Table Extraction Strategy Pattern**, providing a more flexible and extensible approach to table extraction while maintaining full backward compatibility.

## What's New

### Strategy Pattern Implementation

Table extraction now follows the same strategy pattern used throughout Crawl4AI:

- **Consistent Architecture**: Aligns with extraction, chunking, and markdown strategies
- **Extensibility**: Easy to create custom table extraction strategies
- **Better Separation**: Table logic moved from content scraping to dedicated module
- **Full Control**: Fine-grained control over table detection and extraction

### New Classes

```python
from crawl4ai import (
    TableExtractionStrategy,    # Abstract base class
    DefaultTableExtraction,      # Current implementation (default)
    NoTableExtraction           # Explicitly disable extraction
)
```

## Backward Compatibility

**✅ All existing code continues to work without changes.**

### No Changes Required

If your code looks like this, it will continue to work:

```python
# This still works exactly the same
config = CrawlerRunConfig(
    table_score_threshold=7
)
result = await crawler.arun(url, config)
tables = result.tables  # Same structure, same data
```

### What Happens Behind the Scenes

When you don't specify a `table_extraction` strategy:

1. `CrawlerRunConfig` automatically creates `DefaultTableExtraction`
2. It uses your `table_score_threshold` parameter
3. Tables are extracted exactly as before
4. Results appear in `result.tables` with the same structure

## New Capabilities

### 1. Explicit Strategy Configuration

You can now explicitly configure table extraction:

```python
# New: Explicit control
strategy = DefaultTableExtraction(
    table_score_threshold=7,
    min_rows=2,              # New: minimum row filter
    min_cols=2,              # New: minimum column filter
    verbose=True             # New: detailed logging
)

config = CrawlerRunConfig(
    table_extraction=strategy
)
```

### 2. Disable Table Extraction

Improve performance when tables aren't needed:

```python
# New: Skip table extraction entirely
config = CrawlerRunConfig(
    table_extraction=NoTableExtraction()
)
# No CPU cycles spent on table detection/extraction
```

### 3. Custom Extraction Strategies

Create specialized extractors:

```python
class MyTableExtractor(TableExtractionStrategy):
    def extract_tables(self, element, **kwargs):
        # Custom extraction logic
        return custom_tables

config = CrawlerRunConfig(
    table_extraction=MyTableExtractor()
)
```

## Migration Scenarios

### Scenario 1: Basic Usage (No Changes Needed)

**Before (v0.7.2):**
```python
config = CrawlerRunConfig()
result = await crawler.arun(url, config)
for table in result.tables:
    print(table['headers'])
```

**After (v0.7.3):**
```python
# Exactly the same - no changes required
config = CrawlerRunConfig()
result = await crawler.arun(url, config)
for table in result.tables:
    print(table['headers'])
```

### Scenario 2: Custom Threshold (No Changes Needed)

**Before (v0.7.2):**
```python
config = CrawlerRunConfig(
    table_score_threshold=5
)
```

**After (v0.7.3):**
```python
# Still works the same
config = CrawlerRunConfig(
    table_score_threshold=5
)

# Or use new explicit approach for more control
strategy = DefaultTableExtraction(
    table_score_threshold=5,
    min_rows=2  # Additional filtering
)
config = CrawlerRunConfig(
    table_extraction=strategy
)
```

### Scenario 3: Advanced Filtering (New Feature)

**Before (v0.7.2):**
```python
# Had to filter after extraction
config = CrawlerRunConfig(
    table_score_threshold=5
)
result = await crawler.arun(url, config)

# Manual filtering
large_tables = [
    t for t in result.tables 
    if len(t['rows']) >= 5 and len(t['headers']) >= 3
]
```

**After (v0.7.3):**
```python
# Filter during extraction (more efficient)
strategy = DefaultTableExtraction(
    table_score_threshold=5,
    min_rows=5,
    min_cols=3
)
config = CrawlerRunConfig(
    table_extraction=strategy
)
result = await crawler.arun(url, config)
# result.tables already filtered
```

## Code Organization Changes

### Module Structure

**Before (v0.7.2):**
```
crawl4ai/
  content_scraping_strategy.py
    - LXMLWebScrapingStrategy
      - is_data_table()      # Table detection
      - extract_table_data() # Table extraction
```

**After (v0.7.3):**
```
crawl4ai/
  content_scraping_strategy.py
    - LXMLWebScrapingStrategy
      # Table methods removed, uses strategy
  
  table_extraction.py (NEW)
    - TableExtractionStrategy    # Base class
    - DefaultTableExtraction      # Moved logic here
    - NoTableExtraction          # New option
```

### Import Changes

**New imports available (optional):**
```python
# These are now available but not required for existing code
from crawl4ai import (
    TableExtractionStrategy,
    DefaultTableExtraction,
    NoTableExtraction
)
```

## Performance Implications

### No Performance Impact

For existing code, performance remains identical:
- Same extraction logic
- Same scoring algorithm
- Same processing time

### Performance Improvements Available

New options for better performance:

```python
# Skip tables entirely (faster)
config = CrawlerRunConfig(
    table_extraction=NoTableExtraction()
)

# Process only specific areas (faster)
config = CrawlerRunConfig(
    css_selector="main.content",
    table_extraction=DefaultTableExtraction(
        min_rows=5,  # Skip small tables
        min_cols=3
    )
)
```

## Testing Your Migration

### Verification Script

Run this to verify your extraction still works:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def verify_extraction():
    url = "your_url_here"
    
    async with AsyncWebCrawler() as crawler:
        # Test 1: Old approach
        config_old = CrawlerRunConfig(
            table_score_threshold=7
        )
        result_old = await crawler.arun(url, config_old)
        
        # Test 2: New explicit approach
        from crawl4ai import DefaultTableExtraction
        config_new = CrawlerRunConfig(
            table_extraction=DefaultTableExtraction(
                table_score_threshold=7
            )
        )
        result_new = await crawler.arun(url, config_new)
        
        # Compare results
        assert len(result_old.tables) == len(result_new.tables)
        print(f"✓ Both approaches extracted {len(result_old.tables)} tables")
        
        # Verify structure
        for old, new in zip(result_old.tables, result_new.tables):
            assert old['headers'] == new['headers']
            assert old['rows'] == new['rows']
        
        print("✓ Table content identical")

asyncio.run(verify_extraction())
```

## Deprecation Notes

### No Deprecations

- All existing parameters continue to work
- `table_score_threshold` in `CrawlerRunConfig` is still supported
- No breaking changes

### Internal Changes (Transparent to Users)

- `LXMLWebScrapingStrategy.is_data_table()` - Moved to `DefaultTableExtraction`
- `LXMLWebScrapingStrategy.extract_table_data()` - Moved to `DefaultTableExtraction`

These methods were internal and not part of the public API.

## Benefits of Upgrading

While not required, using the new pattern provides:

1. **Better Control**: Filter tables during extraction, not after
2. **Performance Options**: Skip extraction when not needed
3. **Extensibility**: Create custom extractors for specific needs
4. **Consistency**: Same pattern as other Crawl4AI strategies
5. **Future-Proof**: Ready for upcoming advanced strategies

## Troubleshooting

### Issue: Different Number of Tables

**Cause**: Threshold or filtering differences

**Solution**: 
```python
# Ensure same threshold
strategy = DefaultTableExtraction(
    table_score_threshold=7,  # Match your old setting
    min_rows=0,               # No filtering (default)
    min_cols=0                # No filtering (default)
)
```

### Issue: Import Errors

**Cause**: Using new classes without importing

**Solution**:
```python
# Add imports if using new features
from crawl4ai import (
    DefaultTableExtraction,
    NoTableExtraction,
    TableExtractionStrategy
)
```

### Issue: Custom Strategy Not Working

**Cause**: Incorrect method signature

**Solution**:
```python
class CustomExtractor(TableExtractionStrategy):
    def extract_tables(self, element, **kwargs):  # Correct signature
        # Not: extract_tables(self, html)
        # Not: extract(self, element)
        return tables_list
```

## Getting Help

If you encounter issues:

1. Check your `table_score_threshold` matches previous settings
2. Verify imports if using new classes
3. Enable verbose logging: `DefaultTableExtraction(verbose=True)`
4. Review the [Table Extraction Documentation](../core/table_extraction.md)
5. Check [examples](../examples/table_extraction_example.py)

## Summary

- ✅ **Full backward compatibility** - No code changes required
- ✅ **Same results** - Identical extraction behavior by default
- ✅ **New options** - Additional control when needed
- ✅ **Better architecture** - Consistent with Crawl4AI patterns
- ✅ **Ready for future** - Foundation for advanced strategies

The migration to v0.7.3 is seamless with no required changes while providing new capabilities for those who need them.