"""Unit tests for the PDF parsing utility using an in-memory minimal PDF."""

from __future__ import annotations

import io

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from app.tools.pdf_parser import PDFParser, PDFParsingError


def _make_minimal_pdf(text: str = "Hello Resume") -> bytes:
    """Generate a valid single-page PDF containing ``text`` using pypdf."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    content = DecodedStreamObject()
    content.set_data(f"BT /F1 24 Tf 100 700 Td ({text}) Tj ET".encode())
    content_ref = writer._add_object(content)
    res = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})}
    )
    page[NameObject("/Resources")] = res
    page[NameObject("/Contents")] = content_ref
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_extract_text_from_bytes() -> None:
    """Text is extracted from raw PDF bytes."""
    text = PDFParser().extract_text(_make_minimal_pdf())
    assert "Hello Resume" in text


def test_extract_text_from_file_like() -> None:
    """Text is extracted from a file-like (BytesIO) object."""
    text = PDFParser().extract_text(io.BytesIO(_make_minimal_pdf()))
    assert "Hello Resume" in text


def test_extract_text_garbage_raises() -> None:
    """Invalid PDF bytes raise a typed PDFParsingError."""
    with pytest.raises(PDFParsingError):
        PDFParser().extract_text(b"this is not a pdf at all")
