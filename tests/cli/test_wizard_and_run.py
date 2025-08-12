import pytest
from click.testing import CliRunner
from pathlib import Path
import yaml
from unittest.mock import patch

from crawl4ai.cli import cli

@pytest.fixture
def runner():
    return CliRunner()

def test_init_command_creates_config(runner, tmp_path):
    """
    Test that `crwl init` creates a config file with the expected content
    based on simulated user input.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        # Simulate user input for the wizard
        # 1. URL
        # 2. Crawl Type: Deep Crawl
        # 3. Strategy: bfs
        # 4. Max Pages: 5
        # 5. Max Depth: 1
        # 6. Extraction: Clean Markdown
        # 7. Output: Save to file
        # 8. Output Filename: my_output.md
        # 9. Config Filename: my_crawl.yml
        input_text = (
            "https://example.com\n"
            "Deep Crawl (follow links)\n"
            "bfs\n"
            "5\n"
            "1\n"
            "Clean Markdown Content\n"
            "y\n"
            "my_output.md\n"
            "my_crawl.yml\n"
        )

        result = runner.invoke(cli, ['init'], input=input_text)

        assert result.exit_code == 0
        assert "Configuration saved to `my_crawl.yml`!" in result.output

        config_path = Path(td) / "my_crawl.yml"
        assert config_path.exists()

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert config['url'] == 'https://example.com'
        assert config['deep_crawl']['strategy'] == 'bfs'
        assert config['deep_crawl']['max_pages'] == 5
        assert 'extraction' not in config
        assert config['output']['file'] == 'my_output.md'


@patch('crawl4ai.cli.anyio.run')
def test_run_command_parses_config_and_runs_crawler(mock_anyio_run, runner, tmp_path):
    """
    Test that `crwl run` correctly parses a config file and calls the crawler
    with the appropriate settings.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        # Create a sample config file
        config_data = {
            'url': 'https://test.dev',
            'deep_crawl': {
                'strategy': 'dfs',
                'max_pages': 15,
                'max_depth': 3,
            },
            'output': {
                'file': 'test_output.md'
            }
        }
        config_path = Path(td) / "test_config.yml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Mock the result of the crawl
        class MockCrawlResult:
            class MockMarkdown:
                raw_markdown = "Crawled content"
            markdown = MockMarkdown()
            extracted_content = ""

        mock_anyio_run.return_value = MockCrawlResult()

        result = runner.invoke(cli, ['run', str(config_path)])

        assert result.exit_code == 0
        assert "Output saved to test_output.md" in result.output

        # Check that the output file was created
        output_path = Path(td) / "test_output.md"
        assert output_path.exists()
        assert output_path.read_text() == "Crawled content"

        # Check that the crawler was called with the correct arguments
        mock_anyio_run.assert_called_once()
        args, kwargs = mock_anyio_run.call_args

        # args[0] is the function that was run (run_crawler)
        # args[1] is the url
        assert args[1] == 'https://test.dev'

        # args[2] is the BrowserConfig
        # args[3] is the CrawlerRunConfig
        crawler_config = args[3]
        assert crawler_config.deep_crawl_strategy is not None
        assert crawler_config.deep_crawl_strategy.max_pages == 15
        assert crawler_config.deep_crawl_strategy.max_depth == 3
        assert crawler_config.deep_crawl_strategy.__class__.__name__ == 'DFSDeepCrawlStrategy'
