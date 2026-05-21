from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import UserSignup
from app.core.security import hash_password


def create_user(
    db: Session,
    user_data: UserSignup
):
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(
            user_data.password
        )
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user