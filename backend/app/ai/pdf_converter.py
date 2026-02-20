"""
PDF to Markdown conversion.
Extracts text from PDF and formats as markdown preserving structure.
"""
import io
from typing import Optional

from pypdf import PdfReader


def pdf_to_markdown(pdf_bytes: bytes, filename: Optional[str] = None) -> str:
    """
    Convert PDF content to markdown text.
    Extracts text page by page and preserves paragraph structure.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    lines: list[str] = []

    if filename:
        lines.append(f"# Document: {filename}\n")

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
        # Normalize whitespace but preserve paragraph breaks
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for para in paragraphs:
            lines.append(para)
            lines.append("")  # blank line between paragraphs
        if i < len(reader.pages) - 1:
            lines.append("\n---\n")  # page separator

    return "\n".join(lines).strip()
