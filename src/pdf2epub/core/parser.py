"""PDF parsing with PyMuPDF — paragraph-aware extraction with CJK support."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

import fitz  # PyMuPDF


@dataclass
class ContentBlock:
    """A single logical unit: paragraph, heading, or image."""
    text: str = ""
    image_data: bytes = b""
    image_ext: str = ""
    is_heading: bool = False
    font_size: float = 0.0
    page_num: int = 0
    y: float = 0.0        # top of first line on page
    y_end: float = 0.0    # bottom of last line on page


@dataclass
class ParsedDocument:
    """Full parsed document content as a flat ordered list of blocks."""
    blocks: list[ContentBlock] = field(default_factory=list)
    title: str = ""
    page_count: int = 0


class PDFParser:
    """Extract text and images from a PDF, grouping into paragraphs."""

    HEADING_THRESHOLD = 1.3

    def __init__(self, source: str | Path | BinaryIO):
        if isinstance(source, (str, Path)):
            self._doc = fitz.open(str(source))
        elif isinstance(source, (bytes, bytearray)):
            self._doc = fitz.open(stream=bytes(source), filetype="pdf")
        elif hasattr(source, "read"):
            data = source.read()
            if not isinstance(data, (bytes, bytearray)):
                raise TypeError("Binary stream source must return bytes")
            self._doc = fitz.open(stream=bytes(data), filetype="pdf")
        else:
            raise TypeError("source must be a file path, bytes, or binary stream")

    def parse(self) -> ParsedDocument:
        doc = ParsedDocument(page_count=len(self._doc))
        doc.title = self._doc.metadata.get("title", "") or ""

        body_size = self._detect_body_size()

        for page_num in range(len(self._doc)):
            page = self._doc[page_num]
            self._extract_page(page, page_num, body_size, doc)

        # Merge consecutive text blocks that belong to the same paragraph
        doc.blocks = self._merge_subparagraphs(doc.blocks, body_size)

        return doc

    def _detect_body_size(self) -> float:
        """Determine the most common font size across the whole document."""
        size_map: dict[float, int] = {}
        for page_num in range(len(self._doc)):
            page = self._doc[page_num]
            page_dict = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)
            for block in page_dict.get("blocks", []):
                if block["type"] != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        size = span.get("size", 12)
                        size_map[size] = size_map.get(size, 0) + len(span.get("text", ""))
        if not size_map:
            return 12.0
        return max(size_map, key=size_map.get)

    def _extract_page(self, page: fitz.Page, page_num: int, body_size: float,
                      doc: ParsedDocument):
        page_dict = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)
        seen_xrefs: set[int] = set()

        for block in page_dict.get("blocks", []):
            if block["type"] == 0:
                self._extract_text_block(block, page_num, body_size, doc)
            elif block["type"] == 1:
                self._extract_image_block(block, page_num, doc, seen_xrefs)

        self._extract_embedded_images(page, page_num, doc, seen_xrefs)

    def _extract_text_block(self, block: dict, page_num: int, body_size: float,
                            doc: ParsedDocument):
        lines = block.get("lines", [])
        if not lines:
            return

        # Determine the largest font size in this block
        max_size = 0.0
        for line in lines:
            for span in line.get("spans", []):
                size = span.get("size", 12)
                if size > max_size:
                    max_size = size

        # Collapse all lines into one paragraph.
        # For CJK text, join lines without spaces (PDF line-breaks mid-word).
        # For Latin text, join with a single space.
        para_parts: list[str] = []
        for line in lines:
            line_text = "".join(span.get("text", "") for span in line.get("spans", []))
            if line_text:
                para_parts.append(line_text.strip())

        if not para_parts:
            return

        # Detect if the text is primarily CJK
        raw = "".join(para_parts)
        join_char = "" if self._is_mostly_cjk(raw) else " "
        text = join_char.join(para_parts)

        is_heading = body_size > 0 and max_size >= body_size * self.HEADING_THRESHOLD

        # Record vertical extents for gap-based paragraph detection
        y = lines[0].get("bbox", (0, 0, 0, 0))[1] if lines else 0.0
        y_end = lines[-1].get("bbox", (0, 0, 0, 0))[3] if lines else y

        doc.blocks.append(ContentBlock(
            text=text,
            is_heading=is_heading,
            font_size=max_size,
            page_num=page_num,
            y=y,
            y_end=y_end,
        ))

    @staticmethod
    def _is_mostly_cjk(text: str) -> bool:
        """Check if a text is mostly CJK characters."""
        if not text:
            return False
        cjk = sum(1 for c in text
                  if '一' <= c <= '鿿'    # CJK Unified Ideographs
                  or '　' <= c <= '〿'    # CJK Symbols and Punctuation
                  or '＀' <= c <= '￯')    # Fullwidth forms
        return cjk / len(text) > 0.3

    def _merge_subparagraphs(self, blocks: list[ContentBlock],
                             body_size: float) -> list[ContentBlock]:
        """Merge consecutive text blocks split by PDF layout into paragraphs."""
        if not blocks:
            return blocks

        gap_threshold = body_size * 2.0

        merged: list[ContentBlock] = [blocks[0]]
        for block in blocks[1:]:
            prev = merged[-1]

            if not prev.text or not block.text:
                merged.append(block)
                continue

            if prev.is_heading or block.is_heading:
                merged.append(block)
                continue

            if abs(prev.font_size - block.font_size) > 1:
                merged.append(block)
                continue

            if block.page_num == prev.page_num:
                # Gap between bottom of prev block and top of this block
                gap = block.y - prev.y_end
                if gap > gap_threshold:
                    merged.append(block)
                    continue
                # Same paragraph — merge
                joiner = "" if self._is_mostly_cjk(prev.text + block.text) else " "
                prev.text = prev.text.rstrip() + joiner + block.text.lstrip()
                # Update y_end to this block's end
                prev.y_end = block.y_end
            elif block.page_num == prev.page_num + 1:
                joiner = "" if self._is_mostly_cjk(prev.text + block.text) else " "
                prev.text = prev.text.rstrip() + joiner + block.text.lstrip()
                prev.y_end = block.y_end
            else:
                merged.append(block)

        return merged

    def _extract_image_block(self, block: dict, page_num: int, doc: ParsedDocument,
                             seen_xrefs: set[int]):
        try:
            image_ref = block.get("image")
            if isinstance(image_ref, int):
                if image_ref in seen_xrefs:
                    return
                seen_xrefs.add(image_ref)
                image = self._doc.extract_image(image_ref)
            elif isinstance(image_ref, (bytes, bytearray)):
                image = {
                    "image": bytes(image_ref),
                    "ext": block.get("ext", "png"),
                }
            else:
                return

            if image and image.get("image"):
                doc.blocks.append(ContentBlock(
                    image_data=image.get("image", b""),
                    image_ext=image.get("ext", "png"),
                    page_num=page_num,
                ))
        except Exception:
            pass

    def _extract_embedded_images(self, page: fitz.Page, page_num: int,
                                 doc: ParsedDocument, seen_xrefs: set[int]):
        for img in page.get_images(full=True):
            xref = img[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            try:
                base = self._doc.extract_image(xref)
                image_data = base.get("image", b"")
                if not image_data:
                    continue
                doc.blocks.append(ContentBlock(
                    image_data=image_data,
                    image_ext=base.get("ext", "png"),
                    page_num=page_num,
                ))
            except Exception:
                continue

    def close(self):
        self._doc.close()
