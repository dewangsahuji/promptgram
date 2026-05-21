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