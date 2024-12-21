import click
import sys
import asyncio
from pathlib import Path
from typing import List, Optional
from .docs_manager import DocsManager
from .async_logger import AsyncLogger

logger = AsyncLogger(verbose=True)
docs_manager = DocsManager(logger)

def print_table(headers: List[str], rows: List[List[str]], padding: int = 2):
    """Helper function to print formatted tables"""
    col_widths = [max(len(str(cell)) for cell in col) for col in zip(headers, *rows)]
    border = '+' + '+'.join('-' * (width + 2 * padding) for width in col_widths) + '+'
    
    def print_row(row):
        return '|' + '|'.join(
            f"{str(cell):{' '}<{width}}" for cell, width in zip(row, col_widths)
        ) + '|'

    click.echo(border)
    click.echo(print_row(headers))
    click.echo(border)
    for row in rows:
        click.echo(print_row(row))
    click.echo(border)

@click.group()
def cli():
    """Crawl4AI Command Line Interface"""
    pass

@cli.group()
def docs():
    """Documentation and LLM text operations"""
    pass

@docs.command()
@click.argument('sections', nargs=-1)
@click.option('--mode', type=click.Choice(['extended', 'condensed']), default='extended',
              help='Documentation detail level')
def combine(sections: tuple, mode: str):
    """Combine documentation sections.
    
    If no sections are specified, combines all available sections.
    """
    try:
        asyncio.run(docs_manager.ensure_docs_exist())
        result = docs_manager.concatenate_docs(sections, mode)
        click.echo(result)
    except Exception as e:
        logger.error(str(e), tag="ERROR")
        sys.exit(1)

@docs.command()
@click.argument('query')
@click.option('--top-k', '-k', default=5, help='Number of top results to return')
def search(query: str, top_k: int):
    """Search through documentation questions"""
    try:
        results = docs_manager.search_questions(query, top_k)
        click.echo(results)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@docs.command()
def list():
    """List available documentation sections"""
    try:
        file_map = docs_manager.get_file_map()
        rows = [[num, name] for name, num in file_map.items()]
        rows.sort(key=lambda x: int(x[0]))
        print_table(['Number', 'Section Name'], rows)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@docs.command()
def update():
    """Update local documentation cache from GitHub"""
    try:
        docs_manager = DocsManager()
        docs_manager.update_docs()
        click.echo("Documentation updated successfully")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)



if __name__ == '__main__':
    cli()
