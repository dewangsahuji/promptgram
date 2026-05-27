# schemas/social.py
from pydantic import BaseModel, ConfigDict
import uuid
import datetime
from typing import Optional

class CommentCreate(BaseModel):
    body:str

class CommentOut(BaseModel):
    id : uuid.UUID
    user_id : uuid.UUID
    prompt_id : uuid.UUID
    body : str
    created_at : datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class LikeOut(BaseModel):
    liked:bool

class FollowOut(BaseModel):
    following : bool