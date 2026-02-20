from contextlib import asynccontextmanager
from typing import List, Optional

from langchain_openai import AzureOpenAIEmbeddings, OpenAI

from langchain_community.vectorstores import Qdrant
from openai import AsyncAzureOpenAI
from pydantic import BaseModel
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Filter,
    Prefetch,
    FusionQuery,
    Fusion,
)

from app.db.db import get_async_session_maker

class DocumentResult(BaseModel):
    content: str
    metadata: dict
    relevance_score: float
    rerank_score: Optional[float] = None
    fusion_score: Optional[float] = None  # Score from RRF fusion


class RerankedSearchResult(BaseModel):
    documents: List[DocumentResult]
    total_found: int
    search_method: str


class KnowledgeAgent:
    def __init__(
        self,
        openai_client: AsyncAzureOpenAI | OpenAI,
        qdrant_client: QdrantClient,
        embeddings: AzureOpenAIEmbeddings,
        model_name="gpt-o4-mini",
    ):
        self.openai_client = openai_client
        self.qdrant_client = qdrant_client
        self.embeddings = embeddings
        self.model_name = model_name

    async def hybrid_search_with_rrf(
        self,
        query: str,
        collection_name: str,
        qdrant_filter: Filter | None = None,
        initial_k: int = 20,
        final_k: int = 5,
        rrf_k: int = 60,
    ) -> RerankedSearchResult:
        """
        Performs hybrid search using Reciprocal Rank Fusion (RRF) to combine
        dense vector search with text-based search signals.
        
        RRF Formula: score = sum(1 / (k + rank_i)) for each ranking
        
        Args:
            query: The search query
            collection_name: Name of the Qdrant collection
            qdrant_filter: Optional filter to apply
            initial_k: Number of results to fetch from each search method
            final_k: Number of final results to return
            rrf_k: RRF constant (typically 60)
        """
        try:
            query_vector = await self.embeddings.aembed_query(query)
            
            collection_info = self.qdrant_client.get_collection(collection_name=collection_name)
            has_named_vectors = isinstance(collection_info.config.params.vectors, dict)
            
            logger.info(f"Collection '{collection_name}' vector config: {collection_info.config.params.vectors}")
            logger.info(f"Has named vectors: {has_named_vectors}")
            
            if has_named_vectors:
                logger.info(f"Available vector names: {list(collection_info.config.params.vectors.keys())}")
            
                # Use Qdrant's native fusion with prefetch
            return await self._rrf_with_prefetch(
                query=query,
                query_vector=query_vector,
                collection_name=collection_name,
                qdrant_filter=qdrant_filter,
                initial_k=initial_k,
                final_k=final_k,
            )

        except Exception as e:
            logger.error(f"Error in hybrid search with RRF: {str(e)}")
            return await self.fallback_search(query, collection_name, qdrant_filter, final_k)

    async def _rrf_with_prefetch(
        self,
        query: str,
        query_vector: List[float],
        collection_name: str,
        qdrant_filter: Filter | None = None,
        initial_k: int = 20,
        final_k: int = 5,
    ) -> RerankedSearchResult:
        """
        Use Qdrant's native prefetch + fusion for RRF.
        This is the most efficient approach when collection supports it.
        """
        try:
            # Use Qdrant's query API with prefetch and RRF fusion
            results = self.qdrant_client.query_points(
                collection_name=collection_name,
                prefetch=[
                    # Dense vector search
                    Prefetch(
                        query=query_vector,
                        using="dense",
                        limit=initial_k,
                        filter=qdrant_filter,
                    ),
                ],
                query=FusionQuery(fusion=Fusion.RRF),
                limit=final_k,
                with_payload=True,
            )

            documents = []
            for point in results.points:
                doc_result = DocumentResult(
                    content=point.payload.get("page_content", ""),
                    metadata=point.payload.get("metadata", {}),
                    relevance_score=point.score if point.score else 0.0,
                    fusion_score=point.score if point.score else 0.0,
                )
                documents.append(doc_result)

            logger.info(f"RRF with prefetch found {len(documents)} documents")
            return RerankedSearchResult(
                documents=documents,
                total_found=len(results.points),
                search_method="rrf_prefetch_fusion",
            )

        except Exception as e:
            logger.error(f"Error in RRF with prefetch: {str(e)}")
            raise

    @asynccontextmanager
    async def get_session(self):
        """Get database session with proper cleanup."""
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


    async def fallback_search(
        self, query: str, collection_name: str, qdrant_filter: Filter | None = None, k: int = 5
    ) -> RerankedSearchResult:
        """Fallback to simple vector search if hybrid search fails"""
        try:
            # query_vector = await self.embeddings.aembed_query(query)
            vector_store = Qdrant(
                    client=self.qdrant_client,
                    collection_name=collection_name,
                    embeddings=self.embeddings,
                )
            results = vector_store.similarity_search_with_score(
                query=query,
                filter=qdrant_filter,
                k=k,
            )
            documents = [
                DocumentResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    relevance_score=score,
                )
                for doc, score in results
            ]
            logger.info(f"Fallback search found {len(documents)} documents for query: {query}")
            return RerankedSearchResult(
                documents=documents,
                total_found=len(results),
                search_method="fallback_vector_search",
            )

        except Exception as e:
            logger.error(f"Error in fallback search: {str(e)}")
            return RerankedSearchResult(
                documents=[], total_found=0, search_method="error"
            )
