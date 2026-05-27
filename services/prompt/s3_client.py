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


def _public_url(key: str) -> str:
    """Build the public URL for an object."""
    if settings.S3_ENDPOINT_URL:
        # MinIO: http://localhost:9000/bucket/key
        return f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{key}"
    return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


async def ensure_bucket_exists():
    """Create the S3/MinIO bucket if it doesn't already exist."""
    def _create():
        try:
            s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        except Exception:
            try:
                if settings.S3_ENDPOINT_URL:
                    # MinIO doesn't need LocationConstraint for us-east-1 equivalent
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
    await asyncio.to_thread(
        s3.put_object,
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return _public_url(key)


async def delete_from_s3(key: str):
    await asyncio.to_thread(
        s3.delete_object,
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
    )
