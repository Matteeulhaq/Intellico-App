# BACKEND OVERVIEW (FOR FRONTEND INTEGRATION)

## Endpoint Table

| Route | Method | Purpose | Input | Output | Common Errors |
|-------|--------|---------|-------|--------|---------------|
| `/health` | GET | Health check, model status | — | `{ status, server, model: { base_model, adapter_path, use_hf_repo, loaded }, mongodb }` | — |
| `/api/upload` | POST | Upload and process PDF | `multipart/form-data`, field `file` (PDF) | `{ paper_id, status: "success", data: { filename, word_count, page_count, sections, metadata } }` | 400: `{ error: "no file" }`, 500: `{ error: "<message>" }` |
| `/api/summarize/<paper_id>` | GET | Get paper summary | — | `{ paper_id, summary }` | 404: `{ error: "paper not found" }`, 500: `{ error: "<message>" }` |
| `/api/qa/<paper_id>` | POST | RAG-based Q&A | `{ question: string }` (JSON) | `{ paper_id, question, answer, num_chunks_used }` | 400: `{ error: "question required" }`, 500: `{ error: "<message>" }` |
| `/api/flowchart/<paper_id>` | GET | Generate concept flowchart | — | SVG binary (`image/svg+xml`) | 500: `{ error: "<message>" }` (JSON on error) |

## Data Model

- **paper_id**: UUID string, returned from upload. Used for all paper-specific endpoints.
- **Upload response metadata**: `{ title?, authors?, abstract?, keywords?, publication_date? }` — extracted by model from paper text.
- **Papers collection** (MongoDB): `paper_id`, `title`, `author`, `word_count`, `page_count`. No list endpoint exposed.

## Constraints

- **File storage**: PDFs saved to `STORAGE_PATH` (default `./storage`) as `{paper_id}.pdf`.
- **Summary**: Single summary; no `short`/`medium`/`detailed` parameter. Summary uses abstract or first ~1000 chars, model generates ~256 tokens.
- **Flowchart**: Returns raw SVG bytes. GPU memory cleared before/after; long papers may cause OOM — show graceful error and suggest shorter paper or retry.
- **Keywords / relationships**: No dedicated endpoint. Keywords come from upload `data.metadata.keywords`. Relationships are only visualized in the flowchart SVG.
- **List papers**: No backend endpoint. Frontend must persist history locally (e.g. localStorage).

## Assumptions

- `metadata.keywords` from upload may be a string (comma-separated) or array depending on model output; frontend should normalize.
- Flowchart error responses are JSON `{ error: "..." }` when status is 500.
- Default backend port: 2750 (from `FLASK_PORT`).
