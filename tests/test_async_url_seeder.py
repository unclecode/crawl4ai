import pytest
import asyncio
from crawl4ai.async_url_seeder import AsyncUrlSeeder

@pytest.mark.asyncio
async def test_resolve_head_handles_dead_redirects():
    seeder = AsyncUrlSeeder()
    # Should return None – redirects to a dead URL
    assert await seeder._resolve_head("http://youtube.com/sitemap.xml") is None
    assert await seeder._resolve_head("https://stripe.com/sitemap.xml") is None

@pytest.mark.asyncio
async def test_resolve_head_direct_hit():
    seeder = AsyncUrlSeeder()
    # Test with a known live URL, e.g., httpbin
    result = await seeder._resolve_head("https://httpbin.org/status/200")
    assert result == "https://httpbin.org/status/200"

@pytest.mark.asyncio
async def test_resolve_head_verify_redirect_targets_false():
    # Test with verification disabled - should return redirect target without checking if alive
    seeder = AsyncUrlSeeder(verify_redirect_targets=False)
    # This should return the redirect target even if it's dead (old behavior)
    result = await seeder._resolve_head("http://youtube.com/sitemap.xml")
    # The exact redirect target might vary, but it should not be None
    assert result is not None
    assert isinstance(result, str)
    # Should be different from the input URL (indicating redirect was followed)
    assert result != "http://youtube.com/sitemap.xml"