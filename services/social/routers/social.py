from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas.social import LikeOut, CommentCreate, CommentOut
from services import social_service
from dependencies.auth import require_auth

router = APIRouter(tags=["social"])


@router.post("/like/{prompt_id}")
async def toggle_like(
    prompt_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_auth),
):
    return await social_service.toggle_like(db, user_id, prompt_id)


@router.get("/like/{prompt_id}/count")
async def like_count(prompt_id: UUID, db: AsyncSession = Depends(get_db)):
    count = await social_service.get_like_count(db, prompt_id)
    return {"prompt_id": prompt_id, "likes": count}


@router.post("/comment/{prompt_id}", response_model=CommentOut, status_code=201)
async def add_comment(
    prompt_id: UUID,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_auth),
):
    return await social_service.add_comment(db, user_id, prompt_id, body)


@router.get("/comment/{prompt_id}", response_model=List[CommentOut])
async def get_comments(prompt_id: UUID, db: AsyncSession = Depends(get_db)):
    return await social_service.get_comments(db, prompt_id)


@router.delete("/comment/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_auth),
):
    await social_service.delete_comment(db, comment_id, user_id)


@router.post("/follow/{user_id}")
async def toggle_follow(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_auth),
):
    return await social_service.toggle_follow(db, current_user_id, user_id)


@router.get("/follow/{user_id}/followers")
async def get_followers(user_id: UUID, db: AsyncSession = Depends(get_db)):
    follows = await social_service.get_followers(db, user_id)
    return {"user_id": user_id, "followers": [str(f.follower_id) for f in follows]}


@router.get("/follow/{user_id}/following")
async def get_following(user_id: UUID, db: AsyncSession = Depends(get_db)):
    follows = await social_service.get_following(db, user_id)
    return {"user_id": user_id, "following": [str(f.following_id) for f in follows]}
