import uuid
import datetime
from typing import List, Optional
from pydantic import BaseModel


class PromptCreate(BaseModel):
    title: str
    prompt_text: str
    tags: Optional[List[str]] = None
    model_used: Optional[str] = None


class PromptOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    prompt_text: str
    tags: Optional[List[str]] = None
    model_used: Optional[str] = None
    score: Optional[float] = None
    views: int
    downloads: int
    created_at: datetime.datetime
    # Enriched fields (may be None if not yet joined)
    username: Optional[str] = None
    thumbnail_url: Optional[str] = None
    likes_count: Optional[int] = None

    model_config = {"from_attributes": True}


class PromptUpdate(BaseModel):
    title: Optional[str] = None
    prompt_text: Optional[str] = None
    tags: Optional[List[str]] = None
    model_used: Optional[str] = None
