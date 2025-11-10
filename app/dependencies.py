from __future__ import annotations

from fastapi import HTTPException, Request

from .rag_pipeline import RagPipeline


def get_pipeline(request: Request) -> RagPipeline:
    pipeline: RagPipeline | None = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise HTTPException(status_code=503, detail="RAG pipeline is not ready.")
    return pipeline
