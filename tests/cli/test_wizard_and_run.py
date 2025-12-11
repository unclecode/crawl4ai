import pytest
from click.testing import CliRunner
from pathlib import Path
import yaml
from unittest.mock import patch

from crawl4ai.cli import cli

@pytest.fixture
def runner():
    return CliRunner()

def test_scrape_article_preset(runner, tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        input_text = (
            "Scrape a single article (get clean markdown)\n"
            "http://article.com\n"
            "my_article.md\n"
            "article_config.yml\n"
        )
        result = runner.invoke(cli, ['init'], input=input_text)
        assert result.exit_code == 0
        config_path = Path(td) / "article_config.yml"
        assert config_path.exists()
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        assert config['url'] == 'http://article.com'
        assert config['output']['file'] == 'my_article.md'
        assert 'deep_crawl' not in config
        assert 'extraction' not in config

def test_crawl_website_preset(runner, tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        input_text = (
            "Crawl an entire website (deep crawl)\n"
            "http://website.com\n"
            "dfs\n"
            "20\n"
            "5\n"
            "website.md\n"
            "website_config.yml\n"
        )
        result = runner.invoke(cli, ['init'], input=input_text)
        assert result.exit_code == 0
        config_path = Path(td) / "website_config.yml"
        assert config_path.exists()
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        assert config['url'] == 'http://website.com'
        assert config['deep_crawl']['strategy'] == 'dfs'
        assert config['deep_crawl']['max_pages'] == 20
        assert config['deep_crawl']['max_depth'] == 5
        assert config['output']['file'] == 'website.md'

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


@patch('crawl4ai.cli.anyio.run')
def test_run_command_with_css_extraction(mock_anyio_run, runner, tmp_path):
    """
    Test that the run command correctly uses JsonCssExtractionStrategy
    when specified in the config.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        css_schema = {
            'baseSelector': '.item',
            'fields': [
                {'name': 'title', 'selector': 'h2', 'type': 'text'},
                {'name': 'link', 'selector': 'a', 'type': 'attribute', 'attribute': 'href'},
            ]
        }
        config_data = {
            'url': 'https://css-test.dev',
            'extraction': {
                'type': 'json-css',
                'schema': css_schema,
            }
        }
        config_path = Path(td) / "css_config.yml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Mock the result of the crawl
        class MockCrawlResult:
            extracted_content = '[]' # Mock empty json array
        mock_anyio_run.return_value = MockCrawlResult()

        result = runner.invoke(cli, ['run', str(config_path)])

        assert result.exit_code == 0

        # Check that the crawler was called with the correct strategy
        mock_anyio_run.assert_called_once()
        args, kwargs = mock_anyio_run.call_args

        crawler_config = args[3]
        strategy = crawler_config.extraction_strategy
        assert strategy.__class__.__name__ == 'JsonCssExtractionStrategy'
        assert strategy.schema == css_schema
