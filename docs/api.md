## Sử Việt RAG API Reference

Backend base URL mặc định `http://127.0.0.1:8000`. Tất cả endpoint nhận/ trả JSON, chưa bật auth nên frontend chỉ cần gửi request với `Content-Type: application/json`. CORS domain chỉnh trong `.env` (`ALLOW_ORIGINS`).

### Health Check

| Method | Path    | Mô tả            |
| ------ | ------- | ---------------- |
| GET    | `/health` | Kiểm tra service |

**Response**

```json
{ "status": "ok" }
```

---

### 1. Hỏi đáp RAG

| Method | Path             | Mô tả                        |
| ------ | ---------------- | ---------------------------- |
| POST   | `/api/rag/query` | Sinh câu trả lời + nguồn cite |

**Request**

```json
{
  "question": "Vua Quang Trung sinh năm nào?"
}
```

**Response**

```json
{
  "answer": "Vua Quang Trung (Nguyễn Huệ) sinh năm 1753 tại Bình Định...",
  "sources": [
    {
      "id": "3d12...",
      "title": "Lịch sử Việt Nam - Wikipedia",
      "snippet": "Nguyễn Huệ, hay còn gọi là Quang Trung...",
      "score": 0.92,
      "metadata": { "title": "Lịch sử Việt Nam - Wikipedia" }
    }
  ],
  "trace_id": "6734d4b2..."
}
```

Hiển thị `sources[]` để người dùng thấy nguồn tham khảo.

---

### 2. Tóm tắt chủ đề

| Method | Path                 | Mô tả                      |
| ------ | -------------------- | -------------------------- |
| POST   | `/api/rag/summarize` | Tóm tắt theo mức độ chi tiết |

**Request**

```json
{
  "topic": "Nhà Trần",
  "detail_level": "medium" // short | medium | long
}
```

**Response**

```json
{
  "topic": "Nhà Trần",
  "summary": "Nhà Trần (1225-1400) nổi bật với 3 lần kháng chiến...",
  "sources": [ ... ],
  "trace_id": "..."
}
```

---

### 3. Timeline sự kiện

| Method | Path                | Mô tả                           |
| ------ | ------------------- | ------------------------------- |
| POST   | `/api/rag/timeline` | Trả về các mốc sự kiện theo thời gian |

**Request**

```json
{ "entity": "Quang Trung" }
```

**Response**

```json
{
  "entity": "Quang Trung",
  "events": [
    { "year": "1771", "title": "Khởi nghĩa Tây Sơn", "description": "..." },
    { "year": "1789", "title": "Chiến thắng Ngọc Hồi - Đống Đa", "description": "..." }
  ],
  "sources": [ ... ],
  "trace_id": "..."
}
```

---

### 4. Search context (không gọi LLM)

| Method | Path             | Mô tả                             |
| ------ | ---------------- | --------------------------------- |
| POST   | `/api/rag/search` | Chỉ trả về các đoạn văn liên quan |

**Request**

```json
{
  "query": "Ngọc Hồi",
  "top_k": 5
}
```

**Response**

```json
{
  "query": "Ngọc Hồi",
  "results": [
    {
      "id": "source-1",
      "title": "Tư liệu mẫu",
      "snippet": "Nội dung...",
      "score": 0.87,
      "metadata": { "title": "Tư liệu mẫu" }
    }
  ]
}
```

---

### 5. Ingest dữ liệu mới

| Method | Path             | Mô tả                              |
| ------ | ---------------- | ---------------------------------- |
| POST   | `/api/rag/ingest` | Cắt đoạn + embedding + lưu Qdrant |

**Request**

```json
{
  "title": "Việt sử lược",
  "content": "Nội dung dài...",
  "chunk_size": 800,
  "chunk_overlap": 120,
  "metadata": {
    "source": "wiki",
    "year": 1925
  }
}
```

**Response**

```json
{
  "title": "Việt sử lược",
  "chunks_ingested": 42
}
```

Nên bảo vệ endpoint này bằng auth/admin trước khi mở ra frontend.

---

### 6. Sinh câu hỏi trắc nghiệm (MCQ)

| Method | Path                  | Mô tả                         |
| ------ | --------------------- | ----------------------------- |
| POST   | `/api/mcq/generate`   | Tạo câu hỏi trắc nghiệm JSON |

**Request**

```json
{
  "context": "Quang Trung đại phá quân Thanh ... (>=50 ký tự)",
  "num_questions": 3
}
```

**Response**

```json
{
  "questions": [
    {
      "question": "Quang Trung đánh bại quân xâm lược nào?",
      "options": {
        "A": "Quân Minh",
        "B": "Quân Thanh",
        "C": "Quân Tống",
        "D": "Quân Nguyên"
      },
      "correct_answer": "B",
      "explanation": "Theo đoạn văn, ông đại phá quân Thanh.",
      "trace_id": "..."
    }
  ]
}
```

---

### Cách gọi từ frontend (fetch)

```ts
async function callQuery(question: string) {
  const res = await fetch("/api/rag/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error("Query failed");
  return res.json();
}
```

Tương tự cho các endpoint khác; chỉ cần thay body tương ứng. Dùng `trace_id` để hiển thị lịch sử hoặc debug (map tới Mongo `chat_logs`).*** End Patch*** End Patch
