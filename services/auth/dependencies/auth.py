"""
services/auth/dependencies/auth.py

Two dependency functions:

  get_current_user          — validates a short-lived JWT (access_token).
                               Used by POST /auth/authorize only.

  get_user_by_api_token     — looks up an opaque api_token in Redis.
                               Used by GET /auth/me, POST /auth/logout,
                               GET /auth/validate (Nginx auth_request).
"""
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

# ── OAuth2 schemes ────────────────────────────────────────────────────────────
# Swagger "Authorize" button on the auth-service docs uses /auth/api-token so
# users get an api_token (not a raw JWT) in one step.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/api-token", auto_error=False)


def _extract_token(request: Request, bearer_token: Optional[str]) -> Optional[str]:
    """Cookie → Authorization header → None."""
    raw = request.cookies.get("access_token")
    if raw:
        return raw.removeprefix("Bearer ").strip()
    return bearer_token or None


# ── Dependency 1: JWT (access_token) ─────────────────────────────────────────
async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    redis: aioredis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate a short-lived JWT access_token and return the User object."""
    raw = _extract_token(request, token)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check blacklist (handles revoked JWTs)
    if await redis.get(f"blacklist:{raw}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(raw, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


# ── Dependency 2: api_token (opaque, Redis-backed) ───────────────────────────
async def get_user_by_api_token(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    redis: aioredis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Look up an opaque api_token in Redis and return the User object."""
    raw = _extract_token(request, token)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = await redis.get(f"api_token:{raw}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired api_token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


# Aliases
require_auth = get_current_user
require_api_token = get_user_by_api_token