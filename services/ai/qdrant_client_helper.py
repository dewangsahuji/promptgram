from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import settings

_client: AsyncQdrantClient | None = None


def get_qdrant() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    return _client


async def ensure_collection():
    """Create the Qdrant collection if it doesn't already exist."""
    client = get_qdrant()
    collections = await client.get_collections()
    names = [c.name for c in collections.collections]
    if settings.QDRANT_COLLECTION not in names:
        await client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=512, distance=Distance.COSINE),
        )


async def upsert_vector(qdrant_id: str, vector: list[float], payload: dict):
    client = get_qdrant()
    await client.upsert(
        collection_name=settings.QDRANT_COLLECTION,
        points=[PointStruct(id=qdrant_id, vector=vector, payload=payload)],
    )


async def search_vectors(query_vector: list[float], limit: int = 20) -> list:
    client = get_qdrant()
    results = await client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=limit,
    )
    return results


async def get_vector_by_id(qdrant_id: str) -> list[float] | None:
    client = get_qdrant()
    results = await client.retrieve(
        collection_name=settings.QDRANT_COLLECTION,
        ids=[qdrant_id],
        with_vectors=True,
    )
    if not results:
        return None
    return results[0].vector
