import uuid
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response

from config import settings
from dependencies.auth import get_current_user
from models.user import User

router = APIRouter(tags=["prompts"])

_PROMPT_BASE = settings.PROMPT_SERVICE_URL


async def _forward(
    method: str,
    path: str,
    request: Request,
    current_user: User,
    *,
    json: Any = None,
) -> Response:
    """Forward an authenticated request to the prompt-service."""
    url = f"{_PROMPT_BASE}{path}"
    headers = {"Authorization": request.headers.get("authorization", "")}

    # Carry through any query parameters (e.g. ?user_id=...)
    params = dict(request.query_params)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Prompt service unavailable: {exc}",
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )


# ─── Authenticated Prompt Endpoints ──────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new prompt (authenticated)",
)
async def create_prompt(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Create a prompt — validates JWT here, then proxies to prompt-service."""
    body = await request.json()
    return await _forward("POST", "/prompts/", request, current_user, json=body)


@router.patch(
    "/{prompt_id}",
    summary="Update a prompt (authenticated)",
)
async def update_prompt(
    prompt_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Update a prompt — validates JWT here, then proxies to prompt-service."""
    body = await request.json()
    return await _forward("PATCH", f"/prompts/{prompt_id}", request, current_user, json=body)


@router.delete(
    "/{prompt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a prompt (authenticated)",
)
async def delete_prompt(
    prompt_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Delete a prompt — validates JWT here, then proxies to prompt-service."""
    return await _forward("DELETE", f"/prompts/{prompt_id}", request, current_user)
