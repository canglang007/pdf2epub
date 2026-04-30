"""EPUB file builder — generates a single-flow EPUB from parsed content blocks."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import BinaryIO
from xml.sax.saxutils import escape

from ebooklib import epub

from pdf2epub.config import EPUB_DEFAULT_LANGUAGE, EPUB_DEFAULT_AUTHOR
from pdf2epub.core.parser import ContentBlock, ParsedDocument


class EPUBBuilder:
    """Build EPUB from parsed PDF content blocks."""

    def __init__(self, document: ParsedDocument):
        self._doc = document
        self._book = epub.EpubBook()
        self._image_counter = 0

    def build(self, output_path: str | Path | BinaryIO) -> str:
        self._setup_metadata()
        self._add_css()

        body_xhtml = self._build_body()
        chapter = epub.EpubHtml(
            title=self._doc.title or "Document",
            file_name="content.xhtml",
            lang=EPUB_DEFAULT_LANGUAGE,
        )
        chapter.content = body_xhtml.encode("utf-8")
        self._book.add_item(chapter)

        # Spine + TOC
        self._book.spine = ["nav", chapter]
        self._book.add_item(epub.EpubNcx())
        self._book.toc = [
            epub.Link(chapter.file_name, chapter.title, chapter.file_name),
        ]
        self._book.add_item(epub.EpubNav())

        epub.write_epub(output_path, self._book)
        return str(output_path)

    def _setup_metadata(self):
        self._book.set_title(self._doc.title or "Untitled")
        self._book.set_language(EPUB_DEFAULT_LANGUAGE)
        self._book.add_author(EPUB_DEFAULT_AUTHOR)
        self._book.set_identifier(f"urn:uuid:{uuid.uuid4()}")

    def _add_css(self):
        style = """
        @namespace epub "http://www.idpf.org/2007/ops";
        body {
            font-family: serif;
            line-height: 1.8;
            margin: 2em;
        }
        h1 { font-size: 1.8em; margin: 1em 0 0.5em; text-align: center; }
        h2 { font-size: 1.5em; margin: 0.8em 0 0.4em; }
        h3 { font-size: 1.3em; margin: 0.6em 0 0.3em; }
        p {
            text-indent: 2em;
            margin: 0.4em 0;
        }
        p.first { text-indent: 0; }
        img {
            max-width: 100%; height: auto;
            display: block; margin: 1em auto;
        }
        """
        css_item = epub.EpubItem(
            uid="style",
            file_name="style/default.css",
            media_type="text/css",
            content=style.encode("utf-8"),
        )
        self._book.add_item(css_item)

    def _build_body(self) -> str:
        """Generate XHTML body content from the flat block list."""
        parts = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<!DOCTYPE html>',
            '<html xmlns="http://www.w3.org/1999/xhtml"',
            '      xmlns:epub="http://www.idpf.org/2007/ops">',
            '<head>',
            f'  <title>{escape(self._doc.title or "Document")}</title>',
            '  <link rel="stylesheet" type="text/css" href="style/default.css"/>',
            '</head>',
            '<body>',
        ]

        # Only add first-paragraph class to the very first text block
        is_first_text = True

        for block in self._doc.blocks:
            if block.image_data:
                parts.append(self._image_tag(block))
                continue

            # Text block
            text = escape(block.text.strip())
            if not text:
                continue

            if block.is_heading:
                parts.append(f'<h2>{text}</h2>')
            else:
                cls = ' class="first"' if is_first_text else ''
                parts.append(f'<p{cls}>{text}</p>')
                is_first_text = False

        parts.append("</body></html>")
        return "\n".join(parts)

    def _image_tag(self, block: ContentBlock) -> str:
        self._image_counter += 1
        ext = block.image_ext if block.image_ext in ("png", "jpg", "jpeg") else "png"
        img_id = f"img_{self._image_counter}"
        file_name = f"images/{img_id}.{ext}"

        img_item = epub.EpubItem(
            uid=img_id,
            file_name=file_name,
            media_type=f"image/{ext}",
            content=block.image_data,
        )
        self._book.add_item(img_item)
        return f'<div><img src="{file_name}" alt=""/></div>'
