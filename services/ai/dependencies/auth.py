"""
services/ai/dependencies/auth.py

The AI service is an INTERNAL service — it is not exposed directly to users.
All its routes are called either:
  a) by the prompt-service BackgroundTask (unauthenticated internal call), or
  b) via Nginx (public routes that are intentionally open, per the README).

Per the README all AI routes are marked Auth: ❌, so no hard authentication
is enforced here. However, the pipeline endpoint (/ai/pipeline/{image_id})
is triggered internally by the prompt-service; for defence-in-depth we
provide an optional internal-token check that can be enabled via config.

If you later want to lock down the AI service, flip settings.AI_INTERNAL_SECRET
to a non-empty string and pass the same value as the X-Internal-Secret header
from all callers.
"""
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from config import settings  # exposes settings.AI_INTERNAL_SECRET (optional, may be "")


async def verify_internal_secret(
    x_internal_secret: Optional[str] = Header(default=None, alias="X-Internal-Secret"),
) -> None:
    """
    Optional internal-service authentication guard.

    If AI_INTERNAL_SECRET is set in config, the caller must supply the matching
    X-Internal-Secret header. If the secret is empty/unset, the check is skipped
    (convenient for local development).

    Usage in a router:
        @router.post("/pipeline/{image_id}", dependencies=[Depends(verify_internal_secret)])
    """
    secret = getattr(settings, "AI_INTERNAL_SECRET", "")
    if not secret:
        # Secret not configured — open access (local dev / trusted network).
        return

    if x_internal_secret != secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing internal service secret.",
        )


# Convenience alias — attach to any route you want to guard.
require_internal = Depends(verify_internal_secret)