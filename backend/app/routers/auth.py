from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.auth import UserSignup
from app.services.auth_service import create_user

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# @router.post("/signup")
# def signup(
#     user_data: UserSignup,
#     db: Session = Depends(get_db)
# ):
#     user = create_user(db, user_data)

#     return {
#         "message": "User created",
#         "user_id": str(user.id)
#     }



#  Adding login Route
from fastapi import HTTPException

from app.schemas.auth import UserLogin
from app.services.auth_service import authenticate_user
from app.core.jwt_handler import create_access_token


@router.post("/login")
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        db,
        user_data
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "user_id": str(user.id)
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }




from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.dependencies import get_db

from app.schemas.auth import UserSignup
from app.schemas.auth import UserLogin

from app.services.auth_service import (
    create_user,
    authenticate_user
)

from app.core.jwt_handler import create_access_token
from app.core.current_user import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# SIGNUP
@router.post("/signup")
def signup(
    user_data: UserSignup,
    db: Session = Depends(get_db)
):
    user = create_user(db, user_data)

    return {
        "message": "User created",
        "user_id": str(user.id)
    }


# LOGIN
@router.post("/login")
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        db,
        user_data
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "user_id": str(user.id)
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# CURRENT USER
@router.get("/me")
def get_me(
    current_user = Depends(get_current_user)
):
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email
    }