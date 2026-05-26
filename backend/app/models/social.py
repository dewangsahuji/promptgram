# app/models/social


from sqlalchemy import Column, Integer, String, ForeignKey , DateTime ,UniqueConstraint ,Text , Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped, mapped_column , relationship 
from typing import List , Optional
from sqlalchemy.sql import func
import uuid
import datetime
from app.database import Base

class Like(Base):
    __tablename__="likes"

    id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True
    )

    user_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id" , ondelete="CASCADE"),
        nullable=False
    )

    prompt_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("prompts.id" , ondelete="CASCADE"),
        nullable=False
    )

    created_at : Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Only one like from user
    __table_args__=(
        UniqueConstraint("user_id" , "prompt_id", name="uix_user_prompt_like"),
    )

    # Relationships
    # user : Mapped["users"] = relationship(back_populates="likes")
    # prompt : Mapped["prompts"] = relationship(back_populates="likes")

class Comment(Base):
    __tablename__="comments"

    id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id" , ondelete="CASCADE"),
        nullable=False
    )

    prompt_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("prompts.id" , ondelete="CASCADE"),
        nullable=False
    )

    body : Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    created_at : Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now()
    )

class Follow(Base):
    __tablename__="follows"

    follower_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id" , ondelete="CASCADE"),
        primary_key=True
    )

    following_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id" , ondelete="CASCADE"),
        primary_key=True
    )    

    created_at : Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now()
    )


class Collection(Base):
    __tablename__="collections"

    id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id" , ondelete="CASCADE"),
        nullable=False
    )

    name : Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    is_public : Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false"
    )

    created_at : Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now()
    )

    # Relationships
    prompts: Mapped[List["CollectionPrompt"]] = relationship(back_populates="collection", cascade="all, delete-orphan")


class CollectionPrompt(Base):
    __tablename__ = 'collection_prompts'

    collection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('collections.id', ondelete="CASCADE"), 
        primary_key=True
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('prompts.id', ondelete="CASCADE"), 
        primary_key=True
    )
    added_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    # ✅ Relationships needed for serialization
    collection: Mapped["Collection"] = relationship(back_populates="prompts")
    prompt: Mapped["Prompt"] = relationship()

if __name__ == "__main__":
    print("Model loaded successfully with no syntax errors!")