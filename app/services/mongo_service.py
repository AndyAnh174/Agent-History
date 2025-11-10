from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection


class MongoService:
    """Async helper for storing chat logs and metadata."""

    def __init__(self, uri: str, db_name: str, collection_name: str):
        self.client = AsyncIOMotorClient(uri)
        database = self.client[db_name]
        self.collection: AsyncIOMotorCollection = database[collection_name]

    async def save_chat_log(
        self,
        question: str,
        answer: str,
        sources: List[Dict[str, Any]],
        kind: str,
        metadata: Dict[str, Any] | None = None,
    ) -> str:
        payload = {
            "kind": kind,
            "question": question,
            "answer": answer,
            "sources": sources,
            "metadata": metadata or {},
            "created_at": datetime.now(tz=timezone.utc),
        }
        result = await self.collection.insert_one(payload)
        return str(result.inserted_id)

    async def fetch_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        cursor = self.collection.find().sort("created_at", -1).limit(limit)
        return [doc async for doc in cursor]

    async def close(self) -> None:
        self.client.close()
