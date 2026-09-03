"""Unified document parser that routes by file extension.

Provides a single entry point for extracting text from supported document
formats (PDF, DOCX). Callers pass raw bytes plus the filename and the parser
delegates to the correct handler.
"""

from __future__ import annotations

import logging

from app.tools.docx_parser import DocxParser, DocxParsingError
from app.tools.pdf_parser import PDFParser, PDFParsingError

logger = logging.getLogger(__name__)

SupportedExtension = frozenset({".pdf", ".docx"})


class DocumentParsingError(Exception):
    """Raised when a document cannot be parsed by any supported handler.

    Attributes:
        message: Human-readable error description.
        filename: The original filename that failed parsing.
    """

    def __init__(self, message: str, filename: str = "") -> None:
        """Initialize with error message and optional filename."""
        super().__init__(message)
        self.message = message
        self.filename = filename


class DocumentParser:
    """Route document extraction by file extension.

    Supports ``.pdf`` and ``.docx`` formats. Raises ``DocumentParsingError``
    for unsupported extensions or parsing failures.
    """

    def __init__(self) -> None:
        """Initialize the parser with handlers for each supported format."""
        self._pdf = PDFParser()
        self._docx = DocxParser()

    def extract_text(self, raw_bytes: bytes, filename: str) -> str:
        """Extract text from a document given its raw bytes and filename.

        Args:
            raw_bytes: The raw file content.
            filename: Original filename used to determine format.

        Returns:
            The extracted plain text.

        Raises:
            DocumentParsingError: If the extension is unsupported or parsing fails.
        """
        ext = _get_extension(filename)
        if ext == ".pdf":
            try:
                return self._pdf.extract_text(raw_bytes)
            except PDFParsingError as exc:
                raise DocumentParsingError(
                    f"PDF parsing failed: {exc.message}", filename
                ) from exc
        elif ext == ".docx":
            try:
                return self._docx.extract_text(raw_bytes)
            except DocxParsingError as exc:
                raise DocumentParsingError(
                    f"DOCX parsing failed: {exc.message}", filename
                ) from exc
        else:
            raise DocumentParsingError(
                f"Unsupported file format '{ext}'. Accepted formats: .pdf, .docx",
                filename,
            )


def _get_extension(filename: str) -> str:
    """Return the lowercase file extension including the dot."""
    name = filename.strip().lower()
    if "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1]
