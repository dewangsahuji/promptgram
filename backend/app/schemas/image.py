# app/schemas/image.py

import uuid
import datetime
from typing import Optional, List
from pydantic import BaseModel


class ImageOut(BaseModel):
    id: uuid.UUID
    prompt_id: uuid.UUID
    s3_url: str
    thumbnail_url: Optional[str] = None
    nsfw: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class PromptInImageOut(BaseModel):
    id: uuid.UUID
    title: str
    prompt_text: str
    tags: Optional[List[str]] = None
    model_used: Optional[str] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ImageUploadOut(BaseModel):
    """Response returned after a successful upload — contains both the
    newly created prompt and its image."""
    prompt: PromptInImageOut
    image: ImageOut