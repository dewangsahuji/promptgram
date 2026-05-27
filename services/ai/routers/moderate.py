import asyncio
import tempfile
import uuid
from pathlib import Path
from typing import List

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from config import settings
from model_manager import get_nudenet

router = APIRouter(tags=["ai"])

# NudeNet class labels considered NSFW
NSFW_CLASSES = {
    "EXPOSED_ANUS",
    "EXPOSED_BUTTOCKS",
    "EXPOSED_BREAST_F",
    "EXPOSED_GENITALIA_F",
    "EXPOSED_GENITALIA_M",
}


class ModerateRequest(BaseModel):
    image_url: str
    image_id: uuid.UUID


class Detection(BaseModel):
    label: str
    confidence: float


class ModerateResponse(BaseModel):
    nsfw: bool
    confidence: float
    detections: List[Detection]


@router.post("/moderate", response_model=ModerateResponse)
async def moderate_image(body: ModerateRequest, request: Request) -> ModerateResponse:
    """Run NudeNet NSFW detection. Flags the image in prompt-service if NSFW."""
    nude_classifier = get_nudenet(request.app)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(body.image_url)
            resp.raise_for_status()
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Could not fetch image: {e}")

    img_bytes = resp.content

    def _moderate() -> dict:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name
        try:
            result = nude_classifier.classify(tmp_path)
            # result = {path: {label: confidence, ...}}
            return list(result.values())[0] if result else {}
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    detections_dict = await asyncio.to_thread(_moderate)

    nsfw = any(
        conf > 0.5
        for cls, conf in detections_dict.items()
        if cls in NSFW_CLASSES
    )
    max_nsfw_conf = max(
        (conf for cls, conf in detections_dict.items() if cls in NSFW_CLASSES),
        default=0.0,
    )
    detections = [Detection(label=k, confidence=v) for k, v in detections_dict.items()]

    if nsfw:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.patch(
                    f"{settings.PROMPT_SERVICE_URL}/images/{body.image_id}/nsfw",
                    json={"nsfw": True},
                )
        except Exception:
            pass

    return ModerateResponse(
        nsfw=nsfw,
        confidence=round(max_nsfw_conf, 4),
        detections=detections,
    )
