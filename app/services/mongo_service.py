from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError


class MongoService:
    """Async helper for storing chat logs and metadata."""

    def __init__(self, uri: str, db_name: str, collection_name: str):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client: AsyncIOMotorClient | None = None
        self.collection: AsyncIOMotorCollection | None = None
        self._connected = False
        # Initialize connection (will be tested on first use)
        try:
            self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
            database = self.client[db_name]
            self.collection = database[collection_name]
            logger.info(f"MongoDB client initialized for {db_name}.{collection_name}")
        except Exception as e:
            logger.warning(f"MongoDB initialization warning: {e}")
            # Will try to connect on first use

    async def save_chat_log(
        self,
        question: str,
        answer: str,
        sources: List[Dict[str, Any]],
        kind: str,
        metadata: Dict[str, Any] | None = None,
    ) -> str:
        if self.collection is None:
            # Try to initialize if not done
            try:
                self.client = AsyncIOMotorClient(self.uri, serverSelectionTimeoutMS=5000)
                database = self.client[self.db_name]
                self.collection = database[self.collection_name]
            except Exception as e:
                logger.warning(f"MongoDB not available, skipping chat log: {e}")
                return "no-mongo"
        
        try:
            payload = {
                "kind": kind,
                "question": question,
                "answer": answer,
                "sources": sources,
                "metadata": metadata or {},
                "created_at": datetime.now(tz=timezone.utc),
            }
            result = await self.collection.insert_one(payload)
            if not self._connected:
                self._connected = True
                logger.info("MongoDB connection verified")
            return str(result.inserted_id)
        except (OperationFailure, ServerSelectionTimeoutError) as e:
            # Auth failed or server not available
            logger.warning(f"MongoDB save failed (auth/server issue): {e}")
            # Try without auth if URI has auth
            if "@" in self.uri and not self._connected:
                try:
                    parts = self.uri.split("@")
                    if len(parts) == 2:
                        host_part = parts[1].split("/")[0]
                        new_uri = f"mongodb://{host_part}/{self.db_name}"
                        logger.info(f"Retrying MongoDB without auth: {new_uri}")
                        self.client = AsyncIOMotorClient(new_uri, serverSelectionTimeoutMS=5000)
                        database = self.client[self.db_name]
                        self.collection = database[self.collection_name]
                        result = await self.collection.insert_one(payload)
                        self._connected = True
                        logger.info("MongoDB connected without auth")
                        return str(result.inserted_id)
                except Exception as e2:
                    logger.error(f"MongoDB retry failed: {e2}")
            return "error"
        except Exception as e:
            logger.error(f"Failed to save chat log to MongoDB: {e}")
            return "error"

    async def fetch_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        if self.collection is None:
            return []
        try:
            cursor = self.collection.find().sort("created_at", -1).limit(limit)
            return [doc async for doc in cursor]
        except Exception as e:
            logger.error(f"Failed to fetch logs from MongoDB: {e}")
            return []

    async def close(self) -> None:
        if self.client:
            self.client.close()
