Rất chuẩn luôn 🔥
Dưới đây là bản **PROMPT BACKEND HOÀN CHỈNH – FINAL** (phiên bản chi tiết nhất) mà bạn có thể **dán thẳng vào Codex hoặc Claude Code** để nó generate code backend đầy đủ (FastAPI + LangChain + LlamaIndex + Qdrant + MongoDB + Gemini 2.0 Flash).

Mình đã **viết cực kỹ** phần hướng dẫn dùng API **BGE-M3** (endpoint của bạn `https://embed.andyanh.id.vn/embed`), bao gồm cú pháp, headers, request, response, và cách xử lý lỗi.

---

# 🚀 PROMPT BACKEND HOÀN CHỈNH (FastAPI + LangChain + LlamaIndex + Qdrant + MongoDB + Gemini + BGE-M3 API)

---

## 🎯 Mục tiêu dự án

Tạo một **backend Python** cho **AI Agent Lịch Sử Việt Nam** (Sử Việt RAG Agent) có thể:

1. Nhận câu hỏi từ người dùng (`POST /query`)
2. Sinh **embedding bằng API BGE-M3** (qua HTTP)
3. Dùng embedding để **tìm ngữ cảnh** trong **Qdrant Vector DB**
4. Dùng **Gemini 2.0 Flash API** để sinh câu trả lời từ ngữ cảnh đó
5. Lưu lịch sử hội thoại và metadata vào **MongoDB**

---

## ⚙️ Công nghệ chính

| Thành phần      | Công cụ                                              |
| --------------- | ---------------------------------------------------- |
| Framework       | FastAPI                                              |
| RAG Framework   | LangChain + LlamaIndex                               |
| Embedding       | **BGE-M3 API** (`https://embed.andyanh.id.vn/embed`) |
| Vector Database | Qdrant                                               |
| LLM             | Gemini 2.0 Flash API                                 |
| Storage         | MongoDB (motor/pymongo)                              |
| Env Config      | python-dotenv hoặc pydantic_settings                 |

---

## 📁 Cấu trúc thư mục đề xuất

```
/app
├── main.py
├── config.py
├── rag_pipeline.py
├── routers/
│   └── query.py
├── services/
│   ├── embedding_service.py
│   ├── qdrant_service.py
│   ├── llm_service.py
│   └── mongo_service.py
└── utils/
    └── text_splitter.py
```

---

## 🧩 Chức năng chi tiết

### 1️⃣ `/query` Endpoint (Nâng cấp)

**Mục tiêu:** nhận câu hỏi người dùng → trả về câu trả lời có trích nguồn **chi tiết**.

**Input:**

```json
{
  "question": "Vua Quang Trung sinh năm nào?"
}
```

**Output (Nâng cấp với "Minh bạch nguồn trích dẫn"):**

```json
{
  "answer": "Vua Quang Trung (Nguyễn Huệ) sinh năm 1753 tại Bình Định...",
  "sources": [
    {
      "source_name": "Lịch sử Việt Nam - Wikipedia",
      "content": "Nguyễn Huệ, hay còn gọi là Quang Trung hoàng đế, sinh năm Quý Dậu (1753), là con thứ ba của ông Nguyễn Phi Phúc và bà Nguyễn Thị Đồng."
    }
  ]
}
```

**Pipeline xử lý:**

1.  Nhận câu hỏi người dùng.
2.  Gọi API **BGE-M3** để tạo embedding.
3.  Tìm `top_k` đoạn liên quan trong **Qdrant**.
4.  Gộp các đoạn đó thành context.
5.  Gửi prompt (context + câu hỏi) tới **Gemini 2.0 Flash API**.
6.  Nhận phản hồi, **trích xuất các đoạn context đã dùng**, và lưu kết quả vào **MongoDB**.

---

### 2️⃣ (Mới) Endpoint `/summarize`

