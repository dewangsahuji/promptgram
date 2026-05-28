import uuid
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
import httpx

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://auth-service:8001/auth/login", auto_error=False)


async def get_current_user_id(request: Request, token: str = Depends(oauth2_scheme)) -> uuid.UUID:
    """Validate token via auth-service and return the user_id UUID."""
    # 1. Try cookie first, then fall back to Bearer header
    raw_cookie = request.cookies.get("access_token")
    if raw_cookie:
        token = raw_cookie.replace("Bearer ", "")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://auth-service:8001/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if response.status_code == 200:
                user_data = response.json()
                return uuid.UUID(user_data["id"])
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid or revoked token")
            else:
                raise HTTPException(status_code=401, detail="Could not validate token")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Auth service unavailable")


require_auth = get_current_user_id
