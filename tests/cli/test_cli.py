import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch
import json
import yaml
from crawl4ai.cli import cli, load_config_file, parse_key_values
from crawl4ai.models import CrawlResult, MarkdownGenerationResult
import tempfile
import os
import click

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def temp_config_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        old_home = os.environ.get('HOME')
        os.environ['HOME'] = tmpdir
        yield Path(tmpdir)
        if old_home:
            os.environ['HOME'] = old_home

@pytest.fixture
def sample_configs(temp_config_dir):
    configs = {
        'browser.yml': {
            'headless': True,
            'viewport_width': 1280,
            'user_agent_mode': 'random'
        },
        'crawler.yml': {
            'cache_mode': 'bypass',
            'wait_until': 'networkidle',
            'scan_full_page': True
        },
        'extract_css.yml': {
            'type': 'json-css',
            'params': {'verbose': True}
        },
        'css_schema.json': {
            'name': 'ArticleExtractor',
            'baseSelector': '.article',
            'fields': [
                {'name': 'title', 'selector': 'h1.title', 'type': 'text'},
                {'name': 'link', 'selector': 'a.read-more', 'type': 'attribute', 'attribute': 'href'}
            ]
        }
    }
    
    for filename, content in configs.items():
        path = temp_config_dir / filename
        with open(path, 'w') as f:
            if filename.endswith('.yml'):
                yaml.dump(content, f)
            else:
                json.dump(content, f)
                
    return {name: str(temp_config_dir / name) for name in configs}

class TestCLIBasics:
    def test_help(self, runner):
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Crawl4AI CLI' in result.output

    def test_examples(self, runner):
        result = runner.invoke(cli, ['--example'])
        assert result.exit_code == 0
        assert 'Examples' in result.output

    def test_missing_url(self, runner):
        result = runner.invoke(cli)
        assert result.exit_code != 0
        assert 'URL argument is required' in result.output

class TestConfigParsing:
    def test_parse_key_values_basic(self):
        result = parse_key_values(None, None, "key1=value1,key2=true")
        assert result == {'key1': 'value1', 'key2': True}

    def test_parse_key_values_invalid(self):
        with pytest.raises(click.BadParameter):
            parse_key_values(None, None, "invalid_format")

class TestConfigLoading:
    def test_load_yaml_config(self, sample_configs):
        config = load_config_file(sample_configs['browser.yml'])
        assert config['headless'] is True
        assert config['viewport_width'] == 1280

    def test_load_json_config(self, sample_configs):
        config = load_config_file(sample_configs['css_schema.json'])
        assert config['name'] == 'ArticleExtractor'
        assert len(config['fields']) == 2

    def test_load_nonexistent_config(self):
        with pytest.raises(click.BadParameter):
            load_config_file('nonexistent.yml')

class TestLLMConfig:
    def test_llm_config_creation(self, temp_config_dir, runner):
        def input_simulation(inputs):
            return runner.invoke(cli, ['https://example.com', '-q', 'test question'], 
                               input='\n'.join(inputs))
            
class TestCrawlingFeatures:
    def test_basic_crawl(self, runner):
        result = runner.invoke(cli, ['https://example.com'])
        assert result.exit_code == 0


class TestErrorHandling:
    def test_invalid_config_file(self, runner):
        result = runner.invoke(cli, [
            'https://example.com',
            '--browser-config', 'nonexistent.yml'
        ])
        assert result.exit_code != 0

    def test_invalid_schema(self, runner, temp_config_dir):
        invalid_schema = temp_config_dir / 'invalid_schema.json'
        with open(invalid_schema, 'w') as f:
            f.write('invalid json')
            
        result = runner.invoke(cli, [
            'https://example.com',
            '--schema', str(invalid_schema)
        ])
        assert result.exit_code != 0

