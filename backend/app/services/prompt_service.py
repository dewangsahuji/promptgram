# app/services/prompt_service

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, UploadFile, status
from typing import Optional, List
from sqlalchemy import func, or_, cast, String
import httpx

from app.models.prompt import Prompt
from app.models.image import Image
from app.schemas.prompt import PromptCreate


# ─── HELPER ───────────────────────────────────────────────
def _with_images():
    """Reusable eager-load so every query fetches images in one extra query,
    avoiding N+1 and lazy-load errors inside async sessions."""
    return selectinload(Prompt.images)


# ─── CREATE ───────────────────────────────────────────────
async def create_prompt(
    db: AsyncSession,
    user_id: uuid.UUID,
    body: PromptCreate,
    file: Optional[UploadFile] = None,   # ✅ NEW: optional image upload
):
    """Add a new prompt to the database, with an optional image attached."""
    # Avoid circular import — image_service imports Prompt, not prompt_service
    from app.services.image_service import attach_image_to_prompt

    new_prompt = Prompt(
        user_id=user_id,
        title=body.title,
        prompt_text=body.prompt_text,
        tags=body.tags,
        model_used=body.model_used,
    )
    db.add(new_prompt)
    await db.flush()  # assigns new_prompt.id without committing yet

    if file is not None:
        await attach_image_to_prompt(db=db, prompt_id=new_prompt.id, file=file)

    await db.commit()

    # Re-fetch with images eagerly loaded so PromptOut.images is populated
    return await get_prompt_by_id(db, new_prompt.id, increment_views=False)


# ─── LIST ─────────────────────────────────────────────────
async def get_prompts(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
) -> list[Prompt]:
    offset = (page - 1) * limit
    result = await db.execute(
        select(Prompt)
        .options(_with_images())              # ✅ images included
        .order_by(Prompt.created_at.desc())   # Newest first
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


# ─── GET ONE ──────────────────────────────────────────────
async def get_prompt_by_id(
    db: AsyncSession,
    prompt_id: uuid.UUID,
    increment_views: bool = True,             # set False when called internally
) -> Optional[Prompt]:
    result = await db.execute(
        select(Prompt)
        .options(_with_images())              # ✅ images included
        .where(Prompt.id == prompt_id)
    )
    prompt = result.scalars().first()

    if prompt and increment_views:
        prompt.views += 1
        await db.commit()
        await db.refresh(prompt)

    return prompt


# ─── DELETE ───────────────────────────────────────────────
async def delete_prompt(
    db: AsyncSession,
    prompt: Prompt,
) -> None:
    await db.delete(prompt)
    await db.commit()


# ─── FULL-TEXT SEARCH ─────────────────────────────────────
async def search_prompts(
    db: AsyncSession,
    query: str,
    page: int = 1,
    limit: int = 20,
) -> List[Prompt]:
    offset = (page - 1) * limit
    ts_query = func.plainto_tsquery("english", query)

    # ✅ Query the Computed column directly or search within the tags array
    result = await db.execute(
        select(Prompt)
        .options(_with_images())              # ✅ images included
        .where(
            or_(
                Prompt.search_vector.op("@@")(ts_query),
                cast(Prompt.tags, String).ilike(f"%{query}%")
            )
        )
        .order_by(func.ts_rank(Prompt.search_vector, ts_query).desc())
        .limit(limit)
    )
    return result.scalars().all()


# ─── SEMANTIC SEARCH (AI) ─────────────────────────────────
async def semantic_search_prompts(
    db: AsyncSession,
    query: str,
    limit: int = 20,
) -> List[Prompt]:
    """Hits the AI microservice for semantic image search and returns matching Prompts."""
    # Assuming ai-service is running internally on port 8004
    ai_url = "http://ai-service:8004/ai/search"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(ai_url, json={"query": query, "limit": limit})
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

    if not data:
        return []

    # Map image IDs to scores
    scores = {}
    image_ids = []
    for item in data:
        img_id_str = item.get("image_id")
        if img_id_str:
            try:
                img_uuid = uuid.UUID(img_id_str)
                image_ids.append(img_uuid)
                scores[img_uuid] = item.get("score", 0.0)
            except ValueError:
                pass

    if not image_ids:
        return []

    # Fetch Prompts that own these images
    result = await db.execute(
        select(Prompt)
        .join(Image, Image.prompt_id == Prompt.id)
        .options(_with_images())
        .where(Image.id.in_(image_ids))
    )
    prompts = result.scalars().all()

    # Deduplicate prompts and assign max score
    prompt_dict = {}
    for prompt in prompts:
        # find highest score among images that belong to this prompt
        p_score = 0.0
        for img in prompt.images:
            if img.id in scores and scores[img.id] > p_score:
                p_score = scores[img.id]
        
        prompt.score = p_score
        prompt_dict[prompt.id] = prompt

    # Sort descending by score
    sorted_prompts = sorted(prompt_dict.values(), key=lambda p: p.score, reverse=True)
    return sorted_prompts