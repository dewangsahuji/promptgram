# app/models/image.py

import uuid
import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Image(Base):
    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False
    )

    s3_key: Mapped[str] = mapped_column(Text, nullable=False)
    s3_url: Mapped[str] = mapped_column(Text, nullable=False)

    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ✅ Fixed: was nullable=False — but Qdrant runs in Phase 2, so this
    #    column stays NULL until the AI pipeline fills it in.
    qdrant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )

    nsfw: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    prompt: Mapped["Prompt"] = relationship(back_populates="images")