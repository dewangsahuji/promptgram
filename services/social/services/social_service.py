import uuid
from typing import List
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from models.social import Like, Comment, Follow, Collection, CollectionPrompt
from schemas.social import CommentCreate, CollectionCreate


# ---------------------------------------------------------------------------
# Likes
# ---------------------------------------------------------------------------

async def toggle_like(db: AsyncSession, user_id: uuid.UUID, prompt_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(Like).where(Like.user_id == user_id, Like.prompt_id == prompt_id)
    )
    existing = result.scalars().first()
    if existing:
        await db.delete(existing)
        await db.commit()
        return {"liked": False}
    like = Like(user_id=user_id, prompt_id=prompt_id)
    db.add(like)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
    return {"liked": True}


async def get_like_count(db: AsyncSession, prompt_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(Like).where(Like.prompt_id == prompt_id)
    )
    return result.scalar() or 0


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

async def add_comment(
    db: AsyncSession, user_id: uuid.UUID, prompt_id: uuid.UUID, data: CommentCreate
) -> Comment:
    comment = Comment(user_id=user_id, prompt_id=prompt_id, body=data.body)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def get_comments(db: AsyncSession, prompt_id: uuid.UUID) -> List[Comment]:
    result = await db.execute(select(Comment).where(Comment.prompt_id == prompt_id))
    return list(result.scalars().all())


async def delete_comment(db: AsyncSession, comment_id: uuid.UUID, user_id: uuid.UUID):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your comment")
    await db.delete(comment)
    await db.commit()


# ---------------------------------------------------------------------------
# Follows
# ---------------------------------------------------------------------------

async def toggle_follow(
    db: AsyncSession, follower_id: uuid.UUID, following_id: uuid.UUID
) -> dict:
    if follower_id == following_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == follower_id, Follow.following_id == following_id
        )
    )
    existing = result.scalars().first()
    if existing:
        await db.delete(existing)
        await db.commit()
        return {"following": False}
    follow = Follow(follower_id=follower_id, following_id=following_id)
    db.add(follow)
    await db.commit()
    return {"following": True}


async def get_followers(db: AsyncSession, user_id: uuid.UUID) -> List[Follow]:
    result = await db.execute(select(Follow).where(Follow.following_id == user_id))
    return list(result.scalars().all())


async def get_following(db: AsyncSession, user_id: uuid.UUID) -> List[Follow]:
    result = await db.execute(select(Follow).where(Follow.follower_id == user_id))
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------

async def create_collection(
    db: AsyncSession, user_id: uuid.UUID, data: CollectionCreate
) -> Collection:
    collection = Collection(user_id=user_id, **data.model_dump())
    db.add(collection)
    await db.commit()
    await db.refresh(collection)
    return collection


async def get_user_collections(db: AsyncSession, user_id: uuid.UUID) -> List[Collection]:
    result = await db.execute(select(Collection).where(Collection.user_id == user_id))
    return list(result.scalars().all())


async def add_to_collection(
    db: AsyncSession,
    collection_id: uuid.UUID,
    prompt_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict:
    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    collection = result.scalars().first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if collection.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your collection")
    entry = CollectionPrompt(collection_id=collection_id, prompt_id=prompt_id)
    db.add(entry)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Prompt already in collection")
    return {"added": True}
