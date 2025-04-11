import sys

import pytest

from crawl4ai.legacy.docs_manager import DocsManager


@pytest.mark.asyncio
async def test_cli():
    """Test all CLI commands"""
    print("\n1. Testing docs update...")
    docs_manager = DocsManager()
    result = await docs_manager.fetch_docs()
    assert result


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
