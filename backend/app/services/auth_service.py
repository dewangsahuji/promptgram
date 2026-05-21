from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import UserSignup
from app.core.security import hash_password

# Authentication and user management service
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import UserLogin
from app.core.security import verify_password


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

# Authentication and user management service

def authenticate_user(
    db: Session,
    user_data: UserLogin
):
    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if not user:
        return None

    valid = verify_password(
        user_data.password,
        user.password_hash
    )

    if not valid:
        return None

    return user