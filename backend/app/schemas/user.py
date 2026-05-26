# app/schemas/user.py

import uuid
import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    """Public-facing user profile — never exposes password_hash."""
    id: uuid.UUID
    username: str
    email: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """
    All fields are optional — client only sends what they want to change.
    PATCH /users/me
    """
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserPromptsOut(BaseModel):
    """Prompt shape returned from GET /users/{id}/prompts."""
    id: uuid.UUID
    title: str
    prompt_text: str
    tags: Optional[List[str]] = None
    model_used: Optional[str] = None
    views: int
    downloads: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}