import asyncio
import io
import uuid
from typing import List

import httpx
import torch
from fastapi import APIRouter, HTTPException, Request
from PIL import Image, ImageFilter, ImageStat
from pydantic import BaseModel

from config import settings
from model_manager import get_mobilenet

router = APIRouter(tags=["ai"])

# Map ImageNet label keywords → prompt categories
CATEGORY_MAP = {
    "cat": "animals", "dog": "animals", "bird": "animals", "fish": "animals",
    "lion": "animals", "tiger": "animals", "wolf": "animals",
    "car": "vehicles", "truck": "vehicles", "airplane": "vehicles", "boat": "vehicles",
    "castle": "architecture", "church": "architecture", "building": "architecture",
    "mountain": "landscape", "beach": "landscape", "forest": "landscape", "valley": "landscape",
    "sunset": "landscape", "ocean": "landscape", "waterfall": "landscape",
    "portrait": "portrait", "face": "portrait",
    "galaxy": "space", "nebula": "space", "planet": "space", "star": "space",
    "painting": "art", "mural": "art", "sculpture": "art",
    "robot": "sci-fi", "spacecraft": "sci-fi", "drone": "sci-fi", "circuit": "sci-fi",
    "sword": "fantasy", "dragon": "fantasy", "wizard": "fantasy", "castle": "fantasy",
    "anime": "anime", "manga": "anime",
}


class ClassifyRequest(BaseModel):
    image_url: str
    prompt_id: uuid.UUID


class ClassifyResponse(BaseModel):
    tags: List[str]
    quality_score: float
    top_labels: List[str]


def _compute_quality_score(img: Image.Image) -> float:
    """Heuristic quality: sharpness (Laplacian variance) + contrast (std dev), normalized 0–1."""
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    sharpness = min(ImageStat.Stat(edges).var[0] / 5000.0, 1.0)
    contrast = min(ImageStat.Stat(gray).stddev[0] / 128.0, 1.0)
    return round(sharpness * 0.6 + contrast * 0.4, 4)


@router.post("/classify", response_model=ClassifyResponse)
async def classify_image(body: ClassifyRequest, request: Request) -> ClassifyResponse:
    """Run MobileNetV3 on an image to auto-tag the prompt and compute quality score."""
    mobilenet, preprocess, labels = get_mobilenet(request.app)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(body.image_url)
            resp.raise_for_status()
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Could not fetch image: {e}")

    img_bytes = resp.content

    def _classify():
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        quality = _compute_quality_score(img)
        tensor = preprocess(img).unsqueeze(0)
        with torch.no_grad():
            logits = mobilenet(tensor)
        probs = torch.softmax(logits, dim=1)[0]
        top5_idx = probs.topk(5).indices.tolist()
        top5_labels = [labels[i] for i in top5_idx]
        return top5_labels, quality

    top5_labels, quality = await asyncio.to_thread(_classify)

    # Map to prompt categories, deduplicated
    tags = list({
        CATEGORY_MAP[k]
        for label in top5_labels
        for k in CATEGORY_MAP
        if k in label.lower()
    })
    if not tags:
        tags = ["ai-art"]  # sensible default

    # Push tags + score to prompt-service (non-fatal)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.patch(
                f"{settings.PROMPT_SERVICE_URL}/prompts/{body.prompt_id}/tags",
                json={"tags": tags},
            )
            await client.patch(
                f"{settings.PROMPT_SERVICE_URL}/prompts/{body.prompt_id}/score",
                json={"score": quality},
            )
    except Exception:
        pass

    return ClassifyResponse(tags=tags, quality_score=quality, top_labels=top5_labels)
