from typing import Optional, List
from pydantic import BaseModel
from fastapi import Form

class PromptCreate(BaseModel):
    title: str
    prompt_text: str
    tags: Optional[List[str]] = None
    model_used: Optional[str] = None
    
    @classmethod
    def as_form(
        cls,
        title: str = Form(..., description="Title of the prompt"),
        prompt_text: str = Form(..., description="The main text of the prompt"),
        tags: List[str] = Form(default=[], description="List of tags"),
        model_used: Optional[str] = Form(None, description="The AI model used")
    ):
        """Dependency to map form fields to this Pydantic model."""
        return cls(
            title=title, 
            prompt_text=prompt_text, 
            tags=tags, 
            model_used=model_used
        )