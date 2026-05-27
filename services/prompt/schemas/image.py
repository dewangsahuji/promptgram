import uuid
import datetime
from typing import Optional
from pydantic import BaseModel


class ImageOut(BaseModel):
    id: uuid.UUID
    prompt_id: uuid.UUID
    s3_url: str
    thumbnail_url: Optional[str] = None
    nsfw: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
