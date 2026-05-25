## router/prompts.py

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

router = APIRouter(tags=["prompts"])
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

@router.post("/prompts")










