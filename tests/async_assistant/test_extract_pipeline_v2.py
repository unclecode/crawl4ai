"""
Test implementation v2: Combined classification and preparation in one LLM call.
More efficient approach that reduces token usage and LLM calls.
"""

import asyncio
import json
import os
from typing import List, Dict, Any, Optional, Union
from lxml import html as lxml_html
import re

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import LLMConfig
from crawl4ai import JsonCssExtractionStrategy, LLMExtractionStrategy
from crawl4ai.utils import perform_completion_with_backoff


async def extract_pipeline_v2(
    base_url: str,
    urls: Union[str, List[str], None],
    query: str,
    target_json_example: Optional[str] = None,
    force_llm: bool = False,
    verbose: bool = True
) -> Union[Dict, List[Dict]]:
    """
    Improved extraction pipeline with combined classification and preparation.
    
    Pipeline:
    1. Quick crawl & HTML skimming
    2. Combined LLM call for classification + preparation
    3. Execute appropriate extraction strategy
    """
    
    # Normalize URLs
    if urls is None:
        urls = base_url
    target_urls = [urls] if isinstance(urls, str) else urls
    single_result = isinstance(urls, str) or urls is None
    
    # LLM configs
    llm_small = LLMConfig(
        provider="openai/gpt-4o-mini",
        api_token=os.getenv("OPENAI_API_KEY")
    )
    llm_small.temperature = 0.3
    
    llm_strong = LLMConfig(
        provider="openai/gpt-4o",
        api_token=os.getenv("OPENAI_API_KEY")
    )
    llm_strong.temperature = 0.5
    
    def vprint(msg: str):
        if verbose:
            print(f"🔍 {msg}")
    
    vprint(f"Query: '{query}'")
    if target_json_example:
        vprint(f"Target format provided: {target_json_example[:100]}...")
    
    # Step 1: Quick crawl for analysis
    async with AsyncWebCrawler(verbose=False) as crawler:
        vprint(f"Quick crawl: {base_url}")
        quick_result = await crawler.arun(
            url=base_url,
            config=CrawlerRunConfig(
                cache_mode="bypass",
                delay_before_return_html=2.0
            )
        )
        
        if not quick_result.success:
            raise Exception(f"Failed to crawl {base_url}")
        
        # HTML Skimming
        def skim_html(html: str) -> str:
            """Remove non-structural elements using lxml."""
            parser = lxml_html.HTMLParser(remove_comments=True)
            tree = lxml_html.fromstring(html, parser=parser)
            
            # Remove head section entirely
            for head in tree.xpath('//head'):
                head.getparent().remove(head)
            
            # Remove non-structural elements including SVGs
            for element in tree.xpath('//script | //style | //noscript | //meta | //link | //svg'):
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)
            
            # Remove base64 images
            for img in tree.xpath('//img[@src]'):
                src = img.get('src', '')
                if 'base64' in src:
                    img.set('src', 'BASE64_IMAGE')
            
            # Remove long class/id attributes
            for element in tree.xpath('//*[@class or @id]'):
                if element.get('class') and len(element.get('class')) > 100:
                    element.set('class', 'LONG_CLASS')
                if element.get('id') and len(element.get('id')) > 50:
                    element.set('id', 'LONG_ID')
            
            # Truncate text nodes
            for text_node in tree.xpath('//text()'):
                if text_node.strip() and len(text_node) > 100:
                    parent = text_node.getparent()
                    if parent is not None:
                        new_text = text_node[:50] + "..." + text_node[-20:]
                        if text_node.is_text:
                            parent.text = new_text
                        elif text_node.is_tail:
                            parent.tail = new_text
            
            return lxml_html.tostring(tree, encoding='unicode')
        
        skimmed_html = skim_html(quick_result.html)
        vprint(f"Skimmed HTML from {len(quick_result.html)} to {len(skimmed_html)} chars")
        
        # Step 2: Combined classification and preparation
        if force_llm:
            classification_data = {"classification": "semantic"}
            vprint("Forced LLM extraction")
        else:
            combined_prompt = f"""
            Analyze this HTML and prepare for data extraction.
            
            User query: "{query}"
            """
            
            if target_json_example:
                combined_prompt += f"""
            Target format: {target_json_example}
            """
            
            combined_prompt += f"""
            
            HTML:
            <<<<HTML>>>>
            {skimmed_html}
            <<<<END HTML>>>>
            
            STEP 1: Determine extraction strategy
            - If data follows repeating HTML patterns (lists, tables, cards) → "structural"
            - If data requires understanding/inference → "semantic"
            
            STEP 2A: If STRUCTURAL extraction is appropriate:
            - Find the CSS selector for the BASE ELEMENT (repeating pattern)
            - Base element = container holding ONE data item (e.g., product card, table row)
            - Selector should select ALL instances, not too specific, not too general
            - Count approximate number of these elements
            """
            
            if not target_json_example:
                combined_prompt += """
            - Suggest what JSON structure can be extracted from one element
            """
            
            combined_prompt += """
            
            STEP 2B: If SEMANTIC extraction is needed:
            - Write a detailed instruction for what to extract
            - Be specific about the data needed
            """
            
            if not target_json_example:
                combined_prompt += """
            - Suggest expected JSON output structure
            """
            
            combined_prompt += """
            
            Return JSON with ONLY the relevant fields based on classification:
            {
                "classification": "structural" or "semantic",
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation",
                
                // Include ONLY if classification is "structural":
                "base_selector": "css selector",
                "element_count": approximate number,
                
                // Include ONLY if classification is "semantic":
                "extraction_instruction": "detailed instruction",
                
                // Include if no target_json_example was provided:
                "suggested_json_example": { ... }
            }
            """
            
            response = perform_completion_with_backoff(
                provider=llm_small.provider,
                prompt_with_variables=combined_prompt,
                api_token=llm_small.api_token,
                json_response=True,
                temperature=llm_small.temperature
            )
            
            classification_data = json.loads(response.choices[0].message.content)
            vprint(f"Classification: {classification_data['classification']} (confidence: {classification_data['confidence']})")
            vprint(f"Reasoning: {classification_data['reasoning']}")
        
        # Use suggested JSON example if needed
        if not target_json_example and 'suggested_json_example' in classification_data:
            target_json_example = json.dumps(classification_data['suggested_json_example'])
            vprint(f"Using suggested example: {target_json_example}")
        
        # Step 3: Execute extraction based on classification
        if classification_data['classification'] == 'structural':
            vprint(f"Base selector: {classification_data['base_selector']}")
            vprint(f"Found ~{classification_data['element_count']} elements")
            
            # Get sample HTML for schema generation
            tree = lxml_html.fromstring(quick_result.html)
            parent_elements = tree.cssselect(classification_data['base_selector'])
            
            if not parent_elements:
                vprint("Base selector not found, falling back to semantic")
                classification_data['classification'] = 'semantic'
            else:
                # Use first element as sample
                sample_html = lxml_html.tostring(parent_elements[0], encoding='unicode')
                vprint(f"Generating schema from sample ({len(sample_html)} chars)")
                
                # Generate schema
                schema_params = {
                    "html": sample_html,
                    "query": query,
                    "llm_config": llm_strong
                }
                
                if target_json_example:
                    schema_params["target_json_example"] = target_json_example
                
                schema = JsonCssExtractionStrategy.generate_schema(**schema_params)
                vprint(f"Generated schema with {len(schema.get('fields', []))} fields")
                
                # Extract from all URLs
                extraction_strategy = JsonCssExtractionStrategy(schema)
                results = []
                
                for idx, url in enumerate(target_urls):
                    vprint(f"Extracting from: {url}")
                    
                    # Use already crawled HTML for base_url, crawl others
                    if idx == 0 and url == base_url:
                        # We already have this HTML, use raw:// to avoid re-crawling
                        raw_url = f"raw://{quick_result.html}"
                        vprint("Using cached HTML with raw:// scheme")
                    else:
                        # Need to crawl this URL
                        raw_url = url
                    
                    result = await crawler.arun(
                        url=raw_url,
                        config=CrawlerRunConfig(
                            extraction_strategy=extraction_strategy,
                            cache_mode="bypass"
                        )
                    )
                    
                    if result.success and result.extracted_content:
                        data = json.loads(result.extracted_content)
                        results.append({
                            'url': url,  # Keep original URL for reference
                            'data': data,
                            'count': len(data) if isinstance(data, list) else 1,
                            'method': 'JsonCssExtraction',
                            'schema': schema
                        })
                
                return results[0] if single_result else results
        
        # Semantic extraction
        if classification_data['classification'] == 'semantic':
            vprint("Using LLM extraction")
            
            # Use generated instruction or create simple one
            if 'extraction_instruction' in classification_data:
                instruction = classification_data['extraction_instruction']
                vprint(f"Generated instruction: {instruction[:100]}...")
            else:
                instruction = f"{query}\n\nReturn structured JSON data."
            
            extraction_strategy = LLMExtractionStrategy(
                llm_config=llm_strong,
                instruction=instruction
            )
            
            results = []
            for idx, url in enumerate(target_urls):
                vprint(f"LLM extracting from: {url}")
                
                # Use already crawled HTML for base_url, crawl others
                if idx == 0 and url == base_url:
                    # We already have this HTML, use raw:// to avoid re-crawling
                    raw_url = f"raw://{quick_result.html}"
                    vprint("Using cached HTML with raw:// scheme")
                else:
                    # Need to crawl this URL
                    raw_url = url
                
                result = await crawler.arun(
                    url=raw_url,
                    config=CrawlerRunConfig(
                        extraction_strategy=extraction_strategy,
                        cache_mode="bypass"
                    )
                )
                
                if result.success and result.extracted_content:
                    data = json.loads(result.extracted_content)
                    results.append({
                        'url': url,  # Keep original URL for reference
                        'data': data,
                        'count': len(data) if isinstance(data, list) else 1,
                        'method': 'LLMExtraction'
                    })
            
            return results[0] if single_result else results


