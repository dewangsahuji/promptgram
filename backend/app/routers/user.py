# app/routers/user.py

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate, UserPromptsOut
from app.services import user_service

router = APIRouter(tags=["users"])


# ─── GET PUBLIC PROFILE ───────────────────────────────────
@router.get("/{user_id}", response_model=UserOut)
async def get_user_profile(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint — returns any user's profile by ID.
    No auth required.
    """
    user = await user_service.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ─── GET USER'S PROMPTS ───────────────────────────────────
@router.get("/{user_id}/prompts", response_model=List[UserPromptsOut])
async def get_user_prompts(
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns all prompts created by a specific user.
    Paginated. No auth required.
    """
    return await user_service.get_prompts_by_user(db, user_id, page, limit)


# ─── UPDATE MY PROFILE ────────────────────────────────────
@router.patch("/me", response_model=UserOut)
async def update_my_profile(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the currently logged-in user's bio or avatar_url.
    Only sends fields that are explicitly provided (partial update).
    """
    return await user_service.update_user(db, current_user, body)