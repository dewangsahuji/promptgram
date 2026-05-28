import boto3
import asyncio
from config import settings

# Build kwargs for boto3 client — supports both AWS S3 and MinIO (local dev)
_s3_kwargs = dict(
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)
if settings.S3_ENDPOINT_URL:
    # MinIO / S3-compatible endpoint (local dev)
    _s3_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

s3 = boto3.client("s3", **_s3_kwargs)

# Pre-signed URL expiry — 7 days (max for IAM role-based credentials is 12h,
# but for regular IAM user keys it can be up to 7 days)
PRESIGN_EXPIRY = 60 * 60 * 24 * 7  # 7 days in seconds


def _url_for_key(key: str) -> str:
    """
    Return a URL for an S3 object.

    - For MinIO (local dev): plain public URL via the endpoint.
    - For real AWS S3: pre-signed URL so private-bucket objects load in browsers.
    """
    if settings.S3_ENDPOINT_URL:
        # MinIO: http://localhost:9000/bucket/key  (publicly accessible in dev)
        return f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{key}"

    # Real AWS S3 — generate a pre-signed URL (works even with Block Public Access ON)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
        ExpiresIn=PRESIGN_EXPIRY,
    )


async def ensure_bucket_exists():
    """Create the S3/MinIO bucket if it doesn't already exist."""
    def _create():
        try:
            s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        except Exception:
            try:
                if settings.S3_ENDPOINT_URL:
                    s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)
                else:
                    s3.create_bucket(
                        Bucket=settings.S3_BUCKET_NAME,
                        CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION},
                    )
            except Exception:
                pass  # Bucket may already exist via race condition

    await asyncio.to_thread(_create)


async def upload_to_s3(data: bytes, key: str, content_type: str) -> str:
    """Upload bytes to S3/MinIO and return a viewable URL."""
    await asyncio.to_thread(
        s3.put_object,
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return _url_for_key(key)


async def get_presigned_url(key: str) -> str:
    """Generate a fresh pre-signed URL for an existing object (e.g. when refreshing)."""
    return await asyncio.to_thread(_url_for_key, key)


async def delete_from_s3(key: str):
    await asyncio.to_thread(
        s3.delete_object,
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
    )
