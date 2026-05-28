import uuid

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import Response

from config import settings
from dependencies.auth import get_current_user
from models.user import User

router = APIRouter(tags=["images"])

_PROMPT_BASE = settings.PROMPT_SERVICE_URL


async def _forward_delete(
    path: str,
    request: Request,
    current_user: User,
) -> Response:
    """Forward an authenticated DELETE request to the prompt-service."""
    url = f"{_PROMPT_BASE}{path}"
    headers = {"Authorization": request.headers.get("authorization", "")}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.delete(url, headers=headers)
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


# ─── Authenticated Image Endpoints ───────────────────────────────────────────


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image (authenticated)",
)
async def upload_image(
    request: Request,
    prompt_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload an image — validates JWT here, then streams the multipart file
    to the prompt-service which handles S3 storage and AI pipeline trigger.
    """
    url = f"{_PROMPT_BASE}/images/upload"
    headers = {"Authorization": request.headers.get("authorization", "")}
    content = await file.read()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                url,
                headers=headers,
                params={"prompt_id": str(prompt_id)},
                files={"file": (file.filename, content, file.content_type)},
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


@router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an image (authenticated)",
)
async def delete_image(
    image_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Delete an image — validates JWT here, then proxies to prompt-service."""
    return await _forward_delete(f"/images/{image_id}", request, current_user)
