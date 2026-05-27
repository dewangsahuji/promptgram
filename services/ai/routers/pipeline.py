import uuid

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from config import settings
from routers.embed import EmbedRequest, embed_image
from routers.classify import ClassifyRequest, classify_image
from routers.moderate import ModerateRequest, moderate_image

router = APIRouter(tags=["ai"])


class PipelineResult(BaseModel):
    image_id: str
    moderated: bool
    classified: bool
    embedded: bool
    nsfw: bool
    tags: list
    qdrant_id: str | None


@router.post("/pipeline/{image_id}", response_model=PipelineResult)
async def run_pipeline(image_id: uuid.UUID, request: Request) -> PipelineResult:
    """
    Full AI pipeline for a single image — called as BackgroundTask after upload:
      1. Fetch image info from prompt-service
      2. Moderate (NSFW check via NudeNet)
      3. Classify (auto-tag via MobileNetV3) — skipped if NSFW
      4. Embed (CLIP → Qdrant)
    """
    # 1. Fetch image metadata from prompt-service
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{settings.PROMPT_SERVICE_URL}/images/{image_id}")
            resp.raise_for_status()
            image_data = resp.json()
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Could not fetch image from prompt-service: {e}"
        )

    image_url = image_data.get("s3_url")
    prompt_id_str = image_data.get("prompt_id")
    if not image_url:
        raise HTTPException(status_code=422, detail="Image has no s3_url")

    result: dict = {
        "image_id": str(image_id),
        "moderated": False,
        "classified": False,
        "embedded": False,
        "nsfw": False,
        "tags": [],
        "qdrant_id": None,
    }

    # 2. Moderate
    try:
        mod = await moderate_image(
            ModerateRequest(image_url=image_url, image_id=image_id), request
        )
        result["moderated"] = True
        result["nsfw"] = mod.nsfw
    except Exception:
        pass

    # 3. Classify (skip NSFW images)
    if not result["nsfw"] and prompt_id_str:
        try:
            clf = await classify_image(
                ClassifyRequest(
                    image_url=image_url,
                    prompt_id=uuid.UUID(prompt_id_str),
                ),
                request,
            )
            result["classified"] = True
            result["tags"] = clf.tags
        except Exception:
            pass

    # 4. Embed (always — NSFW images are still searchable, just filtered at display)
    try:
        emb = await embed_image(
            EmbedRequest(image_url=image_url, image_id=image_id), request
        )
        result["embedded"] = True
        result["qdrant_id"] = emb.qdrant_id
    except Exception:
        pass

    return PipelineResult(**result)
