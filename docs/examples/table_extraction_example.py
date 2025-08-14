"""
Example: Using Table Extraction Strategies in Crawl4AI

This example demonstrates how to use different table extraction strategies
to extract tables from web pages.
"""

import asyncio
import pandas as pd
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CacheMode,
    DefaultTableExtraction,
    NoTableExtraction,
    TableExtractionStrategy
)
from typing import Dict, List, Any


async def example_default_extraction():
    """Example 1: Using default table extraction (automatic)."""
    print("\n" + "="*50)
    print("Example 1: Default Table Extraction")
    print("="*50)
    
    async with AsyncWebCrawler() as crawler:
        # No need to specify table_extraction - uses DefaultTableExtraction automatically
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            table_score_threshold=7  # Adjust sensitivity (default: 7)
        )
        
        result = await crawler.arun(
            "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)",
            config=config
        )
        
        if result.success and result.tables:
            print(f"Found {len(result.tables)} tables")
            
            # Convert first table to pandas DataFrame
            if result.tables:
                first_table = result.tables[0]
                df = pd.DataFrame(
                    first_table['rows'],
                    columns=first_table['headers'] if first_table['headers'] else None
                )
                print(f"\nFirst table preview:")
                print(df.head())
                print(f"Shape: {df.shape}")


async def example_custom_configuration():
    """Example 2: Custom table extraction configuration."""
    print("\n" + "="*50)
    print("Example 2: Custom Table Configuration")
    print("="*50)
    
    async with AsyncWebCrawler() as crawler:
        # Create custom extraction strategy with specific settings
        table_strategy = DefaultTableExtraction(
            table_score_threshold=5,  # Lower threshold for more permissive detection
            min_rows=3,  # Only extract tables with at least 3 rows
            min_cols=2,  # Only extract tables with at least 2 columns
            verbose=True
        )
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            table_extraction=table_strategy,
            # Target specific tables using CSS selector
            css_selector="div.main-content"
        )
        
        result = await crawler.arun(
            "https://example.com/data",
            config=config
        )
        
        if result.success:
            print(f"Found {len(result.tables)} tables matching criteria")
            
            for i, table in enumerate(result.tables):
                print(f"\nTable {i+1}:")
                print(f"  Caption: {table.get('caption', 'No caption')}")
                print(f"  Size: {table['metadata']['row_count']} rows × {table['metadata']['column_count']} columns")
                print(f"  Has headers: {table['metadata']['has_headers']}")


async def example_disable_extraction():
    """Example 3: Disable table extraction when not needed."""
    print("\n" + "="*50)
    print("Example 3: Disable Table Extraction")
    print("="*50)
    
    async with AsyncWebCrawler() as crawler:
        # Use NoTableExtraction to skip table processing entirely
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            table_extraction=NoTableExtraction()  # No tables will be extracted
        )
        
        result = await crawler.arun(
            "https://example.com",
            config=config
        )
        
        if result.success:
            print(f"Tables extracted: {len(result.tables)} (should be 0)")
            print("Table extraction disabled - better performance for non-table content")


class FinancialTableExtraction(TableExtractionStrategy):
    """
    Custom strategy for extracting financial tables with specific requirements.
    """
    
    def __init__(self, currency_symbols=None, **kwargs):
        super().__init__(**kwargs)
        self.currency_symbols = currency_symbols or ['$', '€', '£', '¥']
    
    def extract_tables(self, element, **kwargs):
        """Extract only tables that appear to contain financial data."""
        tables_data = []
        
        for table in element.xpath(".//table"):
            # Check if table contains currency symbols
            table_text = ''.join(table.itertext())
            has_currency = any(symbol in table_text for symbol in self.currency_symbols)
            
            if not has_currency:
                continue
            
            # Extract using base logic (could reuse DefaultTableExtraction logic)
            headers = []
            rows = []
            
            # Extract headers
            for th in table.xpath(".//thead//th | .//tr[1]//th"):
                headers.append(th.text_content().strip())
            
            # Extract rows
            for tr in table.xpath(".//tbody//tr | .//tr[position()>1]"):
                row = []
                for td in tr.xpath(".//td"):
                    cell_text = td.text_content().strip()
                    # Clean currency values
                    for symbol in self.currency_symbols:
                        cell_text = cell_text.replace(symbol, '')
                    row.append(cell_text)
                if row:
                    rows.append(row)
            
            if headers or rows:
                tables_data.append({
                    "headers": headers,
                    "rows": rows,
                    "caption": table.xpath(".//caption/text()")[0] if table.xpath(".//caption") else "",
                    "summary": table.get("summary", ""),
                    "metadata": {
                        "type": "financial",
                        "has_currency": True,
                        "row_count": len(rows),
                        "column_count": len(headers) if headers else len(rows[0]) if rows else 0
                    }
                })
        
        return tables_data


async def example_custom_strategy():
    """Example 4: Custom table extraction strategy."""
    print("\n" + "="*50)
    print("Example 4: Custom Financial Table Strategy")
    print("="*50)
    
    async with AsyncWebCrawler() as crawler:
        # Use custom strategy for financial tables
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            table_extraction=FinancialTableExtraction(
                currency_symbols=['$', '€'],
                verbose=True
            )
        )
        
        result = await crawler.arun(
            "https://finance.yahoo.com/",
            config=config
        )
        
        if result.success:
            print(f"Found {len(result.tables)} financial tables")
            
            for table in result.tables:
                if table['metadata'].get('type') == 'financial':
                    print(f"  ✓ Financial table with {table['metadata']['row_count']} rows")


async def example_combined_extraction():
    """Example 5: Combine table extraction with other strategies."""
    print("\n" + "="*50)
    print("Example 5: Combined Extraction Strategies")
    print("="*50)
    
    from crawl4ai import LLMExtractionStrategy, LLMConfig
    
    async with AsyncWebCrawler() as crawler:
        # Define schema for structured extraction
        schema = {
            "type": "object",
            "properties": {
                "page_title": {"type": "string"},
                "main_topic": {"type": "string"},
                "key_figures": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            # Table extraction
            table_extraction=DefaultTableExtraction(
                table_score_threshold=6,
                min_rows=2
            ),
            # LLM extraction for structured data
            extraction_strategy=LLMExtractionStrategy(
                llm_config=LLMConfig(provider="openai"),
                schema=schema
            )
        )
        
        result = await crawler.arun(
            "https://en.wikipedia.org/wiki/Economy_of_the_United_States",
            config=config
        )
        
        if result.success:
            print(f"Tables found: {len(result.tables)}")
            
            # Tables are in result.tables
            if result.tables:
                print(f"First table has {len(result.tables[0]['rows'])} rows")
            
            # Structured data is in result.extracted_content
            if result.extracted_content:
                import json
                structured_data = json.loads(result.extracted_content)
                print(f"Page title: {structured_data.get('page_title', 'N/A')}")
                print(f"Main topic: {structured_data.get('main_topic', 'N/A')}")


async def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("CRAWL4AI TABLE EXTRACTION EXAMPLES")
    print("="*60)
    
    # Run examples
    await example_default_extraction()
    await example_custom_configuration()
    await example_disable_extraction()
    await example_custom_strategy()
    # await example_combined_extraction()  # Requires OpenAI API key
    
    print("\n" + "="*60)
    print("EXAMPLES COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())