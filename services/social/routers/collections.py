from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas.social import CollectionCreate, CollectionOut, AddToCollectionRequest
from services import social_service
from dependencies.auth import require_auth

router = APIRouter(tags=["collections"])


@router.post("/", response_model=CollectionOut, status_code=201)
async def create_collection(
    body: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_auth),
):
    return await social_service.create_collection(db, user_id, body)


@router.get("/my", response_model=List[CollectionOut])
async def my_collections(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_auth),
):
    return await social_service.get_user_collections(db, user_id)


@router.get("/user/{user_id}", response_model=List[CollectionOut])
async def user_collections(user_id: UUID, db: AsyncSession = Depends(get_db)):
    return await social_service.get_user_collections(db, user_id)


@router.post("/{collection_id}/prompts")
async def add_prompt_to_collection(
    collection_id: UUID,
    body: AddToCollectionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_auth),
):
    return await social_service.add_to_collection(db, collection_id, body.prompt_id, user_id)
