"""Unit tests for the PDF parsing utility using an in-memory minimal PDF."""

from __future__ import annotations

import io
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from app.tools.pdf_parser import PDFParser, PDFParsingError
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


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


def test_extract_text_falls_back_to_tesseract_when_no_text_layer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A text-less PDF is recovered via Tesseract when the binary is present."""
    pdf_parser = PDFParser()
    monkeypatch.setattr(pdf_parser, "_extract_text_layer", lambda _b: "")
    monkeypatch.setattr(pdf_parser, "_extract_with_pymupdf", lambda _b: "")
    monkeypatch.setattr(pdf_parser, "_render_page_pngs", lambda _b: [b"png-bytes"])

    fake_image = MagicMock()
    fake_image.__enter__.return_value = fake_image
    fake_image.__exit__.return_value = False

    with (
        patch("app.tools.pdf_parser.shutil.which", return_value="/usr/bin/tesseract"),
        patch("pytesseract.image_to_string", return_value="Jane Doe\nPython Engineer"),
        patch("PIL.Image.open", return_value=fake_image),
    ):
        text = pdf_parser.extract_text(_make_minimal_pdf())

    assert "Jane Doe" in text
    assert "Python Engineer" in text


def test_extract_text_falls_back_to_vision_when_tesseract_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When Tesseract is absent, vision OCR recovers scanned-page text."""
    pdf_parser = PDFParser()
    monkeypatch.setattr(pdf_parser, "_extract_text_layer", lambda _b: "")
    monkeypatch.setattr(pdf_parser, "_extract_with_pymupdf", lambda _b: "")
    monkeypatch.setattr(pdf_parser, "_render_page_pngs", lambda _b: [b"png-bytes"])

    fake_settings = SimpleNamespace(
        llm_api_key="sk-test",
        llm_api_base=None,
        llm_model="gpt-4o-mini",
        llm_timeout_seconds=60,
    )
    fake_choice = MagicMock()
    fake_choice.message.content = "Vision OCR line"
    fake_response = MagicMock()
    fake_response.choices = [fake_choice]
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_response

    with (
        patch("app.tools.pdf_parser.shutil.which", return_value=None),
        patch("openai.OpenAI", return_value=fake_client),
        patch("app.config.settings.get_settings", return_value=fake_settings),
    ):
        text = pdf_parser.extract_text(_make_minimal_pdf())

    assert "Vision OCR line" in text
    fake_client.chat.completions.create.assert_called_once()


def test_ocr_skipped_without_tesseract_or_llm_key_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Image PDFs fail clearly when neither Tesseract nor an LLM key exists."""
    pdf_parser = PDFParser()
    monkeypatch.setattr(pdf_parser, "_extract_text_layer", lambda _b: "")
    monkeypatch.setattr(pdf_parser, "_extract_with_pymupdf", lambda _b: "")
    fake_settings = SimpleNamespace(
        llm_api_key="",
        llm_api_base=None,
        llm_model="gpt-4o-mini",
        llm_timeout_seconds=60,
    )
    with (
        patch("app.tools.pdf_parser.shutil.which", return_value=None),
        patch("app.config.settings.get_settings", return_value=fake_settings),
    ):
        with pytest.raises(PDFParsingError, match="image-based"):
            pdf_parser.extract_text(_make_minimal_pdf())
