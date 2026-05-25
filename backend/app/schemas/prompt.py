# schemas/prompt.py

# Imports
from pydantic import BaseModel , ConfigDict
from pydantic import EmailStr
from typing import List , Optional
import uuid
import datetime

class PromptCreate(BaseModel):
    title : str
    prompt_text : str
    tags : Optional[List[str]]
    model_used : Optional[str]
    
    model_config = ConfigDict(from_attributes=True)  # ← add this


class PromptOut(BaseModel):
    id : uuid.UUID
    user_id: uuid.UUID
    title: str
    tags : Optional[List[str]]
    model_used : Optional[str]
    score : Optional[float]
    views : int
    downloads : int
    created_at : datetime.datetime