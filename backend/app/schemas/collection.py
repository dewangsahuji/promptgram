# app/schemas/collection.py

import uuid
import datetime
from typing import Optional, List
from pydantic import BaseModel


class CollectionCreate(BaseModel):
    name: str
    is_public: bool = False


class PromptInCollection(BaseModel):
    """Lightweight prompt shape shown inside a collection."""
    id: uuid.UUID
    title: str
    prompt_text: str
    model_used: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class CollectionPromptOut(BaseModel):
    prompt: PromptInCollection
    added_at: datetime.datetime

    model_config = {"from_attributes": True}


class CollectionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    is_public: bool
    created_at: datetime.datetime
    prompts: List[CollectionPromptOut] = []

    model_config = {"from_attributes": True}