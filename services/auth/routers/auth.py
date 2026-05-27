import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from dependencies.auth import get_current_user
from models.user import User
from redis_client import get_redis
from schemas.auth import TokenResponse, UserCreate, UserOut
from services.auth_service import authenticate_user, create_user, generate_tokens

router = APIRouter(tags=["auth"])

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def signup(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Create a new account and return an access token."""
    user = await create_user(db, user_in)
    tokens = generate_tokens(user)
    return TokenResponse(**tokens)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email + password",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """OAuth2 password flow — pass email in the 'username' field."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tokens = generate_tokens(user)
    return TokenResponse(**tokens)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user profile",
)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """Return the authenticated user's profile information."""
    return UserOut(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
    )


@router.post(
    "/logout",
    summary="Logout and invalidate token",
    status_code=status.HTTP_200_OK,
)
async def logout(
    token: str = Depends(_oauth2_scheme),
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
) -> dict:
    """Blacklist the current JWT in Redis so it cannot be used again (TTL: 24 h)."""
    await redis.setex(f"blacklist:{token}", 86400, "1")
    return {"message": "Successfully logged out."}


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
    """
    Publicly accessible endpoint for inter-service calls.
    The Social Service uses this to proxy user profile requests.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut(id=str(user.id), username=user.username, email=user.email)
