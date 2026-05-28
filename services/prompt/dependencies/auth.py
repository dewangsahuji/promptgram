"""
services/prompt/dependencies/auth.py

The prompt-service does not validate JWTs itself.
It delegates to the auth-service via HTTP and gets back a user UUID.
This keeps the JWT_SECRET out of this service's config entirely.
"""
import uuid
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from config import settings  # exposes settings.AUTH_SERVICE_URL

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.DOCS_AUTH_SERVICE_URL}/auth/login",
    auto_error=False,
)

# Shared client — one TCP connection pool for the lifetime of the process.
# Register close_http_client() in your app's shutdown lifespan handler.
_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=5.0)
    return _http_client


async def close_http_client() -> None:
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()


async def get_current_user_id(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> uuid.UUID:
    """
    Validate a Bearer/cookie token by calling auth-service /auth/me.
    Returns the validated user UUID on success.
    """
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

    # 2. Delegate validation to the auth-service.
    client = get_http_client()
    try:
        response = await client.get(
            f"{settings.AUTH_SERVICE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Auth service timed out.",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable.",
        )

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unexpected response from auth service: {response.status_code}",
        )

    # 3. Parse and validate the returned user UUID.
    try:
        user_data = response.json()
        return uuid.UUID(user_data["id"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Auth service returned an invalid user payload: {exc}",
        )


# Semantic alias used in router dependencies.
require_auth = get_current_user_id