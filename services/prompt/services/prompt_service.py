import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from fastapi import HTTPException
from models.prompt import Prompt
from schemas.prompt import PromptCreate, PromptUpdate


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
) -> List[Prompt]:
    query = (
        select(Prompt)
        .order_by(desc(Prompt.created_at))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_trending(db: AsyncSession, limit: int = 20) -> List[Prompt]:
    # Score = views*0.4 + downloads*0.4 + score*0.2
    # (social metrics such as likes/comments come from a separate service)
    result = await db.execute(
        select(Prompt)
        .order_by(
            desc(Prompt.views * 0.4 + Prompt.downloads * 0.4 + Prompt.score * 0.2)
        )
        .limit(limit)
    )
    return list(result.scalars().all())


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
