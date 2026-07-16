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
    
    url = "https://en.wikipedia.org/wiki/List_of_chemical_elements"
    # url = "https://en.wikipedia.org/wiki/List_of_prime_ministers_of_India"
    
    # Configure LLM
    llm_config = LLMConfig(
        # provider="openai/gpt-4.1-mini",
        # api_token=os.getenv("OPENAI_API_KEY"),
        provider="groq/llama-3.3-70b-versatile",
        api_token="GROQ_API_TOKEN",
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
    
    
    