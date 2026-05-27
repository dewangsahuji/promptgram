import uuid
import datetime
from typing import Optional, List
from pydantic import BaseModel


class LikeOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    prompt_id: uuid.UUID
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    body: str


class CommentOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    prompt_id: uuid.UUID
    body: Optional[str]
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class FollowOut(BaseModel):
    follower_id: uuid.UUID
    following_id: uuid.UUID
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class CollectionCreate(BaseModel):
    name: str
    is_public: bool = False


class CollectionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    is_public: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class AddToCollectionRequest(BaseModel):
    prompt_id: uuid.UUID
