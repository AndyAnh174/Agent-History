from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..dependencies import get_pipeline
from ..rag_pipeline import RagPipeline

router = APIRouter(prefix="/mcq", tags=["MCQ Generator"])


class MCQQuestion(BaseModel):
    question: str
    options: Dict[str, str]
    correct_answer: str
    explanation: str


class MCQRequest(BaseModel):
    context: str = Field(..., min_length=50, description="Ngữ cảnh lịch sử để sinh câu hỏi.")
    num_questions: int = Field(default=3, ge=1, le=10)


class MCQResponse(BaseModel):
    questions: List[MCQQuestion]
    trace_id: Optional[str] = None


@router.post("/generate", response_model=MCQResponse)
async def generate_mcq(payload: MCQRequest, pipeline: RagPipeline = Depends(get_pipeline)) -> MCQResponse:
    result = await pipeline.generate_mcq(payload.context, payload.num_questions)
    return MCQResponse(**result)
