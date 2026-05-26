# app/routers/collection.py

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.collection import CollectionCreate, CollectionOut
from app.services import collection_service

router = APIRouter(tags=["collections"])


# ─── CREATE ───────────────────────────────────────────────
@router.post("/", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
async def create_collection(
    body: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new collection (public or private)."""
    return await collection_service.create_collection(db, current_user.id, body)


# ─── GET ONE ──────────────────────────────────────────────
@router.get("/{collection_id}", response_model=CollectionOut)
async def get_collection(
    collection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a collection with all its prompts.
    Private collections are only visible to their owner.
    """
    collection = await collection_service.get_collection(db, collection_id)

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Private collections are owner-only
    if not collection.is_public and collection.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This collection is private")

    return collection


# ─── ADD PROMPT ───────────────────────────────────────────
@router.post(
    "/{collection_id}/prompts/{prompt_id}",
    status_code=status.HTTP_201_CREATED
)
async def add_prompt_to_collection(
    collection_id: uuid.UUID,
    prompt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a prompt to a collection. Only the collection owner can do this."""
    await collection_service.add_prompt(db, current_user.id, collection_id, prompt_id)
    return {"detail": "Prompt added to collection"}


# ─── REMOVE PROMPT ────────────────────────────────────────
@router.delete(
    "/{collection_id}/prompts/{prompt_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def remove_prompt_from_collection(
    collection_id: uuid.UUID,
    prompt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a prompt from a collection. Only the collection owner can do this."""
    await collection_service.remove_prompt(db, current_user.id, collection_id, prompt_id)