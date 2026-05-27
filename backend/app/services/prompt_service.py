# app/services/prompt_service

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, UploadFile, status
from typing import Optional, List
from sqlalchemy import func

from app.models.prompt import Prompt
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

    # ✅ Query the Computed column directly so Postgres uses your GIN index!
    result = await db.execute(
        select(Prompt)
        .options(_with_images())              # ✅ images included
        .where(Prompt.search_vector.op("@@")(ts_query))
        .order_by(func.ts_rank(Prompt.search_vector, ts_query).desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()