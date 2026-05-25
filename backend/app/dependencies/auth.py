# dependencies/auth.py
import uuid
from fastapi import Depends, HTTPException, Request
from jose import jwt, JWTError

from fastapi import Request

from app.database import get_db
from redis_client import get_redis
from app.models.user import User
from app.config import settings

SECRET_KEY = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM

async def get_current_user(
    request: Request,          # ✅ Request object to read cookies
    redis=Depends(get_redis),
    db=Depends(get_db)
):
    # 1. Read token from cookie
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "Not logged in")
    
    token = token.replace("Bearer ", "")  # strip prefix

    # 2. Check if token was revoked
    if await redis.get(f"blacklist:{token}"):
        raise HTTPException(401, "Token revoked")
    
    # 3. Decode JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
    except JWTError:
        raise HTTPException(401, "Could not validate token")

    # 4. Load user from DB
    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(401, "User not found")
    return user

require_auth = get_current_user