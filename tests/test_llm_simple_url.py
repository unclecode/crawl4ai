#!/usr/bin/env python3
"""
Test LLMTableExtraction with controlled HTML
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    LLMConfig,
    LLMTableExtraction,
    DefaultTableExtraction,
    CacheMode
)

async def test_controlled_html():
    """Test with controlled HTML content."""
    print("\n" + "=" * 60)
    print("LLM TABLE EXTRACTION TEST")
    print("=" * 60)
    
    # Create test HTML with complex tables
    test_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Test Tables</title></head>
    <body>
        <h1>Sales Data</h1>
        
        <table border="1">
            <caption>Q1 2024 Sales Report</caption>
            <thead>
                <tr>
                    <th rowspan="2">Product</th>
                    <th colspan="3">January</th>
                    <th colspan="3">February</th>
                </tr>
                <tr>
                    <th>Week 1</th>
                    <th>Week 2</th>
                    <th>Week 3</th>
                    <th>Week 1</th>
                    <th>Week 2</th>
                    <th>Week 3</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Widget A</td>
                    <td>100</td>
                    <td>120</td>
                    <td>110</td>
                    <td>130</td>
                    <td>140</td>
                    <td>150</td>
                </tr>
                <tr>
                    <td>Widget B</td>
                    <td>200</td>
                    <td>180</td>
                    <td>190</td>
                    <td>210</td>
                    <td>220</td>
                    <td>230</td>
                </tr>
                <tr>
                    <td colspan="7">Note: All values in thousands USD</td>
                </tr>
            </tbody>
        </table>
        
        <br>
        
        <table>
            <tr>
                <th>Country</th>
                <th>Population</th>
                <th>GDP</th>
            </tr>
            <tr>
                <td>USA</td>
                <td>331M</td>
                <td>$21T</td>
            </tr>
            <tr>
                <td>China</td>
                <td>1.4B</td>
                <td>$14T</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # url = "https://www.w3schools.com/html/html_tables.asp"
    url = "https://en.wikipedia.org/wiki/List_of_chemical_elements"
    # url = "https://en.wikipedia.org/wiki/List_of_prime_ministers_of_India"
    
    # Configure LLM
    llm_config = LLMConfig(
        provider="openai/gpt-4.1-mini",
        # provider="groq/llama-3.3-70b-versatile",
        api_token=os.getenv("OPENAI_API_KEY"),
        # api_token=os.getenv("GROQ_API_KEY"),
        # api_token="os.getenv("GROQ_API_KEY")",
        temperature=0.1,
        max_tokens=32000
    )
    
    print("\n1. Testing LLMTableExtraction:")
    
    # Create LLM extraction strategy
    llm_strategy = LLMTableExtraction(
        llm_config=llm_config,
        verbose=True,
        # css_selector="div.w3-example"
        css_selector="div.mw-content-ltr",
        # css_selector="table.wikitable",
        max_tries=2,
        
        enable_chunking=True,
        chunk_token_threshold=5000,  # Lower threshold to force chunking
        min_rows_per_chunk=10,
        max_parallel_chunks=3
    )
    
    config_llm = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        table_extraction=llm_strategy
    )
    
    async with AsyncWebCrawler() as crawler:
        # Test with LLM extraction
        result_llm = await crawler.arun(
            # url=f"raw:{test_html}",
            url=url,
            config=config_llm
        )
        
        if result_llm.success:
            print(f"\n   ✓ LLM Extraction: Found {len(result_llm.tables)} table(s)")
            
            for i, table in enumerate(result_llm.tables, 1):
                print(f"\n   Table {i}:")
                print(f"   - Caption: {table.get('caption', 'No caption')}")
                print(f"   - Headers: {table['headers']}")
                print(f"   - Rows: {len(table['rows'])}")
                
                # Show how colspan/rowspan were handled
                print(f"   - Sample rows:")
                for j, row in enumerate(table['rows'][:2], 1):
                    print(f"     Row {j}: {row}")
                
                metadata = table.get('metadata', {})
                print(f"   - Metadata:")
                print(f"     • Has merged cells: {metadata.get('has_merged_cells', False)}")
                print(f"     • Table type: {metadata.get('table_type', 'unknown')}")
        
        # # Compare with default extraction
        # print("\n2. Comparing with DefaultTableExtraction:")
        
        # default_strategy = DefaultTableExtraction(
        #     table_score_threshold=3,
        #     verbose=False
        # )
        
        # config_default = CrawlerRunConfig(
        #     cache_mode=CacheMode.BYPASS,
        #     table_extraction=default_strategy
        # )
        
        # result_default = await crawler.arun(
        #     # url=f"raw:{test_html}",
        #     url=url,
        #     config=config_default
        # )
        
        # if result_default.success:
        #     print(f"   ✓ Default Extraction: Found {len(result_default.tables)} table(s)")
            
        #     # Compare handling of complex structures
        #     print("\n3. Comparison Summary:")
        #     print(f"   LLM found: {len(result_llm.tables)} tables")
        #     print(f"   Default found: {len(result_default.tables)} tables")
            
        #     if result_llm.tables and result_default.tables:
        #         llm_first = result_llm.tables[0]
        #         default_first = result_default.tables[0]
                
        #         print(f"\n   First table comparison:")
        #         print(f"   LLM headers: {len(llm_first['headers'])} columns")
        #         print(f"   Default headers: {len(default_first['headers'])} columns")
                
        #         # Check if LLM better handled the complex structure
        #         if llm_first.get('metadata', {}).get('has_merged_cells'):
        #             print("   ✓ LLM correctly identified merged cells")
                
        #         # Test pandas compatibility
        #         try:
        #             import pandas as pd
                    
        #             print("\n4. Testing Pandas compatibility:")
                    
        #             # Create DataFrame from LLM extraction
        #             df_llm = pd.DataFrame(
        #                 llm_first['rows'],
        #                 columns=llm_first['headers']
        #             )
        #             print(f"   ✓ LLM table -> DataFrame: Shape {df_llm.shape}")
                    
        #             # Create DataFrame from default extraction
        #             df_default = pd.DataFrame(
        #                 default_first['rows'],
        #                 columns=default_first['headers']
        #             )
        #             print(f"   ✓ Default table -> DataFrame: Shape {df_default.shape}")
                    
        #             print("\n   LLM DataFrame preview:")
        #             print(df_llm.head(2).to_string())
                    
        #         except ImportError:
        #             print("\n4. Pandas not installed, skipping DataFrame test")
        
        print("\n✅ Test completed successfully!")

async def main():
    """Run the test."""
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Please set it to test LLM extraction.")
        print("   You can set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    await test_controlled_html()

if __name__ == "__main__":
    asyncio.run(main())
    
    
    