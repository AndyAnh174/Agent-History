from __future__ import annotations

from typing import Iterable, List

import httpx


class EmbeddingService:
    """Wrapper around the external BGE-M3 embedding API."""

    def __init__(self, endpoint: str, max_length: int = 512, timeout: float = 30.0):
        self.endpoint = endpoint
        self.max_length = max_length
        self.timeout = timeout

    async def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        payload = {
            "texts": list(texts),
            "max_length": self.max_length,
        }
        if not payload["texts"]:
            return []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.endpoint,
                json=payload,
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        embeddings = data.get("embeddings")
        if not embeddings:
            raise ValueError("Embedding API returned no vectors.")
        return embeddings

    async def embed_text(self, text: str) -> List[float]:
        embeddings = await self.embed_texts([text])
        return embeddings[0]
