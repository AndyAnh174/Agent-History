from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence
from uuid import uuid4

from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, PointStruct, VectorParams


@dataclass
class VectorDocument:
    """Payload stored inside Qdrant."""

    text: str
    metadata: Dict[str, Any]
    document_id: str | None = None


class QdrantService:
    """Lightweight helper over Qdrant client for CRUD operations."""

    def __init__(
        self,
        url: str,
        api_key: str | None,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE,
        max_retries: int = 10,
        retry_delay: float = 3.0,
    ):
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance
        self.client = QdrantClient(url=url, api_key=api_key)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                self.client.get_collection(self.collection_name)
                if attempt > 1:
                    logger.info("Connected to Qdrant collection '{}' on attempt {}", self.collection_name, attempt)
                return
            except UnexpectedResponse:
                try:
                    logger.info("Collection '{}' not found. Creating...", self.collection_name)
                    self.client.recreate_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=self.vector_size, distance=self.distance),
                    )
                    logger.info("Created Qdrant collection '{}'", self.collection_name)
                    return
                except Exception as create_error:
                    last_error = create_error
                    logger.warning(
                        "Failed to create Qdrant collection '{}' (attempt {}/{}): {}",
                        self.collection_name,
                        attempt,
                        self.max_retries,
                        create_error,
                    )
            except Exception as err:  # Connection refused, timeouts, etc.
                last_error = err
                logger.warning(
                    "Unable to connect to Qdrant (attempt {}/{}): {}",
                    attempt,
                    self.max_retries,
                    err,
                )

            if attempt < self.max_retries:
                time.sleep(self.retry_delay)

        raise RuntimeError(
            f"Unable to connect to Qdrant after {self.max_retries} attempts. Last error: {last_error}"
        ) from last_error

    def upsert_documents(self, vectors: Sequence[Sequence[float]], documents: Sequence[VectorDocument]) -> int:
        if not vectors or not documents:
            return 0
        if len(vectors) != len(documents):
            raise ValueError("Vectors and documents must have the same length.")

        points: List[PointStruct] = []
        for vector, doc in zip(vectors, documents, strict=True):
            payload = {
                "content": doc.text,
                **doc.metadata,
            }
            point_id = doc.document_id or str(uuid4())
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))

        self.client.upsert(collection_name=self.collection_name, points=points)
        return len(points)

    def similarity_search(
        self,
        vector: Sequence[float],
        limit: int,
        score_threshold: float | None = None,
    ) -> List[Dict[str, Any]]:
        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
        )
        results: List[Dict[str, Any]] = []
        for hit in hits:
            if score_threshold is not None and hit.score < score_threshold:
                continue
            payload = hit.payload or {}
            results.append(
                {
                    "id": hit.id,
                    "score": hit.score,
                    "content": payload.get("content", ""),
                    "metadata": payload,
                }
            )
        return results
