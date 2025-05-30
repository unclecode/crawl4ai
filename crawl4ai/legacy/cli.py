import click
import sys
import asyncio
from typing import List
from .docs_manager import DocsManager
from .async_logger import AsyncLogger

logger = AsyncLogger(verbose=True)
docs_manager = DocsManager(logger)


def print_table(headers: List[str], rows: List[List[str]], padding: int = 2):
    """Print formatted table with headers and rows"""
    widths = [max(len(str(cell)) for cell in col) for col in zip(headers, *rows)]
    border = "+" + "+".join("-" * (w + 2 * padding) for w in widths) + "+"

    def format_row(row):
        return (
            "|"
            + "|".join(
                f"{' ' * padding}{str(cell):<{w}}{' ' * padding}"
                for cell, w in zip(row, widths)
            )
            + "|"
        )

    click.echo(border)
    click.echo(format_row(headers))
    click.echo(border)
    for row in rows:
        click.echo(format_row(row))
    click.echo(border)


@click.group()
def cli():
    """Crawl4AI Command Line Interface"""
    pass


@cli.group()
def docs():
    """Documentation operations"""
    pass


@docs.command()
@click.argument("sections", nargs=-1)
@click.option(
    "--mode", type=click.Choice(["extended", "condensed"]), default="extended"
)
def combine(sections: tuple, mode: str):
    """Combine documentation sections"""
    try:
        asyncio.run(docs_manager.ensure_docs_exist())
        click.echo(docs_manager.generate(sections, mode))
    except Exception as e:
        logger.error(str(e), tag="ERROR")
        sys.exit(1)


@docs.command()
@click.argument("query")
@click.option("--top-k", "-k", default=5)
@click.option("--build-index", is_flag=True, help="Build index if missing")
def search(query: str, top_k: int, build_index: bool):
    """Search documentation"""
    try:
        result = docs_manager.search(query, top_k)
        if result == "No search index available. Call build_search_index() first.":
            if build_index or click.confirm("No search index found. Build it now?"):
                asyncio.run(docs_manager.llm_text.generate_index_files())
                result = docs_manager.search(query, top_k)
        click.echo(result)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@docs.command()
def update():
    """Update docs from GitHub"""
    try:
        asyncio.run(docs_manager.fetch_docs())
        click.echo("Documentation updated successfully")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@docs.command()
@click.option("--force-facts", is_flag=True, help="Force regenerate fact files")
@click.option("--clear-cache", is_flag=True, help="Clear BM25 cache")
def index(force_facts: bool, clear_cache: bool):
    """Build or rebuild search indexes"""
    try:
        asyncio.run(docs_manager.ensure_docs_exist())
        asyncio.run(
            docs_manager.llm_text.generate_index_files(
                force_generate_facts=force_facts, clear_bm25_cache=clear_cache
            )
        )
        click.echo("Search indexes built successfully")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


# Add docs list command
@docs.command()
def list():
    """List available documentation sections"""
    try:
        sections = docs_manager.list()
        print_table(["Sections"], [[section] for section in sections])

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
