## Sử Việt RAG Agent Backend

FastAPI backend that powers an AI agent for Vietnamese history. The service wires together BGE-M3 embeddings (HTTP API), Qdrant vector search, Gemini 2.0 Flash generation, and MongoDB chat logging. Extra endpoints provide summarisation, timeline generation, MCQ authoring, raw vector search, and document ingestion.

### 1. Requirements

- Python 3.11+
- Docker (optional) to run the provided `docker-compose.yml` for MongoDB + Qdrant
- Access tokens:
  - `GEMINI_API_KEY` for Gemini 2.0 Flash
  - If Qdrant is secured, set `QDRANT_API_KEY`
- External embedding endpoint: `https://embed.andyanh.id.vn/embed`

### 2. Installation

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# update .env with real secrets
```

#### Docker (quick start)

```bash
cp .env.example .env  # edit GEMINI_API_KEY at minimum
docker compose up --build -d
```

Services exposed:

- `http://localhost` → Nginx proxy (serves UI and API under `/api`)
- `http://localhost:6334` → Qdrant dashboard
- `mongo://localhost:27017` → MongoDB (mapped only if you publish ports)

Start infrastructure:

```bash
docker-compose up -d
```

### 3. Run the API

```bash
uvicorn app.main:app --reload
```

Interactive docs live at `http://127.0.0.1:8000/docs`.

### 4. Key Environment Variables

| Variable | Description |
| --- | --- |
| `EMBED_API` | BGE-M3 embedding endpoint |
| `QDRANT_URL` / `QDRANT_API_KEY` | Vector database connection |
| `MONGO_URI` | MongoDB connection string (match docker-compose credentials) |
| `GEMINI_API_KEY` | Google Generative Language API token |
| `RAG_TOP_K` / `RAG_SCORE_THRESHOLD` | Retrieval tuning knobs |

See `.env.example` for the full list plus sensible defaults.

### 5. API Surface

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/rag/query` | POST | Full RAG answer with cited sources |
| `/api/rag/summarize` | POST | Topic level summary |
| `/api/rag/timeline` | POST | Chronological events extracted from context |
| `/api/rag/search` | POST | Retrieve raw context chunks (no LLM) |
| `/api/rag/ingest` | POST | Chunk + embed + store new texts |
| `/api/mcq/generate` | POST | Create MCQs (JSON) from supplied context |
| `/health` | GET | Service heartbeat |

### 6. Workflow Notes

1. Ingestion uses LangChain's `RecursiveCharacterTextSplitter` then stores the resulting chunks + metadata in Qdrant. A light usage of LlamaIndex' `Document` object keeps compatibility with future agent features.
2. Queries call the external BGE-M3 API, search Qdrant, craft a Gemini prompt (with citations), and persist logs to MongoDB for analytics.
3. Timeline and MCQ endpoints request JSON-formatted output from Gemini; the router parses and returns structured objects.

### 7. Testing Ideas

- Use `/api/rag/ingest` with a short passage before querying to verify the full loop.
- Hit `/api/mcq/generate` with your own context to validate JSON parsing.
- Monitor MongoDB collection `vietnam_history.chat_logs` to inspect saved transcripts.

### 8. Automated Tests

The `tests/` folder contains FastAPI integration tests that stub the pipeline so no external services are required.

```bash
pytest
```
