## router/auth.py

from fastapi import APIRouter, Depends, HTTPException, status , Response , Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis # Import Redis type hint


from app.database import get_db
from redis_client import get_redis # Import the dependency
from app.schemas.auth import UserCreate, TokenResponse
from app.services import auth_service
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(tags=["auth"])
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm ,OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis # Import Redis type hint

from app.database import get_db
from redis_client import get_redis # Import the dependency
from app.schemas.auth import UserCreate, TokenResponse
from app.services import auth_service
from app.dependencies.auth import get_current_user
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserCreate, db: AsyncSession = Depends(get_db)):
    # Calls the service to hash the password and save the user
    user = await auth_service.create_user(db, body)
    
    # Immediately log them in by returning a token
    return auth_service.generate_tokens(user)

@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Validates credentials against the DB
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    tokens = auth_service.generate_tokens(user)

        # ✅ Set token in cookie automatically
    response.set_cookie(
        key="access_token",
        value=f"Bearer {tokens['access_token']}",
        httponly=True,      # JS can't read it (XSS protection)
        secure=False,       # Set True in production (HTTPS only)
        samesite="lax"
    )
    return tokens



@router.get("/me", tags=["users"])
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Test endpoint to verify the JWT token works. 
    Returns the currently logged-in user's details.
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }

@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    token = request.cookies.get("access_token")
    
    if token:
        clean_token = token.replace("Bearer ", "")
        await redis.setex(f"blacklist:{clean_token}", 3600, "1")
    
    # ✅ options must match exactly how it was set
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax"
    )
    
    return {"detail": "Successfully logged out"}