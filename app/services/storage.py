"""Switchable file storage service (Vercel Blob or AWS S3).

Reads ``STORAGE_BACKEND`` from settings (``""``, ``"blob"``, or ``"s3"``)
and dispatches uploads to the configured backend. When the backend is
unconfigured (``""``), uploads are skipped and ``None`` is returned.
"""

from __future__ import annotations

import logging
import uuid

logger = logging.getLogger(__name__)


async def upload_resume(
    file_bytes: bytes,
    *,
    filename: str,
    user_id: str,
) -> str | None:
    """Upload a resume document to the configured storage backend.

    Args:
        file_bytes: Raw file content.
        filename: Original filename (used to derive extension).
        user_id: Owner's user ID (used as path prefix).

    Returns:
        A public/downloadable URL string, or ``None`` if storage is disabled.
    """
    from app.config.settings import get_settings

    settings = get_settings()
    backend = settings.storage_backend
    if not backend:
        return None

    ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
    key = f"resumes/{user_id}/{uuid.uuid4().hex}.{ext}"

    if backend == "blob":
        return await _upload_blob(file_bytes, key, filename)
    if backend == "s3":
        return await _upload_s3(file_bytes, key)
    logger.warning("Unknown STORAGE_BACKEND=%s — skipping upload", backend)
    return None


async def _upload_blob(file_bytes: bytes, key: str, filename: str) -> str | None:
    """Upload to Vercel Blob via the official Python SDK."""
    try:
        from vercel.blob import AsyncBlobClient

        client = AsyncBlobClient()
        uploaded = await client.put(
            key,
            file_bytes,
            access="private",
            add_random_suffix=True,
            content_type="application/octet-stream",
        )
        logger.info("Uploaded resume to Vercel Blob: %s", uploaded.url)
        return uploaded.url
    except Exception:
        logger.exception("Vercel Blob upload failed")
        return None


async def _upload_s3(file_bytes: bytes, key: str) -> str | None:
    """Upload to AWS S3 via boto3 (runs in executor to stay async)."""
    import asyncio
    from functools import partial

    from app.config.settings import get_settings

    settings = get_settings()

    def _sync_upload() -> str:
        import boto3

        kwargs: dict = {
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
            "region_name": settings.aws_region,
        }
        if settings.aws_endpoint_url:
            kwargs["endpoint_url"] = settings.aws_endpoint_url

        s3 = boto3.client("s3", **kwargs)
        s3.put_object(
            Bucket=settings.aws_s3_bucket,
            Key=key,
            Body=file_bytes,
            ContentType="application/octet-stream",
        )
        if settings.aws_endpoint_url:
            return f"{settings.aws_endpoint_url}/{settings.aws_s3_bucket}/{key}"
        return f"https://{settings.aws_s3_bucket}.s3.{settings.aws_region}.amazonaws.com/{key}"

    try:
        url = await asyncio.get_event_loop().run_in_executor(
            None, partial(_sync_upload)
        )
        logger.info("Uploaded resume to S3: %s", url)
        return url
    except Exception:
        logger.exception("S3 upload failed")
        return None
