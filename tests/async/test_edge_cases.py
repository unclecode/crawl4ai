import os
import re
import sys
import pytest
import json
from bs4 import BeautifulSoup
import asyncio
# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai.async_webcrawler import AsyncWebCrawler

# @pytest.mark.asyncio
# async def test_large_content_page():
#     async with AsyncWebCrawler(verbose=True) as crawler:
#         url = "https://en.wikipedia.org/wiki/List_of_largest_known_stars"  # A page with a large table
#         result = await crawler.arun(url=url, bypass_cache=True)
#         assert result.success
#         assert len(result.html) > 1000000  # Expecting more than 1MB of content

# @pytest.mark.asyncio
# async def test_minimal_content_page():
#     async with AsyncWebCrawler(verbose=True) as crawler:
#         url = "https://example.com"  # A very simple page
#         result = await crawler.arun(url=url, bypass_cache=True)
#         assert result.success
#         assert len(result.html) < 10000  # Expecting less than 10KB of content

# @pytest.mark.asyncio
# async def test_single_page_application():
#     async with AsyncWebCrawler(verbose=True) as crawler:
#         url = "https://reactjs.org/"  # React's website is a SPA
#         result = await crawler.arun(url=url, bypass_cache=True)
#         assert result.success
#         assert "react" in result.html.lower()

# @pytest.mark.asyncio
# async def test_page_with_infinite_scroll():
#     async with AsyncWebCrawler(verbose=True) as crawler:
#         url = "https://news.ycombinator.com/"  # Hacker News has infinite scroll
#         result = await crawler.arun(url=url, bypass_cache=True)
#         assert result.success
#         assert "hacker news" in result.html.lower()

# @pytest.mark.asyncio
# async def test_page_with_heavy_javascript():
#     async with AsyncWebCrawler(verbose=True) as crawler:
#         url = "https://www.airbnb.com/"  # Airbnb uses a lot of JavaScript
#         result = await crawler.arun(url=url, bypass_cache=True)
#         assert result.success
#         assert "airbnb" in result.html.lower()

# @pytest.mark.asyncio
# async def test_page_with_mixed_content():
#     async with AsyncWebCrawler(verbose=True) as crawler:
#         url = "https://github.com/"  # GitHub has a mix of static and dynamic content
#         result = await crawler.arun(url=url, bypass_cache=True)
#         assert result.success
#         assert "github" in result.html.lower()

# Add this test to your existing test file
@pytest.mark.asyncio
async def test_typescript_commits_multi_page():
    first_commit = ""
    async def on_execution_started(page):
        nonlocal first_commit 
        try:
            # Check if the page firct commit h4 text is different from the first commit (use document.querySelector('li.Box-sc-g0xbh4-0 h4'))
            while True:
                await page.wait_for_selector('li.Box-sc-g0xbh4-0 h4')
                commit = await page.query_selector('li.Box-sc-g0xbh4-0 h4')
                commit = await commit.evaluate('(element) => element.textContent')
                commit = re.sub(r'\s+', '', commit)
                if commit and commit != first_commit:
                    first_commit = commit
                    break
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Warning: New content didn't appear after JavaScript execution: {e}")


    async with AsyncWebCrawler(verbose=True) as crawler:
        crawler.crawler_strategy.set_hook('on_execution_started', on_execution_started)

        url = "https://github.com/microsoft/TypeScript/commits/main"
        session_id = "typescript_commits_session"
        all_commits = []

        js_next_page = """
        const button = document.querySelector('a[data-testid="pagination-next-button"]');
        if (button) button.click();
        """

        for page in range(3):  # Crawl 3 pages
            result = await crawler.arun(
                url=url,  # Only use URL for the first page
                session_id=session_id,
                css_selector="li.Box-sc-g0xbh4-0",
                js=js_next_page if page > 0 else None,  # Don't click 'next' on the first page
                bypass_cache=True,
                js_only=page > 0  # Use js_only for subsequent pages
            )

            assert result.success, f"Failed to crawl page {page + 1}"

            # Parse the HTML and extract commits
            soup = BeautifulSoup(result.cleaned_html, 'html.parser')
            commits = soup.select("li")
            # Take first commit find h4 extract text
            first_commit = commits[0].find("h4").text
            first_commit = re.sub(r'\s+', '', first_commit)
            all_commits.extend(commits)

            print(f"Page {page + 1}: Found {len(commits)} commits")

        # Clean up the session
        await crawler.crawler_strategy.kill_session(session_id)

        # Assertions
        assert len(all_commits) >= 90, f"Expected at least 90 commits, but got {len(all_commits)}"
        
        print(f"Successfully crawled {len(all_commits)} commits across 3 pages")                      

# Entry point for debugging
if __name__ == "__main__":
    pytest.main([__file__, "-v"])