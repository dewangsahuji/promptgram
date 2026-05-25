# services/social_service.py
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.social import Like, Comment, Follow
from app.models.prompt import Prompt
from app.schemas.social import CommentCreate

# ─── LIKES ────────────────────────────────────────────────

async def toggle_like(
    db : AsyncSession,
    user_id : uuid.UUID,
    prompt_id : uuid.UUID
) -> dict:
    
    # Check if prompt exists
    prompt = await db.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(404, "Prompt not found")
    
    # Check if like already exists
    result = await db.execute(
        select(Like).where(
            Like.user_id == user_id,
            Like.prompt_id == prompt_id
        )
    )

    existing_like = result.scalars().first()

    if existing_like :
        # Already liked -> Not liked
        await db.delete(existing_like)
        await db.commit()

        return {"liked" : False}

    else :
        # Not liked -> Liked
        new_like = Like(user_id = user_id,
                        prompt_id = prompt_id)
        db.add(new_like)
        await db.commit()

        return {"liked" : True}


# ─── COMMENTS ────────────────────────────────────────────────

async def add_comments(
    db : AsyncSession,
    user_id : uuid.UUID,
    prompt_id : uuid.UUID,
    body : CommentCreate 
    ) -> Comment:

    # Check if prompt exists
    prompt = await db.get(Prompt , prompt_id)
    if not prompt:
        raise HTTPException(404 , "Prompt not found")

    new_comment = Comment(
        user_id = user_id,
        prompt_id = prompt_id,
        body = body.body
    )

    db.add(new_comment)

    await db.commit()
    await db.refresh(new_comment)

    return new_comment

async def delete_comment(
    db :AsyncSession,
    user_id : uuid.UUID,
    comment_id : uuid.UUID
    ) -> None:
    
    comment = await db.get(Comment , comment_id)

    if not comment:
        raise HTTPException(404 , "Comment not found")

    if comment.user_id != user_id:
        raise HTTPException(403 , "(Unauthorized) Not Your Comment")

    await db.delete(comment)
    await db.commit()
    
# ─── FOLLOWS ──────────────────────────────────────────────
async def toggle_follow(
    db : AsyncSession,
    follower_id : uuid.UUID,
    following_id : uuid.UUID
    ) -> dict :

    # Can't Follow yourself
    if follower_id == following_id:
        raise HTTPException(400 , "You cannot follow yourself")
    
    # Check if follow already exists
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == following_id,
        )
    )
    
    existing_follow = result.scalars().first()

    if existing_follow:
        # Already following → unfollow
        await db.delete(existing_follow)
        await db.commit()

        return {"following" : False}
    
    else :
        # Not following → follow

        new_follow = Follow(
            follower_id = follower_id,
            following_id = following_id
        )

    # Add these three lines to finish the function!
    db.add(new_follow)
    await db.commit()
    
    return {"following": True}