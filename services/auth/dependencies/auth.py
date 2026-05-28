"""
services/auth/dependencies/auth.py

The auth-service is the source of truth for JWT validation.
It decodes tokens directly, checks the Redis blacklist, and queries its own DB.
No outbound HTTP calls — this service IS the auth authority.
"""
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
    """
    Resolve the current user from a JWT cookie or Bearer header.

    Steps:
      1. Extract token from cookie (preferred) or Authorization header.
      2. Reject if blacklisted in Redis (i.e. logged out).
      3. Decode and verify the JWT signature + expiry.
      4. Load and return the User row from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Cookie takes priority over the Authorization header.
    raw_cookie = request.cookies.get("access_token")
    if raw_cookie:
        token = raw_cookie.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Reject blacklisted tokens (set by /auth/logout with a 24 h TTL).
    if await redis.get(f"blacklist:{token}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Decode and validate the JWT.
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

    # 4. Resolve the user from the database.
    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


# Semantic alias used in router dependencies.
require_auth = get_current_user