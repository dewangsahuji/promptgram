import asyncio
import io
import uuid

import httpx
import torch
from fastapi import APIRouter, HTTPException, Request
from PIL import Image
from pydantic import BaseModel

from config import settings
from model_manager import get_clip
from qdrant_client_helper import upsert_vector

router = APIRouter(tags=["ai"])


class EmbedRequest(BaseModel):
    image_url: str
    image_id: uuid.UUID


class EmbedResponse(BaseModel):
    qdrant_id: str
    vector_dim: int


async def _fetch_bytes(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


@router.post("/embed", response_model=EmbedResponse)
async def embed_image(body: EmbedRequest, request: Request) -> EmbedResponse:
    """Download an image, generate a 512D CLIP embedding, and store it in Qdrant."""
    clip_model, clip_preprocess, _ = get_clip(request.app)

    try:
        img_bytes = await _fetch_bytes(body.image_url)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not fetch image: {e}")

    def _encode() -> list[float]:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        tensor = clip_preprocess(img).unsqueeze(0)
        with torch.no_grad():
            embedding = clip_model.encode_image(tensor)
        return embedding.squeeze().tolist()

    vector = await asyncio.to_thread(_encode)
    qdrant_id = str(body.image_id)

    await upsert_vector(
        qdrant_id=qdrant_id,
        vector=vector,
        payload={"image_id": str(body.image_id)},
    )

    # Notify prompt-service to save qdrant_id (non-fatal if it fails)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.patch(
                f"{settings.PROMPT_SERVICE_URL}/images/{body.image_id}/qdrant",
                json={"qdrant_id": qdrant_id},
            )
    except Exception:
        pass

    return EmbedResponse(qdrant_id=qdrant_id, vector_dim=len(vector))
