"""
Demonstration of C4A-Script integration with Crawl4AI
Shows various use cases and features
"""

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import c4a_compile, CompilationResult

async def example_basic_usage():
    """Basic C4A-Script usage with Crawl4AI"""
    print("\n" + "="*60)
    print("Example 1: Basic C4A-Script Usage")
    print("="*60)
    
    # Define your automation script
    c4a_script = """
    # Wait for page to load
    WAIT `body` 2
    
    # Handle cookie banner if present
    IF (EXISTS `.cookie-banner`) THEN CLICK `.accept-btn`
    
    # Scroll down to load more content
    SCROLL DOWN 500
    WAIT 1
    
    # Click load more button if exists
    IF (EXISTS `.load-more`) THEN CLICK `.load-more`
    """
    
    # Create crawler config with C4A script
    config = CrawlerRunConfig(
        url="https://example.com",
        c4a_script=c4a_script,
        wait_for="css:.content",
        verbose=False
    )
    
    print("✅ C4A Script compiled successfully!")
    print(f"Generated {len(config.js_code)} JavaScript commands")
    
    # In production, you would run:
    # async with AsyncWebCrawler() as crawler:
    #     result = await crawler.arun(config=config)


async def example_form_filling():
    """Form filling with C4A-Script"""
    print("\n" + "="*60)
    print("Example 2: Form Filling with C4A-Script")
    print("="*60)
    
    # Form automation script
    form_script = """
    # Set form values
    SET email = "test@example.com"
    SET message = "This is a test message"
    
    # Fill the form
    CLICK `#email-input`
    TYPE $email
    
    CLICK `#message-textarea`
    TYPE $message
    
    # Submit the form
    CLICK `button[type="submit"]`
    
    # Wait for success message
    WAIT `.success-message` 10
    """
    
    config = CrawlerRunConfig(
        url="https://example.com/contact",
        c4a_script=form_script
    )
    
    print("✅ Form filling script ready")
    print("Script will:")
    print("  - Fill email field")
    print("  - Fill message textarea")
    print("  - Submit form")
    print("  - Wait for confirmation")


async def example_dynamic_loading():
    """Handle dynamic content loading"""
    print("\n" + "="*60)
    print("Example 3: Dynamic Content Loading")
    print("="*60)
    
    # Script for infinite scroll or pagination
    pagination_script = """
    # Initial wait
    WAIT `.product-list` 5
    
    # Load all products by clicking "Load More" repeatedly
    REPEAT (CLICK `.load-more`, `document.querySelector('.load-more') !== null`)
    
    # Alternative: Scroll to load (infinite scroll)
    # REPEAT (SCROLL DOWN 1000, `document.querySelectorAll('.product').length < 100`)
    
    # Extract count
    EVAL `console.log('Products loaded: ' + document.querySelectorAll('.product').length)`
    """
    
    config = CrawlerRunConfig(
        url="https://example.com/products",
        c4a_script=pagination_script,
        screenshot=True  # Capture final state
    )
    
    print("✅ Dynamic loading script ready")
    print("Script will load all products by repeatedly clicking 'Load More'")


async def example_multi_step_workflow():
    """Complex multi-step workflow with procedures"""
    print("\n" + "="*60)
    print("Example 4: Multi-Step Workflow with Procedures")
    print("="*60)
    
    # Complex workflow with reusable procedures
    workflow_script = """
    # Define login procedure
    PROC login
      CLICK `#username`
      TYPE "demo_user"
      CLICK `#password`
      TYPE "demo_pass"
      CLICK `#login-btn`
      WAIT `.dashboard` 10
    ENDPROC
    
    # Define search procedure
    PROC search_product
      CLICK `.search-box`
      TYPE "laptop"
      PRESS Enter
      WAIT `.search-results` 5
    ENDPROC
    
    # Main workflow
    GO https://example.com
    login
    search_product
    
    # Process results
    IF (EXISTS `.no-results`) THEN EVAL `console.log('No products found')`
    ELSE REPEAT (CLICK `.add-to-cart`, 3)
    """
    
    # Compile to check for errors
    result = c4a_compile(workflow_script)
    
    if result.success:
        print("✅ Complex workflow compiled successfully!")
        print("Workflow includes:")
        print("  - Login procedure")
        print("  - Product search")
        print("  - Conditional cart additions")
        
        config = CrawlerRunConfig(
            url="https://example.com",
            c4a_script=workflow_script
        )
    else:
        print("❌ Compilation error:")
        error = result.first_error
        print(f"  Line {error.line}: {error.message}")


async def example_error_handling():
    """Demonstrate error handling"""
    print("\n" + "="*60)
    print("Example 5: Error Handling")
    print("="*60)
    
    # Script with intentional error
    bad_script = """
    WAIT body 2
    CLICK button
    IF (EXISTS .modal) CLICK .close
    """
    
    try:
        config = CrawlerRunConfig(
            url="https://example.com",
            c4a_script=bad_script
        )
    except ValueError as e:
        print("✅ Error caught as expected:")
        print(f"  {e}")
        
    # Fixed version
    good_script = """
    WAIT `body` 2
    CLICK `button`
    IF (EXISTS `.modal`) THEN CLICK `.close`
    """
    
    config = CrawlerRunConfig(
        url="https://example.com",
        c4a_script=good_script
    )
    
    print("\n✅ Fixed script compiled successfully!")


async def example_combining_with_extraction():
    """Combine C4A-Script with extraction strategies"""
    print("\n" + "="*60)
    print("Example 6: C4A-Script + Extraction Strategies")
    print("="*60)
    
    from crawl4ai import JsonCssExtractionStrategy
    
    # Script to prepare page for extraction
    prep_script = """
    # Expand all collapsed sections
    REPEAT (CLICK `.expand-btn`, `document.querySelectorAll('.expand-btn:not(.expanded)').length > 0`)
    
    # Load all comments
    IF (EXISTS `.load-comments`) THEN CLICK `.load-comments`
    WAIT `.comments-section` 5
    
    # Close any popups
    IF (EXISTS `.popup-close`) THEN CLICK `.popup-close`
    """
    
    # Define extraction schema
    schema = {
        "name": "article",
        "selector": "article.main",
        "fields": {
            "title": {"selector": "h1", "type": "text"},
            "content": {"selector": ".content", "type": "text"},
            "comments": {
                "selector": ".comment",
                "type": "list",
                "fields": {
                    "author": {"selector": ".author", "type": "text"},
                    "text": {"selector": ".text", "type": "text"}
                }
            }
        }
    }
    
    config = CrawlerRunConfig(
        url="https://example.com/article",
        c4a_script=prep_script,
        extraction_strategy=JsonCssExtractionStrategy(schema),
        wait_for="css:.comments-section"
    )
    
    print("✅ Combined C4A + Extraction ready")
    print("Workflow:")
    print("  1. Expand collapsed sections")
    print("  2. Load comments")
    print("  3. Extract structured data")


async def main():
    """Run all examples"""
    print("\n🚀 C4A-Script + Crawl4AI Integration Demo\n")
    
    # Run all examples
    await example_basic_usage()
    await example_form_filling()
    await example_dynamic_loading()
    await example_multi_step_workflow()
    await example_error_handling()
    await example_combining_with_extraction()
    
    print("\n" + "="*60)
    print("✅ All examples completed successfully!")
    print("="*60)
    
    print("\nTo run actual crawls, uncomment the AsyncWebCrawler sections")
    print("or create your own scripts using these examples as templates.")


if __name__ == "__main__":
    asyncio.run(main())