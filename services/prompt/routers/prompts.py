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
    enriched = await prompt_service.list_prompts(db, page, limit)
    return [PromptOut.model_validate(p) for p in enriched]


@router.get("/search", response_model=List[PromptOut])
async def search_prompts(
    q: str,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    enriched = await prompt_service.search_prompts(db, q, page, limit)
    return [PromptOut.model_validate(p) for p in enriched]


@router.get("/semantic-search", response_model=List[PromptOut])
async def semantic_search_prompts(
    q: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    AI Semantic Search over images via AI Microservice.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    enriched = await prompt_service.semantic_search_prompts(db, q, limit)
    return [PromptOut.model_validate(p) for p in enriched]


@router.get("/trending", response_model=List[PromptOut])
async def trending(
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    cached = await redis.get("trending")
    if cached:
        return json.loads(cached)
    enriched = await prompt_service.get_trending(db)
    validated = [PromptOut.model_validate(p).model_dump(mode="json") for p in enriched]
    await redis.setex("trending", 300, json.dumps(validated, default=str))
    return [PromptOut.model_validate(p) for p in enriched]


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


# ─── AI service PATCH endpoints ───────────────────────────────────────────────

from pydantic import BaseModel
from typing import List as _List


class TagsUpdate(BaseModel):
    tags: _List[str]


class ScoreUpdate(BaseModel):
    score: float


@router.patch("/{prompt_id}/tags", status_code=200)
async def update_tags(
    prompt_id: UUID,
    body: TagsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Called by ai-service classifier to append auto-detected tags."""
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    existing = list(prompt.tags or [])
    merged = list(dict.fromkeys(existing + body.tags))  # deduplicate, preserve order
    prompt.tags = merged
    await db.commit()
    return {"tags": merged}


@router.patch("/{prompt_id}/score", status_code=200)
async def update_score(
    prompt_id: UUID,
    body: ScoreUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Called by ai-service classifier to set quality score."""
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    prompt.score = body.score
    await db.commit()
    return {"score": body.score}
