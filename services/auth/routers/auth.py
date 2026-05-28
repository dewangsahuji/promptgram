"""
services/auth/routers/auth.py

Token lifecycle:

  POST /auth/login        — credentials → short-lived JWT (access_token, 5 min)
  POST /auth/authorize    — access_token → long-lived opaque api_token (60 min, Redis)
  POST /auth/api-token    — credentials → api_token directly  ← Swagger UI uses this
  GET  /auth/validate     — internal; called by Nginx auth_request
  GET  /auth/me           — api_token → current user profile
  POST /auth/logout       — api_token → deleted from Redis
  GET  /auth/users/{id}   — public; inter-service user lookup
"""
import secrets
import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from config import settings
from database import get_db
from dependencies.auth import get_current_user, get_user_by_api_token
from models.user import User
from redis_client import get_redis
from schemas.auth import ApiTokenResponse, TokenResponse, UserCreate, UserOut
from services.auth_service import authenticate_user, create_user, generate_tokens

router = APIRouter(tags=["auth"])


# ── 1. Signup ─────────────────────────────────────────────────────────────────
@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and receive an access_token",
)
async def signup(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> TokenResponse:
    """Create a new account. Returns a short-lived access_token."""
    user = await create_user(db, user_in)
    tokens = generate_tokens(user)
    return TokenResponse(**tokens)


# ── 2. Login (Step 1 of two-token flow) ──────────────────────────────────────
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Step 1 — Authenticate and receive a short-lived access_token (5 min)",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    OAuth2 password flow — pass email in the 'username' field.
    Returns a short-lived JWT (5 min). Exchange it for an api_token via /auth/authorize.
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tokens = generate_tokens(user)
    return TokenResponse(**tokens)


# ── 3. Authorize (Step 2 of two-token flow) ───────────────────────────────────
@router.post(
    "/authorize",
    response_model=ApiTokenResponse,
    summary="Step 2 — Exchange access_token for a long-lived api_token (60 min)",
)
async def authorize(
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
) -> ApiTokenResponse:
    """
    Present a valid access_token (JWT) to receive an opaque api_token stored in Redis.
    Use the api_token for all subsequent API calls through the gateway.
    """
    api_token = secrets.token_urlsafe(32)
    ttl = settings.API_TOKEN_EXPIRE_SECONDS
    await redis.setex(f"api_token:{api_token}", ttl, str(current_user.id))
    return ApiTokenResponse(api_token=api_token, token_type="bearer", expires_in=ttl)


# ── 4. API Token — combined login + authorize (Swagger-friendly) ──────────────
@router.post(
    "/api-token",
    response_model=TokenResponse,
    summary="Login and get an api_token in one step (used by Swagger UI)",
)
async def api_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> TokenResponse:
    """
    Convenience endpoint for Swagger UI and dev clients.
    Accepts credentials and returns an api_token directly (skips the two-step exchange).
    The token is returned in the `access_token` field so Swagger UI uses it as Bearer.
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = secrets.token_urlsafe(32)
    await redis.setex(f"api_token:{token}", settings.API_TOKEN_EXPIRE_SECONDS, str(user.id))
    # Return in `access_token` field so OAuth2PasswordBearer picks it up in Swagger
    return TokenResponse(access_token=token, token_type="bearer")


# ── 5. Validate — internal Nginx auth_request endpoint ───────────────────────
@router.get(
    "/validate",
    summary="Internal — called by Nginx auth_request to validate api_token",
    include_in_schema=False,  # hide from public docs
)
async def validate(
    request: Request,
    redis: aioredis.Redis = Depends(get_redis),
) -> Response:
    """
    Nginx sends every protected API request here first.
    Returns 200 + X-User-Id header on success, 401 on failure.
    The gateway injects X-User-Id into the upstream request.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token.")

    token = auth_header.removeprefix("Bearer ").strip()
    user_id: str | None = await redis.get(f"api_token:{token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired api_token.",
        )

    return Response(
        status_code=200,
        headers={"X-User-Id": user_id},
    )


# ── 6. Me ─────────────────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user profile (requires api_token)",
)
async def me(
    current_user: User = Depends(get_user_by_api_token),
) -> UserOut:
    """Return the authenticated user's profile."""
    return UserOut(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
    )


# ── 7. Logout ─────────────────────────────────────────────────────────────────
@router.post(
    "/logout",
    summary="Logout — immediately revoke the api_token",
    status_code=status.HTTP_200_OK,
)
async def logout(
    request: Request,
    redis: aioredis.Redis = Depends(get_redis),
) -> dict:
    """Delete the api_token from Redis, making it instantly invalid across all services."""
    auth_header = request.headers.get("Authorization", "")
    raw_cookie = request.cookies.get("access_token")

    token = None
    if raw_cookie:
        token = raw_cookie.removeprefix("Bearer ").strip()
    elif auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided.")

    deleted = await redis.delete(f"api_token:{token}")
    if not deleted:
        # Fallback: treat as JWT and blacklist it
        await redis.setex(f"blacklist:{token}", 86400, "1")

    return {"message": "Successfully logged out."}


# ── 8. Get user by ID — inter-service call ────────────────────────────────────
@router.get(
    "/users/{user_id}",
    response_model=UserOut,
    summary="Get public user profile by ID (internal use)",
    tags=["users"],
)
async def get_user_by_id(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Publicly accessible — used by social-service to proxy user profile requests."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserOut(id=str(user.id), username=user.username, email=user.email)
