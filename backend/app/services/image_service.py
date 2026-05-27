# app/services/image_service.py

import uuid
import boto3
import magic  # python-magic: detects real file type from bytes
from botocore.exceptions import ClientError
from typing import Optional, List

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image
from app.models.prompt import Prompt
from app.config import settings


# ─── ALLOWED TYPES ────────────────────────────────────────
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

# Maps real mime type → file extension
MIME_TO_EXT = {
    "image/jpeg": "jpg",
    "image/png":  "png",
    "image/webp": "webp",
}


# ─── S3 CLIENT ────────────────────────────────────────────
def get_s3_client():
    kwargs = dict(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )
    # When S3_ENDPOINT_URL is set (e.g. http://minio:9000), boto3 sends all
    # requests there instead of AWS — required for MinIO in Docker.
    if settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


# ─── ATTACH IMAGE TO EXISTING PROMPT ─────────────────────
async def attach_image_to_prompt(
    db: AsyncSession,
    prompt_id: uuid.UUID,
    file: UploadFile,
) -> Image:
    """
    Reads *file*, validates it, uploads to S3, and creates an Image row
    linked to *prompt_id*. The caller owns the transaction (commit/rollback).
    Used by prompt_service.create_prompt when a file is included on creation.
    """
    file_bytes = await file.read()
    real_mime = magic.from_buffer(file_bytes, mime=True)

    if real_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{real_mime}'. Allowed: jpeg, png, webp",
        )

    image_id = uuid.uuid4()
    extension = MIME_TO_EXT[real_mime]
    # ── Flat key: images/<image_id>.ext — no per-prompt subfolder ──
    s3_key = f"images/{image_id}.{extension}"
    s3_url = (
        f"https://{settings.S3_BUCKET_NAME}"
        f".s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    )

    s3 = get_s3_client()
    try:
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=real_mime,
        )
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"S3 upload failed: {e.response['Error']['Message']}",
        )

    image = Image(
        id=image_id,
        prompt_id=prompt_id,
        s3_key=s3_key,
        s3_url=s3_url,
    )
    db.add(image)
    return image


# ─── CREATE PROMPT + IMAGE (atomic) ───────────────────────
async def create_prompt_with_image(
    db: AsyncSession,
    file: UploadFile,
    user_id: uuid.UUID,
    title: str,
    prompt_text: str,
    model_used: Optional[str],
    tags: Optional[List[str]],
) -> dict:
    """
    Creates a Prompt and an Image record together in one DB transaction.
    If the S3 upload fails, the whole transaction is rolled back — no
    orphaned prompt records are left behind.
    """

    # ── Read bytes first (needed for magic-byte type detection) ──
    file_bytes = await file.read()

    # ── Detect real MIME type from magic bytes ────────────
    # This works even if the client sends wrong Content-Type
    real_mime = magic.from_buffer(file_bytes, mime=True)

    if real_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{real_mime}'. Allowed: jpeg, png, webp"
        )

    # ── Auto-generate UUIDs ───────────────────────────────
    prompt_id = uuid.uuid4()
    image_id  = uuid.uuid4()

    # ── Flat key: images/<image_id>.ext — no per-prompt subfolder ──
    extension = MIME_TO_EXT[real_mime]
    s3_key = f"images/{image_id}.{extension}"
    s3_url = (
        f"https://{settings.S3_BUCKET_NAME}"
        f".s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    )

    # ── Upload to S3 BEFORE writing to DB ─────────────────
    s3 = get_s3_client()
    try:
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=real_mime,
        )
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"S3 upload failed: {e.response['Error']['Message']}"
        )

    # ── Write Prompt + Image in one transaction ────────────
    try:
        new_prompt = Prompt(
            id=prompt_id,
            user_id=user_id,
            title=title,
            prompt_text=prompt_text,
            model_used=model_used,
            tags=tags,
        )
        db.add(new_prompt)

        new_image = Image(
            id=image_id,
            prompt_id=prompt_id,
            s3_key=s3_key,
            s3_url=s3_url,
            # qdrant_id is left NULL — filled in Phase 2 when AI pipeline runs
        )
        db.add(new_image)

        await db.commit()
        await db.refresh(new_prompt)
        await db.refresh(new_image)

    except Exception:
        await db.rollback()

        # Best-effort S3 cleanup so we don't leave orphaned files
        try:
            s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
        except ClientError:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save to database. S3 file has been cleaned up."
        )

    return {
        "prompt": new_prompt,
        "image":  new_image,
    }


# ─── DELETE IMAGE ─────────────────────────────────────────
async def delete_image(
    db: AsyncSession,
    image_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    image = await db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    prompt = await db.get(Prompt, image.prompt_id)
    if not prompt or prompt.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your image")

    # ── Delete DB row first, then S3 ──────────────────────
    # This order ensures no dangling DB rows that point to a missing file.
    # If S3 cleanup fails afterward, the file is orphaned in storage but
    # the app stays consistent. The inverse risks a live DB row with a
    # broken S3 reference.
    s3_key_to_delete = image.s3_key
    await db.delete(image)
    await db.commit()

    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key_to_delete)
    except ClientError as e:
        # DB row is already gone — log this for manual S3 cleanup
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Image removed from database but S3 delete failed: {e.response['Error']['Message']}",
        )