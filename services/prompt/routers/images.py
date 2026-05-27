import uuid
import io
import asyncio
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from database import get_db
from s3_client import upload_to_s3, delete_from_s3
from models.image import Image
from schemas.image import ImageOut
from dependencies.auth import require_auth
from PIL import Image as PILImage
import httpx
from config import settings

router = APIRouter(tags=["images"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


# ─── Helper: generate + upload thumbnail ─────────────────────────────────────

async def generate_thumbnail(content: bytes, thumb_key: str) -> str:
    def _make_thumbnail():
        img = PILImage.open(io.BytesIO(content))
        img.thumbnail((400, 400))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    thumb_bytes = await asyncio.to_thread(_make_thumbnail)
    return await upload_to_s3(thumb_bytes, thumb_key, "image/png")


# ─── Helper: call AI pipeline as BackgroundTask ───────────────────────────────

async def _trigger_ai_pipeline(image_id: str):
    """Fire-and-forget call to ai-service pipeline endpoint."""
    ai_url = getattr(settings, "AI_SERVICE_URL", "http://ai-service:8004")
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            await client.post(f"{ai_url}/ai/pipeline/{image_id}")
    except Exception:
        pass  # Non-fatal — AI pipeline can be retried independently


# ─── Upload ───────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=ImageOut, status_code=201)
async def upload_image(
    prompt_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_auth),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: jpeg, png, webp",
        )
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 10MB")

    image_uuid = str(uuid.uuid4())
    s3_key = f"originals/{image_uuid}.png"
    thumb_key = f"thumbnails/{image_uuid}.png"

    s3_url = await upload_to_s3(content, s3_key, file.content_type)
    thumb_url = await generate_thumbnail(content, thumb_key)

    image = Image(
        prompt_id=prompt_id,
        s3_key=s3_key,
        s3_url=s3_url,
        thumbnail_url=thumb_url,
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)

    # Trigger AI pipeline in the background (non-blocking)
    background_tasks.add_task(_trigger_ai_pipeline, str(image.id))

    return image


# ─── List images for a prompt ────────────────────────────────────────────────

@router.get("/prompt/{prompt_id}", response_model=list[ImageOut])
async def get_images_for_prompt(
    prompt_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Image).where(Image.prompt_id == prompt_id))
    return list(result.scalars().all())


# ─── Get single image (used by AI service pipeline) ──────────────────────────

@router.get("/{image_id}", response_model=ImageOut)
async def get_image(image_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalars().first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


# ─── Delete ───────────────────────────────────────────────────────────────────

@router.delete("/{image_id}", status_code=204)
async def delete_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_auth),
):
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalars().first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    await delete_from_s3(image.s3_key)
    if image.thumbnail_url:
        thumb_key = f"thumbnails/{image.s3_key.split('/')[-1]}"
        await delete_from_s3(thumb_key)
    await db.delete(image)
    await db.commit()


# ─── AI service PATCH endpoints ───────────────────────────────────────────────

class QdrantUpdate(BaseModel):
    qdrant_id: str


class NsfwUpdate(BaseModel):
    nsfw: bool


@router.patch("/{image_id}/qdrant", status_code=200)
async def set_qdrant_id(
    image_id: UUID,
    body: QdrantUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Called by ai-service after embedding to save the Qdrant point ID."""
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalars().first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.qdrant_id = uuid.UUID(body.qdrant_id)
    await db.commit()
    return {"qdrant_id": body.qdrant_id}


@router.patch("/{image_id}/nsfw", status_code=200)
async def flag_nsfw(
    image_id: UUID,
    body: NsfwUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Called by ai-service after NSFW moderation."""
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalars().first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.nsfw = body.nsfw
    await db.commit()
    return {"nsfw": body.nsfw}
