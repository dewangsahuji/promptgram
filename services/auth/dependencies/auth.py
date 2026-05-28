import uuid
from typing import Optional

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from config import settings
from database import get_db
from models.user import User
from redis_client import get_redis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    redis: aioredis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Try cookie first, then fall back to Bearer header
    raw_cookie = request.cookies.get("access_token")
    if raw_cookie:
        token = raw_cookie.replace("Bearer ", "")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is blacklisted in Redis
    is_blacklisted = await redis.get(f"blacklist:{token}")
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


# Alias for semantic clarity in router dependencies
require_auth = get_current_user
