import asyncio
import uuid
from typing import List

import torch
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from model_manager import get_clip
from qdrant_client_helper import get_vector_by_id, search_vectors

router = APIRouter(tags=["ai"])


class TextSearchRequest(BaseModel):
    query: str
    limit: int = 20


class SimilarImagesRequest(BaseModel):
    image_id: uuid.UUID
    limit: int = 10


class SearchResult(BaseModel):
    image_id: str
    score: float


@router.post("/search", response_model=List[SearchResult])
async def semantic_search(body: TextSearchRequest, request: Request) -> List[SearchResult]:
    """Encode a text query with CLIP and return the most visually similar images."""
    clip_model, _, clip_tokenizer = get_clip(request.app)

    def _encode_text() -> list[float]:
        tokens = clip_tokenizer([body.query])
        with torch.no_grad():
            embedding = clip_model.encode_text(tokens)
        return embedding.squeeze().tolist()

    vector = await asyncio.to_thread(_encode_text)
    results = await search_vectors(vector, limit=body.limit)

    return [
        SearchResult(image_id=r.payload.get("image_id", ""), score=r.score)
        for r in results
    ]


@router.post("/similar-images", response_model=List[SearchResult])
async def similar_images(body: SimilarImagesRequest, request: Request) -> List[SearchResult]:
    """Find images visually similar to a given image using Qdrant cosine similarity."""
    qdrant_id = str(body.image_id)
    vector = await get_vector_by_id(qdrant_id)
    if vector is None:
        raise HTTPException(status_code=404, detail="Image not embedded yet — run /ai/embed first")

    results = await search_vectors(vector, limit=body.limit + 1)
    return [
        SearchResult(image_id=r.payload.get("image_id", ""), score=r.score)
        for r in results
        if r.payload.get("image_id") != str(body.image_id)
    ][:body.limit]
