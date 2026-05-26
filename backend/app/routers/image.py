# app/routers/image.py

import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.image import ImageUploadOut
from app.services import image_service

router = APIRouter(prefix="/images", tags=["images"])


# ─── UPLOAD (creates prompt + image together) ─────────────
@router.post(
    "/upload",
    response_model=ImageUploadOut,
    status_code=status.HTTP_201_CREATED
)
async def upload_image(
    # ── Prompt fields (sent as form fields alongside the file) ──
    title: str = Form(...),
    prompt_text: str = Form(...),
    model_used: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),   # comma-separated e.g. "anime,fantasy,dark"

    # ── Image file ───────────────────────────────────────────
    file: UploadFile = File(...),

    # ── Injected dependencies ─────────────────────────────────
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a prompt and uploads its image in one request.
    UUIDs for both are auto-generated on the server.

    Send as multipart/form-data:
        title        (str, required)
        prompt_text  (str, required)
        model_used   (str, optional)
        tags         (str, optional)  comma-separated: "anime,fantasy"
        file         (image/jpeg | image/png | image/webp, required)
    """
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: jpeg, png, webp"
        )

    # Parse comma-separated tags into a list if provided
    parsed_tags: Optional[List[str]] = (
        [t.strip() for t in tags.split(",") if t.strip()]
        if tags else None
    )

    return await image_service.create_prompt_with_image(
        db=db,
        file=file,
        user_id=current_user.id,
        title=title,
        prompt_text=prompt_text,
        model_used=model_used,
        tags=parsed_tags,
    )


# ─── DELETE ───────────────────────────────────────────────
@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes the image from S3 and removes its DB record.
    Only the owner of the linked prompt can delete.
    """
    await image_service.delete_image(
        db=db,
        image_id=image_id,
        user_id=current_user.id
    )