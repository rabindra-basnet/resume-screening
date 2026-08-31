"""PDF text extraction utilities.

Provides functions to extract text content from PDF files using
``pdfplumber`` for accurate text and table extraction. Raises explicit typed
exceptions on failure so callers can handle errors predictably rather than
receiving raw error strings.
"""

from __future__ import annotations

import io
import logging

import pdfplumber

logger = logging.getLogger(__name__)


class PDFParsingError(Exception):
    """Raised when a PDF file cannot be parsed or yields no text.

    Args:
        message: A human-readable description of the parsing failure.
    """

    def __init__(self, message: str) -> None:
        """Initialize the exception with the given message."""
        super().__init__(message)
        self.message = message


class PDFParser:
    """Extract plain text content from PDF byte streams or file objects.

    Attributes:
        max_pages: Maximum number of pages to process, protecting against
            pathologically large documents. Zero means process all pages.
    """

    def __init__(self, max_pages: int = 0) -> None:
        """Initialize the parser with an optional page limit.

        Args:
            max_pages: Maximum pages to extract text from; ``0`` means all.
        """
        self.max_pages = max_pages

    def extract_text(self, source: bytes | io.BytesIO | object) -> str:
        """Extract all text from a PDF provided as bytes or a file-like object.

        Args:
            source: Raw PDF bytes, a ``BytesIO`` stream, or any object exposing
                a ``read()`` method (e.g. an open file handle).

        Returns:
            The concatenated text of all processed pages, stripped of
            leading/trailing whitespace.

        Raises:
            PDFParsingError: If the PDF cannot be opened, yields no text, or the
                source type is unsupported.
        """
        try:
            read_method = getattr(source, "read", None)
            if read_method is not None:
                raw_bytes = read_method()
            else:
                raw_bytes = source
        except Exception as exc:  # noqa: BLE001 - surface any read failure
            raise PDFParsingError(f"Could not read PDF source: {exc}") from exc

        try:
            with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
                pages = pdf.pages
                if self.max_pages:
                    pages = pages[: self.max_pages]
                text = "\n".join((page.extract_text() or "") for page in pages)
        except Exception as exc:  # noqa: BLE001 - wrap parser failures
            raise PDFParsingError(f"Failed to parse PDF: {exc}") from exc

        text = text.strip()
        if not text:
            raise PDFParsingError("PDF yielded no extractable text content")
        return text


def parse_pdf(file: object) -> str:
    """Convenience wrapper returning extracted text from a file-like object.

    Args:
        file: A file-like object (e.g. an open file handle or ``UploadFile``)
            containing PDF data.

    Returns:
        The extracted text content of the PDF.

    Raises:
        PDFParsingError: If parsing fails.
    """
    return PDFParser().extract_text(file)
