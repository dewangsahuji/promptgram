## app/models/user.py

from typing import List
import uuid
import datetime
from sqlalchemy import String, DateTime, Text ,Integer
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column ,relationship

# Assuming this is your base import based on your snippet
from app.database import Base

class User(Base):
    __tablename__="users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    username : Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    email : Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    password_hash : Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    avatar_url : Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    bio : Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    created_at : Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    prompts: Mapped[List["Prompt"]] = relationship(back_populates="user")



if __name__ == "__main__":
    print("Model loaded successfully with no syntax errors!")

