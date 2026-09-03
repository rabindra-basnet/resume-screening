"""PDF text extraction utilities.

Uses ``pypdf`` for lightweight, Vercel-compatible PDF text extraction.
Handles standard PDF text streams and raises explicit typed exceptions
so callers can handle errors predictably.
"""

from __future__ import annotations

import io
import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFParsingError(Exception):
    """Raised when a PDF file cannot be parsed or yields no text."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class PDFParser:
    """Extract plain text content from PDF byte streams or file objects.

    Attributes:
        max_pages: Maximum number of pages to process. Zero means all pages.
    """

    def __init__(self, max_pages: int = 0) -> None:
        self.max_pages = max_pages

    def extract_text(self, source: bytes | io.BytesIO | object) -> str:
        """Extract all text from a PDF provided as bytes or a file-like object.

        Args:
            source: Raw PDF bytes, a ``BytesIO`` stream, or any object with ``read()``.

        Returns:
            The concatenated text of all processed pages.

        Raises:
            PDFParsingError: If the PDF cannot be opened, yields no text,
                or the source type is unsupported.
        """
        try:
            read_method = getattr(source, "read", None)
            if read_method is not None:
                raw_bytes = read_method()
            else:
                raw_bytes = source
        except Exception as exc:  # noqa: BLE001
            raise PDFParsingError(f"Could not read PDF source: {exc}") from exc

        try:
            reader = PdfReader(io.BytesIO(raw_bytes))
            pages = reader.pages
            if self.max_pages:
                pages = pages[: self.max_pages]
            text = "\n".join((page.extract_text() or "") for page in pages)
        except Exception as exc:  # noqa: BLE001
            raise PDFParsingError(f"Failed to parse PDF: {exc}") from exc

        text = text.strip()
        if not text:
            raise PDFParsingError("PDF yielded no extractable text content")
        return text


def parse_pdf(file: object) -> str:
    """Convenience wrapper returning extracted text from a file-like object."""
    return PDFParser().extract_text(file)
