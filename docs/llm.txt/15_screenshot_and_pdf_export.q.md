page_capture: Full-page screenshots and PDFs can be generated for massive webpages using Crawl4AI | webpage capture, full page screenshot, pdf export | AsyncWebCrawler().arun(url=url, pdf=True, screenshot=True)
pdf_approach: Pages are first exported as PDF then converted to high-quality images for better handling of large content | pdf conversion, image export, page rendering | result.pdf, result.screenshot
export_benefits: PDF export method never times out and works with any page length | timeout handling, page size limits, reliability | pdf=True
dual_output: Get both PDF and screenshot in single crawl without reloading | multiple formats, single pass, efficient capture | pdf=True, screenshot=True
result_handling: Screenshot and PDF data are returned as base64 encoded strings | base64 encoding, binary data, file saving | b64decode(result.screenshot), b64decode(result.pdf)
cache_control: Cache mode can be bypassed for fresh page captures | caching, fresh content, bypass cache | cache_mode=CacheMode.BYPASS
async_operation: Crawler operates asynchronously using Python's asyncio framework | async/await, concurrent execution | async with AsyncWebCrawler() as crawler
file_saving: Screenshots and PDFs can be saved directly to local files | file output, save results, local storage | open("screenshot.png", "wb"), open("page.pdf", "wb")
error_handling: Success status can be checked before processing results | error checking, result validation | if result.success: