from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence
from uuid import uuid4

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
    ):
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance
        self.client = QdrantClient(url=url, api_key=api_key)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        try:
            self.client.get_collection(self.collection_name)
        except UnexpectedResponse:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=self.distance),
            )

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
