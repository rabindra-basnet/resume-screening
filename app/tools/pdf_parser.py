"""PDF text extraction utilities.

Extraction pipeline (fastest → most powerful, run only as needed):

1. ``pypdf`` — lightweight, fast for normal text-layer PDFs.
2. ``pymupdf`` (MuPDF) — stronger text extraction for odd encodings. Still
   text-layer only.
3. Tesseract OCR — scanned/photo pages are rendered with PyMuPDF and read by
   the ``tesseract`` OS binary (installed in ``Dockerfile.vercel``).
4. Vision LLM — last resort when Tesseract is not on PATH (local machines
   without the Docker image).
"""

from __future__ import annotations

import base64
import io
import logging
import shutil

from pypdf import PdfReader

from app.config.constants import OCR_MAX_PAGES, OCR_MAX_TOKENS, OCR_RENDER_DPI

logger = logging.getLogger(__name__)

_OCR_PROMPT = (
    "These images are pages of a resume PDF that has no selectable text layer. "
    "Transcribe every readable word in reading order, preserving headings and "
    "line breaks. Return only the transcribed text, with no commentary."
)


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

        text = self._extract_with_tesseract(raw_bytes)
        if text.strip():
            logger.info("Extracted text from PDF via Tesseract OCR (no text layer)")
            return text.strip()

        text = self._extract_with_vision(raw_bytes)
        if text.strip():
            logger.info("Extracted text from PDF via vision OCR fallback")
            return text.strip()

        raise PDFParsingError(
            "PDF yielded no extractable text content. The file appears to be "
            "image-based or has no text layer; OCR could not recover text."
        )

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

    def _page_limit(self, doc_len: int) -> int:
        """Return how many pages to OCR, capped for serverless time and cost."""
        wanted = doc_len if not self.max_pages else min(self.max_pages, doc_len)
        return min(wanted, OCR_MAX_PAGES)

    def _render_page_pngs(self, raw_bytes: bytes) -> list[bytes]:
        """Render PDF pages to PNG bytes with PyMuPDF.

        Args:
            raw_bytes: The raw PDF bytes.

        Returns:
            One PNG payload per processed page.
        """
        import pymupdf

        doc = pymupdf.open(stream=raw_bytes, filetype="pdf")
        try:
            page_count = self._page_limit(len(doc))
            return [
                doc[page_no].get_pixmap(dpi=OCR_RENDER_DPI).tobytes("png")
                for page_no in range(page_count)
            ]
        finally:
            doc.close()

    def _extract_with_tesseract(self, raw_bytes: bytes) -> str:
        """Render pages to images and transcribe them with Tesseract.

        Requires the ``tesseract`` executable (provided by ``Dockerfile.vercel``
        on Vercel). Local ``honcho`` / uvicorn still works for text-layer PDFs;
        scanned PDFs need Tesseract on PATH or the vision fallback.

        Args:
            raw_bytes: The raw PDF bytes.

        Returns:
            Transcribed text, or an empty string if Tesseract cannot run.
        """
        if shutil.which("tesseract") is None:
            logger.warning("Tesseract executable not on PATH; skipping OS OCR")
            return ""
        try:
            import pytesseract
            from PIL import Image

            chunks: list[str] = []
            for png in self._render_page_pngs(raw_bytes):
                with Image.open(io.BytesIO(png)) as image:
                    image.load()
                    chunks.append(pytesseract.image_to_string(image) or "")
            return "\n".join(chunks)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Tesseract OCR failed: %s", exc)
            return ""

    def _extract_with_vision(self, raw_bytes: bytes) -> str:
        """Transcribe rendered pages with an OpenAI-compatible vision model.

        Used when Tesseract is not installed (local machines without Docker).

        Args:
            raw_bytes: The raw PDF bytes.

        Returns:
            Transcribed text, or an empty string if vision OCR cannot run.
        """
        try:
            from openai import OpenAI

            from app.config.settings import get_settings

            settings = get_settings()
            if not settings.llm_api_key and not settings.llm_api_base:
                logger.warning("Vision OCR skipped: LLM_API_KEY is not configured")
                return ""

            client_kwargs: dict = {"timeout": settings.llm_timeout_seconds}
            if settings.llm_api_key:
                client_kwargs["api_key"] = settings.llm_api_key
            else:
                client_kwargs["api_key"] = "dummy"
                client_kwargs["default_headers"] = {"Authorization": ""}
            if settings.llm_api_base:
                client_kwargs["base_url"] = settings.llm_api_base

            pngs = self._render_page_pngs(raw_bytes)
            if not pngs:
                return ""

            image_parts = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,"
                        + base64.standard_b64encode(png).decode("ascii")
                    },
                }
                for png in pngs
            ]
            client = OpenAI(**client_kwargs)
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _OCR_PROMPT},
                            *image_parts,
                        ],
                    }
                ],
                temperature=0,
                max_tokens=OCR_MAX_TOKENS,
            )
            content = response.choices[0].message.content or ""
            return content.strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Vision OCR fallback failed: %s", exc)
            return ""


def parse_pdf(file: object) -> str:
    """Convenience wrapper returning extracted text from a file-like object."""
    return PDFParser().extract_text(file)