async def main():
    """Test the improved extraction pipeline."""
    
    print("\n🚀 CRAWL4AI EXTRACTION PIPELINE V2 TEST")
    print("="*50)
    
    try:
        # Test 1: Structural extraction (GitHub issues)
        print("\nTest 1: GitHub Issues (should use structural)")
        result = await extract_pipeline_v2(
            base_url="https://github.com/unclecode/crawl4ai/issues",
            urls=None,
            query="Extract all issue titles, numbers, and authors",
            verbose=True
        )
        
        print(f"\n✅ Extracted {result.get('count', 0)} items using {result.get('method')}")
        if result.get('data'):
            print("Sample:", json.dumps(result['data'][:2] if isinstance(result['data'], list) else result['data'], indent=2))
        
        # Test 2: With target JSON example
        print("\n\nTest 2: With target JSON example")
        target_example = json.dumps({
            "title": "Issue title here",
            "number": "#123",
            "author": "username"
        })
        
        result2 = await extract_pipeline_v2(
            base_url="https://github.com/unclecode/crawl4ai/issues",
            urls=None,
            query="Extract GitHub issues",
            target_json_example=target_example,
            verbose=True
        )
        
        print(f"\n✅ Extracted {result2.get('count', 0)} items")
        
        # Test 3: Semantic extraction (force LLM)
        print("\n\nTest 3: Force semantic extraction")
        result3 = await extract_pipeline_v2(
            base_url="https://en.wikipedia.org/wiki/Artificial_intelligence",
            urls=None,
            query="Extract key concepts and their relationships in AI field",
            force_llm=True,
            verbose=True
        )
        
        print(f"\n✅ Extracted using {result3.get('method')}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Error: OPENAI_API_KEY environment variable not set")
        exit(1)
    
    asyncio.run(main())