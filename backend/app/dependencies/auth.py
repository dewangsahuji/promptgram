import uuid
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.database import get_db
from redis_client import get_redis
from app.models.user import User
from app.config import settings

SECRET_KEY = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
#                                                             ↑ won't crash if no Bearer token

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),  # ← reads Bearer header (for /docs)
    redis=Depends(get_redis),
    db=Depends(get_db)
):
    # 1. Try cookie first, then fall back to Bearer header
    raw = request.cookies.get("access_token")
    if raw:
        token = raw.replace("Bearer ", "")

    if not token:
        raise HTTPException(401, "Not logged in")

    # 2. Check blacklist
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

    # 4. Load user
    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(401, "User not found")
    return user

require_auth = get_current_user