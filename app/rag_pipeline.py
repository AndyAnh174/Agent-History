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
        try:
            vector = await self.embedding.embed_text(question)
            if not vector:
                raise ValueError("Failed to generate embedding")
            
            hits = self.qdrant.similarity_search(
                vector,
                limit=self.settings.rag_top_k,
                score_threshold=self.settings.rag_score_threshold,
            )
            context = self._format_context(hits)
            prompt = self._build_qa_prompt(question, context)
            # System instruction to limit scope to Vietnamese History
            system_instruction = (
                "Bạn là trợ lý AI chuyên về Lịch sử Việt Nam. "
                "Chỉ trả lời các câu hỏi liên quan đến Lịch sử Việt Nam. "
                "Nếu câu hỏi không liên quan, hãy nhẹ nhàng từ chối và hướng dẫn người dùng."
            )
            answer = await self.llm.generate_text(prompt, system_instruction=system_instruction)
            if not answer:
                raise ValueError("LLM returned empty response")
            
            sources = self._build_sources(hits)
            sources_payload = [source.__dict__ for source in sources]
            
            # Try to save log, but don't fail if MongoDB is unavailable
            trace_id = None
            try:
                trace_id = await self.mongo.save_chat_log(
                    question=question,
                    answer=answer,
                    sources=sources_payload,
                    kind="query",
                    metadata={"hits": len(hits)},
                )
            except Exception as e:
                logger.warning(f"Failed to save chat log: {e}")
            
            return {"answer": answer, "sources": sources_payload, "trace_id": trace_id}
        except Exception as e:
            logger.error(f"Error in answer_question: {e}", exc_info=True)
            raise

    async def summarize_topic(self, topic: str, detail_level: str = "medium") -> Dict[str, Any]:
        vector = await self.embedding.embed_text(topic)
        hits = self.qdrant.similarity_search(vector, limit=10)
        context = self._format_context(hits)
        prompt = self._build_summary_prompt(topic, context, detail_level)
        system_instruction = (
            "Bạn là trợ lý AI chuyên về Lịch sử Việt Nam. "
            "Chỉ tóm tắt các chủ đề liên quan đến Lịch sử Việt Nam."
        )
        summary = await self.llm.generate_text(prompt, system_instruction=system_instruction)
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
        system_instruction = (
            "Bạn là trợ lý AI chuyên về Lịch sử Việt Nam. "
            "Chỉ tạo timeline cho các nhân vật/sự kiện trong Lịch sử Việt Nam."
        )
        events = await self.llm.generate_json(prompt, system_instruction=system_instruction)
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

    async def generate_history_image(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a comic-style image about Vietnamese history.
        """
        try:
            image_data = await self.llm.generate_image(prompt)
            return {
                "image_url": image_data,
                "prompt": prompt,
            }
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}", exc_info=True)
            raise ValueError(f"Không thể tạo ảnh: {str(e)}")

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
            "Bạn là trợ lý AI chuyên về Lịch sử Việt Nam. "
            "Bạn có thể sử dụng cả kiến thức của chính bạn và các tư liệu được cung cấp dưới đây.\n\n"
            "**QUAN TRỌNG:** Chỉ trả lời các câu hỏi về Lịch sử Việt Nam. "
            "Nếu câu hỏi không liên quan đến Lịch sử Việt Nam, hãy nhẹ nhàng từ chối và hướng dẫn người dùng đặt câu hỏi về chủ đề này.\n\n"
            "**Tư liệu tham khảo từ cơ sở dữ liệu:**\n"
            f"{context}\n\n"
            f"**Câu hỏi:** {question}\n\n"
            "**Hướng dẫn trả lời:**\n"
            "1. Ưu tiên sử dụng thông tin từ tư liệu tham khảo ở trên (nếu có và liên quan)\n"
            "2. Nếu tư liệu không đủ, bạn có thể bổ sung bằng kiến thức của chính bạn về Lịch sử Việt Nam\n"
            "3. Trích dẫn nguồn theo dạng [số] khi dùng thông tin từ tư liệu\n"
            "4. Trả lời bằng tiếng Việt, thân thiện, chính xác và dễ hiểu\n"
            "5. Sử dụng markdown để format câu trả lời (headings, lists, bold, italic)\n"
            "6. Nếu không có thông tin đáng tin cậy, hãy nói rõ 'Tôi không có đủ dữ liệu để trả lời câu hỏi này.'"
        )

    def _build_summary_prompt(self, topic: str, context: str, detail_level: str) -> str:
        return (
            f"Bạn là trợ lý AI chuyên về Lịch sử Việt Nam. "
            f"Hãy tóm tắt về chủ đề '{topic}' (chỉ về Lịch sử Việt Nam).\n\n"
            f"**Tư liệu tham khảo:**\n{context}\n\n"
            f"**Yêu cầu:**\n"
            f"- Mức độ chi tiết: {detail_level}\n"
            f"- Ưu tiên thông tin từ tư liệu, có thể bổ sung bằng kiến thức của bạn về Lịch sử Việt Nam\n"
            f"- Trả lời bằng tiếng Việt, sử dụng markdown để format\n"
            f"- Liệt kê những điểm chính nếu phù hợp"
        )

    def _build_timeline_prompt(self, entity: str, context: str) -> str:
        return (
            f"Bạn là trợ lý AI chuyên về Lịch sử Việt Nam. "
            f"Tạo timeline các mốc sự kiện quan trọng liên quan tới '{entity}' trong Lịch sử Việt Nam.\n\n"
            f"**Tư liệu tham khảo:**\n{context}\n\n"
            f"**Yêu cầu:**\n"
            f"- Ưu tiên thông tin từ tư liệu, có thể bổ sung bằng kiến thức của bạn về Lịch sử Việt Nam\n"
            f"- Trả về JSON với cấu trúc {{\"events\": [{{\"year\": \"\", \"title\": \"\", \"description\": \"\"}}]}}\n"
            f"- Nếu không chắc chắn về năm tháng, hãy ghi rõ \"Không rõ\"\n"
            f"- Chỉ bao gồm các sự kiện liên quan đến Lịch sử Việt Nam"
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
        max_retries=settings.qdrant_max_retries,
        retry_delay=settings.qdrant_retry_delay,
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
