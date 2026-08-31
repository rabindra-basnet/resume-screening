"""Unit tests for the PDF parsing utility using an in-memory minimal PDF."""

from __future__ import annotations

import io

import pytest
from app.tools.pdf_parser import PDFParser, PDFParsingError

# A minimal valid single-page PDF containing the text "Hello Resume".
_MINIMAL_PDF: bytes = (
    b"%PDF-1.1\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
    b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 44>>stream\n"
    b"BT/F1 24 Tf 100 700 Td(Hello Resume)Tj ET\n"
    b"endstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"trailer<</Root 1 0 R>>\n"
    b"%%EOF\n"
)


def test_extract_text_from_bytes() -> None:
    """Text is extracted from raw PDF bytes."""
    text = PDFParser().extract_text(_MINIMAL_PDF)
    assert "Hello Resume" in text


def test_extract_text_from_file_like() -> None:
    """Text is extracted from a file-like (BytesIO) object."""
    text = PDFParser().extract_text(io.BytesIO(_MINIMAL_PDF))
    assert "Hello Resume" in text


def test_extract_text_garbage_raises() -> None:
    """Invalid PDF bytes raise a typed PDFParsingError."""
    with pytest.raises(PDFParsingError):
        PDFParser().extract_text(b"this is not a pdf at all")
