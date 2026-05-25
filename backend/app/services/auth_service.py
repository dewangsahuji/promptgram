## services/auth_service.py

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import jwt

from typing import Optional

from app.models.user import User
from app.schemas.auth import UserCreate
# Note: In a production environment, pull these from your config.py/environment variables
from app.config import settings






pwd_context = CryptContext(schemes=["bcrypt"] , deprecated="auto")




def get_password_hash(password:str):
    # Helper fxn for passwords
    return pwd_context.hash(password)

def verify_password(plain_password : str , hashed_password : str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def create_user(
        db:AsyncSession , 
        user_in:UserCreate
        ) -> User:
    """
    Hashes the password and saves the new user to the database.
    Handles unique constraint violations (duplicate email/username).
    """

    hashed_password = get_password_hash(user_in.password)

    new_user = User(
        username = user_in.username,
        email = user_in.email,
        password_hash = hashed_password
    )

    db.add(new_user)

    try :
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

async def authenticate_user(
        db:AsyncSession,
        username:str ,
        password:str
        )->Optional[User]:
    """
    Looks up a user by username and verifies their password against the stored hash.
    """
    # E1 = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
        
    return user

def generate_tokens(user:User)->dict:
    """
    Generates a JWT containing the user's UUID as the subject ('sub').
    """
    expire = datetime.utcnow()+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user.id),
        "exp": expire
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM

    )

    return {
        "access_token": encoded_jwt,
        "token_type": "bearer"
    }









