from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.dependencies import get_pipeline
from app.main import create_app


class DummyPipeline:
    """In-memory pipeline stub used to test the API contract without external services."""

    def __init__(self) -> None:
        self.source = {
            "id": "source-1",
            "title": "Tư liệu mẫu",
            "snippet": "Nội dung trích đoạn minh họa.",
            "score": 0.98,
            "metadata": {"title": "Tư liệu mẫu"},
        }

    async def answer_question(self, question: str):
        return {
            "answer": f"Fake answer for: {question}",
            "sources": [self.source],
            "trace_id": "trace-query",
        }

    async def summarize_topic(self, topic: str, detail_level: str):
        return {
            "topic": topic,
            "summary": f"Tóm tắt ({detail_level}) cho {topic}.",
            "sources": [self.source],
            "trace_id": "trace-summary",
        }

    async def build_timeline(self, entity: str):
        return {
            "entity": entity,
            "events": [{"year": "1789", "title": "Chiến thắng", "description": "Chiến thắng Ngọc Hồi - Đống Đa."}],
            "sources": [self.source],
            "trace_id": "trace-timeline",
        }

    async def search_context(self, query: str, top_k: int | None = None):
        return {"query": query, "results": [self.source]}

    async def ingest_text(self, title: str, content: str, chunk_size: int, chunk_overlap: int, extra_metadata=None):
        return {"title": title, "chunks_ingested": 1}

    async def generate_mcq(self, context: str, num_questions: int = 3):
        return {
            "questions": [
                {
                    "question": "Nhân vật nào được nhắc tới trong đoạn văn?",
                    "options": {"A": "Lý Thường Kiệt", "B": "Quang Trung", "C": "Trần Hưng Đạo", "D": "Lê Lợi"},
                    "correct_answer": "B",
                    "explanation": "Quang Trung xuất hiện trong context.",
                }
            ],
            "trace_id": "trace-mcq",
        }


@pytest.fixture(name="client")
def client_fixture():
    app = create_app()
    app.router.on_startup.clear()
    app.router.on_shutdown.clear()

    dummy_pipeline = DummyPipeline()
    app.state.pipeline = dummy_pipeline
    app.dependency_overrides[get_pipeline] = lambda: dummy_pipeline

    with TestClient(app) as client:
        yield client


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_query_endpoint_returns_sources(client: TestClient):
    payload = {"question": "Vua Quang Trung là ai?"}
    response = client.post("/api/rag/query", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert "Fake answer" in body["answer"]
    assert len(body["sources"]) == 1


def test_summarize_endpoint_includes_trace_id(client: TestClient):
    payload = {"topic": "Nhà Trần", "detail_level": "short"}
    response = client.post("/api/rag/summarize", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["topic"] == "Nhà Trần"
    assert body["trace_id"] == "trace-summary"


def test_timeline_endpoint_returns_events(client: TestClient):
    payload = {"entity": "Quang Trung"}
    response = client.post("/api/rag/timeline", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert len(body["events"]) == 1
    assert body["events"][0]["year"] == "1789"


def test_search_endpoint_returns_results(client: TestClient):
    payload = {"query": "Ngọc Hồi", "top_k": 2}
    response = client.post("/api/rag/search", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["query"] == "Ngọc Hồi"
    assert len(body["results"]) == 1


def test_ingest_endpoint_accepts_metadata(client: TestClient):
    payload = {
        "title": "Việt sử lược",
        "content": "Nội dung giả lập để test ingestion.",
        "metadata": {"source": "test-suite"},
    }
    response = client.post("/api/rag/ingest", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["chunks_ingested"] == 1
    assert body["title"] == payload["title"]


def test_generate_mcq_endpoint_returns_questions(client: TestClient):
    payload = {
        "context": "Quang Trung đại phá quân Thanh và củng cố triều Tây Sơn, để lại dấu ấn lớn trong lịch sử.",
        "num_questions": 1,
    }
    response = client.post("/api/mcq/generate", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert len(body["questions"]) == 1
    assert body["trace_id"] == "trace-mcq"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
