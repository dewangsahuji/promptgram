# app/services/collection_service.py

import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.social import Collection, CollectionPrompt
from app.models.prompt import Prompt
from app.schemas.collection import CollectionCreate


# ── Reusable helper: fetch collection with prompts eagerly loaded ──
async def _get_collection_with_prompts(
    db: AsyncSession,
    collection_id: uuid.UUID
) -> Optional[Collection]:
    result = await db.execute(
        select(Collection)
        .where(Collection.id == collection_id)
        .options(
            selectinload(Collection.prompts).selectinload(CollectionPrompt.prompt)
        )
    )
    return result.scalars().first()


async def create_collection(
    db: AsyncSession,
    user_id: uuid.UUID,
    body: CollectionCreate
) -> Collection:
    new_collection = Collection(
        user_id=user_id,
        name=body.name,
        is_public=body.is_public,
    )
    db.add(new_collection)
    await db.commit()

    # ✅ Re-fetch with selectinload so prompts list is populated (empty [])
    # Without this, FastAPI tries to lazy-load it outside the session → MissingGreenlet crash
    return await _get_collection_with_prompts(db, new_collection.id)


async def get_collection(
    db: AsyncSession,
    collection_id: uuid.UUID
) -> Optional[Collection]:
    return await _get_collection_with_prompts(db, collection_id)


async def add_prompt(
    db: AsyncSession,
    user_id: uuid.UUID,
    collection_id: uuid.UUID,
    prompt_id: uuid.UUID
) -> None:
    collection = await db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if collection.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your collection")

    prompt = await db.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Duplicate check
    result = await db.execute(
        select(CollectionPrompt).where(
            CollectionPrompt.collection_id == collection_id,
            CollectionPrompt.prompt_id == prompt_id
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="Prompt already in collection")

    db.add(CollectionPrompt(collection_id=collection_id, prompt_id=prompt_id))
    await db.commit()


async def remove_prompt(
    db: AsyncSession,
    user_id: uuid.UUID,
    collection_id: uuid.UUID,
    prompt_id: uuid.UUID
) -> None:
    collection = await db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if collection.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your collection")

    result = await db.execute(
        select(CollectionPrompt).where(
            CollectionPrompt.collection_id == collection_id,
            CollectionPrompt.prompt_id == prompt_id
        )
    )
    entry = result.scalars().first()
    if not entry:
        raise HTTPException(status_code=404, detail="Prompt not in collection")

    await db.delete(entry)
    await db.commit()