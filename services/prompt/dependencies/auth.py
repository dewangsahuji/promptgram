"""
services/prompt/dependencies/auth.py

Validates JWT tokens locally using the shared JWT_SECRET, then checks the
shared Redis instance for blacklisted tokens (written by auth-service on logout).

No HTTP call is made between services — token revocation propagates instantly
via the shared Redis blacklist.
"""
import uuid
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from config import settings
from redis_client import get_redis

# tokenUrl uses the browser-accessible host so Swagger UI can log in
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.DOCS_AUTH_SERVICE_URL}/auth/login",
    auto_error=False,
)


async def get_current_user_id(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> uuid.UUID:
    """
    Authenticate a request and return the user UUID.

    Token resolution order:
      1. `access_token` cookie  (frontend / browser)
      2. Authorization: Bearer  (Swagger UI / API clients)

    Validation:
      1. Decode and verify the JWT locally (no network hop)
      2. Check the shared Redis blacklist written by auth-service on logout
    """
    # 1. Cookie takes priority over the Authorization header
    raw_cookie = request.cookies.get("access_token")
    if raw_cookie:
        token = raw_cookie.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Verify JWT signature and expiry locally
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Check shared Redis blacklist (auth-service writes here on logout)
    redis = await get_redis()
    if await redis.get(f"blacklist:{token}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return uuid.UUID(user_id)


# Semantic alias used in router dependencies
require_auth = get_current_user_id