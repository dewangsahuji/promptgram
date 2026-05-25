# app/services/prompt_service

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from typing import Optional

from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate

async def create_prompt(
    db : AsyncSession ,
    user_id : uuid.UUID,
    body : PromptCreate
    ):
    """ Add a new prompt to the database
    """

    new_prompt = Prompt(
        user_id = user_id,
        title = body.title,
        prompt_text = body.prompt_text,
        tags = body.tags,
        model_used = body.model_used
    )

    db.add(new_prompt)

    await db.commit()
    await db.refresh(new_prompt)
    return new_prompt
    
    
async def get_prompts(
    db:AsyncSession,
    page : int = 1,
    limit : int = 20
    ) -> list[Prompt]:

    offset = (page - 1) * limit

    result = await db.execute(
        select(Prompt)
        .order_by(Prompt.created_at.desc()) # Newest first
        .offset(offset)
        .limit(limit)
    )
    
    return result.scalars().all()

async def get_prompt_by_id(
    db : AsyncSession,
    prompt_id : uuid.UUID,
) -> Optional[Prompt]:
    
    prompt = await db.get(Prompt, prompt_id)

    if prompt:
        prompt.views += 1
        await db.commit()
        await db.refresh(prompt)

    return prompt


async def delete_prompt(
    db: AsyncSession,
    prompt: Prompt
) -> None:
    await db.delete(prompt)
    await db.commit()






