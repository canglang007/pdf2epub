"""Command-line interface for pdf2epub."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from pdf2epub import __version__
from pdf2epub.config import APP_NAME
from pdf2epub.core.builder import EPUBBuilder
from pdf2epub.core.parser import PDFParser


@click.command(
    name=APP_NAME,
    help="Convert PDF documents to EPUB format.",
)
@click.argument(
    "input_pdf",
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
@click.option(
    "-o", "--output",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Output EPUB file path (default: input name with .epub extension).",
)
@click.version_option(version=__version__, prog_name=APP_NAME)
def main(input_pdf: str, output: str | None) -> None:
    """Convert INPUT_PDF to EPUB format."""
    input_path = Path(input_pdf)

    if output is None:
        output_path = input_path.with_suffix(".epub")
    else:
        output_path = Path(output)

    if output_path.exists():
        click.confirm(f"Overwrite '{output_path}'?", abort=True)

    click.echo(f"Parsing PDF: {input_path.name}...")
    parser = PDFParser(input_pdf)
    try:
        document = parser.parse()
    finally:
        parser.close()

    click.echo(f"Building EPUB ({document.page_count} pages)...")
    builder = EPUBBuilder(document)
    builder.build(str(output_path))

    click.echo(f"Done: {output_path}")


if __name__ == "__main__":
    main()
