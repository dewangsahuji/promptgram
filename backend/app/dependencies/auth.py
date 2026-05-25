# dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis

from app.database import get_db
from redis_client import get_redis
from app.models.user import User
from app.config import settings



SECRET_KEY = settings.JWT_SECRET  # store in .env, never hardcode
ALGORITHM = settings.JWT_ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    redis=Depends(get_redis),
    db=Depends(get_db)
):
    # 1. Check if token was revoked (logout blacklist in Redis)
    if await redis.get(f"blacklist:{token}"):
        raise HTTPException(401, "Token revoked")
    try:
        # 2. Decode and validate the JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
    except JWTError:
        raise HTTPException(401, "Could not validate token")

    # 3. Load user from DB
    user = await db.get(User, uuid.UUID(user_id)) 
    if not user:
        raise HTTPException(401, "User not found")
    return user

# Alias used across all protected routes
require_auth = get_current_user