**Mục tiêu:** Tóm tắt tổng quan về một chủ đề lịch sử.

**Input:**

```json
{
  "topic": "Nhà Trần",
  "detail_level": "medium"
}
```

**Output:**

```json
{
  "topic": "Nhà Trần",
  "summary": "Nhà Trần (1225 – 1400) là một triều đại quân chủ trong lịch sử Việt Nam, nổi bật với ba lần chiến thắng quân xâm lược Nguyên Mông. Triều đại này được thành lập khi Trần Cảnh lên ngôi sau khi được Lý Chiêu Hoàng nhường ngôi. Dưới thời Trần, kinh tế nông nghiệp và thương nghiệp phát triển, văn hóa và giáo dục cũng có nhiều thành tựu, với sự ra đời của chữ Nôm và các tác phẩm văn học nổi tiếng..."
}
```

**Pipeline xử lý:**

1.  Nhận `topic` từ request.
2.  Tạo embedding cho `topic`.
3.  Tìm kiếm `top_k` (ví dụ k=10) văn bản liên quan trong Qdrant.
4.  Gửi toàn bộ context thu thập được cho Gemini với prompt chuyên để **tóm tắt**.

---

### 3️⃣ (Mới) Endpoint `/timeline`

**Mục tiêu:** Tạo dòng thời gian các sự kiện chính của một nhân vật hoặc triều đại.

**Input:**

```json
{
  "entity": "Vua Quang Trung"
}
```

**Output:**

```json
{
  "entity": "Vua Quang Trung",
  "timeline": [
    { "year": 1753, "event": "Năm sinh của Nguyễn Huệ tại Bình Định." },
    { "year": 1771, "event": "Anh em Tây Sơn khởi nghĩa." },
    { "year": 1789, "event": "Đại phá quân Thanh, lên ngôi hoàng đế với niên hiệu Quang Trung." },
    { "year": 1792, "event": "Hoàng đế Quang Trung đột ngột băng hà." }
  ]
}
```

**Pipeline xử lý:**

1.  Nhận `entity` từ request.
2.  Tìm kiếm các văn bản liên quan trong Qdrant.
3.  Gửi context cho Gemini với prompt yêu cầu **trích xuất và sắp xếp các sự kiện theo mốc thời gian** và trả về dưới dạng JSON.

---

### 4️⃣ (Mới) Endpoint `/generate-mcq`

**Mục tiêu:** Nhận một đoạn văn bản (context) và sinh ra các câu hỏi trắc nghiệm (MCQ).

**Input:**

```json
{
  "context": "Trần Hưng Đạo, tên thật là Trần Quốc Tuấn, là một nhà chính trị, nhà quân sự, tôn thất hoàng gia Đại Việt thời Trần...",
  "num_questions": 1
}
```

**Output:**

```json
{
  "questions": [
    {
      "question": "Trần Hưng Đạo đã chỉ huy quân đội Đại Việt chống lại quân xâm lược nào?",
      "options": { "A": "Quân Thanh", "B": "Quân Nguyên Mông", "C": "Quân Minh", "D": "Quân Tống" },
      "correct_answer": "B",
      "explanation": "Dựa vào văn bản, Trần Hưng Đạo được biết đến với vai trò chỉ huy quân đội Đại Việt ba lần đẩy lùi quân xâm lược Nguyên Mông."
    }
  ]
}
```

---

## ⚡ Cách dùng API BGE-M3 (rất quan trọng)

### 🧠 Endpoint:

```
POST https://embed.andyanh.id.vn/embed
```

### 🧾 Headers:

```http
accept: application/json
Content-Type: application/json
```

### 📤 Request body:

```json
{
  "texts": ["Xin chào, tôi là AI lịch sử Việt Nam"],
  "max_length": 512
}
```

* `texts`: danh sách (mảng) chuỗi cần embedding.
* `max_length`: giới hạn token, mặc định 512.

