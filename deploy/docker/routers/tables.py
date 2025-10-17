"""
Table Extraction Router for Crawl4AI Docker Server

This module provides dedicated endpoints for table extraction from HTML or URLs,
separate from the main crawling functionality.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

# Import crawler pool for browser reuse
from crawler_pool import get_crawler

# Import schemas
from schemas import (
    TableExtractionRequest,
    TableExtractionBatchRequest,
    TableExtractionConfig,
)

# Import utilities
from utils import (
    extract_tables_from_html,
    format_table_response,
    create_table_extraction_strategy,
)

# Configure logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/tables", tags=["Table Extraction"])


@router.post(
    "/extract",
    summary="Extract Tables from HTML or URL",
    description="""
Extract tables from HTML content or by fetching a URL.
Supports multiple extraction strategies: default, LLM-based, or financial.
    
**Input Options:**
- Provide `html` for direct HTML content extraction
- Provide `url` to fetch and extract from a live page
- Cannot provide both `html` and `url` simultaneously

**Strategies:**
- `default`: Fast regex and HTML structure-based extraction
- `llm`: AI-powered extraction with semantic understanding (requires LLM config)
- `financial`: Specialized extraction for financial tables with numerical formatting

**Returns:**
- List of extracted tables with headers, rows, and metadata
- Each table includes cell-level details and formatting information
""",
    response_description="Extracted tables with metadata",
)
async def extract_tables(request: TableExtractionRequest) -> JSONResponse:
    """
    Extract tables from HTML content or URL.

    Args:
        request: TableExtractionRequest with html/url and extraction config

    Returns:
        JSONResponse with extracted tables and metadata

    Raises:
        HTTPException: If validation fails or extraction errors occur
    """
    try:
        # Validate input
        if request.html and request.url:
            raise HTTPException(
                status_code=400,
                detail="Cannot provide both 'html' and 'url'. Choose one input method."
            )

        if not request.html and not request.url:
            raise HTTPException(
                status_code=400,
                detail="Must provide either 'html' or 'url' for table extraction."
            )

        # Handle URL-based extraction
        if request.url:
            # Import crawler configs
            from async_configs import BrowserConfig, CrawlerRunConfig

            try:
                # Create minimal browser config
                browser_config = BrowserConfig(
                    headless=True,
                    verbose=False,
                )

                # Create crawler config with table extraction
                table_strategy = create_table_extraction_strategy(request.config)
                crawler_config = CrawlerRunConfig(
                    table_extraction_strategy=table_strategy,
                )

                # Get crawler from pool (browser reuse for memory efficiency)
                crawler = await get_crawler(browser_config, adapter=None)
                
                # Crawl the URL
                result = await crawler.arun(
                    url=request.url,
                    config=crawler_config,
                )

                if not result.success:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to fetch URL: {result.error_message}"
                    )

                # Extract HTML
                html_content = result.html

            except Exception as e:
                logger.error(f"Error fetching URL {request.url}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch and extract from URL: {str(e)}"
                )

        else:
            # Use provided HTML
            html_content = request.html

        # Extract tables from HTML
        tables = await extract_tables_from_html(html_content, request.config)

        # Format response
        formatted_tables = format_table_response(tables)

        return JSONResponse({
            "success": True,
            "table_count": len(formatted_tables),
            "tables": formatted_tables,
            "strategy": request.config.strategy.value,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting tables: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Table extraction failed: {str(e)}"
        )


@router.post(
    "/extract/batch",
    summary="Extract Tables from Multiple Sources (Batch)",
    description="""
Extract tables from multiple HTML contents or URLs in a single request.
Processes each input independently and returns results for all.

**Batch Processing:**
- Provide list of HTML contents and/or URLs
- Each input is processed with the same extraction strategy
- Partial failures are allowed (returns results for successful extractions)

**Use Cases:**
- Extracting tables from multiple pages simultaneously
- Bulk financial data extraction
- Comparing table structures across multiple sources
""",
    response_description="Batch extraction results with per-item success status",
)
async def extract_tables_batch(request: TableExtractionBatchRequest) -> JSONResponse:
    """
    Extract tables from multiple HTML contents or URLs in batch.

    Args:
        request: TableExtractionBatchRequest with list of html/url and config

    Returns:
        JSONResponse with batch results

    Raises:
        HTTPException: If validation fails
    """
    try:
        # Validate batch request
        total_items = len(request.html_list or []) + len(request.url_list or [])
        
        if total_items == 0:
            raise HTTPException(
                status_code=400,
                detail="Must provide at least one HTML content or URL in batch request."
            )

        if total_items > 50:  # Reasonable batch limit
            raise HTTPException(
                status_code=400,
                detail=f"Batch size ({total_items}) exceeds maximum allowed (50)."
            )

        results = []

        # Process HTML list
        if request.html_list:
            for idx, html_content in enumerate(request.html_list):
                try:
                    tables = await extract_tables_from_html(html_content, request.config)
                    formatted_tables = format_table_response(tables)
                    
                    results.append({
                        "success": True,
                        "source": f"html_{idx}",
                        "table_count": len(formatted_tables),
                        "tables": formatted_tables,
                    })
                except Exception as e:
                    logger.error(f"Error extracting tables from html_{idx}: {e}")
                    results.append({
                        "success": False,
                        "source": f"html_{idx}",
                        "error": str(e),
                    })

        # Process URL list
        if request.url_list:
            from async_configs import BrowserConfig, CrawlerRunConfig

            browser_config = BrowserConfig(
                headless=True,
                verbose=False,
            )
            table_strategy = create_table_extraction_strategy(request.config)
            crawler_config = CrawlerRunConfig(
                table_extraction_strategy=table_strategy,
            )

            # Get crawler from pool (reuse browser for all URLs in batch)
            crawler = await get_crawler(browser_config, adapter=None)
            
            for url in request.url_list:
                try:
                    result = await crawler.arun(
                        url=url,
                        config=crawler_config,
                    )

                    if result.success:
                        html_content = result.html
                        tables = await extract_tables_from_html(html_content, request.config)
                        formatted_tables = format_table_response(tables)
                        
                        results.append({
                            "success": True,
                            "source": url,
                            "table_count": len(formatted_tables),
                            "tables": formatted_tables,
                        })
                    else:
                        results.append({
                            "success": False,
                            "source": url,
                            "error": result.error_message,
                        })

                except Exception as e:
                    logger.error(f"Error extracting tables from {url}: {e}")
                    results.append({
                            "success": False,
                            "source": url,
                            "error": str(e),
                        })

        # Calculate summary
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        total_tables = sum(r.get("table_count", 0) for r in results if r["success"])

        return JSONResponse({
            "success": True,
            "summary": {
                "total_processed": len(results),
                "successful": successful,
                "failed": failed,
                "total_tables_extracted": total_tables,
            },
            "results": results,
            "strategy": request.config.strategy.value,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch table extraction: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch table extraction failed: {str(e)}"
        )