class TestDeepCrawlOutput:
    """Tests for deep crawl output formatting"""

    @pytest.fixture
    def mock_crawl_results(self):
        """Create mock CrawlResult objects simulating deep crawl results"""
        def make_result(url, content):
            markdown = MarkdownGenerationResult(
                raw_markdown=content,
                markdown_with_citations=content,
                references_markdown="",
                fit_markdown=content,
            )
            result = CrawlResult(
                url=url,
                html=f"<html>{content}</html>",
                success=True,
                metadata={"depth": 0},
            )
            result._markdown = markdown
            return result

        return [
            make_result("https://example.com/", "# Homepage\n\nWelcome to the homepage."),
            make_result("https://example.com/about", "# About\n\nAbout us page content."),
            make_result("https://example.com/contact", "# Contact\n\nContact information."),
        ]

    def test_deep_crawl_markdown_output_includes_all_pages(self, runner, mock_crawl_results):
        """Test that deep crawl with markdown output includes all pages, not just the first"""
        with patch('crawl4ai.cli.anyio.run') as mock_anyio_run:
            # Return list of results (simulating deep crawl)
            mock_anyio_run.return_value = mock_crawl_results

            result = runner.invoke(cli, [
                'crawl',
                'https://example.com',
                '--deep-crawl', 'bfs',
                '--max-pages', '3',
                '-o', 'markdown'
            ])

            assert result.exit_code == 0, f"CLI failed with: {result.output}"
            # Should contain content from ALL pages
            assert 'https://example.com/' in result.output
            assert 'https://example.com/about' in result.output
            assert 'https://example.com/contact' in result.output
            assert 'Homepage' in result.output
            assert 'About us page content' in result.output
            assert 'Contact information' in result.output

    def test_deep_crawl_markdown_fit_output_includes_all_pages(self, runner, mock_crawl_results):
        """Test that deep crawl with markdown-fit output includes all pages"""
        with patch('crawl4ai.cli.anyio.run') as mock_anyio_run:
            mock_anyio_run.return_value = mock_crawl_results

            result = runner.invoke(cli, [
                'crawl',
                'https://example.com',
                '--deep-crawl', 'bfs',
                '--max-pages', '3',
                '-o', 'markdown-fit'
            ])

            assert result.exit_code == 0, f"CLI failed with: {result.output}"
            # Should contain all URLs
            assert 'https://example.com/' in result.output
            assert 'https://example.com/about' in result.output
            assert 'https://example.com/contact' in result.output

    def test_deep_crawl_file_output_includes_all_pages(self, runner, mock_crawl_results, tmp_path):
        """Test that deep crawl with file output includes all pages"""
        output_file = tmp_path / "output.md"

        with patch('crawl4ai.cli.anyio.run') as mock_anyio_run:
            mock_anyio_run.return_value = mock_crawl_results

            result = runner.invoke(cli, [
                'crawl',
                'https://example.com',
                '--deep-crawl', 'bfs',
                '--max-pages', '3',
                '-o', 'markdown',
                '-O', str(output_file)
            ])

            assert result.exit_code == 0, f"CLI failed with: {result.output}"
            content = output_file.read_text()
            # Should contain content from ALL pages
            assert 'https://example.com/' in content
            assert 'https://example.com/about' in content
            assert 'https://example.com/contact' in content

    def test_single_crawl_markdown_output_unchanged(self, runner):
        """Test that single (non-deep) crawl still works correctly"""
        markdown = MarkdownGenerationResult(
            raw_markdown="# Single Page\n\nContent here.",
            markdown_with_citations="# Single Page\n\nContent here.",
            references_markdown="",
        )
        single_result = CrawlResult(
            url="https://example.com/",
            html="<html>test</html>",
            success=True,
        )
        single_result._markdown = markdown

        with patch('crawl4ai.cli.anyio.run') as mock_anyio_run:
            # Return single result (not a list)
            mock_anyio_run.return_value = single_result

            result = runner.invoke(cli, [
                'crawl',
                'https://example.com',
                '-o', 'markdown'
            ])

            assert result.exit_code == 0, f"CLI failed with: {result.output}"
            assert '# Single Page' in result.output
            assert 'Content here' in result.output


if __name__ == '__main__':
    pytest.main(['-v', '-s', '--tb=native', __file__])
