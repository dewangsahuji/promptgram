## router/prompts.py

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List , Optional
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.prompt import PromptCreate, PromptOut
from app.services import prompt_service

router = APIRouter(tags=["prompts"])

# ─── CREATE ───────────────────────────────────────────────
@router.post("/" ,
             response_model=PromptOut ,
             status_code=status.HTTP_201_CREATED)
async def create_prompt(
    body:PromptCreate,
    current_user :User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    return await prompt_service.create_prompt(db , current_user.id , body)

# ─── LIST ───────────────────────────────────────────────
@router.get("/",response_model=List[PromptOut])
async def list_prompts(
            page : int = 1,
            limit : int = 10,
            db : AsyncSession = Depends(get_db)
            ):
    
    return await prompt_service.get_prompts(db , page ,limit)

# ─── GET ONE ──────────────────────────────────────────────
@router.get("/{prompt_id}" , response_model=PromptOut)
async def get_prompt(
    prompt_id:uuid.UUID,
    db : AsyncSession = Depends(get_db)
):
    prompt = await prompt_service.get_prompt_by_id(db , prompt_id)

    if not prompt:
        raise HTTPException(status_code=404 , detail="Prompt Not Found")
    
    return prompt

# ─── DELETE ───────────────────────────────────────────────
@router.delete("/{prompt_id}" , status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id:uuid.UUID,
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):  
    prompt = await prompt_service.get_prompt_by_id(db, prompt_id)

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    if prompt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your prompt")  # 🔒 ownership check
    
    await prompt_service.delete_prompt(db, prompt)




