"""
Test implementation of AI Assistant extract pipeline using only Crawl4AI capabilities.
This follows the exact flow discussed: query enhancement, classification, HTML skimming,
parent extraction, schema generation, and extraction.
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


async def extract_pipeline(
    base_url: str,
    urls: Union[str, List[str], None],
    query: str,
    target_json_example: Optional[str] = None,
    force_llm: bool = False,
    verbose: bool = True
) -> Union[Dict, List[Dict]]:
    """
    Full implementation of the AI-powered extraction pipeline using only Crawl4AI.
    
    Pipeline:
    1. Quick crawl & HTML skimming
    2. Classification (structural vs semantic) using LLM
    3. Parent element extraction using LLM (for structural)
    4. Schema generation using Crawl4AI's generate_schema
    5. Extraction execution using Crawl4AI strategies
    """
    
    # Normalize URLs
    if urls is None:
        urls = base_url
    target_urls = [urls] if isinstance(urls, str) else urls
    single_result = isinstance(urls, str) or urls is None
    
    # LLM configs for different tasks
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
    
    # Step 1: Starting
    vprint(f"Query: '{query}'")
    
    # Step 2: Quick crawl for analysis
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
        
        # Step 3: HTML Skimming using lxml
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
        
        # Step 4: Classification using LLM
        classification = 'semantic'  # Default
        
        if not force_llm:
            classification_prompt = f"""
            Analyze this HTML to determine extraction strategy.
            
            Query: "{query}"
            
            HTML sample:
            <<<<HTML>>>
            {skimmed_html}
            <<<<END HTML>>>
            
            Determine if this can be extracted using CSS/XPath patterns (structural) 
            or requires semantic understanding (semantic).
            
            Look for:
            - Repeating patterns (lists, cards, tables) → structural
            - Consistent HTML structure → structural
            - Need for inference or understanding → semantic
            
            Return JSON:
            {{
                "strategy": "structural" or "semantic",
                "confidence": 0.0-1.0,
                "reasoning": "..."
            }}
            """
            
            response = perform_completion_with_backoff(
                provider=llm_small.provider,
                prompt_with_variables=classification_prompt,
                api_token=llm_small.api_token,
                json_response=True,
                temperature=llm_small.temperature
            )
            
            classification_result = json.loads(response.choices[0].message.content)
            classification = classification_result['strategy']
            vprint(f"Classification: {classification} (confidence: {classification_result['confidence']})")
            vprint(f"Reasoning: {classification_result['reasoning']}")
        
        if force_llm:
            classification = 'semantic'
            vprint("Forced LLM extraction")
        
        # Step 5 & 6: Execute appropriate extraction strategy
        if classification == 'structural':
            # Extract parent element using LLM with proper explanation
            parent_prompt = f"""
            Identify the CSS selector for the BASE ELEMENT TEMPLATE containing the data to extract.
            
            IMPORTANT: The base element template is a repeating pattern in the HTML where each instance
            contains one item of data (like a product card, article card, issue card, etc.). 
            
            The selector should:
            - Not be too specific (avoid selecting just one item)
            - Not be too general (avoid selecting unrelated elements)
            - Select ALL instances of the repeating pattern
            - Point to the container that holds ONE complete data item
            
            For example:
            - On Amazon: div.s-result-item (each product card)
            - On GitHub issues: div[id^="issue_"] (each issue card)
            - On a blog: article.post-card (each article)
            
            User query: "{query}"
            """
            
            if target_json_example:
                parent_prompt += f"""
            
            The user expects to extract data in this format:
            {target_json_example}
            
            Find the base element that contains all these fields.
            """
            else:
                parent_prompt += """
            
            Also provide a JSON example of what data can be extracted from one instance of this base element.
            """
            
            parent_prompt += f"""
            
            HTML (first 8000 chars):
            <<<<HTML>>>
            {skimmed_html}
            <<<<END HTML>>>
            
            Return JSON:
            {{
                "parent_selector": "css_selector_here",
                "explanation": "why this selector is appropriate","""
            
            if not target_json_example:
                parent_prompt += """
                "suggested_json_example": {
                    "field1": "example value",
                    "field2": "example value"
                }"""
            
            parent_prompt += """
            }}
            """
            
            response = perform_completion_with_backoff(
                provider=llm_small.provider,
                prompt_with_variables=parent_prompt,
                api_token=llm_small.api_token,
                json_response=True,
                temperature=llm_small.temperature
            )
            
            parent_data = json.loads(response.choices[0].message.content)
            parent_selector = parent_data['parent_selector']
            vprint(f"Parent selector: {parent_selector}")
            vprint(f"Explanation: {parent_data['explanation']}")
            
            # Use suggested JSON example if no target provided
            if not target_json_example and 'suggested_json_example' in parent_data:
                target_json_example = json.dumps(parent_data['suggested_json_example'])
                vprint(f"Using LLM suggested example: {target_json_example}")
            
            # Get the actual parent HTML for schema generation
            tree = lxml_html.fromstring(quick_result.html)
            parent_elements = tree.cssselect(parent_selector)
            
            if not parent_elements:
                vprint("Parent selector not found, falling back to semantic")
                classification = 'semantic'
            else:
                # Use the first instance as sample
                sample_html = lxml_html.tostring(parent_elements[0], encoding='unicode')
                vprint(f"Generating schema from sample HTML ({len(sample_html)} chars)")
                
                # Generate schema using Crawl4AI
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
                
                for url in target_urls:
                    vprint(f"Extracting from: {url}")
                    result = await crawler.arun(
                        url=url,
                        config=CrawlerRunConfig(
                            extraction_strategy=extraction_strategy,
                            cache_mode="bypass"
                        )
                    )
                    
                    if result.success and result.extracted_content:
                        data = json.loads(result.extracted_content)
                        results.append({
                            'url': url,
                            'data': data,
                            'count': len(data) if isinstance(data, list) else 1,
                            'method': 'JsonCssExtraction',
                            'schema': schema
                        })
                
                return results[0] if single_result else results
        
        # Semantic extraction (LLM)
        if classification == 'semantic':
            vprint("Using LLM extraction")
            
            # Build instruction from query
            instruction = f"""
            {query}
            
            Return structured JSON data.
            """
            
            extraction_strategy = LLMExtractionStrategy(
                llm_config=llm_strong,
                instruction=instruction
            )
            
            results = []
            for url in target_urls:
                vprint(f"LLM extracting from: {url}")
                result = await crawler.arun(
                    url=url,
                    config=CrawlerRunConfig(
                        extraction_strategy=extraction_strategy,
                        cache_mode="bypass"
                    )
                )
                
                if result.success and result.extracted_content:
                    data = json.loads(result.extracted_content)
                    results.append({
                        'url': url,
                        'data': data,
                        'count': len(data) if isinstance(data, list) else 1,
                        'method': 'LLMExtraction'
                    })
            
            return results[0] if single_result else results


async def main():
    """Test the extraction pipeline."""
    
    print("\n🚀 CRAWL4AI EXTRACTION PIPELINE TEST")
    print("="*50)
    
    # Test structural extraction
    try:
        result = await extract_pipeline(
            base_url="https://github.com/unclecode/crawl4ai/issues",
            urls=None,
            query="I want to extract all issue titles, numbers, and who opened them",
            verbose=True
        )
        
        print(f"\n✅ Success! Extracted {result.get('count', 0)} items")
        print(f"Method used: {result.get('method')}")
        
        if result.get('data'):
            print("\nFirst few items:")
            data = result['data']
            items_to_show = data[:3] if isinstance(data, list) else data
            print(json.dumps(items_to_show, indent=2))
            
            if result.get('schema'):
                print(f"\nGenerated schema fields: {[f['name'] for f in result['schema'].get('fields', [])]}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Error: OPENAI_API_KEY environment variable not set")
        exit(1)
    
    asyncio.run(main())
    
    