### 📥 Response mẫu:

```json
{
  "embeddings": [
    [0.123, -0.234, 0.111, ...]
  ],
  "device": "cuda:0",
  "model_info": {
    "model_name": "BAAI/bge-m3",
    "max_length": 512,
    "truncate_dim": null
  }
}
```

### ✅ Cách gọi bằng Python:

```python
import requests

def get_bge_embedding(text: str):
    url = "https://embed.andyanh.id.vn/embed"
    payload = {
        "texts": [text],
        "max_length": 512
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=30)
        res.raise_for_status()
        data = res.json()
        return data["embeddings"][0]
    except Exception as e:
        print("Embedding API error:", e)
        return None
```

**Ghi chú:**

* Độ dài vector (embedding dimension) thường là **1024** hoặc **1536**, nên Qdrant phải tạo collection có `vector_size` tương ứng.
* Khi lỗi API, trả về `None` hoặc raise exception.

---

## 🧱 Tích hợp vào pipeline RAG

### 2️⃣ Qdrant Service

* Collection: `vietnam_history`
* Vector size: **theo embedding API trả về**
* Sử dụng cosine similarity:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

client = QdrantClient(url="http://localhost:6333")

client.recreate_collection(
    collection_name="vietnam_history",
    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
)
```

**Search:**

```python
hits = client.search(
    collection_name="vietnam_history",
    query_vector=embedding,
    limit=5
)
```

---

### 3️⃣ Gemini 2.0 Flash API Integration

**Endpoint:**

```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
```

**Headers:**

```
Authorization: Bearer <GEMINI_API_KEY>
Content-Type: application/json
```

**Body:**

```json
{
  "contents": [{
    "parts": [{ "text": "Dưới đây là tài liệu lịch sử Việt Nam...\nCâu hỏi: ..." }]
  }]
}
```

**Response Example:**

```json
{
  "candidates": [{
    "content": {
      "parts": [{ "text": "Lý Công Uẩn là người sáng lập nhà Lý..." }]
    }
  }]
}
```

---

### 4️⃣ MongoDB Service

Lưu log hội thoại:

```json
{
  "question": "Vua Quang Trung sinh năm nào?",
  "answer": "1753",
  "sources": ["wiki_quangtrung.txt"],
  "created_at": "2025-11-10T15:30:00Z"
}
```

Dùng `motor.AsyncIOMotorClient`:

```python
from motor.motor_asyncio import AsyncIOMotorClient

mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["vietnam_history"]
logs = db["chat_logs"]
```

---

### 5️⃣ Prompt RAG cho Gemini

```python
prompt = f"""
Dưới đây là một số tư liệu lịch sử Việt Nam:

{context}

Câu hỏi: {question}

Hãy trả lời bằng tiếng Việt, ngắn gọn, chính xác và có dẫn nguồn.
Nếu không chắc chắn, hãy nói "Tôi không có đủ dữ liệu để trả lời."
"""
```

---

## 🔐 File `.env` ví dụ

```
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_key
MONGO_URI=mongodb+srv://user:pass@cluster/db
GEMINI_API_KEY=your_gemini_key
EMBED_API=https://embed.andyanh.id.vn/embed
```

---

## 🧪 Chạy thử

**Cài dependencies:**

```bash
pip install fastapi uvicorn requests langchain llama-index qdrant-client motor python-dotenv
```

**Chạy app:**

```bash
uvicorn app.main:app --reload
```

**Test API:**

* Mở: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Gửi POST `/query`:

  ```json
  { "question": "Chiến thắng Bạch Đằng diễn ra năm nào?" }
  ```

---

## 💡 Tùy chọn mở rộng

* `/ingest`: nạp dữ liệu mới vào Qdrant
* `/search`: chỉ truy xuất context không gọi LLM
* Logging bằng `loguru`
*   Tạo `Dockerfile` và `requirements.txt`

---

## 🌟 (Mới) Chức năng sinh câu hỏi trắc nghiệm (MCQ)

### 1️⃣ Endpoint `/generate-mcq`

**Mục tiêu:** Nhận một đoạn văn bản (context) và sinh ra một danh sách các câu hỏi trắc nghiệm (Multiple-Choice Questions) liên quan, kèm theo đáp án và giải thích.

**Input:**

```json
{
  "context": "Trần Hưng Đạo, tên thật là Trần Quốc Tuấn, là một nhà chính trị, nhà quân sự, tôn thất hoàng gia Đại Việt thời Trần. Ông được biết đến trong lịch sử Việt Nam với vai trò là người chỉ huy quân đội Đại Việt ba lần đẩy lùi quân xâm lược Nguyên Mông vào thế kỷ 13.",
  "num_questions": 1
}
```

**Output:**

```json
{
  "questions": [
    {
      "question": "Trần Hưng Đạo đã chỉ huy quân đội Đại Việt chống lại quân xâm lược nào?",
      "options": {
        "A": "Quân Thanh",
        "B": "Quân Nguyên Mông",
        "C": "Quân Minh",
        "D": "Quân Tống"
      },
      "correct_answer": "B",
      "explanation": "Dựa vào văn bản, Trần Hưng Đạo được biết đến với vai trò chỉ huy quân đội Đại Việt ba lần đẩy lùi quân xâm lược Nguyên Mông."
    }
  ]
}
```

**Pipeline xử lý:**

1.  Nhận `context` và `num_questions` từ request.
2.  Tạo một prompt chuyên dụng để yêu cầu Gemini sinh câu hỏi trắc nghiệm theo định dạng JSON.
3.  Gọi **Gemini 2.0 Flash API**.
4.  Xử lý (parse JSON) và trả về danh sách câu hỏi.

### 2️⃣ Cập nhật cấu trúc thư mục

Để tích hợp endpoint mới, chúng ta sẽ thêm một file router:

```
/app
├── ...
├── routers/
│   ├── query.py
│   └── **mcq_generator.py**  <-- File mới
└── ...
```

### 3️⃣ Prompt cho Gemini để sinh câu hỏi trắc nghiệm

```python
prompt = f"""
Dựa vào đoạn văn bản sau đây:

---
{context}
---

Hãy tạo ra chính xác {num_questions} câu hỏi trắc nghiệm (MCQ) về nội dung của đoạn văn bản trên.

YÊU CẦU ĐỊNH DẠNG OUTPUT:
- Trả về một JSON object duy nhất.
- JSON object đó phải có một key là "questions".
- Value của "questions" là một mảng (array) các object câu hỏi.
- Mỗi object câu hỏi phải có các key sau:
  - "question": (string) Nội dung câu hỏi.
  - "options": (object) Gồm 4 lựa chọn A, B, C, D.
  - "correct_answer": (string) Chỉ ghi chữ cái của đáp án đúng (A, B, C, hoặc D).
  - "explanation": (string) Giải thích ngắn gọn tại sao đáp án đó đúng, dựa vào context.
"""
```

---

✅ **Output kỳ vọng:**
Một **backend FastAPI hoàn chỉnh** có thể:
*   Nhận câu hỏi → gọi BGE-M3 API → search Qdrant → gọi Gemini 2.0 → trả kết quả
*   Lưu lịch sử vào MongoDB
*   Cấu trúc module rõ ràng, dễ mở rộng.
*   **(Mới)** Nhận một đoạn văn bản và tự động tạo ra các câu hỏi trắc nghiệm kèm đáp án.

---

Bạn có muốn mình viết **prompt riêng cho module `/ingest`** (để nạp tài liệu PDF/text vào Qdrant) không?
Nếu bạn định cho agent “học” từ các tài liệu lịch sử Việt Nam thật thì đó là bước cần thiết để hoàn thiện pipeline RAG.
