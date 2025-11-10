from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Su Viet RAG Agent", alias="APP_NAME")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")

    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="vietnam_history", alias="QDRANT_COLLECTION")
    embedding_dimension: int = Field(default=1024, alias="EMBEDDING_DIM")
    rag_top_k: int = Field(default=5, alias="RAG_TOP_K")
    rag_score_threshold: float = Field(default=0.25, alias="RAG_SCORE_THRESHOLD")

    mongo_uri: str = Field(default="mongodb://localhost:27017", alias="MONGO_URI")
    mongo_db_name: str = Field(default="vietnam_history", alias="MONGO_DB_NAME")
    mongo_collection: str = Field(default="chat_logs", alias="MONGO_COLLECTION")

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    gemini_api_url: str | None = Field(default=None, alias="GEMINI_API_URL")

    embed_api: str = Field(default="https://embed.andyanh.id.vn/embed", alias="EMBED_API")
    embed_max_length: int = Field(default=512, alias="EMBED_MAX_LENGTH")
    embed_timeout: float = Field(default=30.0, alias="EMBED_TIMEOUT")

    allow_origins: str | List[str] = Field(default="*", alias="ALLOW_ORIGINS")

    def get_allowed_origins(self) -> List[str]:
        """Return parsed CORS origins."""
        if not self.allow_origins:
            return ["*"]
        if isinstance(self.allow_origins, str):
            if self.allow_origins.strip() == "*":
                return ["*"]
            origins = [origin.strip() for origin in self.allow_origins.split(",") if origin.strip()]
            # Always allow localhost origins for development
            if "*" not in origins:
                origins.extend([
                    "http://localhost:5500",
                    "http://127.0.0.1:5500",
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                ])
            return origins
        return self.allow_origins

    @property
    def resolved_gemini_url(self) -> str:
        if self.gemini_api_url:
            return self.gemini_api_url
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent"


@lru_cache
def get_settings() -> Settings:
    """Cache settings instance for reuse across the app."""
    return Settings()
