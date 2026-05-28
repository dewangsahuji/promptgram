import uuid
import httpx
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func
from fastapi import HTTPException
from models.prompt import Prompt
from models.image import Image
from schemas.prompt import PromptCreate, PromptUpdate
from s3_client import _url_for_key

AUTH_SERVICE_URL = "http://auth-service:8001"


async def _get_username(user_id: uuid.UUID) -> Optional[str]:
    """Fetch username from auth-service. Returns None on any failure."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{AUTH_SERVICE_URL}/auth/users/{str(user_id)}")
            if r.status_code == 200:
                return r.json().get("username")
    except Exception:
        pass
    return None


async def _enrich(db: AsyncSession, prompts: List[Prompt]) -> List[dict]:
    """Attach thumbnail_url and username to each prompt dict."""
    if not prompts:
        return []

    prompt_ids = [p.id for p in prompts]

    # Fetch first image for each prompt in a single query
    img_result = await db.execute(
        select(Image)
        .where(Image.prompt_id.in_(prompt_ids))
        .order_by(Image.created_at)
    )
    images = img_result.scalars().all()

    # Build prompt_id → fresh thumbnail URL from s3_key
    thumb_map: dict[uuid.UUID, Optional[str]] = {}
    for img in images:
        if img.prompt_id not in thumb_map:
            # Always regenerate from s3_key so presigned URLs are fresh
            thumb_key = f"thumbnails/{img.s3_key.split('/')[-1]}"
            thumb_map[img.prompt_id] = _url_for_key(thumb_key)

    # Collect unique user_ids and fetch usernames concurrently
    unique_user_ids = list({p.user_id for p in prompts})
    import asyncio
    usernames_list = await asyncio.gather(*[_get_username(uid) for uid in unique_user_ids])
    username_map = dict(zip(unique_user_ids, usernames_list))

    enriched = []
    for p in prompts:
        d = {
            "id": p.id,
            "user_id": p.user_id,
            "title": p.title,
            "prompt_text": p.prompt_text,
            "tags": p.tags,
            "model_used": p.model_used,
            "score": p.score,
            "views": p.views,
            "downloads": p.downloads,
            "created_at": p.created_at,
            "username": username_map.get(p.user_id),
            "thumbnail_url": thumb_map.get(p.id),
            "likes_count": 0,
        }
        enriched.append(d)
    return enriched


async def create_prompt(
    db: AsyncSession, user_id: uuid.UUID, data: PromptCreate
) -> Prompt:
    prompt = Prompt(user_id=user_id, **data.model_dump())
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)
    return prompt


async def get_prompt(db: AsyncSession, prompt_id: uuid.UUID) -> Optional[Prompt]:
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    return result.scalars().first()


async def list_prompts(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    tags: Optional[List[str]] = None,
) -> List[dict]:
    query = (
        select(Prompt)
        .order_by(desc(Prompt.created_at))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    prompts = list(result.scalars().all())
    return await _enrich(db, prompts)


async def get_trending(db: AsyncSession, limit: int = 20) -> List[dict]:
    # COALESCE score to 0 so NULL doesn't break the sort
    result = await db.execute(
        select(Prompt)
        .order_by(
            desc(
                Prompt.views * 0.4
                + Prompt.downloads * 0.4
                + func.coalesce(Prompt.score, 0.0) * 0.2
            )
        )
        .limit(limit)
    )
    prompts = list(result.scalars().all())
    return await _enrich(db, prompts)


async def update_prompt(
    db: AsyncSession,
    prompt_id: uuid.UUID,
    user_id: uuid.UUID,
    data: PromptUpdate,
) -> Prompt:
    prompt = await get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    if prompt.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your prompt")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(prompt, field, value)
    await db.commit()
    await db.refresh(prompt)
    return prompt


async def delete_prompt(
    db: AsyncSession, prompt_id: uuid.UUID, user_id: uuid.UUID
):
    prompt = await get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    if prompt.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your prompt")
    await db.delete(prompt)
    await db.commit()


async def increment_views(db: AsyncSession, prompt_id: uuid.UUID):
    prompt = await get_prompt(db, prompt_id)
    if prompt:
        prompt.views += 1
        await db.commit()
