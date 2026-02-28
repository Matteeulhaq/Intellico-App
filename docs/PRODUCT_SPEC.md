# Intellico Frontend — Product Spec

## User Flows

### A) Upload paper → processing state → results page

1. User drags/drops or selects a PDF.
2. UI shows file name, size, and progress spinner.
3. On success: paper added to history, user navigated to paper workspace.
4. On error: toast with message and retry option.

### B) Summary modes (short/medium/detailed) + copy/export

- Backend returns a single summary; no length parameter.
- UI provides Short / Medium / Detailed via truncation (first 2, 4, or all sentences).
- "(UI truncated)" label when truncated.
- Copy button copies full summary to clipboard.

### C) Chat-style Q&A grounded in the uploaded paper

- Chat bubbles (user right, assistant left).
- "Sources" collapsible shows `num_chunks_used` from backend.
- Typing indicator while waiting for answer.
- Non-streaming: full answer after response.

### D) Keywords + glossary + relationship view

- Keywords from upload `metadata.keywords` (normalized).
- Search/filter.
- Relationships: no dedicated API; Flowchart tab shows concept flow.
- Keywords tab: list of keywords + note that relationships are in Flowchart.

### E) Flowchart view (render SVG) + download

- SVG from `/api/flowchart/<paper_id>` rendered in container.
- Download SVG button.
- On memory/OOM: graceful message and retry suggestion.

### F) History sidebar of uploaded papers

- Persisted locally via Zustand (`localStorage`).
- No backend list endpoint; history is client-only.
- New Upload button to add more papers.

## States

- **Loading**: Spinners for upload, summary, flowchart, Q&A.
- **Empty**: "No papers yet" in sidebar; upload prompt in main area.
- **Error**: Toast + retry button where applicable.
- **Offline**: No explicit offline detection; failed fetches show error toasts.

## Non-Functional

- Fast, minimal UI (ChatGPT/Claude style).
- Accessible: semantic HTML, ARIA where needed.
- Keyboard-friendly: tab order, Enter to submit.
- Responsive: sidebar + main area adapt to viewport.
