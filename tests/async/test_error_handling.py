# import os
# import sys
# import pytest
# import asyncio

# # Add the parent directory to the Python path
# parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(parent_dir)

# from crawl4ai.async_webcrawler import AsyncWebCrawler
# from crawl4ai.utils import InvalidCSSSelectorError

# class AsyncCrawlerWrapper:
#     def __init__(self):
#         self.crawler = None

#     async def setup(self):
#         self.crawler = AsyncWebCrawler(verbose=True)
#         await self.crawler.awarmup()

#     async def cleanup(self):
#         if self.crawler:
#             await self.crawler.aclear_cache()

# @pytest.fixture(scope="module")
# def crawler_wrapper():
#     wrapper = AsyncCrawlerWrapper()
#     asyncio.get_event_loop().run_until_complete(wrapper.setup())
#     yield wrapper
#     asyncio.get_event_loop().run_until_complete(wrapper.cleanup())

# @pytest.mark.asyncio
# async def test_network_error(crawler_wrapper):
#     url = "https://www.nonexistentwebsite123456789.com"
#     result = await crawler_wrapper.crawler.arun(url=url, bypass_cache=True)
#     assert not result.success
#     assert "Failed to crawl" in result.error_message

# # @pytest.mark.asyncio
# # async def test_timeout_error(crawler_wrapper):
# #     # Simulating a timeout by using a very short timeout value
# #     url = "https://www.nbcnews.com/business"
# #     result = await crawler_wrapper.crawler.arun(url=url, bypass_cache=True, timeout=0.001)
# #     assert not result.success
# #     assert "timeout" in result.error_message.lower()

# # @pytest.mark.asyncio
# # async def test_invalid_css_selector(crawler_wrapper):
# #     url = "https://www.nbcnews.com/business"
# #     with pytest.raises(InvalidCSSSelectorError):
# #         await crawler_wrapper.crawler.arun(url=url, bypass_cache=True, css_selector="invalid>>selector")

# # @pytest.mark.asyncio
# # async def test_js_execution_error(crawler_wrapper):
# #     url = "https://www.nbcnews.com/business"
# #     invalid_js = "This is not valid JavaScript code;"
# #     result = await crawler_wrapper.crawler.arun(url=url, bypass_cache=True, js=invalid_js)
# #     assert not result.success
# #     assert "JavaScript" in result.error_message

# # @pytest.mark.asyncio
# # async def test_empty_page(crawler_wrapper):
# #     # Use a URL that typically returns an empty page
# #     url = "http://example.com/empty"
# #     result = await crawler_wrapper.crawler.arun(url=url, bypass_cache=True)
# #     assert result.success  # The crawl itself should succeed
# #     assert not result.markdown.strip()  # The markdown content should be empty or just whitespace

# # @pytest.mark.asyncio
# # async def test_rate_limiting(crawler_wrapper):
# #     # Simulate rate limiting by making multiple rapid requests
# #     url = "https://www.nbcnews.com/business"
# #     results = await asyncio.gather(*[crawler_wrapper.crawler.arun(url=url, bypass_cache=True) for _ in range(10)])
# #     assert any(not result.success and "rate limit" in result.error_message.lower() for result in results)

# # Entry point for debugging
# if __name__ == "__main__":
#     pytest.main([__file__, "-v"])