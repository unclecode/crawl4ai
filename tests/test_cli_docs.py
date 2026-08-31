import asyncio
from crawl4ai.docs_manager import DocsManager
from click.testing import CliRunner
from crawl4ai.cli import cli


def test_cli():
    """Test all CLI commands"""
    runner = CliRunner()

    print("\n1. Testing docs update...")
    # Use sync version for testing
    docs_manager = DocsManager()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(docs_manager.fetch_docs())

    # print("\n2. Testing listing...")
    # result = runner.invoke(cli, ['docs', 'list'])
    # print(f"Status: {'✅' if result.exit_code == 0 else '❌'}")
    # print(result.output)

    # print("\n2. Testing index building...")
    # result = runner.invoke(cli, ['docs', 'index'])
    # print(f"Status: {'✅' if result.exit_code == 0 else '❌'}")
    # print(f"Output: {result.output}")

    # print("\n3. Testing search...")
    # result = runner.invoke(cli, ['docs', 'search', 'how to use crawler', '--build-index'])
    # print(f"Status: {'✅' if result.exit_code == 0 else '❌'}")
    # print(f"First 200 chars: {result.output[:200]}...")

    # print("\n4. Testing combine with sections...")
    # result = runner.invoke(cli, ['docs', 'combine', 'chunking_strategies', 'extraction_strategies', '--mode', 'extended'])
    # print(f"Status: {'✅' if result.exit_code == 0 else '❌'}")
    # print(f"First 200 chars: {result.output[:200]}...")

    print("\n5. Testing combine all sections...")
    result = runner.invoke(cli, ["docs", "combine", "--mode", "condensed"])
    print(f"Status: {'✅' if result.exit_code == 0 else '❌'}")
    print(f"First 200 chars: {result.output[:200]}...")


if __name__ == "__main__":
    test_cli()
