from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dependencies import get_pipeline
from ..rag_pipeline import RagPipeline

router = APIRouter(prefix="/rag", tags=["Sử Việt RAG"])


class SourceModel(BaseModel):
    id: Optional[str]
    title: Optional[str] = None
    snippet: str
    score: Optional[float] = None
    metadata: Dict[str, Any] | None = None


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=5, description="Câu hỏi lịch sử bằng tiếng Việt.")


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceModel]
    trace_id: Optional[str] = None


class SummarizeRequest(BaseModel):
    topic: str = Field(..., min_length=3)
    detail_level: str = Field(default="medium", pattern="^(short|medium|long)$")


class SummarizeResponse(BaseModel):
    topic: str
    summary: str
    sources: List[SourceModel] | None = None
    trace_id: Optional[str] = None


class TimelineRequest(BaseModel):
    entity: str = Field(..., min_length=3)


class TimelineResponse(BaseModel):
    entity: str
    events: Any
    sources: List[SourceModel] | None = None
    trace_id: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_k: int | None = Field(default=None, ge=1, le=20)


class SearchResponse(BaseModel):
    query: str
    results: List[SourceModel]


class IngestRequest(BaseModel):
    title: str
    content: str
    chunk_size: int = Field(default=800, ge=200, le=2000)
    chunk_overlap: int = Field(default=120, ge=0, le=500)
    metadata: Dict[str, Any] | None = Field(default=None, description="Metadata bổ sung (tác giả, nguồn, năm, ...).")


class IngestResponse(BaseModel):
    title: str
    chunks_ingested: int


class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=5, description="Mô tả về hình ảnh lịch sử Việt Nam muốn tạo.")


class GenerateImageResponse(BaseModel):
    image_url: str
    prompt: str
    trace_id: Optional[str] = None


@router.post("/query", response_model=QueryResponse)
async def ask_question(payload: QueryRequest, pipeline: RagPipeline = Depends(get_pipeline)) -> QueryResponse:
    try:
        result = await pipeline.answer_question(payload.question)
        return QueryResponse(**result)
    except ValueError as e:
        # User-friendly error messages
        error_msg = str(e)
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="API đang quá tải. Vui lòng đợi một chút và thử lại sau."
            )
        elif "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=504,
                detail="Yêu cầu quá thời gian chờ. Vui lòng thử lại."
            )
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        from loguru import logger
        logger.error(f"Error in query endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Có lỗi xảy ra khi xử lý câu hỏi. Vui lòng thử lại sau."
        )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_topic(payload: SummarizeRequest, pipeline: RagPipeline = Depends(get_pipeline)) -> SummarizeResponse:
    detail_level = payload.detail_level.lower()
    result = await pipeline.summarize_topic(payload.topic, detail_level)
    return SummarizeResponse(**result)


@router.post("/timeline", response_model=TimelineResponse)
async def build_timeline(payload: TimelineRequest, pipeline: RagPipeline = Depends(get_pipeline)) -> TimelineResponse:
    result = await pipeline.build_timeline(payload.entity)
    return TimelineResponse(**result)


@router.post("/search", response_model=SearchResponse)
async def search_context(payload: SearchRequest, pipeline: RagPipeline = Depends(get_pipeline)) -> SearchResponse:
    result = await pipeline.search_context(payload.query, payload.top_k)
    return SearchResponse(**result)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(payload: IngestRequest, pipeline: RagPipeline = Depends(get_pipeline)) -> IngestResponse:
    result = await pipeline.ingest_text(
        title=payload.title,
        content=payload.content,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
        extra_metadata=payload.metadata,
    )
    return IngestResponse(**result)


@router.post("/generate-image", response_model=GenerateImageResponse)
async def generate_image(payload: GenerateImageRequest, pipeline: RagPipeline = Depends(get_pipeline)) -> GenerateImageResponse:
    try:
        # Validate prompt before processing
        from ..utils.prompt_validator import PromptValidator
        
        is_valid, error_msg = PromptValidator.validate_prompt(payload.prompt)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        result = await pipeline.generate_history_image(payload.prompt)
        trace_id = str(uuid4())
        return GenerateImageResponse(**result, trace_id=trace_id)
    except ValueError as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="API đang quá tải. Vui lòng đợi một chút và thử lại sau."
            )
        elif "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=504,
                detail="Yêu cầu quá thời gian chờ. Vui lòng thử lại."
            )
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        from loguru import logger
        logger.error(f"Error in generate-image endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Có lỗi xảy ra khi tạo ảnh. Vui lòng thử lại sau."
        )
