from uuid import UUID
from fastapi import APIRouter, HTTPException
import httpx
from config import settings

router = APIRouter(tags=["users"])


@router.get("/{user_id}")
async def get_user_profile(user_id: UUID):
    """Proxy to Auth Service for user profile."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.AUTH_SERVICE_URL}/auth/users/{user_id}", timeout=5.0
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            raise HTTPException(status_code=503, detail="Auth service unavailable")


@router.get("/{user_id}/prompts")
async def get_user_prompts(user_id: UUID):
    """Proxy to Prompt Service for user prompts."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.PROMPT_SERVICE_URL}/prompts/?user_id={user_id}", timeout=5.0
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            raise HTTPException(status_code=503, detail="Prompt service unavailable")
