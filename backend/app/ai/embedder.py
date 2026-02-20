from typing import Optional
import hashlib
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


class QdrantEmbedder:
    """Handles Qdrant collection setup and vector operations"""
    
    def __init__(self, url: str):
        self.client = QdrantClient(url=url)
        self.collection_name = "use_cases"

    def ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            # Collection doesn't exist, create it
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # text-embedding-3-small
                    distance=Distance.COSINE,
                ),
            )

    def upsert_use_case(
        self,
        point_id: str,
        vector: list[float],
        use_case_id: str,
        title: str,
        company_id: str,
        industry_id: Optional[str] = None,
        status: str = "new",
        tags: Optional[list[str]] = None,
        confidence_score: float = 1.0,
    ):
        """Upsert a use case vector with metadata"""
        # Create numeric point ID from string
        numeric_id = int(hashlib.md5(point_id.encode()).hexdigest(), 16) % (2**31)
        
        point = {
            "id": numeric_id,
            "vector": vector,
            "payload": {
                "use_case_id": use_case_id,
                "title": title,
                "company_id": company_id,
                "industry_id": industry_id,
                "status": status,
                "tags": tags or [],
                "confidence_score": confidence_score,
            },
        }
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

    def search_similar(
        self,
        vector: list[float],
        limit: int = 10,
        threshold: Optional[float] = None,
    ) -> list[dict]:
        """Search for similar use cases by vector similarity"""
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=limit,
                score_threshold=threshold,
            )
            return [
                {
                    "use_case_id": hit.payload.get("use_case_id"),
                    "title": hit.payload.get("title"),
                    "score": hit.score,
                    "payload": hit.payload,
                }
                for hit in results
            ]
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def delete_point(self, point_id: str):
        """Delete a use case from Qdrant"""
        numeric_id = int(hashlib.md5(point_id.encode()).hexdigest(), 16) % (2**31)
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[numeric_id],
            )
        except Exception as e:
            print(f"Delete error: {e}")
