# app/services/user_service.py

import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.models.prompt import Prompt
from app.schemas.user import UserUpdate


async def get_user_by_id(
    db: AsyncSession,
    user_id: uuid.UUID
) -> Optional[User]:
    return await db.get(User, user_id)


async def get_prompts_by_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 20
) -> List[Prompt]:
    offset = (page - 1) * limit

    result = await db.execute(
        select(Prompt)
        .where(Prompt.user_id == user_id)
        .order_by(Prompt.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


async def update_user(
    db: AsyncSession,
    user: User,
    body: UserUpdate
) -> User:
    # Only update fields that were explicitly sent in the request
    # model_dump(exclude_unset=True) ignores fields the client didn't include
    updates = body.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user