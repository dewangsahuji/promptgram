"""
services/social/dependencies/auth.py

Production path  (requests through Nginx):
  Nginx validates the api_token via auth_request → auth-service /auth/validate
  → injects X-User-Id header → this service reads it directly. No token logic needed.

Dev/Swagger path (requests direct to :8003):
  No X-User-Id header present, so fall back to validating the api_token against
  the shared Redis instance (same Redis the auth-service writes to on /auth/api-token).
"""
import uuid
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from redis_client import get_redis

# Swagger "Authorize" button points to auth-service /auth/api-token so the user
# enters credentials once and gets an api_token usable on this service directly.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="http://localhost:8001/auth/api-token",
    auto_error=False,
)


async def get_current_user_id(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
) -> uuid.UUID:
    """
    Return the authenticated user's UUID.

    Path 1 — Production (via Nginx gateway):
      Nginx has already validated the api_token and injected X-User-Id.
      We trust this header completely.

    Path 2 — Dev / Swagger UI on localhost:8003:
      No X-User-Id present; validate the api_token against shared Redis directly.
    """
    # ── Path 1: Production — trust Nginx-injected header ─────────────────────
    user_id_header = request.headers.get("X-User-Id")
    if user_id_header:
        try:
            return uuid.UUID(user_id_header)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid X-User-Id header.",
            )

    # ── Path 2: Dev — validate api_token directly against shared Redis ────────
    raw_cookie = request.cookies.get("access_token")
    if raw_cookie:
        token = raw_cookie.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    redis = await get_redis()
    user_id: Optional[str] = await redis.get(f"api_token:{token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired api_token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return uuid.UUID(user_id)


# Semantic alias used in router dependencies
require_auth = get_current_user_id