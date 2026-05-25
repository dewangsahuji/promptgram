import uuid
import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column , relationship 

# Assuming this is your base import based on your snippet
from app.database import Base

class prompts(Base):
    __tablename__="prompts"

    id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id" , ondelete="CASCADE"),
        nullable=False
    ) 

    title : Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    prompt_text : Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    tags : Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text),
        nullable=True
    )

    model_used : Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True
    )

    score : Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    views : Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False
    )

    downloads : Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False
    )

    created_at : Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationship back to the User
    user: Mapped["user"] = relationship(back_populates="prompts")

    # NEW: Relationship to Images (One-to-Many)
    image: Mapped[List["image"]] = relationship(
        back_populates="prompt", 
        cascade="all, delete-orphan"
    )

if __name__ == "__main__":
    print("Model loaded successfully with no syntax errors!")