# Backend Integration Audit Report

**Purpose:** Verify backend implementation matches documented expectations for frontend integration.  
**Scope:** Read-only verification. No backend modifications.

---

## PHASE 1 — BACKEND ROUTE VALIDATION

### GET /health

| Aspect | Documented | Actual | Status |
|--------|------------|--------|--------|
| Route | `/health` | `@app.route("/health")` | MATCH |
| Method | GET | GET (default) | MATCH |
| Response | `{ status, server, model, mongodb }` | `{ status: "ok", server: "running", model: {...}, mongodb: {...} }` | MATCH |
| Status | 200 | 200 | MATCH |

**Notes:** Exact match. `model` includes `base_model`, `adapter_path`, `use_hf_repo`, `loaded`. `mongodb.uri` may be masked (portion after `@`).

**Frontend adjustments:** None.

---

### POST /api/upload

| Aspect | Documented | Actual | Status |
|--------|------------|--------|--------|
| Route | `/api/upload` | `@api.route("/upload", methods=["POST"])` | MATCH |
| Method | POST | POST | MATCH |
| Input | multipart/form-data, field `file` | `request.files.get("file")` | MATCH |
| Success response | `{ paper_id, status, data: {...} }` | Same structure | MATCH |
| 400 error | `{ error: "no file" }` | `jsonify({"error": "no file"}), 400` | MATCH |
| 500 error | `{ error: "<message>" }` | `jsonify({"error": str(e)}), 500` | MATCH |

**Notes:** Exact match. No file extension validation; non-PDF uploads fail during processing with 500.

**Frontend adjustments:** None. Frontend already validates `.pdf` client-side.

---

### GET /api/summarize/<paper_id>

| Aspect | Documented | Actual | Status |
|--------|------------|--------|--------|
| Route | `/api/summarize/<paper_id>` | `@api.route("/summarize/<paper_id>", methods=["GET"])` | MATCH |
| Method | GET | GET | MATCH |
| Success response | `{ paper_id, summary }` | Same | MATCH |
| 404 error | `{ error: "paper not found" }` | `jsonify({"error": "paper not found"}), 404` | MATCH |
| 500 error | `{ error: "<message>" }` | `jsonify({"error": str(e)}), 500` | MATCH |

**Notes:** Exact match.

**Frontend adjustments:** None.

---

### POST /api/qa/<paper_id>

| Aspect | Documented | Actual | Status |
|--------|------------|--------|--------|
| Route | `/api/qa/<paper_id>` | `@api.route("/qa/<paper_id>", methods=["POST"])` | MATCH |
| Method | POST | POST | MATCH |
| Input | `{ question: string }` JSON | `request.get_json() or {}`; `payload.get("question")` | MATCH |
| Success response | `{ paper_id, question, answer, num_chunks_used }` | Same | MATCH |
| 400 error | `{ error: "question required" }` | `jsonify({"error": "question required"}), 400` | MATCH |
| 500 error | `{ error: "<message>" }` | `jsonify({"error": str(e)}), 500` | MATCH |

**Notes:** Exact match. Empty string `question` triggers 400.

**Frontend adjustments:** None.

---

### GET /api/flowchart/<paper_id>

| Aspect | Documented | Actual | Status |
|--------|------------|--------|--------|
| Route | `/api/flowchart/<paper_id>` | `@api.route("/flowchart/<paper_id>", methods=["GET"])` | MATCH |
| Method | GET | GET | MATCH |
| Success response | SVG binary, `image/svg+xml` | `send_file(..., mimetype='image/svg+xml')` | MATCH |
| 500 error | JSON `{ error: "..." }` | `jsonify({"error": str(e)}), 500` | MATCH |

**Notes:** Match. Unknown `paper_id` returns 200 with fallback SVG ("Key terms could not be extracted") rather than 404.

**Frontend adjustments:** None. Treat unknown paper flowchart as valid SVG.

---

## PHASE 2 — RESPONSE SCHEMA CONFIRMATION

### /api/upload response

| Field | Documented | Actual | Status |
|-------|------------|--------|--------|
| `paper_id` | string (UUID) | `str(uuid.uuid4())` | MATCH |
| `status` | `"success"` | `"success"` | MATCH |
| `data.filename` | string | `paper_data['filename']` | MATCH |
| `data.word_count` | number | `paper_data['word_count']` | MATCH |
| `data.page_count` | number | `paper_data['page_count']` | MATCH |
| `data.sections` | array of strings | `list(paper_data['sections'].keys())` | MATCH |
| `data.metadata` | object | `metadata` from `extract_metadata()` | MATCH |

### metadata structure

| Field | Documented | Actual | Status |
|-------|------------|--------|--------|
| `metadata` | `{ title?, authors?, abstract?, keywords?, publication_date? }` | LLM JSON with keys: title, authors, abstract, keywords, publication_date | MATCH |
| `metadata.keywords` exists? | Yes (optional) | Yes, from prompt | MATCH |
| `metadata.keywords` type | string or array | **Unspecified** — model returns JSON; can be string, array, or omitted | PARTIAL |
| `metadata.keywords` null? | Possible | Possible if model omits or parsing fails | MATCH |

**Frontend adaptation:** Normalize `keywords` for both string and array. Handle `undefined`/`null`. Current frontend `normalizeKeywords()` already does this.

---

### /api/summarize response

| Field | Documented | Actual | Status |
|-------|------------|--------|--------|
| `paper_id` | string | string | MATCH |
| `summary` | string | string | MATCH |

**Frontend adaptation:** None.

---

### /api/qa response

| Field | Documented | Actual | Status |
|-------|------------|--------|--------|
| `paper_id` | string | string | MATCH |
| `question` | string | string | MATCH |
| `answer` | string | string | MATCH |
| `num_chunks_used` | number | `result['num_chunks']` | MATCH |

**Frontend adaptation:** None.

---

### /api/flowchart response

| Scenario | Documented | Actual | Status |
|----------|------------|--------|--------|
| Success | `image/svg+xml` binary | `send_file(..., mimetype='image/svg+xml')` | MATCH |
| Failure (500) | JSON `{ error: "..." }` | `jsonify({"error": str(e)}), 500` | MATCH |

**Frontend adaptation:** Use `res.blob()` on success; on `!res.ok`, parse JSON for `error`. Current implementation is correct.

---

## PHASE 3 — CORS & NETWORK VALIDATION

### CORS

| Aspect | Documented | Actual | Status |
|--------|------------|--------|--------|
| CORS enabled | Yes | `CORS(app)` (flask_cors) | MATCH |
| Origin behavior | Allow frontend | Default: allow all origins | MATCH |

**Notes:** `CORS(app)` with no args allows all origins. No auth middleware found.

### Port

| Aspect | Documented | Actual | Status |
|--------|------------|--------|--------|
| Default port | 2750 | `os.getenv("FLASK_PORT", "2750")` | MATCH |

### Auth

| Aspect | Documented | Actual | Status |
|--------|------------|--------|--------|
| Auth middleware | None | None found | MATCH |

**Frontend adaptation:** No credentials needed. Use default `fetch` (no `credentials: 'include'` unless required).

---

## PHASE 4 — UPLOAD COMPATIBILITY CHECK

| Aspect | Documented | Actual | Status |
|--------|------------|--------|--------|
| Content-Type | multipart/form-data | Implicit via `request.files` | MATCH |
| Field name | `file` | `request.files.get("file")` | MATCH |
| File extension validation | Not specified | None — any file accepted | MATCH |
| Storage path | `STORAGE_PATH` (default `./storage`) | `config.STORAGE_PATH` | MATCH |
| Naming | `{paper_id}.pdf` | `pdf_path = storage_path / f"{paper_id}.pdf"` | MATCH |

