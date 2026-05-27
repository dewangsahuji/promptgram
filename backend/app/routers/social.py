# routers/social.py
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.social import CommentCreate, CommentOut, LikeOut, FollowOut
from app.services import social_service

router = APIRouter(tags=["social"])


# ─── LIKES ────────────────────────────────────────────────

@router.post("/like/{prompt_id}" , response_model=LikeOut)
async def toggle_like(
    prompt_id : uuid.UUID,
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
    ):
    return await social_service.toggle_like(db,
                                            user_id=current_user.id,
                                            prompt_id=prompt_id,
                                            )


# ─── COMMENTS ────────────────────────────────────────────────
@router.post("/comment/{comment_id}" , response_model=CommentOut , status_code=status.HTTP_201_CREATED)
async def add_comment(
    prompt_id: uuid.UUID,
    body : CommentCreate,
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    return await social_service.add_comments(db ,
                                       current_user.id,
                                       prompt_id,
                                       body)


@router.delete("/comment/{comment_id}" , status_code = status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id:uuid.UUID,
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    
    await social_service.delete_comment(db ,
                                        user_id=current_user.id ,
                                        comment_id=comment_id)
    
# ─── FOLLOWS ──────────────────────────────────────────────
@router.post("/follow/{user_id}" , response_model=FollowOut  )
async def toggle_follow(
    user_id : uuid.UUID,
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    return await social_service.toggle_follow(db,
                                              current_user.id,
                                              user_id)




