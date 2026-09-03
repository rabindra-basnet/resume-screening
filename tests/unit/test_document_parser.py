"""Unit tests for the DOCX parser and the unified document parser."""

from __future__ import annotations

import io

import pytest
from docx import Document

from app.tools.document_parser import DocumentParser, DocumentParsingError
from app.tools.docx_parser import DocxParser, DocxParsingError


def _make_docx(text: str) -> bytes:
    """Build an in-memory .docx byte stream containing the given text.

    Args:
        text: The paragraph text to embed in the document.

    Returns:
        The docx file bytes.
    """
    buf = io.BytesIO()
    doc = Document()
    doc.add_paragraph(text)
    doc.save(buf)
    return buf.getvalue()


def test_docx_extract_text_from_bytes() -> None:
    """Text is extracted from raw DOCX bytes."""
    text = DocxParser().extract_text(_make_docx("Hello Resume"))
    assert "Hello Resume" in text


def test_docx_extract_text_from_file_like() -> None:
    """Text is extracted from a file-like (BytesIO) object."""
    text = DocxParser().extract_text(io.BytesIO(_make_docx("Hi there")))
    assert "Hi there" in text


def test_docx_garbage_raises() -> None:
    """Invalid DOCX bytes raise a typed DocxParsingError."""
    with pytest.raises(DocxParsingError):
        DocxParser().extract_text(b"this is not a docx at all")


def test_document_parser_routes_pdf_by_extension() -> None:
    """The unified parser routes a .pdf filename to the PDF handler."""
    from app.tools import PDFParsingError

    with pytest.raises(DocumentParsingError):
        DocumentParser().extract_text(b"garbage", "resume.pdf")


def test_document_parser_routes_docx_by_extension() -> None:
    """The unified parser routes a .docx filename to the DOCX handler."""
    text = DocumentParser().extract_text(
        _make_docx("Python FastAPI engineer"), "resume.docx"
    )
    assert "Python FastAPI engineer" in text


def test_document_parser_unsupported_extension() -> None:
    """An unsupported extension raises DocumentParsingError."""
    with pytest.raises(DocumentParsingError):
        DocumentParser().extract_text(b"x", "resume.txt")
