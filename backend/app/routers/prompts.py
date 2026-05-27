## app/routers/prompts.py

import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.prompt import PromptCreate, PromptOut
from app.services import prompt_service

router = APIRouter(tags=["prompts"])


# ─── SEARCH ───────────────────────────────────────────────
# ✅ Must be defined BEFORE /{prompt_id} — otherwise FastAPI
#    matches "search" as a UUID and returns a 422 error
@router.get("/search", response_model=List[PromptOut])
async def search_prompts(
    q: str,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    Full-text search over prompt titles and text.
    Usage: GET /prompts/search?q=cyberpunk+samurai
    Results are ranked by relevance (title matches rank higher than body matches).
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    return await prompt_service.search_prompts(db, q, page, limit)


# ─── CREATE (with optional image) ─────────────────────────
@router.post("/", response_model=PromptOut, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    # Prompt fields — sent as form fields so a file can travel in the same request
    title: str = Form(...),
    prompt_text: str = Form(...),
    model_used: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),        # comma-separated e.g. "anime,fantasy"

    # Optional image — omit entirely to create a text-only prompt
    file: Optional[UploadFile] = File(None),

    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a prompt. Optionally attach an image in the same request.

    Send as **multipart/form-data**:
    - `title`        (str, required)
    - `prompt_text`  (str, required)
    - `model_used`   (str, optional)
    - `tags`         (str, optional) — comma-separated: "anime,fantasy"
    - `file`         (image/jpeg | image/png | image/webp, optional)

    If `file` is omitted the prompt is created with an empty `images` list.
    """
    parsed_tags: Optional[List[str]] = (
        [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    )

    body = PromptCreate(
        title=title,
        prompt_text=prompt_text,
        model_used=model_used,
        tags=parsed_tags,
    )

    return await prompt_service.create_prompt(
        db=db,
        user_id=current_user.id,
        body=body,
        file=file,   # None → no upload, prompt still created fine
    )


# ─── LIST ─────────────────────────────────────────────────
@router.get("/", response_model=List[PromptOut])
async def list_prompts(
    page: int = 1,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    return await prompt_service.get_prompts(db, page, limit)


# ─── GET ONE ──────────────────────────────────────────────
@router.get("/{prompt_id}", response_model=PromptOut)
async def get_prompt(
    prompt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    prompt = await prompt_service.get_prompt_by_id(db, prompt_id)

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return prompt


# ─── DELETE ───────────────────────────────────────────────
@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prompt = await prompt_service.get_prompt_by_id(
        db, prompt_id, increment_views=False   # don't count a delete-check as a view
    )

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    if prompt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your prompt")  # 🔒 ownership check

    await prompt_service.delete_prompt(db, prompt)