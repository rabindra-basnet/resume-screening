"""DOCX text extraction utilities.

Extracts plain text from .docx files using ``python-docx``. Handles paragraphs,
tables, and nested content while preserving logical reading order.
"""

from __future__ import annotations

import io
import logging

from docx import Document

logger = logging.getLogger(__name__)


class DocxParsingError(Exception):
    """Raised when a DOCX file cannot be parsed or yields no text.

    Args:
        message: A human-readable description of the parsing failure.
    """

    def __init__(self, message: str) -> None:
        """Initialize the exception with the given message."""
        super().__init__(message)
        self.message = message


class DocxParser:
    """Extract plain text content from DOCX byte streams or file objects."""

    def extract_text(self, source: bytes | io.BytesIO | object) -> str:
        """Extract all text from a DOCX provided as bytes or a file-like object.

        Args:
            source: Raw DOCX bytes, a ``BytesIO`` stream, or any object exposing
                a ``read()`` method (e.g. an ``UploadFile``).

        Returns:
            The concatenated text of all paragraphs and tables, stripped of
            leading/trailing whitespace.

        Raises:
            DocxParsingError: If the DOCX cannot be opened, yields no text,
                or the source type is unsupported.
        """
        try:
            read_method = getattr(source, "read", None)
            if read_method is not None:
                raw_bytes = read_method()
            else:
                raw_bytes = source
        except Exception as exc:  # noqa: BLE001
            raise DocxParsingError(f"Could not read DOCX source: {exc}") from exc

        try:
            doc = Document(io.BytesIO(raw_bytes))
        except Exception as exc:  # noqa: BLE001
            raise DocxParsingError(f"Failed to open DOCX: {exc}") from exc

        parts: list[str] = []
        for element in doc.element.body:
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
            if tag == "p":
                text = element.text or ""
                for child in element.iter():
                    child_text = child.text or ""
                    text += child_text
                if text.strip():
                    parts.append(text.strip())
            elif tag == "tbl":
                for row in element.iter():
                    row_text = row.text or ""
                    if row_text.strip():
                        parts.append(row_text.strip())

        text = "\n".join(parts)
        if not text:
            raise DocxParsingError("DOCX yielded no extractable text content")
        return text


def parse_docx(file: object) -> str:
    """Convenience wrapper returning extracted text from a file-like object.

    Args:
        file: A file-like object containing DOCX data.

    Returns:
        The extracted text content of the DOCX.

    Raises:
        DocxParsingError: If parsing fails.
    """
    return DocxParser().extract_text(file)
