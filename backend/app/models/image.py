import uuid
import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Float ,Boolean
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column , relationship

from app.database import Base

class image(Base):
    __tablename__ = "images"

    id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    prompt_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("prompts.id" , ondelete="CASCADE"),
        nullable=False
    )

    s3_key : Mapped[str] = mapped_column(
        Text ,
        nullable=False
    )

    s3_url : Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    thumbnail_url : Mapped[Optional[str]] = mapped_column(
        Text ,
        nullable=True
    )
    # Vector DB reference (Qdrant)
    qdrant_id : Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )

    nsfw : Mapped[bool] = mapped_column(
        Boolean,
        default=0,
        server_default="0",
        nullable=False
    )

    created_at : Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    prompt: Mapped["prompt"] = relationship(back_populates="images")

if __name__ == "__main__":
    print("Model loaded successfully with no syntax errors!")
