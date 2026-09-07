"""PDF text extraction utilities.

Extraction pipeline (fastest → most powerful, run only as needed):

1. ``pypdf`` — lightweight, fast for normal text-layer PDFs. Never loads the
   heavy OCR stack.
2. ``pymupdf`` (MuPDF) — much stronger text extraction for oddly-structured
   PDFs (encodings, corrupt tag tables, etc.). Still text-layer only.
3. OCR fallback — when a PDF has no extractable text layer at all (scanned
   pages, or text converted to vector outlines like Canva/Figma exports), the
   pages are rendered to images with PyMuPDF and read by RapidOCR (ONNX, fully
   offline, free, serverless-safe). Kept lazy so normal resumes never import
   onnxruntime/opencv.
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

        text = self._extract_text_layer(raw_bytes)
        if text.strip():
            return text.strip()

        text = self._extract_with_pymupdf(raw_bytes)
        if text.strip():
            logger.info("Extracted text from PDF via PyMuPDF fallback")
            return text.strip()

        raise PDFParsingError("PDF yielded no extractable text content")

    def _extract_text_layer(self, raw_bytes: bytes) -> str:
        """Try the fast pypdf path first."""
        try:
            reader = PdfReader(io.BytesIO(raw_bytes))
            pages = reader.pages
            if self.max_pages:
                pages = pages[: self.max_pages]
            return "\n".join((page.extract_text() or "") for page in pages)
        except Exception as exc:  # noqa: BLE001 - fall through to PyMuPDF
            logger.warning("pypdf failed to parse PDF: %s", exc)
            return ""

    def _extract_with_pymupdf(self, raw_bytes: bytes) -> str:
        """Try MuPDF's text extraction, which handles complex encodings."""
        try:
            import pymupdf  # lazy: lightweight native wheel

            doc = pymupdf.open(stream=raw_bytes, filetype="pdf")
            try:
                page_count = len(doc) if not self.max_pages else min(self.max_pages, len(doc))
                return "\n".join(
                    (doc[page_no].get_text() or "") for page_no in range(page_count)
                )
            finally:
                doc.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning("PyMuPDF text extraction failed: %s", exc)
            return ""


def parse_pdf(file: object) -> str:
    """Convenience wrapper returning extracted text from a file-like object."""
    return PDFParser().extract_text(file)
