from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence
from uuid import uuid4

from loguru import logger
from llama_index.core import Document

from .config import Settings, get_settings
from .services.embedding_service import EmbeddingService
from .services.llm_service import GeminiService
from .services.mongo_service import MongoService
from .services.qdrant_service import QdrantService, VectorDocument
from .utils.text_splitter import split_text


@dataclass
class SourceChunk:
    id: str
    title: str | None
    snippet: str
    score: float | None = None
    metadata: Dict[str, Any] | None = None


class RagPipeline:
    """End-to-end orchestrator for the Sử Việt RAG agent."""

    def __init__(
        self,
        settings: Settings,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService,
        llm_service: GeminiService,
        mongo_service: MongoService,
    ):
        self.settings = settings
        self.embedding = embedding_service
        self.qdrant = qdrant_service
        self.llm = llm_service
        self.mongo = mongo_service

    async def answer_question(self, question: str) -> Dict[str, Any]:
        vector = await self.embedding.embed_text(question)
        hits = self.qdrant.similarity_search(
            vector,
            limit=self.settings.rag_top_k,
            score_threshold=self.settings.rag_score_threshold,
        )
        context = self._format_context(hits)
        prompt = self._build_qa_prompt(question, context)
        answer = await self.llm.generate_text(prompt)
        sources = self._build_sources(hits)
        sources_payload = [source.__dict__ for source in sources]
        trace_id = await self.mongo.save_chat_log(
            question=question,
            answer=answer,
            sources=sources_payload,
            kind="query",
            metadata={"hits": len(hits)},
        )
        return {"answer": answer, "sources": sources_payload, "trace_id": trace_id}

    async def summarize_topic(self, topic: str, detail_level: str = "medium") -> Dict[str, Any]:
        vector = await self.embedding.embed_text(topic)
        hits = self.qdrant.similarity_search(vector, limit=10)
        context = self._format_context(hits)
        prompt = self._build_summary_prompt(topic, context, detail_level)
        summary = await self.llm.generate_text(prompt)
        sources_payload = [source.__dict__ for source in self._build_sources(hits)]
        trace_id = await self.mongo.save_chat_log(
            question=topic,
            answer=summary,
            sources=sources_payload,
            kind="summarize",
            metadata={"detail_level": detail_level},
        )
        return {"topic": topic, "summary": summary, "trace_id": trace_id, "sources": sources_payload}

    async def build_timeline(self, entity: str) -> Dict[str, Any]:
        vector = await self.embedding.embed_text(entity)
        hits = self.qdrant.similarity_search(vector, limit=12)
        context = self._format_context(hits)
        prompt = self._build_timeline_prompt(entity, context)
        events = await self.llm.generate_json(prompt)
        sources_payload = [source.__dict__ for source in self._build_sources(hits)]
        trace_id = await self.mongo.save_chat_log(
            question=entity,
            answer=str(events),
            sources=sources_payload,
            kind="timeline",
            metadata={},
        )
        return {
            "entity": entity,
            "events": events.get("events", events),
            "sources": sources_payload,
            "trace_id": trace_id,
        }

    async def generate_mcq(self, context: str, num_questions: int = 3) -> Dict[str, Any]:
        prompt = self._build_mcq_prompt(context, num_questions)
        mcq_payload = await self.llm.generate_json(prompt)
        trace_id = await self.mongo.save_chat_log(
            question="generate-mcq",
            answer=str(mcq_payload),
            sources=[],
            kind="mcq",
            metadata={"num_questions": num_questions},
        )
        return {"questions": mcq_payload.get("questions", []), "trace_id": trace_id}

    async def ingest_text(
        self,
        title: str,
        content: str,
        chunk_size: int = 800,
        chunk_overlap: int = 120,
        extra_metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        chunks = split_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            return {"chunks_ingested": 0}

        documents = [
            Document(
                text=chunk,
                metadata={
                    "title": title,
                    "chunk_index": idx,
                    **(extra_metadata or {}),
                },
            )
            for idx, chunk in enumerate(chunks)
        ]
        embeddings = await self.embedding.embed_texts([doc.text for doc in documents])
        vector_documents = [
            VectorDocument(
                text=doc.text,
                metadata=doc.metadata,
                document_id=str(uuid4()),
            )
            for doc in documents
        ]
        inserted = self.qdrant.upsert_documents(embeddings, vector_documents)
        return {"chunks_ingested": inserted, "title": title}

    async def search_context(self, query: str, top_k: int | None = None) -> Dict[str, Any]:
        vector = await self.embedding.embed_text(query)
        hits = self.qdrant.similarity_search(
            vector,
            limit=top_k or self.settings.rag_top_k,
            score_threshold=self.settings.rag_score_threshold,
        )
        return {
            "query": query,
            "results": [source.__dict__ for source in self._build_sources(hits)],
        }

    async def shutdown(self) -> None:
        await self.mongo.close()

    def _format_context(self, hits: Sequence[Dict[str, Any]]) -> str:
        context_blocks = []
        for idx, hit in enumerate(hits, start=1):
            metadata = hit.get("metadata", {})
            title = metadata.get("title") or metadata.get("source") or f"Đoạn {idx}"
            snippet = hit.get("content", "")
            block = f"[{idx}] {title}\n{snippet}\n"
            context_blocks.append(block.strip())
        return "\n\n".join(context_blocks)

    def _build_sources(self, hits: Sequence[Dict[str, Any]]) -> List[SourceChunk]:
        sources: List[SourceChunk] = []
        for hit in hits:
            metadata = hit.get("metadata", {})
            snippet = hit.get("content", "")
            sources.append(
                SourceChunk(
                    id=str(hit.get("id")),
                    title=metadata.get("title") or metadata.get("source"),
                    snippet=snippet[:500],
                    score=hit.get("score"),
                    metadata=metadata,
                )
            )
        return sources

    def _build_qa_prompt(self, question: str, context: str) -> str:
        return (
            "Dưới đây là một số tư liệu lịch sử Việt Nam:\n\n"
            f"{context}\n\n"
            f"Câu hỏi: {question}\n\n"
            "Hãy trả lời bằng tiếng Việt, thân thiện nhưng chính xác, kèm trích dẫn nguồn theo dạng [số]. "
            'Nếu không chắc chắn, hãy nói "Tôi không có đủ dữ liệu để trả lời."'
        )

    def _build_summary_prompt(self, topic: str, context: str, detail_level: str) -> str:
        return (
            f"Hãy tóm tắt về chủ đề {topic} dựa trên các trích đoạn dưới đây.\n"
            f"Yêu cầu mức độ chi tiết: {detail_level}.\n\n"
            f"{context}\n\n"
            "Trả lời bằng tiếng Việt, dạng đoạn văn ngắn và có thể liệt kê những điểm chính."
        )

    def _build_timeline_prompt(self, entity: str, context: str) -> str:
        return (
            f"Dựa vào tư liệu sau, tạo timeline các mốc sự kiện quan trọng liên quan tới {entity}.\n"
            "Trả về JSON với cấu trúc {\"events\": [{\"year\": \"\", \"title\": \"\", \"description\": \"\"}]}.\n"
            "Nếu không chắc chắn về năm tháng, hãy ghi rõ \"Không rõ\"."
            f"\n\n{context}"
        )

    def _build_mcq_prompt(self, context: str, num_questions: int) -> str:
        return (
            "Bạn là trợ lý giáo dục lịch sử Việt Nam. "
            "Tạo bộ câu hỏi trắc nghiệm dựa trên đoạn văn bản sau.\n\n"
            f"{context}\n\n"
            "Yêu cầu JSON duy nhất với khóa 'questions', mỗi phần tử gồm "
            "'question', 'options' (A-D), 'correct_answer' và 'explanation'. "
            f"Số lượng câu hỏi: {num_questions}."
        )


def build_pipeline(settings: Settings | None = None) -> RagPipeline:
    settings = settings or get_settings()
    embedding_service = EmbeddingService(
        endpoint=settings.embed_api,
        max_length=settings.embed_max_length,
        timeout=settings.embed_timeout,
    )
    qdrant_service = QdrantService(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=settings.qdrant_collection,
        vector_size=settings.embedding_dimension,
    )
    llm_service = GeminiService(
        api_key=settings.gemini_api_key,
        api_url=settings.resolved_gemini_url,
    )
    mongo_service = MongoService(
        uri=settings.mongo_uri,
        db_name=settings.mongo_db_name,
        collection_name=settings.mongo_collection,
    )
    logger.info("RAG pipeline initialized with collection {}", settings.qdrant_collection)
    return RagPipeline(settings, embedding_service, qdrant_service, llm_service, mongo_service)
