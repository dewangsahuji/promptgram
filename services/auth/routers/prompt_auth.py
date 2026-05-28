# routers/prompt_auth.py


import json
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status, File, Form, UploadFile
from fastapi.responses import Response

from config import settings
from dependencies.auth import get_current_user
from models.user import User

from schemas.prompt import PromptCreate


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
    summary="Create a new prompt with an optional image (authenticated)",
)
async def create_prompt(
    request: Request,
    prompt_in: PromptCreate = Depends(PromptCreate.as_form), # <-- Injected Schema here
    image: UploadFile = File(None, description="Optional image to upload"),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a prompt and optionally uploads an image. 
    Accepts strongly typed form fields and validates them via Pydantic.
    """
    # 1. Convert the validated Pydantic model to a dictionary
    body = prompt_in.model_dump()
    
    # Optional but recommended: Inject the user_id into the body for the downstream service
    body["user_id"] = str(current_user.id)

    headers = {"Authorization": request.headers.get("authorization", "")}
    
    # 2. Forward request to create the prompt
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            prompt_resp = await client.post(
                f"{_PROMPT_BASE}/prompts/",
                headers=headers,
                json=body, # httpx will automatically serialize this dict to JSON
            )
            prompt_resp.raise_for_status()
            
            response_data = prompt_resp.json()
            prompt_id = response_data.get("id") 
            
    except httpx.HTTPStatusError as exc:
        return Response(
            content=exc.response.content,
            status_code=exc.response.status_code,
            media_type=exc.response.headers.get("content-type", "application/json")
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Prompt service unavailable: {exc}",
        )

    # 3. If an image is provided, forward it to the upload endpoint
    if image and prompt_id:
        content = await image.read()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                await client.post(
                    f"{_PROMPT_BASE}/images/upload",
                    headers=headers,
                    params={"prompt_id": str(prompt_id)},
                    files={"file": (image.filename, content, image.content_type)},
                )
        except httpx.RequestError as exc:
            # Note: At this point, the prompt exists but the image upload failed.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Prompt created, but image upload service is unavailable: {exc}",
            )

    return Response(
        content=prompt_resp.content,
        status_code=prompt_resp.status_code,
        media_type=prompt_resp.headers.get("content-type", "application/json"),
    )

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
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing JSON body."
        )
        
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
