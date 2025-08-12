import pytest
from click.testing import CliRunner
from pathlib import Path
import yaml
from unittest.mock import patch

from crawl4ai.cli import cli

@pytest.fixture
def runner():
    return CliRunner()

def test_init_command_creates_config_simple_mode(runner, tmp_path):
    """
    Test that `crwl init` creates a config file with the expected content
    based on simulated user input for simple mode.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        # Simulate user input for the wizard
        # 0. Advanced mode: no
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
            "n\n"
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


def test_init_command_creates_config_advanced_mode(runner, tmp_path):
    """
    Test that `crwl init` creates a config file with advanced settings.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        input_text = (
            "y\n"  # Advanced mode
            "https://advanced.com\n"  # URL
            "Single Page\n"  # Crawl type
            "n\n"  # Headless: no
            "y\n"  # Custom viewport: yes
            "1920\n"  # width
            "1080\n"  # height
            "y\n"  # Proxy: yes
            "http://proxy.com\n"  # Proxy URL
            "y\n"  # Delay: yes
            "3\n"  # Delay seconds
            "Clean Markdown Content\n"  # Extraction
            "n\n"  # Save to file: no
            "advanced_config.yml\n"  # Config filename
        )

        result = runner.invoke(cli, ['init'], input=input_text)

        assert result.exit_code == 0
        config_path = Path(td) / "advanced_config.yml"
        assert config_path.exists()

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert config['url'] == 'https://advanced.com'
        assert config['browser']['headless'] is False
        assert config['browser']['viewport_width'] == 1920
        assert config['browser']['proxy'] == 'http://proxy.com'
        assert config['crawler']['delay_before_return_html'] == 3


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
            'browser': {
                'headless': False,
                'viewport_width': 1024,
            },
            'browser': {
                'headless': False,
                'viewport_width': 1024,
                'proxy': 'http://foo.bar'
            },
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
        browser_config = args[2]
        assert browser_config.headless is False
        assert browser_config.viewport_width == 1024
        assert browser_config.proxy == 'http://foo.bar'

        # args[3] is the CrawlerRunConfig
        crawler_config = args[3]
        assert crawler_config.deep_crawl_strategy is not None
        assert crawler_config.deep_crawl_strategy.max_pages == 15
        assert crawler_config.deep_crawl_strategy.max_depth == 3
        assert crawler_config.deep_crawl_strategy.__class__.__name__ == 'DFSDeepCrawlStrategy'