**Notes:** Non-PDF files cause 500 during `pdf_processor.process_pdf()` (e.g. pdfplumber/PyPDF2 errors). Frontend should restrict to `.pdf` before upload.

**Frontend adaptation:** Keep client-side PDF validation. Use `FormData` with `file` field. No extra headers beyond default `multipart/form-data` boundary.

---

## PHASE 5 — FLOWCHART FRONTEND HANDLING NOTES

### GPU memory

| Aspect | Documented | Actual | Status |
|--------|------------|--------|--------|
| Clear before | Yes | `torch.cuda.empty_cache()` before generation | MATCH |
| Clear after | Yes | `torch.cuda.empty_cache()` after (success and error) | MATCH |

### Error handling

| Aspect | Documented | Actual | Status |
|--------|------------|--------|--------|
| Error format | JSON `{ error: "..." }` | `jsonify({"error": str(e)}), 500` | MATCH |

### Response handling

| Aspect | Frontend action |
|--------|-----------------|
| Success | Use `res.blob()` — response is binary SVG |
| Failure | Check `!res.ok`, then `res.json()` for `error` |
| Content-Type | Success: `image/svg+xml`; failure: `application/json` |

**Notes:** Flowchart can be slow for long papers. Frontend should show loading state and handle timeouts. OOM errors often include "memory", "cuda", or "gpu" in the message.

---

## PHASE 6 — FINAL FRONTEND INTEGRATION CHECKLIST

Based on the backend audit:

### Base URL

- [ ] Use `NEXT_PUBLIC_API_BASE_URL` or default `http://localhost:2750`
- [ ] Ensure backend is running before frontend calls

### Fetch settings

- [ ] **Upload:** `method: "POST"`, `body: FormData`, no `Content-Type` header (browser sets multipart boundary)
- [ ] **QA:** `method: "POST"`, `headers: { "Content-Type": "application/json" }`, `body: JSON.stringify({ question })`
- [ ] **Summary, Flowchart, Health:** `method: "GET"`, no special headers
- [ ] **Credentials:** Do not use `credentials: 'include'` unless backend adds auth

### Error handling

- [ ] All error responses: `{ error: string }` with 4xx/5xx status
- [ ] On non-OK: `const data = await res.json().catch(() => ({})); throw new Error(data.error || "Request failed");`
- [ ] Flowchart: on 500, parse JSON for `error`; show retry for memory-related messages

### Data normalization

- [ ] **metadata.keywords:** Support string (comma/semicolon-separated) and array; handle `null`/`undefined`
- [ ] Example: `Array.isArray(kw) ? kw : (typeof kw === "string" ? kw.split(/[,;]/).map(s => s.trim()) : [])`

### SVG rendering

- [ ] On success: `const blob = await res.blob(); const url = URL.createObjectURL(blob);`
- [ ] Render via `<img src={url} />` or inline SVG (parse blob as text)
- [ ] Revoke object URL on unmount or when paper changes

### Large response delays

- [ ] Flowchart: show loading spinner; consider 60–120s timeout for long papers
- [ ] Upload: show progress; 60s timeout typical
- [ ] Summary/QA: 30s timeout typical

### Edge cases

- [ ] Flowchart for unknown `paper_id`: backend returns 200 with fallback SVG; treat as valid
- [ ] Empty `question` in QA: backend returns 400
- [ ] Missing `file` in upload: backend returns 400

---

## Summary

| Phase | Result |
|-------|--------|
| Route validation | All 5 routes MATCH |
| Response schema | MATCH; `metadata.keywords` type varies (string/array) — frontend must normalize |
| CORS & network | CORS enabled; port 2750; no auth |
| Upload | Field `file`, multipart/form-data; no extension check |
| Flowchart | GPU cleared; JSON on error; treat response as Blob on success |

**Conclusion:** Backend matches documentation. Frontend integration assumptions are valid. Only required adaptation: normalize `metadata.keywords` (string vs array); current frontend already does this.
