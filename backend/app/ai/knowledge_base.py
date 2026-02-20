"""
Qdrant-based knowledge base for transcripts and use cases.
Uses hybrid search with RRF (Reciprocal Rank Fusion) combining dense + sparse vectors.
"""
import re
import logging
from collections import Counter
from typing import Optional

import hashlib
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseVector,
    Filter,
    FieldCondition,
    MatchValue,
    Prefetch,
    FusionQuery,
    Fusion,
    PayloadSchemaType,
)
from app.config import settings
from app.clients import get_openai_client


logger = logging.getLogger(__name__)


def _text_to_sparse_indices_values(text: str) -> tuple[list[int], list[float]]:
    """
    Convert text to sparse vector representation (bag-of-words with hashed indices).
    Used for keyword-based search to combine with dense semantic search via RRF.
    """
    tokens = re.findall(r"\b\w{2,}\b", text.lower())[:500]  # limit tokens
    if not tokens:
        return [], []
    counts = Counter(tokens)
    indices = []
    values = []
    for token, count in counts.items():
        idx = abs(hash(token)) % (2**31 - 1)
        indices.append(idx)
        values.append(float(count))
    return indices, values


class KnowledgeBase:
    """
    Manages transcript and use case embeddings in Qdrant.
    Performs hybrid search using Reciprocal Rank Fusion (RRF) to combine
    dense vector search with text-based sparse search.
    RRF Formula: score = sum(1 / (k + rank_i)) for each ranking
    """

    def __init__(self, qdrant_url: str):
        self.client = QdrantClient(url=qdrant_url, check_compatibility=False)
        self.openai = get_openai_client()

    def _embed(self, text: str) -> list[float]:
        """Generate dense embedding for text."""
        resp = self.openai.embeddings.create(model=settings.EMBEDDING_MODEL, input=text[:8000])
        return resp.data[0].embedding

    def _sparse_vector(self, text: str) -> SparseVector:
        """Generate sparse vector from text for keyword search."""
        indices, values = _text_to_sparse_indices_values(text)
        if not indices:
            return SparseVector(indices=[0], values=[0.0])
        return SparseVector(indices=indices, values=values)

    def _point_id(self, prefix: str, id: str) -> int:
        return int(hashlib.md5(f"{prefix}:{id}".encode()).hexdigest(), 16) % (2**31)

    def _create_payload_indexes(self, collection_name: str):
        """Create payload indexes for fast filtering."""
        try:
            for field_name, schema_type in [
                ("company_id", PayloadSchemaType.KEYWORD),
                ("transcript_id", PayloadSchemaType.KEYWORD),
                ("use_case_id", PayloadSchemaType.KEYWORD),
            ]:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=schema_type,
                )
                logger.info(f"Created payload index {field_name} on {collection_name}")
        except Exception as e:
            logger.warning(f"Payload index creation (may already exist): {e}")

    def _supports_hybrid(self, collection_name: str) -> bool:
        """Check if collection has named vectors (dense + sparse) for hybrid search."""
        try:
            info = self.client.get_collection(collection_name)
            params = getattr(info.config, "params", None)
            if not params or not params.vectors:
                return False
            vectors = params.vectors
            if isinstance(vectors, dict):
                return settings.DENSE_VECTOR_NAME in vectors and settings.SPARSE_VECTOR_NAME in vectors
            return False
        except Exception:
            return False

    def ensure_transcripts_collection(self):
        """Create transcripts collection with dense + sparse vectors and indexes."""
        try:
            self.client.get_collection(settings.TRANSCRIPTS_COLLECTION)
            logger.info(f"Collection {settings.TRANSCRIPTS_COLLECTION} already exists")
        except Exception:
            self.client.create_collection(
                collection_name=settings.TRANSCRIPTS_COLLECTION,
                vectors_config={
                    settings.DENSE_VECTOR_NAME: VectorParams(
                        size=settings.VECTOR_SIZE,
                        distance=Distance.COSINE,
                    )
                },
                sparse_vectors_config={
                    settings.SPARSE_VECTOR_NAME: SparseVectorParams(),
                },
            )
            self._create_payload_indexes(settings.TRANSCRIPTS_COLLECTION)
            logger.info(f"Created collection {settings.TRANSCRIPTS_COLLECTION} with hybrid vectors")

    def ensure_use_cases_collection(self):
        """Create use_cases collection with dense + sparse vectors and indexes."""
        try:
            self.client.get_collection(settings.USE_CASES_COLLECTION)
            logger.info(f"Collection {settings.USE_CASES_COLLECTION} already exists")
        except Exception:
            self.client.create_collection(
                collection_name=settings.USE_CASES_COLLECTION,
                vectors_config={
                    settings.DENSE_VECTOR_NAME: VectorParams(
                        size=settings.VECTOR_SIZE,
                        distance=Distance.COSINE,
                    )
                },
                sparse_vectors_config={
                    settings.SPARSE_VECTOR_NAME: SparseVectorParams(),
                },
            )
            self._create_payload_indexes(settings.USE_CASES_COLLECTION)
            logger.info(f"Created collection {settings.USE_CASES_COLLECTION} with hybrid vectors")

    def upsert_transcript_chunk(
        self,
        transcript_id: str,
        company_id: str,
        chunk_index: int,
        text: str,
        metadata: Optional[dict] = None,
    ):
        """Upsert a transcript chunk with dense and sparse vectors (or dense only for legacy)."""
        point_id = self._point_id("transcript", f"{transcript_id}:{chunk_index}")
        dense = self._embed(text)
        payload = {
            "transcript_id": transcript_id,
            "company_id": company_id,
            "chunk_index": chunk_index,
            "text": text[:2000],
            **(metadata or {}),
        }
        if self._supports_hybrid(settings.TRANSCRIPTS_COLLECTION):
            sparse = self._sparse_vector(text)
            vector = {settings.DENSE_VECTOR_NAME: dense, settings.SPARSE_VECTOR_NAME: sparse}
        else:
            vector = dense
        self.client.upsert(
            collection_name=settings.TRANSCRIPTS_COLLECTION,
            points=[{"id": point_id, "vector": vector, "payload": payload}],
        )

    def upsert_use_case(
        self,
        use_case_id: str,
        company_id: str,
        title: str,
        description: str,
        metadata: Optional[dict] = None,
    ):
        """Upsert a use case with dense and sparse vectors (or dense only for legacy)."""
        point_id = self._point_id("usecase", use_case_id)
        text = f"{title}\n\n{description}"
        dense = self._embed(text)
        payload = {
            "use_case_id": use_case_id,
            "company_id": company_id,
            "title": title,
            "description": description[:2000],
            **(metadata or {}),
        }
        if self._supports_hybrid(settings.USE_CASES_COLLECTION):
            sparse = self._sparse_vector(text)
            vector = {settings.DENSE_VECTOR_NAME: dense, settings.SPARSE_VECTOR_NAME: sparse}
        else:
            vector = dense
        self.client.upsert(
            collection_name=settings.USE_CASES_COLLECTION,
            points=[{"id": point_id, "vector": vector, "payload": payload}],
        )

    def _qdrant_filter(self, company_id: Optional[str] = None) -> Optional[Filter]:
        if not company_id:
            return None
        return Filter(
            must=[FieldCondition(key="company_id", match=MatchValue(value=company_id))]
        )

    def _hybrid_search(
        self,
        collection_name: str,
        query: str,
        limit: int = 5,
        company_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Performs hybrid search using Reciprocal Rank Fusion (RRF) to combine
        dense vector search with text-based sparse search.
        RRF Formula: score = sum(1 / (k + rank_i)) for each ranking
        """
        q_filter = self._qdrant_filter(company_id)
        dense_vector = self._embed(query)

        if not self._supports_hybrid(collection_name):
            return self._dense_only_search(
                collection_name, dense_vector, limit, q_filter
            )

        sparse_vector = self._sparse_vector(query)
        try:
            results = self.client.query_points(
                collection_name=collection_name,
                prefetch=[
                    Prefetch(
                        query=dense_vector,
                        using=settings.DENSE_VECTOR_NAME,
                        limit=settings.INITIAL_K,
                        filter=q_filter,
                    ),
                    Prefetch(
                        query=sparse_vector,
                        using=settings.SPARSE_VECTOR_NAME,
                        limit=settings.INITIAL_K,
                        filter=q_filter,
                    ),
                ],
                query=FusionQuery(fusion=Fusion.RRF),
                limit=limit,
                with_payload=True,
            )

            return [
                {
                    "score": point.score if point.score else 0.0,
                    "payload": point.payload or {},
                }
                for point in results.points
            ]
        except Exception as e:
            logger.warning(f"Hybrid search failed, falling back to dense only: {e}")
            return self._dense_only_search(
                collection_name, dense_vector, limit, q_filter
            )

    def _dense_only_search(
        self,
        collection_name: str,
        dense_vector: list[float],
        limit: int,
        q_filter: Optional[Filter],
    ) -> list[dict]:
        """Fallback when collection has single vector or hybrid fails."""
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=dense_vector,
                limit=limit,
                query_filter=q_filter,
            )
            return [{"score": r.score, "payload": r.payload} for r in results]
        except Exception:
            try:
                results = self.client.search(
                    collection_name=collection_name,
                    query_vector=(settings.DENSE_VECTOR_NAME, dense_vector),
                    limit=limit,
                    query_filter=q_filter,
                )
                return [{"score": r.score, "payload": r.payload} for r in results]
            except Exception as e:
                logger.error(f"Dense search failed: {e}")
                return []

    def search_transcripts(
        self, query: str, limit: int = 5, company_id: Optional[str] = None
    ):
        """Hybrid search over transcript chunks."""
        return self._hybrid_search(
            settings.TRANSCRIPTS_COLLECTION, query, limit, company_id
        )

    def search_use_cases(
        self, query: str, limit: int = 5, company_id: Optional[str] = None
    ):
        """Hybrid search over use cases."""
        return self._hybrid_search(
            settings.USE_CASES_COLLECTION, query, limit, company_id
        )

    def search_all(
        self, query: str, limit: int = 10, company_id: Optional[str] = None
    ):
        """Search both transcripts and use cases with hybrid RRF."""
        transcripts = self.search_transcripts(
            query, limit=limit // 2, company_id=company_id
        )
        use_cases = self.search_use_cases(
            query, limit=limit // 2, company_id=company_id
        )
        return {"transcripts": transcripts, "use_cases": use_cases}

    def delete_transcript(self, transcript_id: str):
        """Delete all chunks for a transcript."""
        self.client.delete(
            collection_name=settings.TRANSCRIPTS_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="transcript_id", match=MatchValue(value=transcript_id)
                    )
                ]
            ),
        )

    def delete_use_case(self, use_case_id: str):
        """Delete a use case from the knowledge base."""
        point_id = self._point_id("usecase", use_case_id)
        self.client.delete(
            collection_name=settings.USE_CASES_COLLECTION,
            points_selector=[point_id],
        )

    def delete_company_embeddings(self, company_id: str):
        """Delete all transcript and use case embeddings for a company."""
        q_filter = self._qdrant_filter(company_id)
        if not q_filter:
            return
        for collection_name in (settings.TRANSCRIPTS_COLLECTION, settings.USE_CASES_COLLECTION):
            try:
                self.client.delete(
                    collection_name=collection_name,
                    points_selector=q_filter,
                )
                logger.info(f"Deleted company embeddings | company_id={company_id} | collection={collection_name}")
            except Exception as e:
                logger.warning(f"Failed to delete company embeddings | company_id={company_id} | collection={collection_name} | error={e}")
