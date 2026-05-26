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
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


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

    # ── Build S3 key using real extension ─────────────────
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

    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=image.s3_key)
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"S3 delete failed: {e.response['Error']['Message']}"
        )

    await db.delete(image)
    await db.commit()