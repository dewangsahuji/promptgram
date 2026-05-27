import json
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from database import get_db
from redis_client import get_redis
from schemas.prompt import PromptCreate, PromptOut, PromptUpdate
from services import prompt_service
from dependencies.auth import require_auth

router = APIRouter(tags=["prompts"])


@router.post("/", response_model=PromptOut, status_code=201)
async def create_prompt(
    body: PromptCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_auth),
):
    return await prompt_service.create_prompt(db, user_id, body)


@router.get("/", response_model=List[PromptOut])
async def list_prompts(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    return await prompt_service.list_prompts(db, page, limit)


@router.get("/trending", response_model=List[PromptOut])
async def trending(
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    cached = await redis.get("trending")
    if cached:
        return json.loads(cached)
    results = await prompt_service.get_trending(db)
    serialized = [PromptOut.model_validate(r).model_dump(mode="json") for r in results]
    await redis.setex("trending", 600, json.dumps(serialized, default=str))
    return results


@router.get("/{prompt_id}", response_model=PromptOut)
async def get_prompt(
    prompt_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    background_tasks.add_task(prompt_service.increment_views, db, prompt_id)
    return prompt


@router.patch("/{prompt_id}", response_model=PromptOut)
async def update_prompt(
    prompt_id: UUID,
    body: PromptUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_auth),
):
    return await prompt_service.update_prompt(db, prompt_id, user_id, body)


@router.delete("/{prompt_id}", status_code=204)
async def delete_prompt(
    prompt_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_auth),
):
    await prompt_service.delete_prompt(db, prompt_id, user_id)
