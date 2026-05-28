import uuid
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response

from config import settings
from dependencies.auth import get_current_user
from models.user import User

router = APIRouter(tags=["social"])

_SOCIAL_BASE = settings.SOCIAL_SERVICE_URL


async def _forward(
    method: str,
    path: str,
    request: Request,
    current_user: User,
    *,
    json: Any = None,
) -> Response:
    """Forward an authenticated request to the social-service."""
    url = f"{_SOCIAL_BASE}{path}"
    headers = {"Authorization": request.headers.get("authorization", "")}
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
            detail=f"Social service unavailable: {exc}",
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )


# ─── Likes ───────────────────────────────────────────────────────────────────


@router.post(
    "/like/{prompt_id}",
    summary="Toggle like on a prompt (authenticated)",
)
async def toggle_like(
    prompt_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Toggle like — validates JWT here, then proxies to social-service."""
    return await _forward("POST", f"/like/{prompt_id}", request, current_user)


# ─── Comments ─────────────────────────────────────────────────────────────────


@router.post(
    "/comment/{prompt_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a prompt (authenticated)",
)
async def add_comment(
    prompt_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Add a comment — validates JWT here, then proxies to social-service."""
    body = await request.json()
    return await _forward("POST", f"/comment/{prompt_id}", request, current_user, json=body)


@router.delete(
    "/comment/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment (authenticated)",
)
async def delete_comment(
    comment_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Delete a comment — validates JWT here, then proxies to social-service."""
    return await _forward("DELETE", f"/comment/{comment_id}", request, current_user)


# ─── Follows ──────────────────────────────────────────────────────────────────


@router.post(
    "/follow/{user_id}",
    summary="Toggle follow on a user (authenticated)",
)
async def toggle_follow(
    user_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Toggle follow — validates JWT here, then proxies to social-service."""
    return await _forward("POST", f"/follow/{user_id}", request, current_user)


# ─── Collections ──────────────────────────────────────────────────────────────


@router.post(
    "/collections/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a collection (authenticated)",
)
async def create_collection(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Create a collection — validates JWT here, then proxies to social-service."""
    body = await request.json()
    return await _forward("POST", "/collections/", request, current_user, json=body)


@router.get(
    "/collections/my",
    summary="Get my collections (authenticated)",
)
async def my_collections(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get own collections — validates JWT here, then proxies to social-service."""
    return await _forward("GET", "/collections/my", request, current_user)


@router.post(
    "/collections/{collection_id}/prompts",
    summary="Add a prompt to a collection (authenticated)",
)
async def add_prompt_to_collection(
    collection_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Add to collection — validates JWT here, then proxies to social-service."""
    body = await request.json()
    return await _forward(
        "POST", f"/collections/{collection_id}/prompts", request, current_user, json=body
    )
