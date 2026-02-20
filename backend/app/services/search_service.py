from typing import Optional
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, NamedVector, SparseVector
import hashlib


class SearchService:
    """Wrapper around Qdrant hybrid search operations"""
    
    def __init__(self, qdrant_url: str):
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = "use_cases"

    async def ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            await self.client.get_collection(self.collection_name)
        except Exception:
            # Collection doesn't exist, create it
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": VectorParams(size=1536, distance=Distance.COSINE),
                    # Sparse vectors for BM25-style keyword matching
                    "sparse": {
                        "datatype": "uint32",
                        "index": {"on_disk": True},
                    },
                },
            )

    async def embed_and_upsert(
        self,
        point_id: str,
        dense_vector: list[float],
        sparse_vector: dict,
        payload: dict,
    ):
        """Upsert a point with dense + sparse vectors"""
        point = PointStruct(
            id=int(hashlib.md5(point_id.encode()).hexdigest(), 16) % (2**31),
            vector={
                "dense": dense_vector,
                "sparse": SparseVector(
                    indices=list(sparse_vector.keys()),
                    values=list(sparse_vector.values()),
                ),
            },
            payload=payload,
        )
        await self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

    async def hybrid_search(
        self,
        dense_vector: list[float],
        sparse_indices: list[int],
        sparse_values: list[float],
        limit: int = 10,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """Hybrid search using RRF fusion"""
        # This is a simplified implementation
        # In production, use qdrant_client's proper fusion logic or implement RRF manually
        try:
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=NamedVector(name="dense", vector=dense_vector),
                limit=limit,
                query_filter=filters,
            )
            return [hit.payload for hit in results]
        except Exception as e:
            print(f"Search error: {e}")
            return []

    async def delete_point(self, point_id: int):
        """Delete a point from Qdrant"""
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=[point_id],
        )
